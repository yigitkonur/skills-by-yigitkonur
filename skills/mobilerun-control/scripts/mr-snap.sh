#!/usr/bin/env bash
# mr-snap.sh — capture the screen once, correctly, for the DECIDE step.
# Prints the indexed UI tree to stdout and refuses an empty/again tree, so the tree you plan from
# is always a real one; saves the screenshot to a stable path (the raw one is an OS temp file).
#
# Usage:  mr-snap.sh [SERIAL] [--boxes]
#   --boxes : also save an overlay-annotated PNG (numbered boxes) via raw screencap.
# Output:  the UI tree on stdout; the last two lines are:
#            SHOT=<plain.png>
#            BOXES=<annotated.png>   (only with --boxes)
set -uo pipefail
export PATH="/opt/homebrew/bin:$HOME/.local/bin:$PATH"

DEV="${MR_DEVICE:-}"; BOXES=0
for a in "$@"; do
  case "$a" in
    --boxes) BOXES=1 ;;
    *) DEV="$a" ;;
  esac
done
[ -z "$DEV" ] && DEV="$(adb devices | awk 'NR>1 && $2=="device"{print $1; exit}')"
OUT="/tmp/mr/${DEV}"; mkdir -p "$OUT"
TS="$(date +%H%M%S)"

# UI tree, captured without a pipe so mobilerun's own exit code surfaces
ui="$(mobilerun device ui -d "$DEV" 2>/dev/null)"
if [ -z "$ui" ] || ! printf '%s' "$ui" | grep -q "Clickable UI elements"; then
  echo "SNAP FAIL: empty/again UI tree (a11y wedged or app blocks a11y). Run mr-preflight.sh; retry once." >&2
  exit 1
fi
printf '%s\n' "$ui"

# Plain screenshot -> copy off the OS temp path so it survives for later reads
tmp="$(mobilerun device screenshot -d "$DEV" 2>/dev/null | tail -1)"
shot="$OUT/snap_${TS}.png"
if [ -f "$tmp" ]; then cp "$tmp" "$shot"; echo "SHOT=$shot"; else echo "SHOT=ERROR" >&2; fi

# Optional annotated boxes: turn overlay on, raw screencap (captures the boxes), turn off
if [ "$BOXES" = 1 ]; then
  adb -s "$DEV" shell content insert --uri content://com.mobilerun.portal/overlay_visible --bind visible:b:true >/dev/null 2>&1
  sleep 0.5
  boxes="$OUT/boxes_${TS}.png"
  adb -s "$DEV" exec-out screencap -p > "$boxes" 2>/dev/null
  adb -s "$DEV" shell content insert --uri content://com.mobilerun.portal/overlay_visible --bind visible:b:false >/dev/null 2>&1
  echo "BOXES=$boxes"
fi
