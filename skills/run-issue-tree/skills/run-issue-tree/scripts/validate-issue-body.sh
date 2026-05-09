#!/usr/bin/env bash
# Validates a GitHub Issue body before creation or dispatch.
# Usage: validate-issue-body.sh BODY_FILE [--repo OWNER/REPO]
set -euo pipefail

usage() {
  echo "Usage: validate-issue-body.sh BODY_FILE [--repo OWNER/REPO]" >&2
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

BODY_FILE="${1:-}"
REPO=""

if [ -z "$BODY_FILE" ]; then
  usage
  exit 1
fi
shift

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo)
      REPO="${2:-}"
      shift 2
      ;;
    *)
      usage
      exit 1
      ;;
  esac
done

if [ ! -f "$BODY_FILE" ]; then
  echo "ERROR: body file not found: $BODY_FILE" >&2
  exit 1
fi

if [ -n "$REPO" ]; then
  command -v gh >/dev/null || { echo "ERROR: gh CLI is required when --repo is used" >&2; exit 1; }
fi

errors=0
warnings=0
char_count=$(wc -c < "$BODY_FILE" | tr -d ' ')

if [ "$char_count" -gt 60000 ]; then
  echo "ERROR: body is $char_count chars; split before creating the issue"
  errors=$((errors + 1))
elif [ "$char_count" -gt 40000 ]; then
  echo "WARNING: body is $char_count chars; consider splitting for readability"
  warnings=$((warnings + 1))
fi

required_sections=(
  "## Context & Rationale"
  "## Strategic Intent"
  "## Definition of Done"
  "## Wave & Dependencies"
)

for section in "${required_sections[@]}"; do
  if ! grep -qF "$section" "$BODY_FILE"; then
    echo "ERROR: missing required section: $section"
    errors=$((errors + 1))
  fi
done

required_lines=(
  "You own this problem. Explore freely, trust your judgment, adapt as needed."
  "You must achieve 100% of every criterion above before stopping."
  "Partial completion = not complete. Do not hand back until every item is fully satisfied."
)

for line in "${required_lines[@]}"; do
  if ! grep -qF "$line" "$BODY_FILE"; then
    echo "ERROR: missing protocol line: $line"
    errors=$((errors + 1))
  fi
done

vague_patterns=(
  "tests pass"
  "works correctly"
  "code is clean"
  "follows best practices"
  "good performance"
  "handles errors gracefully"
  "is user-friendly"
  "should be fast"
)

for pattern in "${vague_patterns[@]}"; do
  if grep -qiF "$pattern" "$BODY_FILE"; then
    echo "ERROR: vague DoD pattern detected: $pattern"
    errors=$((errors + 1))
  fi
done

tool_specific_pattern='(^|[^[:alnum:]_-])(npm|pnpm|yarn|bun|pytest|go test|cargo test|mvn|gradle|make|jest|vitest|playwright|eslint|biome|ruff|tsc --noEmit)([^[:alnum:]_-]|$)'
if grep -Eiq "$tool_specific_pattern" "$BODY_FILE"; then
  echo "ERROR: tool-specific command pattern detected; describe verification outcomes instead"
  errors=$((errors + 1))
fi

if [ -n "$REPO" ]; then
  refs=$(grep -Eo '#[0-9]+' "$BODY_FILE" | sort -u || true)
  for ref in $refs; do
    number="${ref#\#}"
    if ! gh issue view "$number" --repo "$REPO" --json number -q .number >/dev/null 2>&1; then
      echo "ERROR: referenced issue does not exist in $REPO: $ref"
      errors=$((errors + 1))
    fi
  done
fi

if [ "$errors" -gt 0 ]; then
  echo "FAILED: $errors error(s), $warnings warning(s)"
  exit 1
fi

echo "OK: $BODY_FILE ($char_count chars, $warnings warning(s))"
