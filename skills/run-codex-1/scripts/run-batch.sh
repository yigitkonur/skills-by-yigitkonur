#!/usr/bin/env bash
# run-batch.sh — batch mode bounded-concurrency runner.
#
# For every prompts/<slug>.md, spawn a `codex exec` worker, write the last
# message to answers/<slug>.md, capture stdout/stderr to logs/<slug>.log.
# Idempotent: a non-empty answers/<slug>.md is treated as DONE and skipped.
# Atomic write: codex writes to a `<slug>.partial` file; we mv to the final
# answer path only on a clean non-empty exit. Crashes leave no answer file,
# so a re-run retries instead of treating partial output as complete.
#
# Monitor contract: emits one stdout line per state transition:
#   START <slug>      worker starting
#   DONE  <slug>      answer written successfully
#   FAIL  <slug>      codex exited non-zero OR produced empty output
#   SKIP  <slug>      pre-existing non-empty answer
# Final line: `--- all jobs finished ---`.
#
# Usage (both invocation styles work; flags win when both are given):
#   run-batch.sh                        # all defaults
#   JOBS=20 PROMPTS=p ANSWERS=a run-batch.sh
#   run-batch.sh --manifest m.json --prompts-dir p --answers-dir a \
#                --concurrency 8 --min-bytes 5000 [--only id,id] [--dry-run]
#   DRY_RUN=1 run-batch.sh              # print planned commands; do not invoke codex
#
# Inputs (env or flag; flag wins):
#   --concurrency N / JOBS=N      parallel concurrency (default 10; warns above 20)
#   --prompts-dir <p> / PROMPTS=p prompts dir (default ./prompts)
#   --answers-dir <a> / ANSWERS=a answers dir (default ./answers)
#   --logs-dir <l> / LOGS=l       per-job logs dir (default ./logs)
#   --manifest <m> / ORCHESTRATE_MANIFEST=m   path to manifest.json for status writes
#   --min-bytes N / MIN_BYTES=N   below_floor threshold (default 10000)
#   DRY_RUN=1                     print planned commands without invoking codex
#
# Manifest writes per entry (manifest-contract.md):
#   - log_path / jsonl_path / answer_path  (populated before each spawn)
#   - mode_state.answer_size_bytes / mode_state.below_floor (populated on
#     successful answer write)
#   - status / started_at / finished_at / attempts / exit_code / last_error
#
# Spawn flags: every codex spawn carries "${CODEX_FLAGS[@]}" + --json + -o.
# `--json` is paired with `-o` because MCP-active sessions can drop JSONL
# events silently (upstream issue 15451) — the answer file is the source of
# truth for "did codex produce output".
#
# Signal handling: a `trap 'kill 0' TERM INT EXIT` near top propagates SIGTERM
# from the runner down to xargs and every codex child. Killing this script
# leaves no orphan codex processes (verified against pgrep -f codex within 5s).
#
# Exit codes: 0 all jobs reached a terminal state, 1 prompts dir missing or
#             empty, 2 codex CLI missing, 3 JOBS=0 or invalid.

set -u

# ── Signal trap: on SIGTERM/SIGINT propagate to xargs children (and the
# codex CLIs they spawn) so a runner kill leaves no orphan codex processes.
# Bash defers traps while waiting on a foreground process — to avoid that
# we run xargs in the background at the bottom and use `wait`. EXIT is
# intentionally NOT in this trap (clean runs would otherwise also signal
# the pgid leader and exit 143).
#
# Hammer: BSD xargs on macOS doesn't propagate SIGTERM to its children, so
# `kill -TERM <xargs>` orphans the codex grandchildren. `pkill -TERM -g $$`
# signals every process in our process group; a brief 0.5s grace period;
# then `pkill -KILL -g $$` to ensure any straggler dies. The runner itself
# survives long enough to record state because it's sleeping in `wait` and
# the trap runs after `wait` returns.
_run_batch_signal() {
  trap - TERM INT
  if [[ -n "${_run_batch_xargs_pid:-}" ]]; then
    kill -TERM "$_run_batch_xargs_pid" 2>/dev/null || true
  fi
  # Process-group sweep — catches every descendant regardless of depth.
  pkill -TERM -g $$ 2>/dev/null || true
  sleep 0.5
  pkill -KILL -g $$ 2>/dev/null || true
  exit 143
}
trap _run_batch_signal TERM INT

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=codex-flags.sh
. "$SCRIPT_DIR/codex-flags.sh"

# Defaults sourced from env first; flag parser below overrides on demand.
JOBS="${JOBS:-10}"
PROMPTS="${PROMPTS:-prompts}"
ANSWERS="${ANSWERS:-answers}"
LOGS="${LOGS:-logs}"
DRY_RUN="${DRY_RUN:-0}"
ORCHESTRATE_MANIFEST="${ORCHESTRATE_MANIFEST:-}"
ONLY_IDS="${ONLY_IDS:-}"
RUNNER_LOG="${RUNNER_LOG:-}"
AUDIT_REPORT="${AUDIT_REPORT:-}"
MIN_BYTES="${MIN_BYTES:-10000}"
CONCURRENCY_JUSTIFICATION="${ORCHESTRATE_CONCURRENCY_JUSTIFICATION:-}"

# ── Flag parsing ───────────────────────────────────────────────
# Documented in run-batch.md / references/modes/batch.md. Both env-style and
# flag-style invocations work; flags win when both are given. Unknown args
# are rejected to surface typos early.

usage() {
  cat >&2 <<'EOF'
run-batch.sh — run rendered prompts through codex exec.

Usage:
  run-batch.sh --manifest <manifest.json> --prompts-dir <dir>
               --answers-dir <dir> --logs-dir <dir>
               [--concurrency N] [--min-bytes N] [--only id,id] [--dry-run]
               [--runner-log <file>] [--audit-report <file>]
               [--i-have-measured "<justification>"]

  Both env-style invocation (JOBS=10 PROMPTS=p ANSWERS=a run-batch.sh)
  and flag-style invocation are supported. Flags win when both are given.
EOF
  exit 3
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest) ORCHESTRATE_MANIFEST="$2"; shift 2 ;;
    # `--inputs` and `--template` are dispatcher-render-time concerns; the
    # runner consumes already-rendered prompts. Accept-and-ignore.
    --inputs|--template) shift 2 ;;
    --prompts-dir|--prompts) PROMPTS="$2"; shift 2 ;;
    --answers-dir|--answers) ANSWERS="$2"; shift 2 ;;
    --logs-dir|--logs) LOGS="$2"; shift 2 ;;
    --runner-log) RUNNER_LOG="$2"; shift 2 ;;
    --audit-report) AUDIT_REPORT="$2"; shift 2 ;;
    --min-bytes) MIN_BYTES="$2"; shift 2 ;;
    --concurrency|--jobs) JOBS="$2"; shift 2 ;;
    --only) ONLY_IDS="$2"; shift 2 ;;
    --i-have-measured) CONCURRENCY_JUSTIFICATION="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage ;;
    *)
      echo "unknown arg: $1" >&2
      usage
      ;;
  esac
done

# ── Pre-flight ─────────────────────────────────────────────────
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
if ! [[ "$MIN_BYTES" =~ ^[0-9]+$ ]]; then
  echo "FATAL MIN_BYTES must be a non-negative integer, got: $MIN_BYTES" >&2
  exit 3
fi

if ! command -v codex >/dev/null 2>&1 && [[ "$DRY_RUN" != "1" ]]; then
  echo "FATAL codex CLI not found on PATH" >&2
  exit 2
fi

# A missing or empty prompts dir is a configuration error, not a successful
# empty batch. Bail before printing the finished sentinel so the watcher
# cannot mistake the case for a clean run.
if [[ ! -d "$PROMPTS" ]]; then
  echo "FATAL prompts dir not found: $PROMPTS (run render-prompts.sh first)" >&2
  exit 1
fi
prompt_count="$(find "$PROMPTS" -maxdepth 1 -name '*.md' -type f | wc -l | tr -d ' ')"
if [[ "$prompt_count" -eq 0 ]]; then
  echo "FATAL no *.md prompts in $PROMPTS — render-prompts.sh produced nothing or the dir was wiped" >&2
  exit 1
fi

mkdir -p "$ANSWERS" "$LOGS"
# Bug 3 fix: do NOT tee runner stdout/stderr into $RUNNER_LOG here. The
# dispatcher (run-codex-1.mjs spawnRunnerDetached) is the canonical
# owner of the runner-log redirect — when the dispatcher launches the
# runner it opens $RUNNER_LOG and binds stdio to that fd, so every printed
# START/DONE/SKIP/FAIL line lands in the file once. A runner-side `tee` on
# top of that produced two copies of every line (audit-sizes.sh `grep -c`
# then over-counted by 2x). When the runner is invoked DIRECTLY by an
# operator (no dispatcher), there is no redirect — stdout flows to the
# terminal as expected.
if [[ -n "$RUNNER_LOG" ]]; then
  mkdir -p "$(dirname "$RUNNER_LOG")"
fi

# ── Per-job runner ─────────────────────────────────────────────
# Exported below so xargs subshells can call it. We pass `CODEX_FLAGS` as a
# newline-delimited string in CODEX_FLAGS_STR — bash exported arrays don't
# survive the `xargs bash -c` boundary on macOS bash 3.2.
run_one() {
  local prompt="$1"
  local name answer log jsonl tmp
  name="$(basename "$prompt" .md)"
  if [[ -n "$ONLY_IDS_LOCAL" && ",$ONLY_IDS_LOCAL," != *",$name,"* ]]; then
    return 0
  fi
  answer="$ANSWERS/${name}.md"
  log="$LOGS/${name}.log"
  jsonl="$LOGS/${name}.jsonl"
  # Partial filename matches run-batch.md: `<slug>.partial`, no leading dot.
  tmp="$ANSWERS/${name}.partial"

  # ── Idempotent skip ────────────────────────────────────────
  # When the answer already exists AND is non-empty, the entry is already
  # done. We MUST NOT demote a `done` entry to `skipped` — only flip to
  # `skipped` if the manifest entry was `queued`. (Otherwise a re-run after
  # the manifest landed `done` would silently rewrite history.)
  #
  # Exception: in DRY_RUN mode the answer file is a stub from a prior
  # dry-run; always re-execute to keep dry-run idempotent across rescue
  # redispatch (otherwise rescue --redo --dry-run would demote the entry to
  # skipped instead of re-running it).
  if [[ -s "$answer" && "$DRY_RUN" != "1" ]]; then
    echo "SKIP  $name"
    if [[ -n "$ORCHESTRATE_MANIFEST" && -x "$SCRIPT_DIR_ABS/manifest-update.sh" ]]; then
      local prior_status=""
      prior_status="$(jq -r --arg id "$name" '
        .entries[] | select(.id == $id) | .status // ""
      ' "$ORCHESTRATE_MANIFEST" 2>/dev/null || echo "")"
      if [[ "$prior_status" == "queued" || -z "$prior_status" ]]; then
        "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$name" \
          status=skipped finished_at=now 2>/dev/null || true
      fi
    fi
    return 0
  fi

  echo "START $name"
  if [[ -n "$ORCHESTRATE_MANIFEST" && -x "$SCRIPT_DIR_ABS/manifest-update.sh" ]]; then
    "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$name" \
      status=running started_at=now attempts=+1 \
      log_path="$log" \
      jsonl_path="$jsonl" \
      answer_path="$answer" 2>/dev/null || true
  fi

  # Reconstruct the array from the exported newline-delimited string.
  # NULs would be ideal but `$(...)` command substitution strips them; no
  # flag value in our policy contains a newline, so this is safe.
  local -a flags=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && flags+=("$f")
  done <<<"$CODEX_FLAGS_STR"

  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] codex exec ${flags[*]} --json -o $tmp < $prompt > $jsonl 2> $log"
    # Materialize stub artifacts so downstream tests see the expected files.
    printf 'dry-run answer for %s\n' "$name" > "$answer"
    printf '{"type":"turn.completed","dry_run":true}\n' > "$jsonl"
    echo "DONE  $name (dry-run)"
    if [[ -n "$ORCHESTRATE_MANIFEST" && -x "$SCRIPT_DIR_ABS/manifest-update.sh" ]]; then
      # P0-1: dry-run discriminator — see run-fleet.sh for rationale.
      "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$name" \
        status=done finished_at=now exit_code=0 dry_run=true 2>/dev/null || true
    fi
    return 0
  fi

  # Atomic write: codex writes to $tmp; we mv to $answer only on success.
  # `--json` produces JSONL events on stdout; we redirect them to the JSONL
  # log. stderr (auth errors, deprecation warnings) goes to the .log so the
  # JSONL stream stays parseable.
  if codex exec "${flags[@]}" --json -o "$tmp" < "$prompt" > "$jsonl" 2> "$log"; then
    if [[ -s "$tmp" ]]; then
      mv -f "$tmp" "$answer"
      local size below_floor
      size="$(wc -c < "$answer" | tr -d ' ')"
      if [[ "$size" -lt "$MIN_BYTES" ]]; then
        below_floor=true
        echo "DONE  $name ($size bytes) [SMALL]"
      else
        below_floor=false
        echo "DONE  $name ($size bytes)"
      fi
      if [[ -n "$ORCHESTRATE_MANIFEST" && -x "$SCRIPT_DIR_ABS/manifest-update.sh" ]]; then
        # mode_state.answer_size_bytes / mode_state.below_floor populated
        # per the manifest contract for batch mode. The dot-notation key is
        # forwarded directly into the jq filter by manifest-update.sh.
        "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$name" \
          status=done finished_at=now exit_code=0 \
          mode_state.answer_size_bytes="$size" \
          mode_state.below_floor="$below_floor" 2>/dev/null || true
      fi
    else
      rm -f "$tmp"
      echo "FAIL  $name (codex exited 0 but produced empty output; see $log)"
      if [[ -n "$ORCHESTRATE_MANIFEST" && -x "$SCRIPT_DIR_ABS/manifest-update.sh" ]]; then
        "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$name" \
          status=failed finished_at=now exit_code=0 last_error="empty output" 2>/dev/null || true
      fi
    fi
  else
    local rc=$?
    rm -f "$tmp"
    echo "FAIL  $name (exit=$rc; see $log)"
    if [[ -n "$ORCHESTRATE_MANIFEST" && -x "$SCRIPT_DIR_ABS/manifest-update.sh" ]]; then
      "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$name" \
        status=failed finished_at=now exit_code="$rc" last_error="codex exit $rc" 2>/dev/null || true
    fi
  fi
}

# Build the newline-delimited string of CODEX_FLAGS for export across the
# xargs subshell boundary (NULs get stripped by `$(...)`). We also pass
# through SCRIPT_DIR_ABS so the subshell can locate manifest-update.sh.
CODEX_FLAGS_STR="$(printf '%s\n' "${CODEX_FLAGS[@]}")"
SCRIPT_DIR_ABS="$SCRIPT_DIR"
export CODEX_FLAGS_STR SCRIPT_DIR_ABS ANSWERS LOGS DRY_RUN ORCHESTRATE_MANIFEST MIN_BYTES ONLY_IDS_LOCAL="$ONLY_IDS"
export -f run_one

# Fan-out via xargs. -0 (NUL-delimited) keeps filenames-with-spaces safe.
# We run the pipeline in the background and `wait` so bash can dispatch the
# TERM/INT trap immediately. The xargs PID is captured in
# _run_batch_xargs_pid so the trap can SIGTERM it directly.
find "$PROMPTS" -maxdepth 1 -name '*.md' -print0 \
  | xargs -0 -n 1 -P "$JOBS" bash -c 'run_one "$0"' &
_run_batch_xargs_pid=$!
wait "$_run_batch_xargs_pid"

if [[ -n "$AUDIT_REPORT" ]]; then
  mkdir -p "$(dirname "$AUDIT_REPORT")"
  "$SCRIPT_DIR/audit-sizes.sh" "$ANSWERS" "${RUNNER_LOG:-$LOGS/_runner.log}" "$MIN_BYTES" > "$AUDIT_REPORT" 2>&1 || true
  echo "[run-batch] audit report: $AUDIT_REPORT"
fi

echo "--- all jobs finished ---"
