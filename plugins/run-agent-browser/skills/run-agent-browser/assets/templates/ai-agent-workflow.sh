#!/usr/bin/env bash
set -euo pipefail

# Reusable managed-pool workflow. For ad hoc work, run commands individually.
URL="${1:-https://example.com}"
EXPECTED_TEXT="${2:-Example Domain}"
OWNED_TAB=""

cleanup() {
  if [[ -n "$OWNED_TAB" ]]; then
    if ! agent-browser tab close "$OWNED_TAB" >/dev/null 2>&1; then
      agent-browser tab "$OWNED_TAB" >/dev/null 2>&1 || true
      agent-browser open about:blank >/dev/null 2>&1 || true
    fi
  fi
  # Exact top-level close is required to release the managed lane.
  agent-browser close >/dev/null 2>&1 || true
}
trap cleanup EXIT

agent-browser pool status
agent-browser open "$URL"
agent-browser pool current

# Capture the active stable tab ID (tN), not a positional index.
OWNED_TAB="$(agent-browser --json tab | sed -n 's/.*"active":true[^}]*"tabId":"\([^"]*\)".*/\1/p' | head -n 1)"
if [[ -z "$OWNED_TAB" ]]; then
  echo "Could not determine the task-owned active tab" >&2
  exit 1
fi

agent-browser snapshot -i -u
agent-browser wait --text "$EXPECTED_TEXT"
agent-browser get url
agent-browser get title
agent-browser errors
