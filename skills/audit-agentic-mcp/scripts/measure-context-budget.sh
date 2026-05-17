#!/usr/bin/env bash
set -euo pipefail

DESCRIPTION_THRESHOLD=400
SCHEMA_THRESHOLD=2000
RESPONSE_THRESHOLD=4000
TOOL_THRESHOLD=20

usage() {
  cat <<'USAGE'
measure-context-budget.sh - heuristic MCP token budget scan

Usage:
  measure-context-budget.sh [target-path] [options]
  measure-context-budget.sh --help

Options:
  --description-chars N   Flag description lines over N chars (default 400)
  --schema-chars N        Flag schema-ish files over N chars (default 2000)
  --response-chars N      Flag response/example lines over N chars (default 4000)
  --tool-threshold N      Flag active tool candidates over N (default 20)

Estimates tokens with chars/4. Output is deterministic Markdown. The scan is
heuristic and does not parse ASTs.
USAGE
}

TARGET="."
while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --description-chars)
      DESCRIPTION_THRESHOLD="${2:?missing value for --description-chars}"
      shift 2
      ;;
    --schema-chars)
      SCHEMA_THRESHOLD="${2:?missing value for --schema-chars}"
      shift 2
      ;;
    --response-chars)
      RESPONSE_THRESHOLD="${2:?missing value for --response-chars}"
      shift 2
      ;;
    --tool-threshold)
      TOOL_THRESHOLD="${2:?missing value for --tool-threshold}"
      shift 2
      ;;
    -*)
      echo "error: unknown option: $1" >&2
      exit 2
      ;;
    *)
      TARGET="$1"
      shift
      ;;
  esac
done

if [[ ! -d "$TARGET" ]]; then
  echo "error: target path is not a directory: $TARGET" >&2
  exit 2
fi

if command -v rg >/dev/null 2>&1; then
  HAS_RG=1
else
  HAS_RG=0
fi

scan() {
  local pattern="$1"
  if [[ "$HAS_RG" -eq 1 ]]; then
    rg -n --hidden \
      -g '!node_modules' -g '!vendor' -g '!dist' -g '!build' -g '!coverage' \
      -g '!*.lock' -g '!package-lock.json' -g '!pnpm-lock.yaml' \
      "$pattern" "$TARGET" 2>/dev/null || true
  else
    grep -RInE "$pattern" "$TARGET" \
      --exclude-dir=node_modules --exclude-dir=vendor --exclude-dir=dist \
      --exclude-dir=build --exclude-dir=coverage 2>/dev/null || true
  fi
}

token_estimate() {
  awk '{ total += length($0) } END { printf "%d", int((total + 3) / 4) }'
}

line_report_over() {
  local pattern="$1"
  local threshold="$2"
  local limit="${3:-20}"
  scan "$pattern" | awk -F: -v threshold="$threshold" -v limit="$limit" '
    {
      text=$0
      sub($1 ":" $2 ":", "", text)
      chars=length(text)
      if (chars > threshold && shown < limit) {
        printf "- %s:%s ~%d chars (~%d tok)\n", $1, $2, chars, int((chars + 3) / 4)
        shown++
      }
      count += (chars > threshold)
    }
    END {
      if (count > shown) printf "- ... %d more over threshold\n", count - shown
    }
  '
}

count_matches() {
  scan "$1" | wc -l | tr -d ' '
}

real_target() {
  (cd "$TARGET" && pwd)
}

TOOL_PATTERN='server\.tool|registerTool|@mcp\.tool|@tool|tool\('
DESCRIPTION_PATTERN='description[[:space:]]*:|\.describe\('
SCHEMA_PATTERN='inputSchema|outputSchema|z\.object|BaseModel|Field\(|jsonschema|JsonSchema'
RESPONSE_PATTERN='structuredContent|content:[[:space:]]*\[|return[[:space:]]*\{|JSON\.stringify|json\.dumps|example_response|sample_response'

tool_count="$(count_matches "$TOOL_PATTERN")"
description_lines="$(scan "$DESCRIPTION_PATTERN")"
schema_lines="$(scan "$SCHEMA_PATTERN")"
response_lines="$(scan "$RESPONSE_PATTERN")"

description_tokens="$(printf '%s\n' "$description_lines" | token_estimate)"
schema_tokens="$(printf '%s\n' "$schema_lines" | token_estimate)"
response_tokens="$(printf '%s\n' "$response_lines" | token_estimate)"
total_tokens=$((description_tokens + schema_tokens + response_tokens))

echo "# MCP Context Budget Scan"
echo
echo "Target: \`$(real_target)\`"
echo

echo "## Summary"
echo "- Tool registration candidates: $tool_count"
echo "- Description-ish lines: $(printf '%s\n' "$description_lines" | sed '/^$/d' | wc -l | tr -d ' ') (~${description_tokens} tok)"
echo "- Schema-ish lines: $(printf '%s\n' "$schema_lines" | sed '/^$/d' | wc -l | tr -d ' ') (~${schema_tokens} tok)"
echo "- Static response/example-ish lines: $(printf '%s\n' "$response_lines" | sed '/^$/d' | wc -l | tr -d ' ') (~${response_tokens} tok)"
echo "- Combined heuristic budget: ~${total_tokens} tok"
echo

echo "## Flags"
flagged=0
if [[ "$tool_count" -gt "$TOOL_THRESHOLD" ]]; then
  echo "- Active tool candidate count $tool_count exceeds threshold $TOOL_THRESHOLD."
  flagged=1
fi
long_descriptions="$(line_report_over "$DESCRIPTION_PATTERN" "$DESCRIPTION_THRESHOLD" 12)"
if [[ -n "$long_descriptions" ]]; then
  echo "### Long descriptions"
  echo "$long_descriptions"
  flagged=1
fi
long_schemas="$(line_report_over "$SCHEMA_PATTERN" "$SCHEMA_THRESHOLD" 12)"
if [[ -n "$long_schemas" ]]; then
  echo "### Large schema-ish lines"
  echo "$long_schemas"
  flagged=1
fi
long_responses="$(line_report_over "$RESPONSE_PATTERN" "$RESPONSE_THRESHOLD" 12)"
if [[ -n "$long_responses" ]]; then
  echo "### Large response/example-ish lines"
  echo "$long_responses"
  flagged=1
fi
if [[ "$flagged" -eq 0 ]]; then
  echo "- No threshold flags from the heuristic scan."
fi
echo

echo "## Likely Tool Definitions"
scan "$TOOL_PATTERN" | sed -n '1,25p' | sed 's/^/- /'
if [[ -z "$(scan "$TOOL_PATTERN" | sed -n '1p')" ]]; then
  echo "- No likely tool definitions found."
fi
echo

echo "## Assumptions"
echo "- Token estimate uses chars/4 and is intentionally rough."
echo "- Line-based matching may undercount multi-line schema blocks and overcount examples."
echo "- Tool candidates are regex matches, not confirmed active tools."
echo "- Thresholds are configurable; use stricter values for small-model or high-cost hosts."
echo "- No files were modified."
