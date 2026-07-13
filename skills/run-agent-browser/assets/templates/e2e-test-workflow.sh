#!/usr/bin/env bash
set -euo pipefail

# Deterministic smoke workflow. Customize selectors and expected state before use.
URL="${1:?target URL required}"
EXPECTED_URL="${2:?expected URL glob required}"
EXPECTED_TEXT="${3:?expected result text required}"
OWNED_TAB=""

cleanup() {
  if [[ -n "$OWNED_TAB" ]]; then
    if ! agent-browser tab close "$OWNED_TAB" >/dev/null 2>&1; then
      agent-browser tab "$OWNED_TAB" >/dev/null 2>&1 || true
      agent-browser open about:blank >/dev/null 2>&1 || true
    fi
  fi
  agent-browser close >/dev/null 2>&1 || true
}
trap cleanup EXIT

agent-browser pool status
agent-browser open "$URL"
agent-browser pool current
OWNED_TAB="$(agent-browser --json tab | sed -n 's/.*"active":true[^}]*"tabId":"\([^"]*\)".*/\1/p' | head -n 1)"
[[ -n "$OWNED_TAB" ]] || { echo "Could not determine active task tab" >&2; exit 1; }

agent-browser snapshot -i
# Replace this example action with a fresh ref or semantic locator:
agent-browser find role link click --name 'More information'
agent-browser wait --url "$EXPECTED_URL"
agent-browser wait --text "$EXPECTED_TEXT"
agent-browser snapshot -i
agent-browser get url
agent-browser get title
agent-browser errors
