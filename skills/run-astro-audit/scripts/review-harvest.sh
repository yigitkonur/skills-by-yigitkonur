#!/usr/bin/env bash
# ==============================================================================
# review-harvest.sh — Pull Request Review Comments Harvester
# ==============================================================================
set -euo pipefail

usage() {
  cat << 'EOF'
Usage:
  bash scripts/review-harvest.sh <PR_NUMBER>
  bash scripts/review-harvest.sh list-all [LIMIT]

Examples:
  bash scripts/review-harvest.sh 1356
  bash scripts/review-harvest.sh list-all 20
EOF
  exit 1
}

CMD="${1:-}"

if [ -z "$CMD" ]; then
  usage
fi

if [ "$CMD" = "list-all" ]; then
  LIMIT="${2:-15}"
  echo "🔍 Listing last $LIMIT open audit PRs with review status..."
  gh pr list --state open --limit "$LIMIT" --json number,title,headRefName,reviews,comments \
    --jq '.[] | "PR #\(.number) [\(.headRefName)]: \(.title) (Reviews: \(.reviews | length), Comments: \(.comments | length))"'
  exit 0
fi

PR_NUMBER="$CMD"
echo "🔍 Harvesting review comments for PR #$PR_NUMBER..."

echo "--- Review Comments (Inline Diff) ---"
gh api "repos/:owner/:repo/pulls/${PR_NUMBER}/comments" \
  --jq '.[] | "[\(.user.login) on \(.path):\(.line // .original_line // 0)]:\n\(.body)\n"' || true

echo "--- General Conversation Comments ---"
gh pr view "$PR_NUMBER" --json comments \
  --jq '.comments[] | "[\(.author.login)]:\n\(.body)\n"' || true

echo "✅ Harvest complete for PR #$PR_NUMBER."
