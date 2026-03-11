#!/usr/bin/env bash
# E2E test workflow using agent-browser
# Source: official agent-browser documentation

set -euo pipefail

URL="${1:?Usage: $0 <url>}"
RESULTS_DIR="${2:-./test-results}"

mkdir -p "$RESULTS_DIR"

echo "Starting E2E test: $URL"

# Navigate
agent-browser open "$URL"
agent-browser wait --load networkidle

# Capture initial state
agent-browser snapshot -i > "$RESULTS_DIR/initial-snapshot.txt"
agent-browser screenshot "$RESULTS_DIR/initial.png"

# Check for errors
ERRORS=$(agent-browser errors 2>&1 || true)
if [ -n "$ERRORS" ] && [ "$ERRORS" != "No errors" ]; then
  echo "⚠ Console errors detected:"
  echo "$ERRORS"
  echo "$ERRORS" > "$RESULTS_DIR/errors.txt"
fi

# Check page title
TITLE=$(agent-browser get title)
echo "Page title: $TITLE"

# Check interactive elements
echo "Interactive elements:"
agent-browser snapshot -i -c

agent-browser close
echo "E2E test complete. Results in: $RESULTS_DIR"
