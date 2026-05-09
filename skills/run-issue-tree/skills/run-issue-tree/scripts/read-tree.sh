#!/usr/bin/env bash
# Recursively reads a GitHub issue tree and outputs structured markdown.
# Usage: read-tree.sh OWNER/REPO ISSUE_NUMBER [DEPTH]
# Set FULL=1 to include issue bodies. Set MAX_DEPTH to limit recursion (default 8).
# Set VERIFY_PARENTS=0 to skip REST parent checks.
set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  sed -n '2,5p' "$0" | sed 's/^# //'
  exit 0
fi

REPO="${1:?Usage: read-tree.sh OWNER/REPO ISSUE_NUMBER [DEPTH]}"
ISSUE="${2:?Usage: read-tree.sh OWNER/REPO ISSUE_NUMBER [DEPTH]}"
DEPTH="${3:-0}"
MAX_DEPTH="${MAX_DEPTH:-8}"
VERIFY_PARENTS="${VERIFY_PARENTS:-1}"

command -v gh >/dev/null || { echo "ERROR: gh CLI is required" >&2; exit 1; }
command -v jq >/dev/null || { echo "ERROR: jq is required" >&2; exit 1; }

api() {
  gh api \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2026-03-10" \
    "$@"
}

if [ "$DEPTH" -ge "$MAX_DEPTH" ]; then
  printf '%*s' $((DEPTH * 2)) ''
  echo "... (max depth $MAX_DEPTH reached)"
  exit 0
fi

INDENT=$(printf '%*s' $((DEPTH * 2)) '')

ISSUE_JSON=$(api "repos/$REPO/issues/$ISSUE" 2>/dev/null) || {
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

CHILDREN=$(api --paginate "repos/$REPO/issues/$ISSUE/sub_issues" --jq '.[].number') || {
  echo "${INDENT}- ERROR: could not list sub-issues for #$ISSUE" >&2
  exit 1
}

for CHILD in $CHILDREN; do
  if [ "$VERIFY_PARENTS" != "0" ]; then
    PARENT=$(api "repos/$REPO/issues/$CHILD/parent" --jq '.number') || {
      echo "${INDENT}- ERROR: could not fetch parent for child #$CHILD" >&2
      exit 1
    }
    if [ "$PARENT" != "$ISSUE" ]; then
      echo "${INDENT}- ERROR: child #$CHILD reports parent #$PARENT, expected #$ISSUE" >&2
      exit 1
    fi
  fi
  bash "$0" "$REPO" "$CHILD" "$((DEPTH + 1))"
done
