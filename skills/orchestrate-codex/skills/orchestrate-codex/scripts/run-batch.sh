#!/usr/bin/env bash
# run-batch.sh — batch mode bounded-concurrency runner.
#
# For every prompts/<slug>.md, spawn a `codex exec` worker, write the last
# message to answers/<slug>.md, capture stdout/stderr to logs/<slug>.log.
# Idempotent: a non-empty answers/<slug>.md is treated as DONE and skipped.
# Atomic write: codex writes to a `.partial` file; we mv to the final answer
# path only on a clean non-empty exit. Crashes leave no answer file, so a
# re-run retries instead of treating partial output as complete.
#
# Monitor contract: emits one stdout line per state transition:
#   START <slug>      worker starting
#   DONE  <slug>      answer written successfully
#   FAIL  <slug>      codex exited non-zero OR produced empty output
#   SKIP  <slug>      pre-existing non-empty answer
# Final line: `--- all jobs finished ---`.
#
# Usage:
#   run-batch.sh                # default JOBS=10, ./prompts → ./answers
#   JOBS=20 PROMPTS=p ANSWERS=a run-batch.sh
#   DRY_RUN=1 run-batch.sh      # print planned commands; do not invoke codex
#
# Inputs (env):
#   JOBS         parallel concurrency (default 10; warns above 20)
#   PROMPTS      prompts dir (default ./prompts)
#   ANSWERS      answers dir (default ./answers)
#   LOGS         per-job logs dir (default ./logs)
#   DRY_RUN      1 to print planned commands without invoking codex
#   ORCHESTRATE_MANIFEST  optional: path to manifest.json for status writes
#                         (manifest-update.sh is called for each transition)
#
# Spawn flags: every codex spawn carries "${CODEX_FLAGS[@]}" + --json + -o.
# `--json` is paired with `-o` because MCP-active sessions can drop JSONL
# events silently (upstream issue 15451) — the answer file is the source of
# truth for "did codex produce output".
#
# Exit codes: 0 all jobs reached a terminal state, 1 prompts dir missing or
#             empty, 2 codex CLI missing, 3 JOBS=0 or invalid.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=codex-flags.sh
. "$SCRIPT_DIR/codex-flags.sh"

# Defaults.
JOBS="${JOBS:-10}"
PROMPTS="${PROMPTS:-prompts}"
ANSWERS="${ANSWERS:-answers}"
LOGS="${LOGS:-logs}"
DRY_RUN="${DRY_RUN:-0}"
ORCHESTRATE_MANIFEST="${ORCHESTRATE_MANIFEST:-}"

# ── Pre-flight ─────────────────────────────────────────────────
if ! [[ "$JOBS" =~ ^[1-9][0-9]*$ ]]; then
  echo "FATAL JOBS must be a positive integer, got: $JOBS" >&2
  exit 3
fi
if [[ "$JOBS" -gt 20 ]]; then
  echo "WARN JOBS=$JOBS exceeds soft cap of 20; consider lowering unless you've measured." >&2
fi

if ! command -v codex >/dev/null 2>&1; then
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

# ── Per-job runner ─────────────────────────────────────────────
# Exported below so xargs subshells can call it. We pass `CODEX_FLAGS` as a
# space-joined string in CODEX_FLAGS_STR — bash exported arrays don't survive
# the `xargs bash -c` boundary on macOS bash 3.2.
run_one() {
  local prompt="$1"
  local name answer log tmp
  name="$(basename "$prompt" .md)"
  answer="$ANSWERS/${name}.md"
  log="$LOGS/${name}.log"
  tmp="$ANSWERS/.${name}.partial"

  # Idempotent skip
  if [[ -s "$answer" ]]; then
    echo "SKIP  $name"
    if [[ -n "$ORCHESTRATE_MANIFEST" && -x "$SCRIPT_DIR_ABS/manifest-update.sh" ]]; then
      "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$name" \
        status=skipped finished_at=now 2>/dev/null || true
    fi
    return 0
  fi

  echo "START $name"
  if [[ -n "$ORCHESTRATE_MANIFEST" && -x "$SCRIPT_DIR_ABS/manifest-update.sh" ]]; then
    "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$name" \
      status=running started_at=now attempts=+1 2>/dev/null || true
  fi

  # Reconstruct the array from the exported newline-delimited string.
  # NULs would be ideal but `$(...)` command substitution strips them; no
  # flag value in our policy contains a newline, so this is safe.
  local -a flags=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && flags+=("$f")
  done <<<"$CODEX_FLAGS_STR"

  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] codex exec ${flags[*]} --json -o $tmp < $prompt > $log"
    echo "DONE  $name (dry-run)"
    return 0
  fi

  # Atomic write: codex writes to $tmp; we mv to $answer only on success.
  # `--json` produces JSONL events on stdout; we redirect them to the log
  # alongside stderr. The answer file (-o) is the source of truth.
  if codex exec "${flags[@]}" --json -o "$tmp" < "$prompt" > "$log" 2>&1; then
    if [[ -s "$tmp" ]]; then
      mv -f "$tmp" "$answer"
      echo "DONE  $name"
      if [[ -n "$ORCHESTRATE_MANIFEST" && -x "$SCRIPT_DIR_ABS/manifest-update.sh" ]]; then
        "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$name" \
          status=done finished_at=now exit_code=0 2>/dev/null || true
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
export CODEX_FLAGS_STR SCRIPT_DIR_ABS ANSWERS LOGS DRY_RUN ORCHESTRATE_MANIFEST
export -f run_one

# Fan-out via xargs. -0 (NUL-delimited) keeps filenames-with-spaces safe.
find "$PROMPTS" -maxdepth 1 -name '*.md' -print0 \
  | xargs -0 -n 1 -P "$JOBS" bash -c 'run_one "$0"'

echo "--- all jobs finished ---"
