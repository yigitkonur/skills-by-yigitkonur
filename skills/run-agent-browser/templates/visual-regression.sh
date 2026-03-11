#!/usr/bin/env bash
# Visual regression testing using agent-browser diff commands
# Source: official agent-browser diffing documentation

set -euo pipefail

URL="${1:?Usage: $0 <url> [baseline-dir]}"
BASELINE_DIR="${2:-./baselines}"

mkdir -p "$BASELINE_DIR"

BASELINE_SNAPSHOT="$BASELINE_DIR/snapshot-baseline.txt"
BASELINE_SCREENSHOT="$BASELINE_DIR/screenshot-baseline.png"

if [ ! -f "$BASELINE_SCREENSHOT" ]; then
  echo "Creating baselines..."
  agent-browser open "$URL"
  agent-browser wait --load networkidle
  agent-browser snapshot -i -c > "$BASELINE_SNAPSHOT"
  agent-browser screenshot "$BASELINE_SCREENSHOT"
  agent-browser close
  echo "Baselines created in: $BASELINE_DIR"
  echo "Run again to compare against baselines."
  exit 0
fi

echo "Comparing against baselines..."
agent-browser open "$URL"
agent-browser wait --load networkidle

# Snapshot diff
echo "=== Snapshot Diff ==="
agent-browser diff snapshot --baseline "$BASELINE_SNAPSHOT"

# Screenshot diff
echo ""
echo "=== Screenshot Diff ==="
agent-browser diff screenshot --baseline "$BASELINE_SCREENSHOT"

agent-browser close
echo "Regression check complete."
