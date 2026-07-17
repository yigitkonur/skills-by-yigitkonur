#!/usr/bin/env bash
set -euo pipefail

# Use an existing authenticated headed-CDP lane without exporting credentials.
# Usage: authenticated-session.sh <lane> <url> 'expected signed-in text'
LANE="${1:?authenticated lane name required, e.g. app1}"
URL="${2:?URL required}"
EXPECTED_TEXT="${3:?expected signed-in text required}"
OWNED_TAB=""

# `agent-browser pool use "$LANE"` below already validates the lane exists
# (prints "Unknown CDP lane: ..." and exits non-zero otherwise) — no need to
# duplicate that with a hardcoded name whitelist here.

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
