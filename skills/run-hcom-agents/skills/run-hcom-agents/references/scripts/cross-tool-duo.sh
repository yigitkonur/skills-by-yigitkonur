#!/usr/bin/env bash
# Claude designs spec, Codex implements it, and the script fails with actionable diagnostics.
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
wait_for_idle() {
  local agent_name="$1"
  local result
  result=$(hcom events --wait 30 --idle "$agent_name" $name_arg 2>/dev/null || true)
  if [[ -n "$result" ]]; then
    return 0
  fi
  echo "WAIT FAILED: ${agent_name} never reached idle/listening state" >&2
  hcom list 2>/dev/null || true
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
task="${task:-write a python function that adds two numbers}"
thread="duo-$(date +%s)"

preflight
trap cleanup ERR

launch_out=$(hcom 1 codex --tag eng --go --headless \
  --hcom-prompt "Wait for spec from @arch-. Implement it. Then confirm: hcom send \"@arch-\" --thread ${thread} --intent inform -- \"IMPLEMENTED\". Then stop: hcom stop" 2>&1)
track_launch "$launch_out"
eng=$(echo "$launch_out" | grep '^Names: ' | sed 's/^Names: //' | tr -d ' ')
echo "Engineer (Codex): $eng"
wait_for_idle "$eng"

launch_out=$(hcom 1 claude --tag arch --go --headless \
  --hcom-prompt "Design a 2-3 sentence spec for: ${task}. Send to @eng-: hcom send \"@eng-\" --thread ${thread} --intent request -- \"SPEC: <spec>\". Wait for IMPLEMENTED. Then send: hcom send --thread ${thread} --intent inform -- \"APPROVED\". Then stop: hcom stop" 2>&1)
track_launch "$launch_out"
arch=$(echo "$launch_out" | grep '^Names: ' | sed 's/^Names: //' | tr -d ' ')
echo "Architect (Claude): $arch"
echo "Thread: $thread"
echo "Waiting..."

if result=$(wait_for_match 180 "type='message' AND msg_thread='${thread}' AND msg_text LIKE '%APPROVED%'"); then
  echo "PASS: $result"
else
  echo "FAIL"
fi

trap - ERR
for name in "${LAUNCHED_NAMES[@]}"; do hcom kill "$name" --go 2>/dev/null || true; done
hcom events --sql "msg_thread='${thread}'" --last 10 2>&1
