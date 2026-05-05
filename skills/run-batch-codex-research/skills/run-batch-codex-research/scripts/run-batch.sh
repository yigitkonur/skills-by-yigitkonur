#!/usr/bin/env bash
# run-batch.sh — bounded-parallel codex runner over a directory of prompt files.
#
# Reads every prompts/*.md, runs `codex exec` per file, writes the last
# message to answers/<name>.md, captures stdout/stderr to logs/<name>.log,
# and emits one structured event per state transition to stdout (the runner
# log). Idempotent: skips any prompt whose answer file is already non-empty.
#
# Usage:
#   JOBS=10 MODEL=gpt-5.5 EFFORT=medium ./run-batch.sh
#
# Env vars:
#   JOBS    parallel concurrency (default 10)
#   MODEL   codex --model (default gpt-5.5)
#   EFFORT  model_reasoning_effort (default medium)
#   PROMPTS prompts dir (default ./prompts)
#   ANSWERS answers dir (default ./answers)
#   LOGS    per-job logs dir (default ./logs)

set -u
cd "$(dirname "$0")/.." || { echo "FATAL cd to workdir failed" >&2; exit 1; }

JOBS="${JOBS:-10}"
MODEL="${MODEL:-gpt-5.5}"
EFFORT="${EFFORT:-medium}"
PROMPTS="${PROMPTS:-prompts}"
ANSWERS="${ANSWERS:-answers}"
LOGS="${LOGS:-logs}"

# Preflight: a missing or empty prompts dir is a configuration error, not a
# successful empty batch. Bail before printing the finished sentinel so the
# Monitor watcher cannot mistake the case for a clean run.
if [ ! -d "$PROMPTS" ]; then
  echo "FATAL prompts dir not found: $PROMPTS (run render-prompts.sh first)" >&2
  exit 1
fi
prompt_count="$(find "$PROMPTS" -maxdepth 1 -name '*.md' -type f | wc -l | tr -d ' ')"
if [ "$prompt_count" -eq 0 ]; then
  echo "FATAL no *.md prompts in $PROMPTS — render-prompts.sh produced nothing or the dir was wiped" >&2
  exit 1
fi

mkdir -p "$ANSWERS" "$LOGS"

run_one() {
  local prompt="$1"
  local name
  name="$(basename "$prompt" .md)"
  local answer="$ANSWERS/${name}.md"
  local log="$LOGS/${name}.log"
  local tmp="$ANSWERS/.${name}.partial"

  if [ -s "$answer" ]; then
    echo "SKIP  $name (answer already exists)"
    return 0
  fi

  echo "START $name"
  # Direct `command codex` invocation with explicit flags. xargs spawns
  # `bash -c` subshells that do NOT inherit any zsh codex wrapper function,
  # so we must pass the bypass + skip-git flags ourselves.
  #
  # Atomic write: codex writes to `$tmp`. We `mv` to `$answer` only on
  # success. A nonzero exit leaves no file at the answer path, so a re-run
  # retries the prompt instead of treating partial output as complete.
  if command codex --dangerously-bypass-approvals-and-sandbox \
       exec --skip-git-repo-check \
       -m "$MODEL" -c model_reasoning_effort="$EFFORT" \
       -o "$tmp" < "$prompt" > "$log" 2>&1; then
    if [ -s "$tmp" ]; then
      mv -f "$tmp" "$answer"
      echo "DONE  $name"
    else
      rm -f "$tmp"
      echo "FAIL  $name (codex exited 0 but produced empty output; see $log)"
    fi
  else
    rm -f "$tmp"
    echo "FAIL  $name (see $log)"
  fi
}

export -f run_one
export MODEL EFFORT ANSWERS LOGS

find "$PROMPTS" -maxdepth 1 -name '*.md' -print0 \
  | xargs -0 -n 1 -P "$JOBS" bash -c 'run_one "$0"'

echo "--- all jobs finished ---"
