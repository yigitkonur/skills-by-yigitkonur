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
cd "$(dirname "$0")/.."   # workdir is one level above bin/

JOBS="${JOBS:-10}"
MODEL="${MODEL:-gpt-5.5}"
EFFORT="${EFFORT:-medium}"
PROMPTS="${PROMPTS:-prompts}"
ANSWERS="${ANSWERS:-answers}"
LOGS="${LOGS:-logs}"

mkdir -p "$ANSWERS" "$LOGS"

run_one() {
  local prompt="$1"
  local name
  name="$(basename "$prompt" .md)"
  local answer="$ANSWERS/${name}.md"
  local log="$LOGS/${name}.log"

  if [ -s "$answer" ]; then
    echo "SKIP  $name (answer already exists)"
    return 0
  fi

  echo "START $name"
  # Direct `command codex` invocation with explicit flags. xargs spawns
  # `bash -c` subshells that do NOT inherit any zsh codex wrapper function,
  # so we must pass the bypass + skip-git flags ourselves.
  if command codex --dangerously-bypass-approvals-and-sandbox \
       exec --skip-git-repo-check \
       -m "$MODEL" -c model_reasoning_effort="$EFFORT" \
       -o "$answer" < "$prompt" > "$log" 2>&1; then
    echo "DONE  $name"
  else
    echo "FAIL  $name (see $log)"
  fi
}

export -f run_one
export MODEL EFFORT ANSWERS LOGS

find "$PROMPTS" -maxdepth 1 -name '*.md' -print0 \
  | xargs -0 -n 1 -P "$JOBS" bash -c 'run_one "$0"'

echo "--- all jobs finished ---"
