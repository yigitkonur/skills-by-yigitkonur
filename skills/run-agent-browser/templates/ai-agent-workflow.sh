#!/usr/bin/env bash
# ai-agent-workflow.sh — Template for AI agent browser automation
# Usage: ./ai-agent-workflow.sh <url> [task-description]
set -euo pipefail

URL="${1:?Usage: ai-agent-workflow.sh <url> [task-description]}"
TASK="${2:-explore and capture page content}"

# === Configuration ===
export AGENT_BROWSER_CONTENT_BOUNDARIES=1
export AGENT_BROWSER_MAX_OUTPUT=50000
SCREENSHOT_DIR="./agent-screenshots"
mkdir -p "$SCREENSHOT_DIR"

# === Safety boundaries (uncomment to restrict) ===
# export AGENT_BROWSER_ALLOWED_DOMAINS="example.com,*.example.com"
# export AGENT_BROWSER_ACTION_POLICY=./policy.json

echo "🌐 Starting agent workflow: $TASK"
echo "   URL: $URL"

# === 1. Navigate and wait ===
agent-browser open "$URL"
agent-browser wait --load networkidle

# === 2. Initial snapshot (interactive elements only) ===
echo "📸 Taking initial snapshot..."
agent-browser snapshot -i

# === 3. Capture screenshot for visual context ===
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
agent-browser screenshot "$SCREENSHOT_DIR/initial-${TIMESTAMP}.png"

# === 4. Extract page metadata ===
PAGE_URL=$(agent-browser get url)
PAGE_TITLE=$(agent-browser get title)
echo "📄 Page: $PAGE_TITLE"
echo "🔗 URL:  $PAGE_URL"

# === 5. Example: Fill a search form ===
# Uncomment and modify for your use case:
# agent-browser fill @e1 "search query"
# agent-browser click @e2
# agent-browser wait --load networkidle
# agent-browser snapshot -i

# === 6. Example: Extract structured data ===
# agent-browser get text "#main-content"
# agent-browser snapshot -i --json | jq '.data.refs | to_entries[] | select(.value.role == "heading")'

# === 7. Final capture ===
agent-browser screenshot "$SCREENSHOT_DIR/final-${TIMESTAMP}.png"

# === 8. Cleanup ===
agent-browser close
echo "✅ Agent workflow complete"
