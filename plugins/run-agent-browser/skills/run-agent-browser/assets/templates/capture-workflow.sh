#!/usr/bin/env bash
set -euo pipefail

# Capture a narrow, reproducible page artifact set via Steel Browser CDP.
URL="${1:-https://example.com}"
OUT_DIR="${2:-./agent-browser-capture}"
EXPECTED_TEXT="${3:-}"
SESSION="steel-capture-$$-$(date +%s)"

mkdir -p "$OUT_DIR"

source "$HOME/.config/steel-browser-cdp.env"

ab() {
  env -u AGENT_BROWSER_PROVIDER agent-browser --session "$SESSION" --cdp "$STEEL_AGENT_BROWSER_CDP" "$@"
}

cleanup() {
  ab close >/dev/null 2>&1 || true
}
trap cleanup EXIT

ab open "$URL"
ab wait --load domcontentloaded
if [[ -n "$EXPECTED_TEXT" ]]; then
  ab wait --text "$EXPECTED_TEXT"
fi

ab read >"$OUT_DIR/page.md"
ab screenshot "$OUT_DIR/viewport.png"
ab --json snapshot >"$OUT_DIR/snapshot.json"
ab errors >"$OUT_DIR/errors.txt"
ab get url
ab get title

echo "Artifacts may contain private page data; review before sharing: $OUT_DIR"
