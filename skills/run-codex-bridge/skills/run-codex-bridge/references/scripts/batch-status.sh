#!/usr/bin/env bash
set -euo pipefail

STATUS_FILTER=""
CWD_FILTER=""
RECENT_COUNT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --status) STATUS_FILTER="$2"; shift 2 ;;
    --cwd) CWD_FILTER="$2"; shift 2 ;;
    --recent) RECENT_COUNT="$2"; shift 2 ;;
    --help|-h)
      cat <<'EOF'
Usage: batch-status.sh [--status STATUS] [--cwd PATH] [--recent N]

Print a compact summary of codex-worker threads using `codex-worker --output json thread list`.
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

if ! command -v codex-worker >/dev/null 2>&1; then
  echo "codex-worker is required on PATH" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required on PATH" >&2
  exit 1
fi

args=(--output json thread list)
if [[ -n "$CWD_FILTER" ]]; then
  args+=(--cwd "$CWD_FILTER")
fi

json=$(codex-worker "${args[@]}")

rows=$(printf '%s' "$json" | jq -r --arg status "$STATUS_FILTER" '
  .data[]
  | select($status == "" or .status == $status)
  | [(.updatedAt // .createdAt // ""), .id, .status, .cwd, (.latestTurnId // "-"), (.lastError // "")]
  | @tsv
')

if [[ -z "$rows" ]]; then
  echo "No threads matched."
  exit 0
fi

sorted=$(printf '%s\n' "$rows" | sort -r)
if [[ "$RECENT_COUNT" -gt 0 ]]; then
  sorted=$(printf '%s\n' "$sorted" | head -n "$RECENT_COUNT")
fi

printf "%-28s %-18s %-40s %s\n" "THREAD_ID" "STATUS" "CWD" "LATEST_TURN"
printf "%-28s %-18s %-40s %s\n" "---------" "------" "---" "-----------"
printf '%s\n' "$sorted" | while IFS=$'\t' read -r _ts id status cwd latest_turn last_error; do
  short_cwd=$cwd
  if [[ ${#short_cwd} -gt 40 ]]; then
    short_cwd="...${short_cwd: -37}"
  fi
  printf "%-28s %-18s %-40s %s\n" "$id" "$status" "$short_cwd" "$latest_turn"
  if [[ -n "$last_error" ]]; then
    printf "  error: %s\n" "$last_error"
  fi
done
