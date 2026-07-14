#!/usr/bin/env bash
set -euo pipefail

# Use an existing authenticated headed-CDP lane without exporting credentials.
# Usage: authenticated-session.sh peec https://app.peec.ai 'Dashboard'
LANE="${1:?lane required: peec or profound}"
URL="${2:?URL required}"
EXPECTED_TEXT="${3:?expected signed-in text required}"
OWNED_TAB=""

case "$LANE" in
  peec|profound) ;;
  *) echo "Authenticated lane must be peec or profound" >&2; exit 2 ;;
esac

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
agent-browser pool use "$LANE"
agent-browser pool current
agent-browser open "$URL"
OWNED_TAB="$(agent-browser --json tab | sed -n 's/.*"active":true[^}]*"tabId":"\([^"]*\)".*/\1/p' | head -n 1)"
[[ -n "$OWNED_TAB" ]] || { echo "Could not determine active task tab" >&2; exit 1; }

# Verify through ordinary UI. Never dump cookies, storage, or tokens.
agent-browser wait --text "$EXPECTED_TEXT"
agent-browser snapshot -i
agent-browser get url
agent-browser errors
