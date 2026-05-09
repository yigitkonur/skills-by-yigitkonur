#!/usr/bin/env bash
# run-fleet.sh — exec mode bounded-concurrency runner.
#
# For every queued/failed entry in the manifest, spawn a worker that:
#   1. Calls setup-worktree.sh to create the per-task worktree.
#   2. Spawns `codex exec` with the universal CODEX_FLAGS, --json, -o, -C.
#   3. On success, auto-commits inside the worktree.
#   4. Optionally runs a post-verify. Per-task `mode_state.post_verify_cmd`
#      from the manifest wins; otherwise auto-detected:
#        - package.json + pnpm-lock.yaml → `pnpm test`
#        - package.json + bun.lockb      → `bun test`
#        - package.json + package-lock.json (or default) → `npm test`
#        - tsconfig.json (no package.json) → `npx --no-install tsc --noEmit`
#        - pyproject.toml | mypy.ini       → `mypy --strict .`
#        - Cargo.toml                       → `cargo check --quiet`
#        - go.mod                           → `go vet ./...`
#
# Idempotent: entries already `done` are skipped. Entries `failed` are retried.
#
# Monitor contract: emits one stdout line per state transition:
#   START <id>     worker starting
#   DONE  <id>     codex exited 0, commit landed (or no-changes commit-skip)
#   FAIL  <id>     codex exited non-zero OR no output OR commit failed
#   SKIP <id>      pre-existing `done` entry
# Final line: `--- all jobs finished ---`.
#
# Manifest writes per entry (manifest-contract.md):
#   - log_path / jsonl_path / answer_path   (populated before each spawn)
#   - mode_state.post_verify_cmd (resolved) / mode_state.post_verify_exit
#   - status / started_at / finished_at / attempts / exit_code / last_error
#   - codex_thread_id / worktree_path
#
# Usage:
#   run-fleet.sh --manifest <manifest.json> [--concurrency N] [--dry-run]
#
# The manifest's `entries[]` shape (relevant fields):
#   { id, slug, branch, base_branch?, prompt_path, worktree_path?, status,
#     mode_state: { task: { ... post_verify_cmd? } | post_verify_cmd? }, ... }
#
# Inputs (env):
#   JOBS              parallel concurrency (default reads manifest.policy.
#                     concurrency_cap → falls back to 5; warns above 20)
#   DRY_RUN           1 to print planned commands without invoking codex
#   PROJECT_DIR       repo root (default: cwd)
#   AUTO_COMMIT       1 to auto-commit on success (default: 1)
#   COMMIT_LEVEL      1 minimal | 2 standard | 3 verbose (default: 3)
#   POST_VERIFY       1 to run auto-detected post-verify (default: 1)
#   ORCHESTRATE_MODE  exported to setup-worktree.sh as `exec`
#
# Signal handling: a `trap 'kill 0' TERM INT EXIT` near top propagates SIGTERM
# from the runner down to xargs and every codex child. Killing this script
# leaves no orphan codex processes (verified against pgrep -f codex within 5s).
#
# Exit codes: 0 fleet ran (per-task failures recorded in manifest),
#             1 manifest missing or malformed, 2 codex/jq missing,
#             3 invalid JOBS or no queued entries.

set -u

# ── Signal trap: on SIGTERM/SIGINT propagate to xargs children (and the
# codex CLIs they spawn) so a runner kill leaves no orphan codex processes.
# Bash defers traps while waiting on a foreground process — to avoid that
# we run xargs in the background at the bottom of the script and use
# `wait`. EXIT is handled separately (worklist cleanup only).
_run_fleet_signal() {
  trap - TERM INT
  if [[ -n "${_run_fleet_xargs_pid:-}" ]]; then
    kill -TERM "$_run_fleet_xargs_pid" 2>/dev/null || true
  fi
  # Process-group sweep: BSD xargs on macOS doesn't propagate SIGTERM to
  # its children, so we hit every descendant via the pgid.
  pkill -TERM -g $$ 2>/dev/null || true
  sleep 0.5
  pkill -KILL -g $$ 2>/dev/null || true
  exit 143
}
trap _run_fleet_signal TERM INT

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=codex-flags.sh
. "$SCRIPT_DIR/codex-flags.sh"

DRY_RUN="${DRY_RUN:-0}"
# JOBS resolution: explicit env > manifest.policy.concurrency_cap (or
# top-level concurrency_cap) > built-in default of 5. The manifest hop is
# evaluated after we've validated the manifest exists and is JSON.
JOBS_DEFAULT=5
JOBS_ENV_SET="${JOBS+1}"
JOBS="${JOBS:-$JOBS_DEFAULT}"
PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
AUTO_COMMIT="${AUTO_COMMIT:-1}"
COMMIT_LEVEL="${COMMIT_LEVEL:-3}"
POST_VERIFY="${POST_VERIFY:-1}"
MANIFEST="${ORCHESTRATE_MANIFEST:-}"
ONLY_IDS="${ONLY_IDS:-}"
CONCURRENCY_JUSTIFICATION="${ORCHESTRATE_CONCURRENCY_JUSTIFICATION:-}"
export ORCHESTRATE_MODE="${ORCHESTRATE_MODE:-exec}"

usage() {
  echo "usage: $0 --manifest <manifest.json> [--concurrency N] [--only id,id] [--dry-run]" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest) MANIFEST="$2"; shift 2 ;;
    --concurrency|--jobs) JOBS="$2"; shift 2 ;;
    --project-dir) PROJECT_DIR="$2"; shift 2 ;;
    --only) ONLY_IDS="$2"; shift 2 ;;
    --i-have-measured) CONCURRENCY_JUSTIFICATION="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage ;;
    -*)
      echo "unknown arg: $1" >&2
      usage
      ;;
    *)
      if [[ -z "$MANIFEST" ]]; then MANIFEST="$1"; else usage; fi
      shift
      ;;
  esac
done

[[ -n "$MANIFEST" ]] || usage
export ORCHESTRATE_MANIFEST="$MANIFEST"

if [[ ! -f "$MANIFEST" ]]; then
  echo "FATAL manifest not found: $MANIFEST" >&2
  exit 1
fi
if ! jq -e . "$MANIFEST" >/dev/null 2>&1; then
  echo "FATAL manifest is not valid JSON: $MANIFEST" >&2
  exit 1
fi
# Absolute-ize the manifest path so worker subshells (which `cd` into per-
# task worktrees) still see the same file via $ORCHESTRATE_MANIFEST.
case "$MANIFEST" in
  /*) ;;
  *)  MANIFEST="$(cd "$(dirname "$MANIFEST")" && pwd -P)/$(basename "$MANIFEST")" ;;
esac

if ! command -v codex >/dev/null 2>&1 && [[ "$DRY_RUN" != "1" ]]; then
  echo "FATAL codex CLI not found on PATH" >&2
  exit 2
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "FATAL jq not found on PATH" >&2
  exit 2
fi

# If the operator didn't pin JOBS in the env, prefer the manifest's
# effective concurrency_cap (set by the dispatcher). This is what makes
# `JOBS=3` from the env genuinely override and a missing JOBS pick up the
# dispatcher's seed instead of the static `5`.
if [[ "$JOBS_ENV_SET" != "1" ]]; then
  manifest_cap="$(jq -r '
    (.policy.concurrency_cap // .concurrency_cap // empty)
    | tostring
  ' "$MANIFEST" 2>/dev/null)"
  if [[ -n "$manifest_cap" && "$manifest_cap" =~ ^[1-9][0-9]*$ ]]; then
    JOBS="$manifest_cap"
  fi
fi

if ! [[ "$JOBS" =~ ^[1-9][0-9]*$ ]]; then
  echo "FATAL JOBS must be a positive integer, got: $JOBS" >&2
  exit 3
fi
if [[ "$JOBS" -gt 100 ]]; then
  echo "FATAL JOBS=$JOBS exceeds hard cap of 100" >&2
  exit 3
fi
if [[ "$JOBS" -gt 20 && -z "$CONCURRENCY_JUSTIFICATION" ]]; then
  echo "FATAL JOBS=$JOBS exceeds 20; pass --i-have-measured <justification>" >&2
  exit 3
fi

# ── Build the work list — queued + failed entries only ─────────
# Each row: id<TAB>slug<TAB>branch<TAB>base_branch<TAB>prompt_path<TAB>worktree_path<TAB>status
WORKLIST="$(mktemp)"
# Resource cleanup on EXIT (separate from signal propagation above).
trap 'rm -f "$WORKLIST"' EXIT

jq -r '
  .entries[]
  | [
      .id,
      (.slug // .id),
      (.branch // .id),
      (.base_branch // "main"),
      (.prompt_path // ""),
      (.worktree_path // ""),
      (.status // "queued")
    ]
  | @tsv
' "$MANIFEST" > "$WORKLIST"

if [[ -n "$ONLY_IDS" ]]; then
  FILTERED="$(mktemp)"
  awk -F'\t' -v only="$ONLY_IDS" '
    BEGIN { n = split(only, ids, ","); for (i = 1; i <= n; i++) wanted[ids[i]] = 1 }
    wanted[$1]
  ' "$WORKLIST" > "$FILTERED"
  mv "$FILTERED" "$WORKLIST"
fi

if [[ ! -s "$WORKLIST" ]]; then
  echo "FATAL no entries in manifest: $MANIFEST" >&2
  exit 3
fi

queued_count="$(awk -F'\t' '$7 == "queued" || $7 == "failed" { c++ } END { print c+0 }' "$WORKLIST")"
done_count="$(awk -F'\t' '$7 == "done" { c++ } END { print c+0 }' "$WORKLIST")"
echo "[run-fleet] manifest: $MANIFEST"
echo "[run-fleet] entries: $(wc -l < "$WORKLIST" | tr -d ' ') total / $queued_count to run / $done_count already done"

# ── Per-task runner ────────────────────────────────────────────
# Inputs: TSV row on stdin (one task per line). Reads CODEX_FLAGS_STR for
# the spawn flags + AUTO_COMMIT/COMMIT_LEVEL/POST_VERIFY for commit logic.
run_one() {
  local row="$1"
  IFS=$'\t' read -r id slug branch base prompt_path wt_path status <<<"$row"

  # Idempotent skip
  if [[ "$status" == "done" ]]; then
    echo "SKIP  $id"
    return 0
  fi

  if [[ -z "$prompt_path" || ! -f "$prompt_path" ]]; then
    echo "FAIL  $id (prompt_path not found: '$prompt_path')"
    "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
      status=failed finished_at=now last_error="prompt missing: $prompt_path" 2>/dev/null || true
    return 1
  fi

  echo "START $id"
  "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
    status=running started_at=now attempts=+1 2>/dev/null || true

  # ── 1. Setup worktree ────────────────────────────────────────
  local wt_resolved=""
  if [[ -n "$wt_path" && -d "$wt_path" ]]; then
    wt_resolved="$wt_path"
  else
    if [[ "$DRY_RUN_LOCAL" == "1" ]]; then
      wt_resolved="<dry-run-wt>/$slug"
    else
      local setup_out
      if ! setup_out="$(ALLOW_REUSE=1 "$SCRIPT_DIR_ABS/setup-worktree.sh" "$slug" "$branch" "$base" 2>&1)"; then
        echo "FAIL  $id (setup-worktree failed)"
        printf '%s\n' "$setup_out" | sed 's/^/  [setup] /'
        "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
          status=failed finished_at=now last_error="setup-worktree failed" 2>/dev/null || true
        return 1
      fi
      # Extract WORKTREE_PATH=... from setup-worktree's stdout
      wt_resolved="$(printf '%s\n' "$setup_out" | awk -F= '/^WORKTREE_PATH=/ { sub(/^WORKTREE_PATH=/, ""); print; exit }')"
      if [[ -z "$wt_resolved" ]]; then
        echo "FAIL  $id (could not parse WORKTREE_PATH from setup-worktree)"
        "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
          status=failed finished_at=now last_error="setup-worktree parse failed" 2>/dev/null || true
        return 1
      fi
    fi
  fi

  # Persist the worktree_path back into the manifest so a re-run can find it.
  "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
    worktree_path="$wt_resolved" 2>/dev/null || true

  # ── 2. Compose log + jsonl + answer paths ───────────────────
  # The manifest contract requires log_path / jsonl_path / answer_path on
  # every entry. We honour any value the dispatcher already wrote; otherwise
  # we synthesise paths under monitor_root/<run_id> (the dispatcher's per-
  # run logs dir) and fall back to the worktree's .orchestrate-codex dir if
  # monitor_root is missing.
  local log_path jsonl_path answer_path monitor_root run_id base_dir
  log_path="$(jq -r --arg id "$id" '.entries[] | select(.id == $id) | .log_path // ""' "$ORCHESTRATE_MANIFEST")"
  jsonl_path="$(jq -r --arg id "$id" '.entries[] | select(.id == $id) | .jsonl_path // ""' "$ORCHESTRATE_MANIFEST")"
  answer_path="$(jq -r --arg id "$id" '.entries[] | select(.id == $id) | .answer_path // ""' "$ORCHESTRATE_MANIFEST")"
  monitor_root="$(jq -r '.monitor_root // ""' "$ORCHESTRATE_MANIFEST")"
  run_id="$(jq -r '.run_id // ""' "$ORCHESTRATE_MANIFEST")"
  if [[ -n "$monitor_root" ]]; then
    if [[ -n "$run_id" ]]; then
      base_dir="$monitor_root/logs/$run_id"
    else
      base_dir="$monitor_root/logs"
    fi
  else
    base_dir="$wt_resolved/.orchestrate-codex"
  fi
  [[ -z "$log_path"    ]] && log_path="$base_dir/$id.log"
  [[ -z "$jsonl_path"  ]] && jsonl_path="$base_dir/$id.jsonl"
  [[ -z "$answer_path" ]] && answer_path="$base_dir/$id.last.md"
  mkdir -p "$(dirname "$log_path")" "$(dirname "$jsonl_path")" "$(dirname "$answer_path")"

  # Persist the resolved paths back into the manifest entry per the
  # manifest contract. The runner only does this once per entry — these
  # paths are derived from a stable `<id>` and don't change across retries.
  "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
    log_path="$log_path" \
    jsonl_path="$jsonl_path" \
    answer_path="$answer_path" 2>/dev/null || true

  # ── 3. Reconstruct CODEX_FLAGS array in the subshell ─────────
  # Bash arrays don't survive `xargs bash -c` boundaries directly. We pass
  # a newline-delimited string (CODEX_FLAGS_STR) — no flag value in our
  # policy contains a newline, so this is safe. NULs would be ideal but
  # `$(...)` command substitution strips them.
  local -a flags=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && flags+=("$f")
  done <<<"$CODEX_FLAGS_STR"

  # ── 4. Spawn codex exec ──────────────────────────────────────
  if [[ "$DRY_RUN_LOCAL" == "1" ]]; then
    echo "[dry-run] codex exec ${flags[*]} --json -C $wt_resolved -o $answer_path < $prompt_path > $jsonl_path 2> $log_path"
    # Materialize stub artifacts so downstream tests / manifest writes see
    # the expected files. The runner contract says answer_path must be
    # non-empty for status=done; this preserves that invariant in dry-run.
    printf 'dry-run answer for %s\n' "$id" > "$answer_path"
    printf '{"type":"turn.completed","dry_run":true}\n' > "$jsonl_path"
    echo "DONE  $id (dry-run)"
    "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
      status=done finished_at=now exit_code=0 verify_status=dry-run 2>/dev/null || true
    return 0
  fi

  local start_ts end_ts elapsed exit_code thread_id=""
  start_ts="$(date +%s)"
  # `codex exec --json` writes JSONL events to stdout → jsonl_path.
  # stderr (auth errors, deprecation warnings, panics) → log_path.
  # `-o` writes the final agent message to answer_path. `-C` pins cwd.
  if codex exec "${flags[@]}" --json -C "$wt_resolved" -o "$answer_path" < "$prompt_path" > "$jsonl_path" 2> "$log_path"; then
    exit_code=0
  else
    exit_code=$?
  fi
  end_ts="$(date +%s)"
  elapsed=$(( end_ts - start_ts ))

  # Parse thread_id from the JSONL stream (first thread.started event)
  if [[ -f "$jsonl_path" ]]; then
    thread_id="$(grep -m1 '"type":"thread.started"' "$jsonl_path" 2>/dev/null \
                  | jq -r '.thread_id // ""' 2>/dev/null || echo "")"
  fi
  if [[ -n "$thread_id" ]]; then
    "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
      codex_thread_id="$thread_id" 2>/dev/null || true
  fi

  if [[ "$exit_code" -ne 0 ]]; then
    echo "FAIL  $id (codex exit=$exit_code; runtime=${elapsed}s; see $log_path)"
    "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
      status=failed finished_at=now exit_code="$exit_code" last_error="codex exit $exit_code" 2>/dev/null || true
    return 1
  fi

  # Empty answer file is a soft failure (advisory) — JSONL drop possible
  # under MCP. Only flag as failed if BOTH the JSONL stream and the answer
  # file are empty.
  if [[ ! -s "$answer_path" ]]; then
    if [[ -s "$jsonl_path" || -s "$log_path" ]]; then
      echo "FAIL  $id (codex exit=0 but answer file empty; see $jsonl_path / $log_path)"
      "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
        status=failed finished_at=now exit_code=0 last_error="empty answer" 2>/dev/null || true
      return 1
    fi
  fi

  # ── 5. Auto-commit ──
  if [[ "$AUTO_COMMIT" == "1" ]]; then
    local commit_summary commit_stats commit_msg files
    commit_summary="$(head -1 < "$prompt_path" | cut -c1-60)"
    [[ -z "$commit_summary" ]] && commit_summary="$id"

    if (cd "$wt_resolved" && git diff --quiet && git diff --cached --quiet); then
      echo "[run-fleet] $id: no changes to commit"
    else
      (cd "$wt_resolved" && git add -A) || true

      case "$COMMIT_LEVEL" in
        1)
          (cd "$wt_resolved" && git commit -m "agent($id): $commit_summary [auto]" >/dev/null 2>&1) || {
            echo "FAIL  $id (commit failed)"
            "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
              status=failed finished_at=now last_error="commit failed" 2>/dev/null || true
            return 1
          }
          ;;
        2)
          commit_stats="$(cd "$wt_resolved" && git diff --cached --stat | tail -1)"
          (cd "$wt_resolved" && git commit -m "agent($id): $commit_summary

Stats:    $commit_stats
Runtime:  ${elapsed}s
Branch:   $branch
Source:   codex exec ($CODEX_MODEL $CODEX_EFFORT)" >/dev/null 2>&1) || {
            echo "FAIL  $id (commit failed)"
            "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
              status=failed finished_at=now last_error="commit failed" 2>/dev/null || true
            return 1
          }
          ;;
        3|*)
          commit_stats="$(cd "$wt_resolved" && git diff --cached --stat)"
          files="$(cd "$wt_resolved" && git diff --cached --name-only | head -10 | tr '\n' ',' | sed 's/,$//')"
          commit_msg="agent($id): $commit_summary

Branch:    $branch
Runtime:   ${elapsed}s
Files:     $files
Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)

--- diff stats ---
$commit_stats

Source:    codex exec ($CODEX_MODEL $CODEX_EFFORT)"
          (cd "$wt_resolved" && git commit -m "$commit_msg" >/dev/null 2>&1) || {
            echo "FAIL  $id (commit failed)"
            "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
              status=failed finished_at=now last_error="commit failed" 2>/dev/null || true
            return 1
          }
          ;;
      esac
    fi
  fi

  # ── 6. Post-verify (per-task override > auto-detect, advisory) ──
  # Resolution order:
  #   1. Manifest entry's mode_state.post_verify_cmd (set by the dispatcher
  #      from tasks.json). This is the ground-truth per-task override.
  #   2. Manifest entry's mode_state.task.post_verify_cmd (alternate shape
  #      used when the dispatcher nests under .task).
  #   3. Auto-detect from project files in the worktree:
  #        package.json + lockfile  → pnpm/bun/npm test
  #        tsconfig.json (no pkg)   → npx --no-install tsc --noEmit
  #        pyproject.toml | mypy.ini→ mypy --strict .
  #        Cargo.toml               → cargo check --quiet
  #        go.mod                   → go vet ./...
  #   4. Nothing — verify_status stays "not-run".
  # `verify_status` and `mode_state.post_verify_exit` are advisory; they
  # never demote a successful codex spawn to `failed`.
  local verify_status="not-run"
  local pv_exit="null"
  if [[ "$POST_VERIFY" == "1" ]]; then
    local pv_cmd=""
    pv_cmd="$(jq -r --arg id "$id" '
      .entries[]
      | select(.id == $id)
      | (.mode_state.post_verify_cmd
         // .mode_state.task.post_verify_cmd
         // "")
    ' "$ORCHESTRATE_MANIFEST" 2>/dev/null || echo "")"
    if [[ -z "$pv_cmd" ]]; then
      if   [[ -f "$wt_resolved/package.json" ]]; then
        # Lockfile preference: pnpm > bun > npm. Fall back to npm test if no
        # lockfile is present (handles freshly scaffolded projects).
        if   [[ -f "$wt_resolved/pnpm-lock.yaml" ]] && command -v pnpm >/dev/null 2>&1; then
          pv_cmd="pnpm test"
        elif [[ -f "$wt_resolved/bun.lockb" ]] && command -v bun >/dev/null 2>&1; then
          pv_cmd="bun test"
        elif command -v npm >/dev/null 2>&1; then
          pv_cmd="npm test --silent"
        fi
      elif [[ -f "$wt_resolved/tsconfig.json" ]] && command -v npx >/dev/null 2>&1; then
        pv_cmd="npx --no-install tsc --noEmit"
      elif [[ -f "$wt_resolved/pyproject.toml" || -f "$wt_resolved/mypy.ini" ]] && command -v mypy >/dev/null 2>&1; then
        pv_cmd="mypy --strict ."
      elif [[ -f "$wt_resolved/Cargo.toml" ]] && command -v cargo >/dev/null 2>&1; then
        pv_cmd="cargo check --quiet"
      elif [[ -f "$wt_resolved/go.mod" ]] && command -v go >/dev/null 2>&1; then
        pv_cmd="go vet ./..."
      fi
    fi
    if [[ -n "$pv_cmd" ]]; then
      if (cd "$wt_resolved" && eval "$pv_cmd" >/dev/null 2>&1); then
        verify_status="pass"
        pv_exit=0
      else
        local rc=$?
        verify_status="fail"
        pv_exit="$rc"
      fi
      # Persist the resolved command + exit code on mode_state so audit
      # and rescue can reconstruct what was actually run.
      "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
        mode_state.post_verify_cmd="$pv_cmd" \
        mode_state.post_verify_exit="$pv_exit" 2>/dev/null || true
    fi
  fi

  echo "DONE  $id (runtime=${elapsed}s verify=$verify_status)"
  "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
    status=done finished_at=now exit_code=0 verify_status="$verify_status" 2>/dev/null || true
}

# Export for xargs subshells. CODEX_FLAGS_STR is newline-delimited (NULs get
# stripped by `$(...)`); no flag value contains a newline so this is safe.
CODEX_FLAGS_STR="$(printf '%s\n' "${CODEX_FLAGS[@]}")"
export CODEX_FLAGS_STR
export SCRIPT_DIR_ABS="$SCRIPT_DIR"
export ORCHESTRATE_MANIFEST="$MANIFEST"
export PROJECT_DIR AUTO_COMMIT COMMIT_LEVEL POST_VERIFY CODEX_MODEL CODEX_EFFORT
export DRY_RUN_LOCAL="$DRY_RUN"
export -f run_one

# ── Fan-out via xargs over the worklist ────────────────────────
# Skip the `done` rows up front so xargs only schedules real work. Running
# in the background + `wait` lets bash dispatch TERM/INT traps immediately
# (otherwise traps queue until the foreground job returns).
awk -F'\t' '$7 != "done"' "$WORKLIST" \
  | tr '\n' '\0' \
  | xargs -0 -n 1 -P "$JOBS" bash -c 'run_one "$0"' &
_run_fleet_xargs_pid=$!
wait "$_run_fleet_xargs_pid"

echo "--- all jobs finished ---"
