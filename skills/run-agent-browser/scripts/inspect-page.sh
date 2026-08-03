#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: inspect-page.sh [--screenshot] URL [output-dir]

Captures URL, title, interactive snapshots, readable DOM, and browser errors via
Steel Browser CDP using a unique named agent-browser session. Unsets any global
provider variable for the subprocess to avoid runtime conflicts.
EOF
}

SCREENSHOT=0
URL=""
OUTPUT_DIR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --screenshot) SCREENSHOT=1; shift ;;
    -*) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    *)
      if [[ -z "$URL" ]]; then URL="$1"
      elif [[ -z "$OUTPUT_DIR" ]]; then OUTPUT_DIR="$1"
      else echo "Unexpected argument: $1" >&2; usage >&2; exit 2
      fi
      shift
      ;;
  esac
done
[[ -n "$URL" ]] || { usage >&2; exit 2; }

OUTPUT_DIR="${OUTPUT_DIR:-./agent-browser-inspect}"
mkdir -p "$OUTPUT_DIR"

if [[ -r "$HOME/.config/steel-browser-cdp.env" ]]; then
  # shellcheck disable=SC1091
  source "$HOME/.config/steel-browser-cdp.env"
fi

if [[ -z "${STEEL_AGENT_BROWSER_CDP:-}" ]]; then
  echo "STEEL_AGENT_BROWSER_CDP is missing (source ~/.config/steel-browser-cdp.env)" >&2
  exit 1
fi

if command -v agent-browser >/dev/null 2>&1; then
  AB_BIN=(agent-browser)
else
  AB_BIN=(npx --no-install agent-browser)
fi

SESSION="inspect-page-$$-$(date +%s)"

run_ab() {
  env -u AGENT_BROWSER_PROVIDER "${AB_BIN[@]}" --session "$SESSION" --cdp "$STEEL_AGENT_BROWSER_CDP" "$@"
}

cleanup() {
  run_ab close >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "resolved command: ${AB_BIN[*]}"
echo "runtime:          Steel Browser CDP"
echo "session:          $SESSION"
echo "endpoint:         $STEEL_AGENT_BROWSER_CDP"
echo "url:              $URL"
echo "output dir:       $OUTPUT_DIR"

run_ab open "$URL"

if ! run_ab wait --load networkidle >/dev/null 2>&1; then
  run_ab wait --load domcontentloaded >/dev/null 2>&1 || true
fi

run_ab get url >"$OUTPUT_DIR/final-url.txt"
run_ab get title >"$OUTPUT_DIR/title.txt"
run_ab --json snapshot -i >"$OUTPUT_DIR/snapshot-interactive.json"
run_ab snapshot -i >"$OUTPUT_DIR/snapshot-interactive.txt"
run_ab read >"$OUTPUT_DIR/page.md"
run_ab errors >"$OUTPUT_DIR/errors.txt"
if [[ "$SCREENSHOT" -eq 1 ]]; then
  run_ab screenshot "$OUTPUT_DIR/screenshot.png"
fi

printf 'Artifacts written to %s (review for private data before sharing)\n' "$OUTPUT_DIR"
