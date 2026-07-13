#!/usr/bin/env bash
set -euo pipefail

# Authorized form submission template. Do not place passwords/tokens in arguments.
URL="${1:?form URL required}"
NAME="${2:?name required}"
EMAIL="${3:?email required}"
EXPECTED_TEXT="${4:?post-submit confirmation text required}"
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
agent-browser find label 'Name' fill "$NAME"
agent-browser find label 'Email' fill "$EMAIL"
agent-browser get value 'input[type="email"]'

# Submission is outward-facing. Run this template only when the user authorized it.
agent-browser find role button click --name 'Submit'
agent-browser wait --text "$EXPECTED_TEXT"
agent-browser snapshot -i
agent-browser errors
