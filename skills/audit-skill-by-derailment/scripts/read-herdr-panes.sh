#!/usr/bin/env bash
# scripts/read-herdr-panes.sh
# Read, format, and extract thought blocks and tool calls from one or multiple Herdr agent panes.
set -euo pipefail

LINES=300
SOURCE="recent-unwrapped"
EXTRACT_THOUGHTS=false
EXTRACT_TOOLS=false
TARGET_PANES=()

print_usage() {
  cat <<HELP
Usage: $(basename "$0") [options] <pane-id> [pane-id2 ...]

Arguments:
  pane-id                  One or more Herdr pane IDs (e.g., wJ:p2, wH:p4, wK:p2)

Options:
  -n, --lines <N>          Number of scrollback lines to fetch per pane (default: 300)
      --source <src>       Herdr source: recent-unwrapped (default), visible, recent, detection
      --thoughts           Extract and highlight agent thought/reasoning blocks
      --tools              Extract and highlight agent tool call execution lines
  -h, --help               Show this help message

Examples:
  $(basename "$0") wJ:p2 wH:p4 --lines 400
  $(basename "$0") wK:p2 --thoughts
  $(basename "$0") $(herdr agent list | jq -r '.result.agents[].pane_id') --lines 200
HELP
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--lines) LINES="$2"; shift 2 ;;
    --source) SOURCE="$2"; shift 2 ;;
    --thoughts) EXTRACT_THOUGHTS=true; shift ;;
    --tools) EXTRACT_TOOLS=true; shift ;;
    -h|--help) print_usage; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; print_usage; exit 1 ;;
    *) TARGET_PANES+=("$1"); shift ;;
  esac
done

if [[ ${#TARGET_PANES[@]} -eq 0 ]]; then
  echo "❌ Error: No target panes specified." >&2
  print_usage
  exit 1
fi

if ! command -v herdr &>/dev/null; then
  echo "❌ Error: 'herdr' command not found in PATH." >&2
  exit 1
fi

for pane in "${TARGET_PANES[@]}"; do
  echo "════════════════════════════════════════════════════════════════"
  echo "  Herdr Pane Scrollback: $pane (Lines: $LINES, Source: $SOURCE)"
  echo "════════════════════════════════════════════════════════════════"

  RAW_OUTPUT=$(herdr pane read "$pane" --source "$SOURCE" --lines "$LINES" 2>/dev/null || echo "ERROR: Could not read pane $pane")

  if [[ "$EXTRACT_THOUGHTS" == "true" ]]; then
    echo "─── Thought / Reasoning Blocks ───"
    echo "$RAW_OUTPUT" | grep -E "(Thought for|▸ Thought|thinking:)" -A 2 || echo "No thought blocks found."
    echo ""
  fi

  if [[ "$EXTRACT_TOOLS" == "true" ]]; then
    echo "─── Tool Invocations ───"
    echo "$RAW_OUTPUT" | grep -E "(● Edit|● Read|● Bash|● ListDir|● Find|● ManageTask)" || echo "No tool calls found."
    echo ""
  fi

  if [[ "$EXTRACT_THOUGHTS" != "true" && "$EXTRACT_TOOLS" != "true" ]]; then
    echo "$RAW_OUTPUT"
  fi
  echo ""
done
