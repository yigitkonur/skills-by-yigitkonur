#!/usr/bin/env bash
# Links a child issue as a sub-issue of a parent via GraphQL addSubIssue mutation.
# Uses GraphQL because the REST POST endpoint has known reliability issues.
# Usage: link-sub-issue.sh OWNER/REPO PARENT_NUMBER CHILD_NUMBER
set -euo pipefail

REPO="${1:?Usage: link-sub-issue.sh OWNER/REPO PARENT_NUMBER CHILD_NUMBER}"
OWNER="${REPO%%/*}"
REPONAME="${REPO##*/}"
PARENT="${2:?Parent issue number required}"
CHILD="${3:?Child issue number required}"

command -v gh >/dev/null || { echo "ERROR: gh CLI is required" >&2; exit 1; }
command -v jq >/dev/null || { echo "ERROR: jq is required" >&2; exit 1; }

PARENT_ID=$(gh api graphql -f query="
  query {
    repository(owner:\"$OWNER\", name:\"$REPONAME\") {
      issue(number:$PARENT) { id }
    }
  }
" --jq '.data.repository.issue.id')

[ -z "$PARENT_ID" ] || [ "$PARENT_ID" = "null" ] && { echo "ERROR: parent #$PARENT not found" >&2; exit 1; }

CHILD_ID=$(gh api graphql -f query="
  query {
    repository(owner:\"$OWNER\", name:\"$REPONAME\") {
      issue(number:$CHILD) { id }
    }
  }
" --jq '.data.repository.issue.id')

[ -z "$CHILD_ID" ] || [ "$CHILD_ID" = "null" ] && { echo "ERROR: child #$CHILD not found" >&2; exit 1; }

RESULT=$(gh api graphql \
  -H "GraphQL-Features: sub_issues" \
  -f query="
    mutation {
      addSubIssue(input: {issueId: \"$PARENT_ID\", subIssueId: \"$CHILD_ID\"}) {
        issue { number title }
        subIssue { number title }
      }
    }
  " 2>&1)

if echo "$RESULT" | jq -e '.errors' >/dev/null 2>&1; then
  echo "ERROR: $(echo "$RESULT" | jq -r '.errors[0].message')" >&2
  exit 1
fi

echo "$RESULT" | jq -r '.data.addSubIssue | "✓ #\(.subIssue.number) → sub-issue of #\(.issue.number)"'
