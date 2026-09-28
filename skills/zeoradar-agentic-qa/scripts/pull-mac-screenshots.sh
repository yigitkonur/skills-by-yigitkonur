#!/usr/bin/env bash
# pull-mac-screenshots.sh — Pulls remote Ego Browser screenshots from MacBook display to local evidence folder via SCP
# Usage: pull-mac-screenshots.sh <remote_pattern> <local_dest_dir>

set -euo pipefail

REMOTE_PATTERN="${1:-}"
LOCAL_DEST="${2:-}"

if [[ -z "$REMOTE_PATTERN" || -z "$LOCAL_DEST" ]]; then
  echo "Usage: $0 <remote_pattern_e.g._case-vis-*> <local_destination_directory>" >&2
  exit 1
fi

mkdir -p "$LOCAL_DEST"

echo "[HARVEST] Pulling shots matching '$REMOTE_PATTERN' from MacBook to $LOCAL_DEST ..."
if scp "macbook:/tmp/ego-shots/$REMOTE_PATTERN.png" "$LOCAL_DEST/" 2>/dev/null; then
  echo "[HARVEST_SUCCESS] Artifacts retrieved."
  ssh macbook "rm -f /tmp/ego-shots/$REMOTE_PATTERN.png" 2>/dev/null || true
else
  echo "[HARVEST_NOTICE] No matching shots found on MacBook (/tmp/ego-shots/$REMOTE_PATTERN.png)."
fi
