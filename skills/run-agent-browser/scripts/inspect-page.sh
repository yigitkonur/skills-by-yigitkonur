#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: inspect-page.sh [--screenshot] URL [output-dir]

Runs a first-pass agent-browser DOM inspection in an isolated temporary session.

Artifacts:
  final-url.txt
  title.txt
  snapshot-interactive.json
  snapshot-interactive.txt
  screenshot.png              only with --screenshot

The script does not load, save, or persist auth state.
EOF
}

SCREENSHOT=0
URL=""
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --screenshot)
      SCREENSHOT=1
      shift
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -z "$URL" ]]; then
        URL="$1"
      elif [[ -z "$OUTPUT_DIR" ]]; then
        OUTPUT_DIR="$1"
      else
        echo "Unexpected argument: $1" >&2
        usage >&2
        exit 2
      fi
      shift
      ;;
  esac
done

if [[ -z "$URL" ]]; then
  usage >&2
  exit 2
fi

OUTPUT_DIR="${OUTPUT_DIR:-./agent-browser-inspect}"
mkdir -p "$OUTPUT_DIR"

if command -v agent-browser >/dev/null 2>&1; then
  AB_CMD=(agent-browser)
else
  AB_CMD=(npx --no-install agent-browser)
fi

SESSION="inspect-page-$$-$(date +%s)"

run_ab() {
  "${AB_CMD[@]}" --session "$SESSION" "$@"
}

cleanup() {
  run_ab close >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "resolved command: ${AB_CMD[*]}"
echo "session:          $SESSION"
echo "url:              $URL"
echo "output dir:       $OUTPUT_DIR"

run_ab open "$URL"

if ! run_ab wait --load networkidle >/dev/null 2>&1; then
  run_ab wait 1000 >/dev/null 2>&1 || true
fi

run_ab get url >"$OUTPUT_DIR/final-url.txt"
run_ab get title >"$OUTPUT_DIR/title.txt"
run_ab snapshot -i --json >"$OUTPUT_DIR/snapshot-interactive.json"
run_ab snapshot -i >"$OUTPUT_DIR/snapshot-interactive.txt"

if [[ "$SCREENSHOT" -eq 1 ]]; then
  run_ab screenshot "$OUTPUT_DIR/screenshot.png"
fi

echo ""
echo "Artifacts written:"
echo "  $OUTPUT_DIR/final-url.txt"
echo "  $OUTPUT_DIR/title.txt"
echo "  $OUTPUT_DIR/snapshot-interactive.json"
echo "  $OUTPUT_DIR/snapshot-interactive.txt"
if [[ "$SCREENSHOT" -eq 1 ]]; then
  echo "  $OUTPUT_DIR/screenshot.png"
fi
