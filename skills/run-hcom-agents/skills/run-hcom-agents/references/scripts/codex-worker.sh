#!/usr/bin/env bash
# Codex writes code, Claude reviews the transcript, and the script fails with diagnostics.
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
  require_hooks codex
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
task="${task:-write /tmp/hello.py that prints hello world and run it}"
thread="codex-$(date +%s)"

preflight
trap cleanup ERR

launch_out=$(hcom 1 claude --tag reviewer --go --headless \
  --hcom-prompt "Wait for a control message in thread ${thread} that says CODER NAME: <name>. Replace <name> with that coder name, then wait for CODE DONE from @coder-. Read that coder's transcript with: hcom transcript @<name> --last 5 --full. Send: hcom send --thread ${thread} --intent inform -- \"REVIEWED: <pass/fail>\". Then stop: hcom stop" 2>&1)
track_launch "$launch_out"
reviewer=$(echo "$launch_out" | grep '^Names: ' | sed 's/^Names: //' | tr -d ' ')
echo "Reviewer (Claude): $reviewer"

launch_out=$(hcom 1 codex --tag coder --go --headless \
  --hcom-prompt "Do this: ${task}. When done, send output: hcom send \"@reviewer-\" --thread ${thread} --intent inform -- \"CODE DONE: <output>\". Then stop: hcom stop" 2>&1)
track_launch "$launch_out"
coder=$(echo "$launch_out" | grep '^Names: ' | sed 's/^Names: //' | tr -d ' ')
echo "Coder (Codex): $coder"
hcom send @"${reviewer}" --thread "$thread" --intent inform -- "CODER NAME: ${coder}" >/dev/null 2>&1 || true
echo "Thread: $thread"
echo "Waiting..."

if result=$(wait_for_match 180 "type='message' AND msg_thread='${thread}' AND msg_text LIKE '%REVIEWED%'"); then
  echo "PASS: $result"
else
  echo "FAIL"
fi

trap - ERR
for name in "${LAUNCHED_NAMES[@]}"; do hcom kill "$name" --go 2>/dev/null || true; done
hcom events --sql "msg_thread='${thread}'" --last 10 2>&1
