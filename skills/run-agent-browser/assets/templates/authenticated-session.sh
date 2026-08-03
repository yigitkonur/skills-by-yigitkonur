#!/usr/bin/env bash
set -euo pipefail

# Reconnect to a saved auth-state file over Steel Browser CDP without exporting
# raw cookies. Usage: authenticated-session.sh <state-file> <url> 'expected signed-in text'
STATE_FILE="${1:?path to a saved --state auth file required}"
URL="${2:?URL required}"
EXPECTED_TEXT="${3:?expected signed-in text required}"
SESSION="steel-auth-$$-$(date +%s)"

[[ -r "$STATE_FILE" ]] || { echo "Cannot read state file: $STATE_FILE" >&2; exit 1; }

source "$HOME/.config/steel-browser-cdp.env"

ab() {
  env -u AGENT_BROWSER_PROVIDER agent-browser --session "$SESSION" --cdp "$STEEL_AGENT_BROWSER_CDP" "$@"
}

cleanup() {
  ab close >/dev/null 2>&1 || true
}
trap cleanup EXIT

env -u AGENT_BROWSER_PROVIDER agent-browser --session "$SESSION" --cdp "$STEEL_AGENT_BROWSER_CDP" --state "$STATE_FILE" open "$URL"

# Verify through ordinary UI. Never dump cookies, storage, or tokens.
ab wait --text "$EXPECTED_TEXT"
ab snapshot -i
ab get url
ab errors
