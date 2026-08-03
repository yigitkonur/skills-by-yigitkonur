#!/usr/bin/env bash
set -euo pipefail

# Deterministic smoke workflow. Customize selectors and expected state before use.
URL="${1:?target URL required}"
EXPECTED_URL="${2:?expected URL glob required}"
EXPECTED_TEXT="${3:?expected result text required}"
SESSION="steel-e2e-$$-$(date +%s)"

source "$HOME/.config/steel-browser-cdp.env"

ab() {
  env -u AGENT_BROWSER_PROVIDER agent-browser --session "$SESSION" --cdp "$STEEL_AGENT_BROWSER_CDP" "$@"
}

cleanup() {
  ab close >/dev/null 2>&1 || true
}
trap cleanup EXIT

ab open "$URL"
ab snapshot -i
# Replace this example action with a fresh ref or semantic locator:
ab find role link click --name 'More information'
ab wait --url "$EXPECTED_URL"
ab wait --text "$EXPECTED_TEXT"
ab snapshot -i
ab get url
ab get title
ab errors
