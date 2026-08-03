#!/usr/bin/env bash
set -euo pipefail

# Authorized form submission template. Do not place passwords/tokens in arguments.
URL="${1:?form URL required}"
NAME="${2:?name required}"
EMAIL="${3:?email required}"
EXPECTED_TEXT="${4:?post-submit confirmation text required}"
SESSION="steel-form-$$-$(date +%s)"

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
ab find label 'Name' fill "$NAME"
ab find label 'Email' fill "$EMAIL"
ab get value 'input[type="email"]'

# Submission is outward-facing. Run only when the user authorized it.
ab find role button click --name 'Submit'
ab wait --text "$EXPECTED_TEXT"
ab snapshot -i
ab errors
