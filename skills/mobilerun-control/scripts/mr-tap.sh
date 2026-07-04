#!/usr/bin/env bash
# mr-tap.sh — tap by box-center with human jitter.
# Uses the center formula ((x1+x2)/2,(y1+y2)/2) — the same point mobilerun computes — plus a small
# random offset, so taps scatter like a finger instead of landing dead-center every time (which
# reads robotic and can catch an overlapping child element).
#
# Usage:
#   mr-tap.sh --bounds "x1,y1,x2,y2" [--jitter PX] [SERIAL]   # tap a box
#   mr-tap.sh --xy X Y [SERIAL]                               # tap a raw point
# Default jitter: 6px (clamped to stay >=8px inside the box).
set -uo pipefail
export PATH="/opt/homebrew/bin:$HOME/.local/bin:$PATH"

DEV="${MR_DEVICE:-}"; B=""; JIT=6; PX=""; PY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --bounds) B="$2"; shift 2 ;;
    --jitter) JIT="$2"; shift 2 ;;
    --xy) PX="$2"; PY="$3"; shift 3 ;;
    *) DEV="$1"; shift ;;
  esac
done
[ -z "$DEV" ] && DEV="$(adb devices | awk 'NR>1 && $2=="device"{print $1; exit}')"

if [ -n "$B" ]; then
  IFS=', ' read -r X1 Y1 X2 Y2 <<EOF
$B
EOF
  CX=$(( (X1 + X2) / 2 )); CY=$(( (Y1 + Y2) / 2 ))
  # clamp jitter so we stay safely inside the box
  HW=$(( (X2 - X1) / 2 - 8 )); HH=$(( (Y2 - Y1) / 2 - 8 ))
  [ "$HW" -lt 0 ] && HW=0; [ "$HH" -lt 0 ] && HH=0
  JX=$JIT; [ "$JX" -gt "$HW" ] && JX=$HW
  JY=$JIT; [ "$JY" -gt "$HH" ] && JY=$HH
  OX=0; OY=0
  [ "$JX" -gt 0 ] && OX=$(( RANDOM % (2*JX+1) - JX ))
  [ "$JY" -gt 0 ] && OY=$(( RANDOM % (2*JY+1) - JY ))
  PX=$(( CX + OX )); PY=$(( CY + OY ))
fi
[ -z "$PX" ] && { echo "mr-tap: need --bounds or --xy" >&2; exit 2; }

mobilerun device tap "$PX" "$PY" -d "$DEV" 2>&1 | tail -1
