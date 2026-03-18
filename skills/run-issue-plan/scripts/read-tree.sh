#!/usr/bin/env bash
# Recursively reads a GitHub issue tree and outputs structured markdown.
# Usage: read-tree.sh OWNER/REPO ISSUE_NUMBER [DEPTH]
# Set FULL=1 to include issue bodies. Set MAX_DEPTH to limit recursion (default 8).
set -euo pipefail

REPO="${1:?Usage: read-tree.sh OWNER/REPO ISSUE_NUMBER [DEPTH]}"
ISSUE="${2:?Usage: read-tree.sh OWNER/REPO ISSUE_NUMBER [DEPTH]}"
DEPTH="${3:-0}"
MAX_DEPTH="${MAX_DEPTH:-8}"

if [ "$DEPTH" -ge "$MAX_DEPTH" ]; then
  printf '%*s' $((DEPTH * 2)) ''
  echo "... (max depth $MAX_DEPTH reached)"
  exit 0
fi

INDENT=$(printf '%*s' $((DEPTH * 2)) '')

ISSUE_JSON=$(gh api "repos/$REPO/issues/$ISSUE" 2>/dev/null) || {
  echo "${INDENT}- ERROR: could not fetch #$ISSUE" >&2; exit 1
}

TITLE=$(echo "$ISSUE_JSON" | jq -r '.title')
STATE=$(echo "$ISSUE_JSON" | jq -r '.state')
LABELS=$(echo "$ISSUE_JSON" | jq -r '[.labels[].name] | join(", ")')
BODY=$(echo "$ISSUE_JSON" | jq -r '.body // ""')
ASSIGNEES=$(echo "$ISSUE_JSON" | jq -r '[.assignees[].login] | join(", ")')

[ "$STATE" = "closed" ] && ICON="[x]" || ICON="[ ]"

echo "${INDENT}- ${ICON} **#${ISSUE}**: ${TITLE}"
[ -n "$LABELS" ] && echo "${INDENT}  Labels: \`${LABELS}\`"
[ -n "$ASSIGNEES" ] && echo "${INDENT}  Assignees: ${ASSIGNEES}"

if [ "${FULL:-0}" = "1" ] && [ -n "$BODY" ]; then
  echo "${INDENT}  <details><summary>Body</summary>"
  echo ""
  echo "$BODY" | sed "s/^/${INDENT}  /"
  echo ""
  echo "${INDENT}  </details>"
fi

CHILDREN=$(gh api "repos/$REPO/issues/$ISSUE/sub_issues" --jq '.[].number' 2>/dev/null || true)
for CHILD in $CHILDREN; do
  bash "$0" "$REPO" "$CHILD" "$((DEPTH + 1))"
done
