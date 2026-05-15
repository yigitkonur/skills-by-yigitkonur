#!/usr/bin/env bash
# _lib.sh — shared bash helpers for orchestrate-codex runners.
#
# Source (don't execute) from every runner:
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   source "$SCRIPT_DIR/_lib.sh"
#
# Exposes:
#   oc_load_constants                # reads constants.json into OC_* env
#   oc_source_codex_flags            # sources codex-flags.sh + serializes arrays to CODEX_FLAGS_STR
#   oc_install_signal_trap NAME PID  # SIGTERM/SIGINT → pkill -g $$ → exit 143
#   oc_manifest_set MANIFEST ID K=V… # shells to python3 manifest-update.py --execute
#   oc_monitor_emit LINE             # stdout + tee to OC_RUN_LEDGER
#   oc_log_run_ledger LEVEL MSG …    # structured event line
#   oc_concurrency_check             # JOBS policy enforcement
#   oc_compute_slug PATH             # delegates to python3 _lib.py for cross-lang parity
#   oc_acquire_run_lock              # optional per-run lock for tests
#
# Bash 3.2-compatible (macOS default). No associative arrays, no mapfile.
#
# CI gate: callers must NOT use the legacy "2>/dev/null || true" silencer.
# Replace with: SOMECMD 2>> "$OC_RUN_LEDGER" || oc_log_run_ledger ERROR "..."

# Idempotency guard
if [[ -n "${ORCHESTRATE_LIB_LOADED:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
ORCHESTRATE_LIB_LOADED=1

# Resolve our own directory for sibling lookups (codex-flags.sh, constants.json, manifest-update.py)
OC_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export OC_LIB_DIR

# ---------------------------------------------------------------------------
# Constants loader
# ---------------------------------------------------------------------------
oc_load_constants() {
  local constants="${OC_LIB_DIR}/constants.json"
  if [[ ! -f "$constants" ]]; then
    echo "_lib.sh: constants.json missing at $constants" >&2
    return 1
  fi
  # Use jq to read individual fields; export as OC_* env vars.
  if ! command -v jq >/dev/null 2>&1; then
    echo "_lib.sh: jq is required" >&2
    return 1
  fi
  OC_SCHEMA_VERSION="$(jq -r '.schema_version' "$constants")"
  OC_LOCK_TIMEOUT_SEC="$(jq -r '.lock_timeout_seconds' "$constants")"
  OC_MONITOR_HARD_MAX_MS="$(jq -r '.monitor_hard_max_ms' "$constants")"
  OC_CONCURRENCY_SOFT_CAP="$(jq -r '.concurrency.soft_cap' "$constants")"
  OC_CONCURRENCY_HARD_CAP="$(jq -r '.concurrency.hard_cap' "$constants")"
  OC_EXEC_DEFAULT_JOBS="$(jq -r '.concurrency.defaults.exec' "$constants")"
  OC_BATCH_DEFAULT_JOBS="$(jq -r '.concurrency.defaults.batch' "$constants")"
  OC_SINGLE_DEFAULT_JOBS="$(jq -r '.concurrency.defaults.single' "$constants")"
  OC_REVIEW_DEFAULT_JOBS="$(jq -r '.concurrency.defaults.review' "$constants")"
  OC_AUDIT_MIN_BYTES_DEFAULT="$(jq -r '.audit.min_bytes_default' "$constants")"
  OC_MONITOR_INTERVAL_DEFAULT="$(jq -r '.monitor.interval_default_sec' "$constants")"
  OC_REVIEW_ROUND_SOFT_CAP="$(jq -r '.review.round_soft_cap' "$constants")"
  OC_CODEX_MODEL_DEFAULT="$(jq -r '.codex.model_default' "$constants")"
  OC_CODEX_EFFORT_DEFAULT="$(jq -r '.codex.effort_default' "$constants")"
  OC_EXIT_BAD_INPUT="$(jq -r '.exit_codes.bad_input' "$constants")"
  OC_EXIT_ENVIRONMENTAL="$(jq -r '.exit_codes.environmental' "$constants")"
  OC_EXIT_LOCK_OR_WRITE="$(jq -r '.exit_codes.lock_or_write_failed' "$constants")"
  OC_EXIT_MISSING_DEP="$(jq -r '.exit_codes.missing_dependency' "$constants")"
  OC_EXIT_WORKTREE_HOOK="$(jq -r '.exit_codes.worktree_setup_hook_failed' "$constants")"
  OC_EXIT_SIGNAL="$(jq -r '.exit_codes.signal' "$constants")"
  export OC_SCHEMA_VERSION OC_LOCK_TIMEOUT_SEC OC_MONITOR_HARD_MAX_MS
  export OC_CONCURRENCY_SOFT_CAP OC_CONCURRENCY_HARD_CAP
  export OC_EXEC_DEFAULT_JOBS OC_BATCH_DEFAULT_JOBS OC_SINGLE_DEFAULT_JOBS OC_REVIEW_DEFAULT_JOBS
  export OC_AUDIT_MIN_BYTES_DEFAULT OC_MONITOR_INTERVAL_DEFAULT OC_REVIEW_ROUND_SOFT_CAP
  export OC_CODEX_MODEL_DEFAULT OC_CODEX_EFFORT_DEFAULT
  export OC_EXIT_BAD_INPUT OC_EXIT_ENVIRONMENTAL OC_EXIT_LOCK_OR_WRITE OC_EXIT_MISSING_DEP
  export OC_EXIT_WORKTREE_HOOK OC_EXIT_SIGNAL
}

# ---------------------------------------------------------------------------
# Codex flags loader + array serialization
# ---------------------------------------------------------------------------
oc_source_codex_flags() {
  if [[ -n "${ORCHESTRATE_CODEX_FLAGS_LOADED:-}" ]]; then
    return 0
  fi
  source "${OC_LIB_DIR}/codex-flags.sh"
  # Serialize CODEX_FLAGS array to a newline-delimited string for cross-`bash -c`
  # propagation. Bash arrays don't survive subshell boundaries; export the string
  # form so xargs subshells can reconstruct: `IFS=$'\n' read -r -d '' -a FLAGS <<<"$CODEX_FLAGS_STR"`
  local i flag
  CODEX_FLAGS_STR=""
  for flag in "${CODEX_FLAGS[@]}"; do
    [[ -n "$flag" ]] && CODEX_FLAGS_STR="${CODEX_FLAGS_STR}${flag}"$'\n'
  done
  CODEX_REVIEW_FLAGS_STR=""
  for flag in "${CODEX_REVIEW_FLAGS[@]}"; do
    [[ -n "$flag" ]] && CODEX_REVIEW_FLAGS_STR="${CODEX_REVIEW_FLAGS_STR}${flag}"$'\n'
  done
  export CODEX_FLAGS_STR CODEX_REVIEW_FLAGS_STR
}

# Reconstruct an array from a CODEX_*_STR string inside a subshell.
# Usage:
#   declare -a FLAGS
#   oc_unmarshal_flags FLAGS "$CODEX_FLAGS_STR"
oc_unmarshal_flags() {
  local out_name="$1"
  local str="$2"
  local line
  eval "$out_name=()"
  while IFS= read -r line; do
    [[ -n "$line" ]] && eval "${out_name}+=(\"\$line\")"
  done <<<"$str"
}

# ---------------------------------------------------------------------------
# Signal handler
# ---------------------------------------------------------------------------
# Installs a named TERM/INT handler that sweeps the process group and exits 143.
# Usage:
#   oc_install_signal_trap "run_fleet" XARGS_PID
# (where XARGS_PID is the variable name holding the xargs pid; can be empty if no xargs)
oc_install_signal_trap() {
  local handler_name="$1"
  local xargs_pid_var="${2:-}"
  # Define the trap handler as a function. Use a closure-like pattern by embedding
  # the xargs pid variable name into the function body.
  eval "_oc_signal_handler_${handler_name}() {
    trap '' TERM INT
    if [[ -n \"${xargs_pid_var}\" ]] && [[ -n \"\${${xargs_pid_var}:-}\" ]]; then
      kill -TERM \"\${${xargs_pid_var}}\" 2>/dev/null
    fi
    pkill -TERM -g \$\$ 2>/dev/null
    sleep 0.5
    pkill -KILL -g \$\$ 2>/dev/null
    exit 143
  }"
  trap "_oc_signal_handler_${handler_name}" TERM INT
}

# ---------------------------------------------------------------------------
# Run-ledger structured logging (replaces `2>/dev/null || true`)
# ---------------------------------------------------------------------------
oc_log_run_ledger() {
  local level="$1"
  local msg="$2"
  shift 2
  local path="${OC_RUN_LEDGER:-}"
  [[ -z "$path" ]] && return 0
  local ts
  ts="$(date -u +%H:%M:%SZ)"
  local source
  source="$(basename -- "${BASH_SOURCE[1]:-${0:-unknown}}")"
  local kv=""
  local pair
  for pair in "$@"; do
    kv="${kv} ${pair}"
  done
  mkdir -p "$(dirname -- "$path")" 2>/dev/null
  printf '%s [%s] %s: %s%s\n' "$ts" "$level" "$source" "$msg" "$kv" >> "$path" 2>/dev/null
}

# ---------------------------------------------------------------------------
# Monitor stdout emission with ledger tee
# ---------------------------------------------------------------------------
oc_monitor_emit() {
  local line="$1"
  printf '%s\n' "$line"
  [[ -n "${OC_RUN_LEDGER:-}" ]] && oc_log_run_ledger INFO "monitor_line" line="$line"
}

# ---------------------------------------------------------------------------
# Manifest write wrapper (Python-only)
# ---------------------------------------------------------------------------
# Shell to python3 manifest-update.py entry --execute …
# Failures land in the run ledger; the runner continues.
#
# Usage:
#   oc_manifest_set <manifest> <entry-id> KEY=VALUE [KEY=VALUE ...]
oc_manifest_set() {
  local manifest="$1"
  local entry_id="$2"
  shift 2
  local set_args=()
  local pair
  for pair in "$@"; do
    set_args+=("--set" "$pair")
  done
  local mu="${OC_LIB_DIR}/manifest-update.py"
  if ! python3 "$mu" entry --manifest "$manifest" --entry "$entry_id" \
      "${set_args[@]}" --execute 2>> "${OC_RUN_LEDGER:-/dev/null}"; then
    oc_log_run_ledger ERROR "manifest_set_failed" entry="$entry_id" rc=$?
    return 1
  fi
  return 0
}

# Top-level manifest mutation (no entry; for run-level fields).
oc_manifest_top_set() {
  local manifest="$1"
  shift
  local set_args=()
  local pair
  for pair in "$@"; do
    set_args+=("--set" "$pair")
  done
  local mu="${OC_LIB_DIR}/manifest-update.py"
  if ! python3 "$mu" top --manifest "$manifest" \
      "${set_args[@]}" --execute 2>> "${OC_RUN_LEDGER:-/dev/null}"; then
    oc_log_run_ledger ERROR "manifest_top_set_failed" rc=$?
    return 1
  fi
  return 0
}

# ---------------------------------------------------------------------------
# Concurrency policy check (JOBS env enforcement)
# ---------------------------------------------------------------------------
# Reads JOBS env; refuses 0 / non-numeric / > hard cap; requires
# ORCHESTRATE_CONCURRENCY_JUSTIFICATION above soft cap.
# Defaults JOBS to the per-mode default if unset.
#
# Usage:
#   ORCHESTRATE_MODE=exec oc_concurrency_check
oc_concurrency_check() {
  local mode="${ORCHESTRATE_MODE:-exec}"
  local default_jobs
  case "$mode" in
    exec)   default_jobs="$OC_EXEC_DEFAULT_JOBS";;
    batch)  default_jobs="$OC_BATCH_DEFAULT_JOBS";;
    single) default_jobs="$OC_SINGLE_DEFAULT_JOBS";;
    review) default_jobs="$OC_REVIEW_DEFAULT_JOBS";;
    *)      default_jobs="$OC_EXEC_DEFAULT_JOBS";;
  esac
  : "${JOBS:=$default_jobs}"
  if ! [[ "$JOBS" =~ ^[1-9][0-9]*$ ]]; then
    echo "FATAL JOBS must be a positive integer (got '$JOBS')" >&2
    return "${OC_EXIT_ENVIRONMENTAL:-3}"
  fi
  if (( JOBS > OC_CONCURRENCY_HARD_CAP )); then
    echo "FATAL JOBS=$JOBS exceeds hard cap ($OC_CONCURRENCY_HARD_CAP)" >&2
    return "${OC_EXIT_ENVIRONMENTAL:-3}"
  fi
  if (( JOBS > OC_CONCURRENCY_SOFT_CAP )); then
    if [[ -z "${ORCHESTRATE_CONCURRENCY_JUSTIFICATION:-}" ]]; then
      echo "FATAL JOBS=$JOBS exceeds soft cap ($OC_CONCURRENCY_SOFT_CAP); pass --i-have-measured \"<reason>\"" >&2
      return "${OC_EXIT_ENVIRONMENTAL:-3}"
    fi
    oc_log_run_ledger INFO "concurrency_override" jobs=$JOBS reason="${ORCHESTRATE_CONCURRENCY_JUSTIFICATION}"
  fi
  export JOBS
  return 0
}

# ---------------------------------------------------------------------------
# Slug derivation (delegates to _lib.py for cross-language parity)
# ---------------------------------------------------------------------------
oc_compute_slug() {
  local path="$1"
  python3 "${OC_LIB_DIR}/_lib.py" --slug-for="$path"
}

# ---------------------------------------------------------------------------
# Optional per-run lock (for tests)
# ---------------------------------------------------------------------------
oc_acquire_run_lock() {
  local lockfile="${1:-/tmp/orchestrate-codex-test.lock}"
  exec 9>>"$lockfile"
  if command -v flock >/dev/null 2>&1; then
    if ! flock -n 9; then
      echo "oc_acquire_run_lock: $lockfile is held by another process" >&2
      return 1
    fi
  fi
  return 0
}

# ---------------------------------------------------------------------------
# Self-test entry point: `bash _lib.sh --verify-fixtures`
# ---------------------------------------------------------------------------
if [[ "${BASH_SOURCE[0]}" == "$0" ]] && [[ "${1:-}" == "--verify-fixtures" ]]; then
  oc_load_constants || exit 1
  echo "_lib.sh: constants loaded; OC_LOCK_TIMEOUT_SEC=$OC_LOCK_TIMEOUT_SEC OC_CONCURRENCY_SOFT_CAP=$OC_CONCURRENCY_SOFT_CAP"
  # Verify slug derivation matches Python (cross-language fixture)
  py_slug="$(python3 "${OC_LIB_DIR}/_lib.py" --slug-for=/tmp/test-repo)"
  sh_slug="$(oc_compute_slug /tmp/test-repo)"
  if [[ "$py_slug" != "$sh_slug" ]]; then
    echo "FAIL slug derivation mismatch: py=$py_slug sh=$sh_slug" >&2
    exit 1
  fi
  echo "_lib.sh: cross-language slug parity OK ($sh_slug)"
  exit 0
fi

# When sourced, exit cleanly without running self-test
return 0 2>/dev/null || true
