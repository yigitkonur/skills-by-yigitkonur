#!/usr/bin/env bash
# Links a child issue as a sub-issue of a parent via the GitHub REST API.
# Usage: link-sub-issue.sh OWNER/REPO PARENT_NUMBER CHILD_NUMBER [--replace-parent]
set -euo pipefail

usage() {
  echo "Usage: link-sub-issue.sh OWNER/REPO PARENT_NUMBER CHILD_NUMBER [--replace-parent]" >&2
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  echo ""
  echo "Links CHILD_NUMBER under PARENT_NUMBER using REST POST /issues/{issue_number}/sub_issues."
  echo "The child issue is fetched first because the REST body requires its numeric REST id."
  exit 0
fi

REPO="${1:-}"
PARENT="${2:-}"
CHILD="${3:-}"
REPLACE_PARENT="${4:-}"

if [ -z "$REPO" ] || [ -z "$PARENT" ] || [ -z "$CHILD" ]; then
  usage
  exit 1
fi

if [ -n "$REPLACE_PARENT" ] && [ "$REPLACE_PARENT" != "--replace-parent" ]; then
  usage
  exit 1
fi

command -v gh >/dev/null || { echo "ERROR: gh CLI is required" >&2; exit 1; }
command -v jq >/dev/null || { echo "ERROR: jq is required" >&2; exit 1; }

api() {
  gh api \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2026-03-10" \
    "$@"
}

PARENT_NUMBER=$(api "repos/$REPO/issues/$PARENT" --jq '.number') || {
  echo "ERROR: parent #$PARENT not found in $REPO" >&2
  exit 1
}

CHILD_JSON=$(api "repos/$REPO/issues/$CHILD") || {
  echo "ERROR: child #$CHILD not found in $REPO" >&2
  exit 1
}

CHILD_REST_ID=$(echo "$CHILD_JSON" | jq -r '.id')
CHILD_OWNER=$(echo "$CHILD_JSON" | jq -r '.repository_url | split("/")[-2]')
PARENT_OWNER="${REPO%%/*}"

if [ "$CHILD_REST_ID" = "null" ] || [ -z "$CHILD_REST_ID" ]; then
  echo "ERROR: child #$CHILD has no REST id" >&2
  exit 1
fi

if [ "$CHILD_OWNER" != "$PARENT_OWNER" ]; then
  echo "ERROR: REST add-sub-issue requires the child to share the parent repository owner" >&2
  exit 1
fi

ARGS=(
  "repos/$REPO/issues/$PARENT_NUMBER/sub_issues"
  --method POST
  -F "sub_issue_id=$CHILD_REST_ID"
  --jq '{parent: '"$PARENT_NUMBER"', child: .number, title: .title}'
)

if [ "$REPLACE_PARENT" = "--replace-parent" ]; then
  ARGS+=(-F "replace_parent=true")
fi

RESULT=$(api "${ARGS[@]}") || {
  echo "ERROR: failed to link #$CHILD as sub-issue of #$PARENT_NUMBER" >&2
  exit 1
}

echo "$RESULT" | jq -r '"Linked #\(.child) as a sub-issue of #\(.parent): \(.title)"'
