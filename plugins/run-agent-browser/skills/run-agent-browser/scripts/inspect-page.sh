#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: inspect-page.sh [--screenshot] URL [output-dir]

Captures URL, title, interactive snapshots, readable DOM, and browser errors.
On Yigit's Mac it uses and safely releases the managed headed-CDP pool. Where
the pool is unavailable it uses an isolated temporary upstream session.
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

if command -v agent-browser >/dev/null 2>&1; then
  AB_CMD=(agent-browser)
else
  AB_CMD=(npx --no-install agent-browser)
fi

MANAGED=0
SESSION=""
OWNED_TAB=""
if "${AB_CMD[@]}" pool status >/dev/null 2>&1; then
  MANAGED=1
else
  SESSION="inspect-page-$$-$(date +%s)"
fi

run_ab() {
  if [[ "$MANAGED" -eq 1 ]]; then
    "${AB_CMD[@]}" "$@"
  else
    "${AB_CMD[@]}" --session "$SESSION" "$@"
  fi
}

cleanup() {
  if [[ "$MANAGED" -eq 1 ]]; then
    if [[ -n "$OWNED_TAB" ]]; then
      if ! "${AB_CMD[@]}" tab close "$OWNED_TAB" >/dev/null 2>&1; then
        "${AB_CMD[@]}" tab "$OWNED_TAB" >/dev/null 2>&1 || true
        "${AB_CMD[@]}" open about:blank >/dev/null 2>&1 || true
      fi
    fi
    "${AB_CMD[@]}" close >/dev/null 2>&1 || true
  else
    run_ab close >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "resolved command: ${AB_CMD[*]}"
echo "runtime:          $([[ "$MANAGED" -eq 1 ]] && echo managed-pool || echo upstream-session)"
[[ -z "$SESSION" ]] || echo "session:          $SESSION"
echo "url:              $URL"
echo "output dir:       $OUTPUT_DIR"

run_ab open "$URL"
if [[ "$MANAGED" -eq 1 ]]; then
  "${AB_CMD[@]}" pool current
  OWNED_TAB="$("${AB_CMD[@]}" --json tab | sed -n 's/.*"active":true[^}]*"tabId":"\([^"]*\)".*/\1/p' | head -n 1)"
  [[ -n "$OWNED_TAB" ]] || { echo "Could not determine active task tab" >&2; exit 1; }
fi

if ! run_ab wait --load networkidle >/dev/null 2>&1; then
  run_ab wait --load domcontentloaded >/dev/null
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
