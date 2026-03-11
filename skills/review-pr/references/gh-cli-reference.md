# gh CLI Reference for PR Review

> Definitive cheat sheet for all `gh` CLI commands and GitHub API calls used during PR review. An agent should be able to read this file and know the exact syntax for every operation.

---

## PR Operations

### Get PR metadata
```bash
gh pr view <N> --repo owner/repo --json title,body,state,author,labels,baseRefName,headRefName,reviewDecision,statusCheckRollup,files,commits,reviewRequests,milestone,number,url
```
Use when: gathering PR metadata — understanding what the PR is about.

Available JSON fields: title, body, state, number, url, author, baseRefName, headRefName, labels, milestone, reviewDecision, reviewRequests, statusCheckRollup, files, commits, additions, deletions, changedFiles, createdAt, updatedAt, mergedAt, mergeable, isDraft

### Get PR diff
```bash
gh pr diff <N> --repo owner/repo
```
Use when: goal validation and systematic cluster review.
Note: For large PRs, prefer file-by-file review using checkout + git diff.

### Get changed files with stats
```bash
gh api repos/{owner}/{repo}/pulls/{N}/files --paginate
```
Returns: Array of objects with filename, status (added/modified/removed/renamed), additions, deletions, changes, patch.
Use when: scoping the diff — clustering files by concern.

### Checkout PR locally
```bash
gh pr checkout <N> --repo owner/repo
```
Use when: You need to browse the full codebase, run tests, or use local tools like grep.
After checkout: `git diff main...HEAD` to see all changes.

---

## Review State Operations

### Get all reviews
```bash
gh api repos/{owner}/{repo}/pulls/{N}/reviews
```
Returns: Array of reviews with state (APPROVED, CHANGES_REQUESTED, COMMENTED, DISMISSED), user, body, submitted_at.
Use when: reading existing review state — understanding who reviewed and their stance.

### Get review comment threads
```bash
gh api repos/{owner}/{repo}/pulls/{N}/comments --paginate
```
Returns: Inline review comments with path, line, body, user, created_at, in_reply_to_id, pull_request_review_id.
Use when: reading existing review state — building the already-reviewed map.
Note: Thread structure is determined by in_reply_to_id. Comments with no in_reply_to_id are thread starters.

### Get general PR conversation
```bash
gh api repos/{owner}/{repo}/issues/{N}/comments
```
Returns: Non-inline PR conversation comments (discussion, status updates, bot comments).
Use when: reading existing review state — reading PR discussion for context.
Note: PRs are issues in GitHub's API, so issue comments endpoint works for PR conversations.

### Get PR comments (simple view)
```bash
gh pr view <N> --repo owner/repo --comments
```
Use when: Quick scan of PR discussion without JSON parsing.

---

## Repository Content Operations

### Get file contents (specific branch)
```bash
# Via API (returns base64-encoded content)
gh api repos/{owner}/{repo}/contents/{path}?ref={branch}

# Via local checkout (simpler, requires checkout)
git show {branch}:{path}
```
Use when: cluster review — reading full file for context around diff hunks, comparing head vs base.

### Search code in repo
```bash
# Via GitHub search (works without checkout)
gh search code "query repo:owner/repo"

# Via local checkout (faster, more flexible)
grep -rn "pattern" .
```
Use when: cluster review — tracing blast radius (who calls this function?).

---

## Commit Operations

### Get PR commits
```bash
gh api repos/{owner}/{repo}/pulls/{N}/commits
```
Returns: Array of commits with sha, message, author, date.
Use when: gathering context — reading commit messages to understand PR evolution.

### Get specific commit details
```bash
gh api repos/{owner}/{repo}/commits/{sha}
```
Returns: Commit message, author, date, files changed, stats.
Use when: Understanding individual commits.

---

## CI / Status Operations

### Get check status
```bash
gh pr checks <N> --repo owner/repo
```
Use when: gathering context — checking CI status.

### Get failed CI logs
```bash
# List runs for the PR's head branch
gh run list --repo owner/repo --branch <head-branch> --limit 5

# View failed run logs
gh run view <run-id> --repo owner/repo --log-failed
```
Use when: CI is failing — read the logs to understand what's broken.

---

## Issue Operations

### Get linked issue details
```bash
gh issue view <N> --repo owner/repo --json title,body,state,labels,comments
```
Use when: gathering context — understanding linked issues referenced in PR body.

---

## Submitting Reviews

### Submit a review
```bash
# Approve
gh pr review <N> --repo owner/repo --approve --body "Review body here"

# Request changes
gh pr review <N> --repo owner/repo --request-changes --body "Review body here"

# Comment only
gh pr review <N> --repo owner/repo --comment --body "Review body here"
```

### Post a general comment
```bash
gh pr comment <N> --repo owner/repo --body "Comment text"
```

### Post an inline review comment
```bash
gh api repos/{owner}/{repo}/pulls/{N}/comments \
  --method POST \
  -f body="Comment text" \
  -f commit_id="<head-sha>" \
  -f path="src/file.ts" \
  -F line=42 \
  -f side="RIGHT"
```

### Reply to a review thread
```bash
gh api repos/{owner}/{repo}/pulls/{N}/comments/{comment_id}/replies \
  --method POST \
  -f body="Reply text"
```

---

## Labels & Management

### Add labels based on review
```bash
gh pr edit <N> --repo owner/repo --add-label "needs-changes"
gh pr edit <N> --repo owner/repo --remove-label "ready-for-review"
```

---

## Common Patterns

### Pattern: Full PR context gathering
```bash
# 1. Get metadata + files + CI in one call
gh pr view <N> --repo owner/repo --json title,body,state,author,labels,baseRefName,headRefName,files,statusCheckRollup

# 2. Get linked issues (parse #NNN from body)
gh issue view <issue-N> --repo owner/repo --json title,body,state,labels

# 3. Get commit messages
gh api repos/{owner}/{repo}/pulls/{N}/commits
```

### Pattern: File-level deep dive
```bash
# 1. Get file list with stats
gh api repos/{owner}/{repo}/pulls/{N}/files --paginate

# 2. For interesting files, compare head vs base
git show main:src/auth/middleware.ts > /tmp/base.ts
git show HEAD:src/auth/middleware.ts > /tmp/head.ts
diff /tmp/base.ts /tmp/head.ts
```

### Pattern: Blast radius analysis
```bash
# 1. Identify changed function name from diff
# 2. Search for all callers
gh search code "functionName repo:owner/repo"
# Or locally:
grep -rn "functionName" --include="*.ts" src/
```

### Pattern: Review thread correlation
```bash
# 1. Get all inline comments
gh api repos/{owner}/{repo}/pulls/{N}/comments --paginate

# 2. Parse JSON: extract path, line, body, in_reply_to_id for threading
# 3. Build already-reviewed map: {file: [{line, issue, resolved}]}
# 4. Skip locations already covered unless resolution is incorrect
```

### Pattern: Local checkout workflow
```bash
# Full local review setup
gh pr checkout <N> --repo owner/repo
git diff main...HEAD --stat            # File summary
git diff main...HEAD                    # Full diff
git diff main...HEAD -- src/auth/       # Diff for specific directory
git log main..HEAD --oneline           # Commit messages
grep -rn "pattern" src/                 # Search locally
```

---

## MCP Server Tool Equivalents

If GitHub MCP server tools are available, prefer them over `gh` CLI commands. They return the same data without requiring shell access.

| gh CLI command | MCP tool | Method/parameters |
|---|---|---|
| `gh pr view N --json ...` | `pull_request_read` | `method: "get"`, `pullNumber: N` |
| `gh pr diff N` | `pull_request_read` | `method: "get_diff"`, `pullNumber: N` |
| `gh pr view N --json files` | `pull_request_read` | `method: "get_files"`, `pullNumber: N` |
| `gh pr checks N` | `pull_request_read` | `method: "get_check_runs"`, `pullNumber: N` |
| `gh pr status` | `pull_request_read` | `method: "get_status"`, `pullNumber: N` |
| `gh api repos/.../pulls/N/reviews` | `pull_request_read` | `method: "get_reviews"`, `pullNumber: N` |
| `gh api repos/.../pulls/N/comments` | `pull_request_read` | `method: "get_review_comments"`, `pullNumber: N` |
| `gh api repos/.../issues/N/comments` | `issue_read` | `method: "get_comments"`, `issue_number: N` |
| `gh api repos/.../contents/PATH` | `get_file_contents` | `owner`, `repo`, `path` |
| `gh api repos/.../commits` | `list_commits` | `owner`, `repo` |
| `gh api repos/.../commits/SHA` | `get_commit` | `owner`, `repo`, `sha` |
| `gh issue view N` | `issue_read` | `method: "get"`, `issue_number: N` |
| `gh api search/code?q=...` | `search_code` | `query: "..."` |

### Steering note

Use whichever tool access you have. The review quality depends on the data gathered, not the tool used to gather it. If both are available, MCP tools are slightly preferred because they avoid shell escaping issues and work in sandboxed environments.

## Steering notes

> These notes capture real mistakes observed during derailment testing.

1. **MCP tools and gh CLI return identical data -- choose based on environment.** If GitHub MCP server tools are available (e.g., `pull_request_read`, `get_file_contents`), prefer them -- they avoid shell access requirements. If only bash is available, use gh CLI.
2. **Always use `--json` output for gh CLI commands.** Human-readable output is unparseable for automated review workflows. Every command in this reference has a `--json` variant -- use it.
3. **Pagination matters for large PRs.** A PR with 100+ changed files or 50+ comments requires pagination parameters (`--per-page`, `--page`). Without pagination, you will miss files or comments and produce an incomplete review.
4. **The MCP Server Tool Equivalents table at the bottom of this file maps every gh CLI command to its MCP equivalent.** Check there before constructing a new MCP tool call -- the mapping handles parameter name differences between the two interfaces.

> **Cross-reference:** See SKILL.md "Tool access" note for when to prefer MCP tools over gh CLI.
