#!/usr/bin/env bash
# mr-type.sh — enter text two ways: atomic paste (default) or human-paced typing.
# Text lands in the focused field, so focus it first (tap it, wait ~0.5s) before calling this.
#
#   mr-type.sh "text" [--clear] [SERIAL]            # ATOMIC paste (default)
#       -> Portal keyboard/input content endpoint, base64. Instant, handles
#          long/Unicode/special text, and works even when the Mobilerun IME
#          is not the active keyboard.
#   mr-type.sh "text" --human [--clear] [SERIAL]    # HUMAN typing
#       -> splits into word chunks typed via 'mobilerun device type' with
#          randomized 0.25-0.7s pauses, so it reads hand-typed (use for
#          comments/messages, not search boxes).
#   mr-type.sh --clear [SERIAL]                     # CLEAR-TO-EMPTY
#       -> blanks the focused field (no new text). Prints "Cleared field".
#          Use to empty a search/box rather than replace it; verify the
#          field's text returns to its placeholder.
set -uo pipefail
export PATH="/opt/homebrew/bin:$HOME/.local/bin:$PATH"

DEV="${MR_DEVICE:-}"; TXT=""; CLEAR="false"; HUMAN=0
while [ $# -gt 0 ]; do
  case "$1" in
    --clear) CLEAR="true"; shift ;;
    --human) HUMAN=1; shift ;;
    -*) shift ;;
    *) if [ -z "$TXT" ]; then TXT="$1"; else DEV="$1"; fi; shift ;;
  esac
done
[ -z "$DEV" ] && DEV="$(adb devices | awk 'NR>1 && $2=="device"{print $1; exit}')"

# clear-to-empty: `--clear` with no text blanks the focused field (honor the flag instead of
# erroring — clearing a field IS a valid type op, and the paste endpoint can't blank from here).
if [ -z "$TXT" ] && [ "$CLEAR" = "true" ]; then
  mobilerun device type "" --clear -d "$DEV" >/dev/null 2>&1 \
    && { echo "Cleared field"; exit 0; } \
    || { echo "mr-type: clear failed" >&2; exit 1; }
fi
[ -z "$TXT" ] && { echo "mr-type: no text (pass --clear alone to blank a field)" >&2; exit 2; }

rand_sleep() { awk -v min="$1" -v max="$2" 'BEGIN{srand();printf "%.2f",min+rand()*(max-min)}'; }

if [ "$HUMAN" = 1 ]; then
  # type chunk-by-chunk with human pauses
  [ "$CLEAR" = "true" ] && mobilerun device type "" --clear -d "$DEV" >/dev/null 2>&1
  first=1
  # split on spaces, re-adding a trailing space per word
  for word in $TXT; do
    seg="$word"; [ "$first" = 0 ] && seg=" $word"; first=0
    mobilerun device type "$seg" -d "$DEV" >/dev/null 2>&1
    sleep "$(rand_sleep 0.25 0.7)"
  done
  echo "Typed (human): $TXT"
else
  # atomic paste via Portal keyboard/input (base64)
  B64="$(printf '%s' "$TXT" | base64 | tr -d '\n')"
  adb -s "$DEV" shell content insert --uri content://com.mobilerun.portal/keyboard/input \
      --bind "base64_text:s:$B64" --bind "clear:b:$CLEAR" >/dev/null 2>&1 \
    && echo "Pasted: $TXT" \
    || { echo "paste endpoint failed; falling back to device type"; \
         mobilerun device type "$TXT" ${CLEAR:+--clear} -d "$DEV" 2>&1 | tail -1; }
fi
