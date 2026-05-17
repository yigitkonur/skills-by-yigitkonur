#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Usage: %s owner/repo PR_NUMBER\n' "$(basename "$0")" >&2
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ "$#" -ne 2 ]; then
  usage
  exit 2
fi

repo="$1"
pr="$2"

case "$repo" in
  */*) ;;
  *)
    printf 'error: repo must be owner/repo, got: %s\n' "$repo" >&2
    exit 2
    ;;
esac

case "$pr" in
  ''|*[!0-9]*)
    printf 'error: PR number must be numeric, got: %s\n' "$pr" >&2
    exit 2
    ;;
esac

command -v gh >/dev/null 2>&1 || {
  printf 'error: gh CLI is required\n' >&2
  exit 127
}

gh auth status >/dev/null

safe_repo="${repo//\//-}"
artifact_dir="$(mktemp -d "${TMPDIR:-/tmp}/review-pr-${safe_repo}-${pr}.XXXXXX")"

gh pr view "$pr" \
  --repo "$repo" \
  --json title,body,state,author,labels,baseRefName,headRefName,reviewDecision,statusCheckRollup,files,commits,reviewRequests,milestone,number,url,additions,deletions,changedFiles,createdAt,updatedAt,isDraft,mergeable,headRefOid \
  > "$artifact_dir/metadata.json"

gh api "repos/$repo/pulls/$pr/files" --paginate > "$artifact_dir/files.json"
gh api "repos/$repo/pulls/$pr/commits" --paginate > "$artifact_dir/commits.json"
gh api "repos/$repo/pulls/$pr/reviews" --paginate > "$artifact_dir/reviews.json"
gh api "repos/$repo/pulls/$pr/comments" --paginate > "$artifact_dir/inline-comments.json"
gh api "repos/$repo/issues/$pr/comments" --paginate > "$artifact_dir/conversation-comments.json"

if gh pr checks "$pr" --repo "$repo" > "$artifact_dir/checks.txt" 2> "$artifact_dir/checks.err"; then
  checks_state="available"
else
  checks_state="unavailable or failed; see checks.err"
fi

if command -v jq >/dev/null 2>&1; then
  title="$(jq -r '.title // ""' "$artifact_dir/metadata.json")"
  url="$(jq -r '.url // ""' "$artifact_dir/metadata.json")"
  state="$(jq -r '.state // ""' "$artifact_dir/metadata.json")"
  draft="$(jq -r '.isDraft // false' "$artifact_dir/metadata.json")"
  base="$(jq -r '.baseRefName // ""' "$artifact_dir/metadata.json")"
  head="$(jq -r '.headRefName // ""' "$artifact_dir/metadata.json")"
  additions="$(jq -r '.additions // 0' "$artifact_dir/metadata.json")"
  deletions="$(jq -r '.deletions // 0' "$artifact_dir/metadata.json")"
  changed="$(jq -r '.changedFiles // 0' "$artifact_dir/metadata.json")"
  review_decision="$(jq -r '.reviewDecision // "UNKNOWN"' "$artifact_dir/metadata.json")"
  formal_reviews="$(jq 'length' "$artifact_dir/reviews.json")"
  inline_comments="$(jq 'length' "$artifact_dir/inline-comments.json")"
  conversation_comments="$(jq 'length' "$artifact_dir/conversation-comments.json")"
  commit_count="$(jq 'length' "$artifact_dir/commits.json")"

  cat <<EOF
# PR Context Summary

- Target: \`$repo#$pr\`
- URL: $url
- Title: $title
- State: $state (draft: $draft)
- Base/head: \`$base...$head\`
- Size: $changed files (+$additions/-$deletions)
- Review decision: $review_decision
- Commits: $commit_count
- Formal reviews: $formal_reviews
- Inline review comments: $inline_comments
- Conversation comments: $conversation_comments
- Checks: $checks_state
- Artifacts: \`$artifact_dir\`

## Files

$(jq -r '.[] | "- " + .filename + " (" + (.status // "unknown") + ", +" + ((.additions // 0)|tostring) + "/-" + ((.deletions // 0)|tostring) + ")"' "$artifact_dir/files.json")
EOF
else
  cat <<EOF
# PR Context Summary

- Target: \`$repo#$pr\`
- Checks: $checks_state
- Artifacts: \`$artifact_dir\`

\`jq\` was not found, so the compact summary is limited. Read the JSON artifacts directly.
EOF
fi
