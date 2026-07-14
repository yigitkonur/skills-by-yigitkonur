#!/usr/bin/env bash
set -euo pipefail

# Capture a narrow, reproducible page artifact set on the managed pool.
URL="${1:-https://example.com}"
OUT_DIR="${2:-./agent-browser-capture}"
EXPECTED_TEXT="${3:-}"
OWNED_TAB=""

mkdir -p "$OUT_DIR"

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

agent-browser wait --load domcontentloaded
if [[ -n "$EXPECTED_TEXT" ]]; then
  agent-browser wait --text "$EXPECTED_TEXT"
fi

agent-browser read >"$OUT_DIR/page.md"
agent-browser screenshot "$OUT_DIR/viewport.png"
agent-browser --json snapshot >"$OUT_DIR/snapshot.json"
agent-browser errors >"$OUT_DIR/errors.txt"
agent-browser get url
agent-browser get title

echo "Artifacts may contain private page data; review before sharing: $OUT_DIR"
