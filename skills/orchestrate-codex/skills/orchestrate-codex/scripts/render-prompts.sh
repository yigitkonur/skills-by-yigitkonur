#!/usr/bin/env bash
# render-prompts.sh — generate per-input prompt files from a template.
#
# Used by batch mode and by exec mode (when tasks share a template). For each
# line in INPUT_LIST, substitute PLACEHOLDER in TEMPLATE with the line's
# content, write to PROMPTS_DIR/<slug>.md.
#
# Usage:
#   render-prompts.sh INPUT_LIST TEMPLATE PROMPTS_DIR [PLACEHOLDER]
#
#   INPUT_LIST    path to file. Two formats accepted:
#                   (a) tab-delimited "name<TAB>content" (one per line)
#                   (b) plain lines — each line becomes both slug and content.
#                   Collisions on the slug are hard failures; disambiguate
#                   the input before dispatching.
#   TEMPLATE      template file containing PLACEHOLDER.
#   PROMPTS_DIR   destination dir (created if missing).
#   PLACEHOLDER   token to replace. Default: XXXXXXXXXXXXX.
#
# Slug rule: chars outside [a-zA-Z0-9._-] are replaced with '-' and runs of
# '-' collapse. Empty slugs are skipped with a stderr warning.
#
# Exit codes: 0 OK,
#             1 input list / template not found, 2 usage error.
#
# The awk substitution semantics (no regex, no backslash interpretation,
# ENVIRON-based value passing) are load-bearing for inputs containing
# `\n`, `C:\path`, etc.

set -u

if [[ "$#" -lt 3 || "$#" -gt 4 ]]; then
  echo "usage: $0 INPUT_LIST TEMPLATE PROMPTS_DIR [PLACEHOLDER]" >&2
  exit 2
fi

INPUT_LIST="$1"
TEMPLATE="$2"
PROMPTS_DIR="$3"
PLACEHOLDER="${4:-XXXXXXXXXXXXX}"

[[ -f "$INPUT_LIST" ]] || { echo "input list not found: $INPUT_LIST" >&2; exit 1; }
[[ -f "$TEMPLATE" ]]   || { echo "template not found: $TEMPLATE" >&2; exit 1; }

mkdir -p "$PROMPTS_DIR"

template="$(cat "$TEMPLATE")"
written=0
linenum=0

while IFS= read -r line || [[ -n "$line" ]]; do
  linenum=$((linenum + 1))
  [[ -z "$line" ]] && continue

  if [[ "$line" == *$'\t'* ]]; then
    name="${line%%$'\t'*}"
    content="${line#*$'\t'}"
  else
    name="$line"
    content="$line"
  fi

  # Sanitise slug
  slug="$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9._-' '-' | sed -E 's/^-+|-+$//g; s/-+/-/g')"
  if [[ -z "$slug" ]]; then
    echo "error: line $linenum produced empty slug: $line" >&2
    exit 1
  fi

  out="$PROMPTS_DIR/$slug.md"
  if [[ -e "$out" ]]; then
    echo "error: collision on $slug.md (line $linenum); disambiguate input" >&2
    exit 1
  fi

  # Substitute placeholder via awk for safe literal replacement (no regex,
  # no backslash interpretation). Pass `val` through ENVIRON so awk does NOT
  # interpret `\n` / `\\` escapes — `-v val=...` would corrupt `C:\path`.
  PROMPT_VAL="$content" awk -v ph="$PLACEHOLDER" '
    BEGIN { val = ENVIRON["PROMPT_VAL"]; lp = length(ph) }
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
exit 0
