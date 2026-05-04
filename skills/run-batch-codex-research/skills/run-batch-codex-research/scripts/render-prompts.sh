#!/usr/bin/env bash
# render-prompts.sh — generate per-input prompt files from a template.
#
# Usage:
#   render-prompts.sh INPUT_LIST TEMPLATE PROMPTS_DIR [PLACEHOLDER]
#
#   INPUT_LIST    path to file. Two formats accepted:
#                   (a) tab-delimited "name<TAB>content" (one per line)
#                   (b) plain lines — each line becomes both slug and content.
#                   Collisions on the resulting slug are skipped (with a stderr
#                   warning) — the first occurrence wins; disambiguate the
#                   input list and re-render to recover dropped entries.
#   TEMPLATE      path to template file containing PLACEHOLDER.
#   PROMPTS_DIR   directory to write rendered prompts into (created if missing).
#   PLACEHOLDER   token to replace in the template. Default: XXXXXXXXXXXXX.
#
# Filename rule: <slug>.md, where slug comes from column 1 of the input
# (tab-delimited form) or from sanitising the line (plain form).
# A slug with characters outside [a-zA-Z0-9._-] gets those characters
# replaced with '-'. Collisions emit a warning to stderr and skip writing —
# the user must disambiguate.

set -u

if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  echo "usage: $0 INPUT_LIST TEMPLATE PROMPTS_DIR [PLACEHOLDER]" >&2
  exit 2
fi

INPUT_LIST="$1"
TEMPLATE="$2"
PROMPTS_DIR="$3"
PLACEHOLDER="${4:-XXXXXXXXXXXXX}"

[ -f "$INPUT_LIST" ] || { echo "input list not found: $INPUT_LIST" >&2; exit 1; }
[ -f "$TEMPLATE" ]   || { echo "template not found: $TEMPLATE" >&2; exit 1; }

mkdir -p "$PROMPTS_DIR"

template="$(cat "$TEMPLATE")"
written=0
skipped=0
linenum=0

while IFS= read -r line || [ -n "$line" ]; do
  linenum=$((linenum + 1))
  [ -z "$line" ] && continue

  if [[ "$line" == *$'\t'* ]]; then
    name="${line%%$'\t'*}"
    content="${line#*$'\t'}"
  else
    name="$line"
    content="$line"
  fi

  # Sanitise slug
  slug="$(printf '%s' "$name" | tr -c 'a-zA-Z0-9._-' '-' | sed -E 's/^-+|-+$//g; s/-+/-/g')"
  if [ -z "$slug" ]; then
    echo "warn: line $linenum produced empty slug, skipping: $line" >&2
    skipped=$((skipped + 1))
    continue
  fi

  out="$PROMPTS_DIR/$slug.md"
  if [ -e "$out" ]; then
    echo "warn: collision on $slug.md (line $linenum), skipping — disambiguate input" >&2
    skipped=$((skipped + 1))
    continue
  fi

  # Substitute placeholder. Use awk for safe literal replacement
  # (no regex interpretation of either side).
  awk -v ph="$PLACEHOLDER" -v val="$content" '
    BEGIN { lp = length(ph) }
    {
      out = ""; line = $0
      while ( (i = index(line, ph)) > 0 ) {
        out = out substr(line, 1, i-1) val
        line = substr(line, i + lp)
      }
      print out line
    }
  ' <<<"$template" > "$out"

  written=$((written + 1))
done < "$INPUT_LIST"

echo "rendered: $written file(s) into $PROMPTS_DIR"
[ "$skipped" -gt 0 ] && echo "skipped:  $skipped (collisions or empty slugs — see warnings)" >&2
