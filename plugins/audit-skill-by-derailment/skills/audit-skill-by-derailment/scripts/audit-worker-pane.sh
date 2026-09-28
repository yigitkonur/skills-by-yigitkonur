#!/usr/bin/env bash
# scripts/audit-worker-pane.sh
# Performs an automated forensic audit on a Herdr worker agent pane, extracting
# unwrapped terminal scrollback, tool calls, errors, thoughts, and physical disk artifacts.
set -euo pipefail

LINES=500
OUTPUT_DIR=""
TARGET_PANE=""
EXTRACT_THOUGHTS=false
EXTRACT_TOOLS=false
EXTRACT_RECEIPTS=false

print_usage() {
  cat <<HELP
Usage: $(basename "$0") <pane-id> [options]

Arguments:
  <pane-id>                Herdr pane ID to audit (e.g., w2N:pP, w2N:pQ)

Options:
  -n, --lines <N>          Number of scrollback lines to fetch (default: 500)
  -d, --output-dir <DIR>   Physical directory to audit for generated file artifacts
      --thoughts           Extract and display model thought/reasoning blocks
      --tools              Extract and display executed tool commands
      --receipts           Extract delimited JSON receipts (__TAKE_RESULT_JSON...)
  -h, --help               Show this help message

Examples:
  $(basename "$0") w2N:pP
  $(basename "$0") w2N:pP -d ~/Downloads/flow-videos/scenes/
  $(basename "$0") w2N:pQ --thoughts --tools
HELP
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--lines) LINES="$2"; shift 2 ;;
    -d|--output-dir) OUTPUT_DIR="$2"; shift 2 ;;
    --thoughts) EXTRACT_THOUGHTS=true; shift ;;
    --tools) EXTRACT_TOOLS=true; shift ;;
    --receipts) EXTRACT_RECEIPTS=true; shift ;;
    -h|--help) print_usage; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; print_usage; exit 1 ;;
    *) TARGET_PANE="$1"; shift ;;
  esac
done

if [[ -z "$TARGET_PANE" ]]; then
  echo "❌ Error: Target pane ID is required." >&2
  print_usage
  exit 1
fi

if ! command -v herdr &>/dev/null; then
  echo "❌ Error: 'herdr' command not found in PATH." >&2
  exit 1
fi

if ! command -v jq &>/dev/null; then
  echo "❌ Error: 'jq' command not found in PATH." >&2
  exit 1
fi

echo "════════════════════════════════════════════════════════════════"
echo "  FORENSIC AUDIT: Herdr Pane $TARGET_PANE"
echo "════════════════════════════════════════════════════════════════"

# 1. Inspect Agent Status via herdr agent list
AGENT_INFO=$(herdr agent list 2>/dev/null | jq -r --arg p "$TARGET_PANE" '.result.agents[]? | select(.pane_id == $p)' || true)

if [[ -n "$AGENT_INFO" ]]; then
  STATUS=$(echo "$AGENT_INFO" | jq -r '.agent_status // "unknown"')
  NAME=$(echo "$AGENT_INFO" | jq -r '.name // "unnamed"')
  KIND=$(echo "$AGENT_INFO" | jq -r '.agent // "unknown"')
  CWD=$(echo "$AGENT_INFO" | jq -r '.cwd // "unknown"')
  echo "Agent Name:   $NAME"
  echo "Engine Kind:  $KIND"
  echo "Status:       $STATUS"
  echo "Working Dir:  $CWD"
else
  echo "Agent Status: Pane not listed in active agent registry or agent terminated."
fi
echo ""

# 2. Fetch Recent Unwrapped Scrollback
if ! SCROLLBACK=$(herdr pane read "$TARGET_PANE" --source recent-unwrapped --lines "$LINES" 2>/dev/null); then
  echo "❌ Error: Failed to read scrollback from pane '$TARGET_PANE'." >&2
  exit 1
fi

# Check for non-zero exits or errors
ERRORS=$(echo "$SCROLLBACK" | grep -E "(exited with code [1-9]|TypeError:|Error:|Exception:|[Ff]ailed to)" || true)

echo "─── 1. Error & Crash Signals ───"
if [[ -n "$ERRORS" ]]; then
  echo "⚠️ Detected potential error signals in scrollback:"
  echo "$ERRORS" | head -n 15
else
  echo "✅ No prominent crash lines detected in last $LINES lines."
fi
echo ""

# 3. Extract Tools / Commands if requested
if [[ "$EXTRACT_TOOLS" == "true" ]]; then
  echo "─── 2. Executed CLI & Tool Commands ───"
  echo "$SCROLLBACK" | grep -E "(CommandLine:|● Run command:|● Bash|Running command:)" | tail -n 20 || echo "No tool calls detected."
  echo ""
fi

# 4. Extract Thoughts if requested or by default brief
if [[ "$EXTRACT_THOUGHTS" == "true" ]]; then
  echo "─── 3. Thought & Reasoning Chains ───"
  echo "$SCROLLBACK" | grep -E "(Thinking Process:|▸ Thought|Thought for|thinking:)" -A 4 || echo "No thought blocks detected."
  echo ""
fi

# 5. Extract JSON Receipts
if [[ "$EXTRACT_RECEIPTS" == "true" || "$SCROLLBACK" == *"__TAKE_RESULT_JSON"* ]]; then
  echo "─── 4. Machine-Readable JSON Receipts ───"
  if [[ "$SCROLLBACK" == *"__TAKE_RESULT_JSON_START__"* && "$SCROLLBACK" == *"__TAKE_RESULT_JSON_END__"* ]]; then
    RECEIPTS=$(echo "$SCROLLBACK" | sed -n '/__TAKE_RESULT_JSON_START__/,/__TAKE_RESULT_JSON_END__/p' | grep -v "__TAKE_RESULT_JSON" || true)
    if [[ -n "$RECEIPTS" ]]; then
      echo "$RECEIPTS"
    else
      echo "No valid delimited JSON receipts found."
    fi
  elif [[ "$SCROLLBACK" == *"__TAKE_RESULT_JSON_START__"* ]]; then
    echo "⚠️ Unterminated receipt detected: __TAKE_RESULT_JSON_START__ present without matching __TAKE_RESULT_JSON_END__."
  else
    if [[ "$EXTRACT_RECEIPTS" == "true" ]]; then
      echo "No delimited JSON receipts found."
    fi
  fi
  echo ""
fi

# 6. Physical Disk Evidence Audit
if [[ -n "$OUTPUT_DIR" ]]; then
  echo "─── 5. Physical Disk Verification: $OUTPUT_DIR ───"
  if [[ -d "$OUTPUT_DIR" ]]; then
    FILES=$(find "$OUTPUT_DIR" -type f \( -name "*.mp4" -o -name "*.mp3" -o -name "*.png" -o -name "*.json" \) 2>/dev/null || true)
    if [[ -z "$FILES" ]]; then
      echo "⚠️ Output directory exists but contains zero matching media files!"
    else
      printf "%-35s | %10s | %-25s | %s\n" "Filename" "Size (B)" "Type / Magic Header" "Status"
      echo "----------------------------------------------------------------------------------------"
      find "$OUTPUT_DIR" -type f \( -name "*.mp4" -o -name "*.mp3" -o -name "*.png" -o -name "*.json" \) -print0 2>/dev/null | while IFS= read -r -d '' f; do
        sz=$(wc -c < "$f" 2>/dev/null | tr -d ' ' || echo "-1")
        [[ -z "$sz" ]] && sz="-1"
        mtype=$(file --brief "$f" 2>/dev/null || echo "unknown")
        ext="${f##*.}"
        ext_lower=$(echo "$ext" | tr '[:upper:]' '[:lower:]')
        mtype_lower=$(echo "$mtype" | tr '[:upper:]' '[:lower:]')

        if [[ "$sz" -eq -1 ]]; then
          st="UNREADABLE"
        elif [[ "$sz" -lt 1000 ]]; then
          st="SUSPICIOUS (<1KB)"
        elif [[ "$mtype" == "unknown" ]]; then
          st="SUSPICIOUS (unknown format)"
        elif [[ "$ext_lower" == "mp4" && "$mtype_lower" != *"mp4"* && "$mtype_lower" != *"iso media"* && "$mtype_lower" != *"video"* ]]; then
          st="MISMATCH (expected MP4, got $mtype)"
        elif [[ "$ext_lower" == "mp3" && "$mtype_lower" != *"audio"* && "$mtype_lower" != *"mpeg"* && "$mtype_lower" != *"id3"* ]]; then
          st="MISMATCH (expected MP3, got $mtype)"
        elif [[ "$ext_lower" == "png" && "$mtype_lower" != *"png"* && "$mtype_lower" != *"image"* ]]; then
          st="MISMATCH (expected PNG, got $mtype)"
        elif [[ "$ext_lower" == "json" && "$mtype_lower" != *"json"* && "$mtype_lower" != *"text"* && "$mtype_lower" != *"ascii"* ]]; then
          st="MISMATCH (expected JSON, got $mtype)"
        else
          st="OK"
        fi
        printf "%-35s | %10s | %-25s | %s\n" "$(basename "$f")" "$sz" "${mtype:0:25}" "$st"
      done
    fi
  else
    echo "❌ Output directory does not exist: $OUTPUT_DIR"
  fi
  echo ""
fi

echo "════════════════════════════════════════════════════════════════"
echo "  Audit Extraction Complete."
echo "════════════════════════════════════════════════════════════════"
