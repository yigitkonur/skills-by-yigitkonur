# parse-pr.sh

## Purpose

Read-only GitHub PR context collector for `review-pr`. It gathers the same metadata, file list, checks, commits, formal reviews, inline comments, and conversation comments that the skill needs before diff review.

## Inputs

```bash
scripts/parse-pr.sh owner/repo 123
```

- `owner/repo`: GitHub repository slug.
- `123`: numeric pull request number.

## Outputs

- Prints a compact markdown summary to stdout.
- Writes raw artifacts to a temporary directory and prints that path.
- Artifact files:
  - `metadata.json`
  - `files.json`
  - `commits.json`
  - `reviews.json`
  - `inline-comments.json`
  - `conversation-comments.json`
  - `checks.txt`
  - `checks.err`

## Examples

```bash
scripts/parse-pr.sh yigitkonur/skills-by-yigitkonur 42
```

Use the printed artifact path during Phase 2 and Phase 4:

```bash
jq '.[] | {filename, additions, deletions}' /tmp/review-pr-*/files.json
jq '.[] | {author: .user.login, state, body}' /tmp/review-pr-*/reviews.json
```

## Read / Write Surface

- Reads from GitHub through `gh pr view`, `gh pr checks`, and `gh api`.
- Writes only to a new temporary directory under `${TMPDIR:-/tmp}`.
- Does not post comments, submit reviews, edit labels, mutate branches, or change the working tree.

## Failure Modes

- `gh` missing: exits 127.
- `gh auth status` fails: exits non-zero before fetching anything.
- Repo argument is not `owner/repo`: exits 2.
- PR number is not numeric: exits 2.
- Checks unavailable or failed: still writes other artifacts and records details in `checks.err`.
- `jq` missing: prints a limited summary and leaves raw JSON artifacts for manual inspection.

## SKILL.md Routing

Phase 2 routes here for repeatable PR context gathering. Phase 4 routes here for formal reviews, inline comments, general conversation comments, and bot/scanner state before deduplication.
