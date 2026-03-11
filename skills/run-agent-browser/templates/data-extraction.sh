#!/usr/bin/env bash
# Data extraction workflow using agent-browser
# Source: official agent-browser documentation

set -euo pipefail

URL="${1:?Usage: $0 <url> [selector]}"
SELECTOR="${2:-body}"

echo "Extracting data from: $URL"

agent-browser open "$URL"
agent-browser wait --load networkidle

# Get text content
echo "=== Text Content ==="
agent-browser get text "$SELECTOR"

# Get HTML content
echo ""
echo "=== HTML Content ==="
agent-browser get html "$SELECTOR"

# Get snapshot for structured data
echo ""
echo "=== Accessibility Snapshot ==="
agent-browser snapshot -s "$SELECTOR" -c

agent-browser close
