#!/usr/bin/env bash
# mr-wait.sh — human-like randomized pause between actions (stealth/pacing).
# Real users do not act on a fixed cadence. Use after taps/scrolls and as a
# "reading dwell" when the task implies the user is looking at content.
#
# Usage:  mr-wait.sh [MIN] [MAX]      # seconds (float); defaults 0.6 1.8
#         mr-wait.sh read             # longer "reading a post" dwell 2.5-6.0
#         mr-wait.sh think            # short "deciding" dwell 0.4-1.2
set -uo pipefail
case "${1:-}" in
  read)  MIN=2.5; MAX=6.0 ;;
  think) MIN=0.4; MAX=1.2 ;;
  *)     MIN="${1:-0.6}"; MAX="${2:-1.8}" ;;
esac
S="$(awk -v min="$MIN" -v max="$MAX" 'BEGIN{srand();printf "%.2f",min+rand()*(max-min)}')"
sleep "$S"
echo "waited ${S}s"
