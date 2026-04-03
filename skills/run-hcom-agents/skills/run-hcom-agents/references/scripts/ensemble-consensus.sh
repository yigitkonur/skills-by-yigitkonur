#!/usr/bin/env bash
# 3 agents independently answer the same question, judge picks best, and timeouts dump diagnostics.
set -euo pipefail

LAUNCHED_NAMES=()
track_launch() {
  local names=$(echo "$1" | grep '^Names: ' | sed 's/^Names: //')
  for n in $names; do LAUNCHED_NAMES+=("$n"); done
}
cleanup() {
  for name in "${LAUNCHED_NAMES[@]}"; do
    hcom kill "$name" --go 2>/dev/null || true
  done
}
require_hooks() {
  local tool="$1"
  if hcom hooks 2>/dev/null | grep -Eq "^${tool}:[[:space:]]+installed"; then
    return 0
  fi
  echo "PREFLIGHT FAILED: ${tool} hooks are not installed." >&2
  echo "Run: hcom hooks add ${tool}" >&2
  echo "Restart ${tool}, then confirm with: hcom status --logs" >&2
  hcom status --logs 2>/dev/null || hcom status 2>/dev/null || true
  return 1
}
preflight() {
  command -v hcom >/dev/null || { echo "PREFLIGHT FAILED: hcom is not in PATH" >&2; return 1; }
  require_hooks claude
}
wait_for_match() {
  local timeout="$1"
  local sql="$2"
  local result
  result=$(hcom events --wait "$timeout" --sql "$sql" $name_arg 2>/dev/null || true)
  if [[ -n "$result" ]]; then
    echo "$result"
    return 0
  fi
  echo "TIMEOUT: no matching event for thread ${thread}" >&2
  hcom events --sql "msg_thread='${thread}'" --last 20 $name_arg 2>/dev/null || true
  hcom status --logs 2>/dev/null || hcom status 2>/dev/null || true
  return 1
}

name_flag=""
task=""
while [[ $# -gt 0 ]]; do
  case "$1" in --name) name_flag="$2"; shift 2 ;; -*) shift ;; *) task="$1"; shift ;; esac
done
name_arg=""
[[ -n "$name_flag" ]] && name_arg="--name $name_flag"
task="${task:-what is 17 * 23}"
thread="ens-$(date +%s)"

preflight
trap cleanup ERR

launch_out=$(hcom 1 claude --tag judge --go --headless \
  --hcom-prompt "Wait for 3 answers in thread '${thread}'. Check: hcom events --sql \"msg_thread='${thread}'\" --last 10. Pick best. Send: hcom send --thread ${thread} --intent inform -- \"VERDICT: <winner>\". Then stop: hcom stop" 2>&1)
track_launch "$launch_out"
judge=$(echo "$launch_out" | grep '^Names: ' | sed 's/^Names: //' | tr -d ' ')
echo "Judge: $judge"

for i in 1 2 3; do
  launch_out=$(hcom 1 claude --tag "c${i}" --go --headless \
    --hcom-prompt "Answer: ${task}. Send ONLY your answer: hcom send \"@judge-\" --thread ${thread} --intent inform -- \"C${i}: <answer>\". Then stop: hcom stop" 2>&1)
  track_launch "$launch_out"
  name=$(echo "$launch_out" | grep '^Names: ' | sed 's/^Names: //' | tr -d ' ')
  echo "Contestant $i: $name"
done

echo "Thread: $thread"
echo "Waiting..."

if result=$(wait_for_match 120 "type='message' AND msg_thread='${thread}' AND msg_text LIKE '%VERDICT%'"); then
  echo "PASS: $result"
else
  echo "FAIL"
fi

trap - ERR
for name in "${LAUNCHED_NAMES[@]}"; do hcom kill "$name" --go 2>/dev/null || true; done
hcom events --sql "msg_thread='${thread}'" --last 10 2>&1
