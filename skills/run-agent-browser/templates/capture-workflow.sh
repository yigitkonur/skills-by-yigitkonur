#!/usr/bin/env bash
# Capture workflow: screenshot + snapshot + optional video
# Source: official agent-browser documentation

set -euo pipefail

URL="${1:?Usage: $0 <url> [output-dir]}"
OUTPUT_DIR="${2:-.}"

mkdir -p "$OUTPUT_DIR"

echo "Capturing: $URL"

# Navigate and wait for stable state
agent-browser open "$URL"
agent-browser wait --load networkidle

# Capture snapshot
agent-browser snapshot -i -c > "$OUTPUT_DIR/snapshot.txt"
echo "Snapshot saved: $OUTPUT_DIR/snapshot.txt"

# Capture screenshot
agent-browser screenshot "$OUTPUT_DIR/screenshot.png"
echo "Screenshot saved: $OUTPUT_DIR/screenshot.png"

# Capture annotated screenshot
agent-browser screenshot --annotate "$OUTPUT_DIR/annotated.png"
echo "Annotated screenshot saved: $OUTPUT_DIR/annotated.png"

# Capture full page
agent-browser screenshot --full "$OUTPUT_DIR/full-page.png"
echo "Full page screenshot saved: $OUTPUT_DIR/full-page.png"

agent-browser close
echo "Done. All captures in: $OUTPUT_DIR"
