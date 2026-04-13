#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  cat <<'EOF'
Usage: merged-monitor.sh <thread-id-1> [thread-id-2] [...]

Resolve each thread's log path via `codex-worker read`, then tail them together with prefixes.
EOF
  exit 1
fi

if ! command -v codex-worker >/dev/null 2>&1; then
  echo "codex-worker is required on PATH" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required on PATH" >&2
  exit 1
fi

TAIL_PIDS=()

cleanup() {
  for pid in "${TAIL_PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}

trap cleanup EXIT INT TERM

for thread_id in "$@"; do
  log_path=$(codex-worker --output json read "$thread_id" | jq -r '.artifacts.logPath')
  if [[ -z "$log_path" || "$log_path" == "null" ]]; then
    echo "[monitor] WARNING: no log path for $thread_id" >&2
    continue
  fi

  mkdir -p "$(dirname "$log_path")"
  touch "$log_path"

  short_id=${thread_id:0:8}
  if command -v gsed >/dev/null 2>&1; then
    tail -f "$log_path" | gsed --unbuffered "s/^/[$short_id] /" &
  elif sed --unbuffered '' </dev/null 2>/dev/null; then
    tail -f "$log_path" | sed --unbuffered "s/^/[$short_id] /" &
  else
    tail -f "$log_path" | sed -l "s/^/[$short_id] /" &
  fi
  TAIL_PIDS+=("$!")
done

if [[ ${#TAIL_PIDS[@]} -eq 0 ]]; then
  echo "[monitor] No valid threads to monitor." >&2
  exit 1
fi

echo "[monitor] Watching ${#TAIL_PIDS[@]} thread log(s). Press Ctrl+C to stop."
wait
