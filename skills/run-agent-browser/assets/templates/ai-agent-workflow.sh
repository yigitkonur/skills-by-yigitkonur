#!/usr/bin/env bash
set -euo pipefail

# Reusable Steel Browser workflow. For ad hoc work, run commands individually.
URL="${1:-https://example.com}"
EXPECTED_TEXT="${2:-Example Domain}"
SESSION="steel-workflow-$$-$(date +%s)"

source "$HOME/.config/steel-browser-cdp.env"

ab() {
  env -u AGENT_BROWSER_PROVIDER agent-browser --session "$SESSION" --cdp "$STEEL_AGENT_BROWSER_CDP" "$@"
}

cleanup() {
  ab close >/dev/null 2>&1 || true
}
trap cleanup EXIT

curl -fsS "$STEEL_HEALTH_URL" >/dev/null
ab open "$URL"
ab snapshot -i -u
ab wait --text "$EXPECTED_TEXT"
ab get url
ab get title
ab errors
