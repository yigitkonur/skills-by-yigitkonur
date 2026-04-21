# gh CLI for PR Review Feedback

Mechanics for fetching review feedback from GitHub and replying correctly. Assumes `gh` is installed and authenticated (`gh auth status`).

## The three comment channels

GitHub has three distinct places review feedback lives. Each is fetched and replied-to differently.

| Channel | What it is | Fetch | Reply target |
|---|---|---|---|
| **Reviews** | Top-level PR reviews ("Approved", "Changes requested" with a summary body) | `gh pr view <N> --json reviews` | Top-level PR comment (via `gh pr comment`) |
| **Review comments** | Inline comments pinned to a file:line in the diff | `gh api repos/<o>/<r>/pulls/<N>/comments` | Reply within the thread (via `gh api .../replies`) |
| **Issue comments** | Top-level PR discussion (not attached to a review) | `gh api repos/<o>/<r>/issues/<N>/comments` | Top-level PR comment (via `gh pr comment`) |

Mixing channels is a common mistake — replying to an inline comment at the top level makes your response detached from the code it's about.

## Fetching everything for a PR

```bash
PR=42
REPO=owner/name

# 1. Top-level PR reviews (summary comments)
gh pr view $PR --repo $REPO --json reviews \
  --jq '.reviews[] | {id, author: .author.login, state, submittedAt, body}' \
  > /tmp/pr-reviews.json

# 2. Inline review comments (line-pinned)
gh api "repos/$REPO/pulls/$PR/comments" --paginate \
  --jq '.[] | {id, user: .user.login, path, line: (.line // .original_line), body, commit_id, in_reply_to_id, created_at}' \
  > /tmp/pr-inline-comments.json

# 3. PR discussion (non-review)
gh api "repos/$REPO/issues/$PR/comments" --paginate \
  --jq '.[] | {id, user: .user.login, body, created_at}' \
  > /tmp/pr-issue-comments.json
```

Save to temp files so downstream parsing / clustering / evaluation can reference the same snapshot.

## Useful field extraction

Review comments (inline) have these commonly-needed fields:

| Field | Meaning |
|---|---|
| `id` | The comment ID — use for thread replies |
| `path` | The file path the comment is on |
| `line` | The line number (new side of the diff) |
| `original_line` | Line number at the commit the reviewer viewed |
| `side` | `RIGHT` (new code) or `LEFT` (old code) |
| `commit_id` | The commit the reviewer was viewing |
| `in_reply_to_id` | If set, this is a reply in an existing thread |
| `body` | The comment text (markdown) |
| `user.login` | The reviewer's username |

`line` may be null if the comment is on a range or a deleted line; `original_line` always has a value. Prefer `line` and fall back to `original_line` (see the `--jq` above).

## Reply mechanics (don't mix channels)

### Reply to an inline review comment — THREAD reply

```bash
REPO=owner/name
PR=42
COMMENT_ID=98765   # from the review-comments fetch

gh api "repos/$REPO/pulls/$PR/comments/$COMMENT_ID/replies" \
  --method POST \
  --field body="Fixed in commit abc1234. <one-line description>."
```

This places the reply in the same thread as the original inline comment. GitHub shows it under the comment's file/line context.

### Reply to a top-level PR review (summary) — PR COMMENT

```bash
gh pr comment $PR --repo $REPO --body "Addressing the four items below:
- Item 1 (auth.ts:L42): Fixed. <what changed>.
- Item 2 (session.ts:L87): Fixed. <what changed>.
- Item 3 (README.md:L14): Fixed. Typo corrected.
- Item 4 (worker.ts:L100): Pushed back — <technical reason>."
```

This creates a new top-level discussion comment.

### Reply to a PR discussion comment — same channel

```bash
# PR discussion comments don't have thread replies in the same way.
# Reply as a new top-level PR comment, optionally @mentioning the author.
gh pr comment $PR --repo $REPO --body "@alice <response text>"
```

## Reviewing one's own past responses (self-audit)

If evaluating your own past output, fetch your previous PR comments:

```bash
# My PR comments on PR #N
gh api "repos/$REPO/issues/$PR/comments" --paginate \
  --jq '.[] | select(.user.login == "'"$(gh api user --jq .login)"'") | {id, body, created_at}'

# My inline review replies
gh api "repos/$REPO/pulls/$PR/comments" --paginate \
  --jq '.[] | select(.user.login == "'"$(gh api user --jq .login)"'") | {id, path, line, body, created_at}'
```

## Bulk-fetching multi-agent feedback

For PRs with 5+ bot reviewers, compile a single combined stream:

```bash
# All comments from all sources, flat stream
{
  gh api "repos/$REPO/pulls/$PR/comments" --paginate \
    --jq '.[] | {channel: "inline", id, user: .user.login, path, line: (.line // .original_line), body}'
  gh api "repos/$REPO/issues/$PR/comments" --paginate \
    --jq '.[] | {channel: "discussion", id, user: .user.login, body}'
  gh pr view $PR --repo $REPO --json reviews \
    --jq '.reviews[] | {channel: "review", id, user: .author.login, body, state}'
} > /tmp/all-pr-feedback.json
```

Then per-source parsing (see `multi-agent-consolidation.md`) normalizes each reviewer's format.

## Common mistakes

| Mistake | Consequence | Fix |
|---|---|---|
| Reply to inline comment at top level | Response detached from code context; reviewer has to search | Use `.../comments/$ID/replies` |
| Reply to thread with `gh pr comment` | Same as above | Same as above |
| Use `--jq '.[]'` without `--paginate` | Only first 30 comments fetched | Always `--paginate` for comments |
| Trust `line` field without fallback | null values on range comments | `(.line // .original_line)` |
| Ignore `commit_id` on comments | Respond to a suggestion that was already fixed in a later commit | Record `commit_id`; check if still applicable |

## CI-bot comments vs. reviewer comments

Some CI bots (Greptile, CodeRabbit, Devin, Cubic) are wired as GitHub Apps and their comments have `user.type == "Bot"`. You can filter:

```bash
# Only human reviews
gh api "repos/$REPO/pulls/$PR/comments" --paginate \
  --jq '.[] | select(.user.type == "User") | {id, user: .user.login, body}'

# Only bot reviews
gh api "repos/$REPO/pulls/$PR/comments" --paginate \
  --jq '.[] | select(.user.type == "Bot") | {id, user: .user.login, body}'
```

When running the voice discipline, replies to bots are usually machine-parsed; still follow the no-gratitude rule — the reply is readable by humans too.

## Repo-explicit `--repo` rule

Every `gh pr`-family command can infer the repo from `git remote`. **Don't rely on it.** If you're on a fork, the inference is wrong. Always pass `--repo <owner>/<name>` explicitly, as the sibling `request-code-review` skill also requires.

For `gh api` calls, the repo is explicit in the URL path — no inference risk.

## Example full flow

```bash
PR=42
REPO=yigitkonur/skills-by-yigitkonur

# 1. Pull everything
gh api "repos/$REPO/pulls/$PR/comments" --paginate > /tmp/inline.json
gh api "repos/$REPO/issues/$PR/comments" --paginate > /tmp/discussion.json
gh pr view $PR --repo $REPO --json reviews > /tmp/reviews.json

# 2. Consolidate + evaluate (per multi-agent-consolidation.md + verification.md)
#    ...produces per-item verdicts...

# 3. Reply per-verdict (inline vs. top-level)
gh api "repos/$REPO/pulls/$PR/comments/98765/replies" \
  --method POST --field body="Fixed. Changed retry to exponential backoff in worker.ts:L104."

gh pr comment $PR --repo $REPO --body "$(cat <<'EOF'
Addressing the reviews. Details inline per-thread; summary:

- 3 items accepted and fixed (see commit abc1234)
- 1 item pushed back (retry strategy — linear is correct here; see thread for reasoning)
- 1 item needs clarification on scope
EOF
)"

# 4. Confirm replies landed
gh api "repos/$REPO/pulls/$PR/comments/98765" --jq '.body'
```
