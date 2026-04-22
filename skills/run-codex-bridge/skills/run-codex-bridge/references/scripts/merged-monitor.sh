#!/usr/bin/env bash
# merged-monitor.sh — tail one or more codex-worker threads' rawLogPath firehose
# with a milestone-only jq filter and a short-id prefix per line.
#
# Usage:
#   merged-monitor.sh <thread-id-1> [thread-id-2] ...
#
# Env:
#   CODEX_WORKER_TURN_TIMEOUT_MS — configure the worker's idle watchdog window.
#     Inline example:
#       CODEX_WORKER_TURN_TIMEOUT_MS=3600000 ./merged-monitor.sh <tid>
#
# Requires:
#   - codex-worker on PATH  (see ../command-reference.md for install)
#   - jq  (brew install jq)
#
# See ../recovery-and-diagnostics.md for raw log paths and recovery workflow,
# and ../orchestration-patterns.md for multi-thread monitoring patterns.

set -euo pipefail

if [[ $# -eq 0 ]]; then
  cat <<'EOF' >&2
Usage: merged-monitor.sh <thread-id-1> [thread-id-2] [...]

Resolves each thread's artifacts.rawLogPath via `codex-worker read`, then tails
them together with a milestone-only jq filter.
EOF
  exit 1
fi

if ! command -v codex-worker >/dev/null 2>&1; then
  echo "[monitor] codex-worker is required on PATH" >&2
  exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "[monitor] jq is required on PATH (brew install jq)" >&2
  exit 2
fi

TAIL_PIDS=()

cleanup() {
  for pid in "${TAIL_PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

FILTER='
  select(
    .method == "turn/started"              or
    .method == "turn/completed"            or
    .method == "item/completed"            or
    .method == "thread/tokenUsage/updated" or
    .method == "thread/status/changed"     or
    .dir    == "server_request"            or
    .dir    == "exit"                      or
    .dir    == "stderr"                    or
    .dir    == "protocol_error"            or
    (.dir == "daemon" and (.message | test("watchdog|fail|completeExecution")))
  ) |
  "\(.ts[11:19])  \(.dir)  \(.method // .message)  \(.params.item.type // "")"
'

for thread_id in "$@"; do
  raw_path=$(codex-worker --output json read "$thread_id" 2>/dev/null | jq -r '.artifacts.rawLogPath // empty')
  if [[ -z "$raw_path" || "$raw_path" == "null" ]]; then
    echo "[monitor] WARNING: no rawLogPath for $thread_id (thread predates codex-worker@0.1.4?)" >&2
    continue
  fi

  mkdir -p "$(dirname "$raw_path")"
  touch "$raw_path"

  short_id=${thread_id:0:8}
  # -n +1 replays the file from byte 0 so fast turns don't slip past the
  # default 10-line tail before we attach; then live-tails as usual.
  tail -n +1 -F "$raw_path" 2>/dev/null \
    | jq -rc --unbuffered "$FILTER" 2>/dev/null \
    | awk -v tag="[$short_id] " '{ print tag $0; fflush() }' &
  TAIL_PIDS+=("$!")
done

if [[ ${#TAIL_PIDS[@]} -eq 0 ]]; then
  echo "[monitor] No valid threads to monitor." >&2
  exit 1
fi

echo "[monitor] Watching ${#TAIL_PIDS[@]} thread raw log(s). Ctrl+C to stop."
wait
