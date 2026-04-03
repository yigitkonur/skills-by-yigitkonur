# Review Workflow — Full Procedure

Step-by-step review procedure with exact CLI examples for every phase.
This is the primary reference for `SKILL.md`. Follow phases in order; do not skip.

> **Prerequisites:**
> - **GitHub PR mode:** you need `gh` (GitHub CLI) authenticated. Run `gh auth status` to confirm.
> - **Local diff mode:** you need a local git checkout with the target diff available. `gh` auth is not required.
>
> If the repository is cloned locally, many commands can be replaced with faster local equivalents noted throughout.

## Target bootstrap

### Local diff mode bootstrap

When no GitHub PR exists, establish one exact comparison target before reading code.

Use the first case that applies:

| Situation | Comparison target | Commands |
|---|---|---|
| User supplied base + head refs | `<base>...<head>` | `git diff --stat <base>...<head>` and `git log --oneline <base>..<head>` |
| Current branch review against repo default branch | `<default-branch>...HEAD` | `git branch --show-current`, resolve `<default-branch>`, then `git diff --stat <default-branch>...HEAD` |
| Uncommitted work only | `HEAD + staged + unstaged` | `git diff --cached --stat` and `git diff --stat` |

Common bootstrap commands:

```bash
git rev-parse --show-toplevel
git branch --show-current
git symbolic-ref --quiet --short refs/remotes/origin/HEAD | sed 's@^origin/@@'
git diff --stat <base>...<head>
git log --oneline <base>..<head>
```

If `refs/remotes/origin/HEAD` is unset, `git remote show origin | sed -n '/HEAD branch/s/.*: //p'` is the fallback for resolving the default branch.

If you are reviewing uncommitted work, inspect both staged and unstaged state explicitly:

```bash
git diff --cached --stat
git diff --stat
```

If a file you expect to review is missing from `git status` or the diff, check whether ignore rules are hiding it:

```bash
git check-ignore -v path/to/file
```

If you still cannot identify the exact comparison target or whether staged/unstaged changes are in scope, stop and ask. Do not invent a diff target.

### Navigation — SKILL.md phase mapping

SKILL.md defines 8 phases; this file covers phases 2-8 as its internal phases 1-7. Use this table to navigate:

| SKILL.md phase | This file's section |
|---|---|
| Phase 1 — Triage | Handled in SKILL.md directly (not in this file) |
| Phase 2 — Gather context | Phase 1 — Gather Context |
| Phase 3 — Scope the diff | Phase 2 — Scope and Cluster |
| Phase 4 — Read existing review state | Phase 3 — Read Existing Review State |
| Phase 5 — Validate goals | Phase 4 — Goal Validation |
| Phase 6 — Review by cluster | Phase 5 — Systematic Review by Cluster |
| Phase 7 — Cross-cutting sweep | Phase 6 — Cross-cutting Analysis |
| Phase 8 — Synthesize and output | Phase 7 — Synthesize and Output |

> The offset is intentional: SKILL.md Phase 1 (Triage) has no counterpart here.

---

## Phase 1 — Gather Context

**Goal:** Build a mental model of what the PR is trying to do and why, before looking at any code.

If you are in local diff mode, replace PR metadata/issue/CI fields with local equivalents:
- branch name + recent commits instead of PR title/body
- user request or branch naming instead of linked issues
- local test results only if the user or workflow provides them

Mark GitHub-only fields as unavailable rather than fabricating them.

Use this source mapping in local diff mode:

| Need | GitHub PR mode | Local diff mode |
|---|---|---|
| Goal statement | PR title/body + linked issues | user request + branch name + commit history |
| Base/head refs | `baseRefName` / `headRefName` | explicit comparison target from bootstrap |
| CI/checks | `gh pr checks` and check runs | local test/build output if provided; otherwise unavailable |
| Existing review state | PR reviews and comments | unavailable unless the user supplies copied comments or exported review data |

### 1.1 Get PR metadata

```bash
gh pr view <N> --repo owner/repo --json title,body,state,author,labels,baseRefName,headRefName,reviewDecision,statusCheckRollup,files,createdAt,updatedAt,isDraft,mergeable,milestone
```

Record these fields immediately — you will reference them throughout the review:

| Field | Why it matters |
|-------|----------------|
| `title` | First signal of intent; should match the actual diff |
| `body` | The PR description is the contract — goal validation checks against this |
| `baseRefName` / `headRefName` | Needed for file content comparisons later |
| `labels` | May indicate priority, area, or review requirements (e.g. `security`, `breaking-change`) |
| `author.login` | Context for calibration — first-time contributor vs. team lead |
| `state` | Current PR state |
| `isDraft` | If `true`, do not review unless explicitly asked |
| `reviewDecision` | Shows if already approved, changes requested, or no decision yet |

In local diff mode, record the local equivalents:
- repo root from `git rev-parse --show-toplevel`
- current branch from `git branch --show-current`
- comparison target from bootstrap
- author, labels, milestone, and mergeability only if the user explicitly provides them

#### Red flags in metadata
- **Empty body:** PR has no description — flag immediately as a finding
- **Draft state:** Only review if explicitly asked; otherwise note and stop
- **`breaking-change` label:** Heightened scrutiny on backward compatibility
- **Stale PR:** `updatedAt` weeks ago suggests abandoned work or merge conflicts

### 1.2 Extract and fetch linked issues

In local diff mode, use the user request, branch naming, and commit messages as the issue source unless the user supplies a linked issue or copied task text.

Parse the PR body for issue references using these patterns:

```
Regex patterns (case-insensitive):
  #(\d+)                           → general reference
  (?:fix|fixes|fixed)\s+#(\d+)    → closing reference
  (?:close|closes|closed)\s+#(\d+) → closing reference
  (?:resolve|resolves|resolved)\s+#(\d+) → closing reference
```

For each unique issue number found:

```bash
gh issue view <N> --repo owner/repo --json title,body,state,labels,comments,assignees,milestone
```

Read the issue body carefully. It often contains acceptance criteria, reproduction steps, or design constraints that the PR body omits. If the PR references multiple issues, synthesize a unified understanding of the goal.

**If no issues are linked:** This is a yellow flag. The PR may be exploratory, a refactor, or missing context. Note this in your review summary and rely more heavily on the PR body and commit messages for intent.

#### What good linked issues look like
- Clear problem statement with reproduction steps
- Acceptance criteria that can be verified against the diff
- Design discussion in comments showing the chosen approach

#### What bad linked issues look like
- Single-line title with no body ("Fix the thing")
- Closed issues that don't relate to the PR's actual changes
- Issues that describe a different scope than what the PR implements

### 1.3 Get CI / check run status

```bash
gh pr checks <N> --repo owner/repo
```

For more detail on check runs (including output summaries):

```bash
gh pr view <N> --repo owner/repo --json statusCheckRollup --jq '.statusCheckRollup[] | {name: .name, status: .status, conclusion: .conclusion}'
```

Interpret CI status using this decision tree:

```
All checks passed (conclusion: "success")
  → Proceed normally.

Some checks failed (conclusion: "failure")
  → Record which checks failed.
  → If tests failed: note in review — the author may already know.
  → If lint/format failed: do NOT raise style issues the CI already catches.
  → If security scan failed: escalate — read the scan output.
  → Proceed with review, but note CI status in the summary.

Checks pending or in_progress
  → Note that CI has not completed.
  → Proceed with review but caveat that test results are unknown.
  → Do NOT block on pending CI unless the user specifically asked to wait.

No checks configured
  → Note the absence. This is worth mentioning if the repo normally has CI.
```

In local diff mode:
- local test/build output provided → record it as your verification state
- no local verification output available → write `Checks unavailable in local diff mode` and continue

When a specific CI run failed and you need logs:

```bash
# List workflow runs for the PR's head branch
gh run list --repo owner/repo --branch <head-branch> --limit 5

# Get logs for a failed run
gh run view <run-id> --repo owner/repo --log-failed
```

### 1.4 Get commit history

```bash
gh api repos/{owner}/{repo}/pulls/{N}/commits --paginate --jq '.[] | {sha: .sha[:8], message: .commit.message, author: .commit.author.name, date: .commit.author.date}'
```

Local diff mode equivalent:

```bash
git log --oneline <base>..<head>
```

Scan commit messages for:
- **Incremental development story** — how the author built this change step by step
- **Fixup commits** (`fixup!`, `squash!`) that indicate areas of uncertainty or iteration
- **Markers the author left** — `WIP`, `TODO`, `HACK`, `FIXME` suggest unfinished work
- **Commit message quality** — well-structured messages suggest intentional, thoughtful changes
- **Force pushes** — if the commit history looks rewritten, prior review comments may be outdated

#### Red flags in commit history
- `"fix tests"` or `"make it work"` — suggests the author is not confident in the approach
- Many small fixup commits touching the same file — the design may not be settled
- Commits that revert previous commits in the same PR — the approach changed mid-flight
- Single massive commit — makes it harder to understand the change incrementally

### 1.5 Phase output

Write a one-paragraph internal summary:

> This PR by [author] targets [base branch] and aims to [goal from PR body/issues].
> It links to issues [#X, #Y] which describe [problem]. CI status: [all green / N failures / pending].
> Key signals: [any labels, milestone, red flags from commit messages].

Local diff mode version:

> Local diff review for [repo root] comparing [comparison target].
> Intended goal: [goal from user request / branch / commits].
> GitHub-only context unavailable: [PR body, linked issues, CI, review threads].
> Key signals: [branch name, commit markers, local verification state].

---

## Phase 2 — Scope and Cluster

**Goal:** Understand the shape of the change and build a review plan before reading any diffs.

### 2.1 Get the changed file list

```bash
gh api repos/{owner}/{repo}/pulls/{N}/files --paginate --jq '.[] | {filename: .filename, status: .status, additions: .additions, deletions: .deletions, changes: .changes}'
```

This returns each file's name, status (`added`, `modified`, `removed`, `renamed`), and line counts. For a quick overview:

```bash
gh pr view <N> --repo owner/repo --json files --jq '.files[] | "\(.additions)+/\(.deletions)- \(.path)"'
```

Local diff mode equivalents:

```bash
# Branch diff
git diff --name-status <base>...<head>
git diff --stat <base>...<head>

# Working tree review
git diff --name-status --cached
git diff --name-status
```

### 2.2 Clustering algorithm

Process the file list through these steps in order:

**Step 1 — Parse directory prefixes.** Extract the first 1–2 directory segments from each file path. Example: `src/api/routes/users.ts` → `src/api`.

**Step 2 — Group by common ancestor.** Files sharing a common directory prefix form a natural cluster. Example: `src/api/routes/users.ts` and `src/api/middleware/auth.ts` both belong to the `API` cluster.

**Step 3 — Identify test files.** Match files against these patterns:
```
*_test.*          → Go convention
*.test.*          → JS/TS convention (jest, vitest)
*.spec.*          → JS/TS convention (mocha, jasmine)
test_*            → Python convention
__tests__/*       → React/Jest convention
tests/*           → General convention
*_test.go         → Go
*_spec.rb         → Ruby/RSpec
Test*.java        → Java/JUnit
*Tests.cs         → C#/xUnit
```

**Step 4 — Map test files to source counterparts.** For each test file, identify the source file it exercises. Example: `src/api/__tests__/users.test.ts` maps to `src/api/routes/users.ts`. If a source file changed but its test file did not, flag this as a potential test gap.

**Step 5 — Assign cluster labels.** Use these categories:

| Cluster | Path signals | Risk level |
|---------|-------------|------------|
| Data | `migrations/`, `models/`, `schema`, `prisma/`, `alembic/`, `sql/` | 🔴 Highest |
| API | `routes/`, `controllers/`, `handlers/`, `endpoints/`, `api/` | 🟡 High |
| Backend Logic | `services/`, `lib/`, `utils/`, `helpers/`, `core/` | 🟡 High |
| Frontend | `components/`, `pages/`, `views/`, `styles/`, `assets/`, `public/` | 🟢 Medium |
| Tests | Matches test patterns from Step 3 | 🟢 Medium |
| Docs | `docs/`, `*.md`, `CHANGELOG`, `README` | ⚪ Low |
| Config/Infra | `Dockerfile`, `docker-compose`, `.github/`, `ci/`, `*.yml`, `*.toml`, `*.json` (root) | Varies |

**Step 6 — Handle ambiguous files.** For files that don't clearly belong to one cluster, use content heuristics:
- Check the file extension for language
- Check if the first few lines contain telltale imports (e.g., `import express` → API, `import React` → Frontend)
- Check the file's directory siblings for context
- When truly ambiguous, assign to the cluster with the most related files

**Step 7 — Order clusters by review priority.** Review in this order (highest risk first):
1. Data migrations and schema changes
2. API endpoint and contract changes
3. Backend logic and business rules
4. Frontend behavior changes
5. Test changes
6. Documentation changes
7. Configuration and infrastructure

### 2.3 Handling large PRs (>500 lines changed)

When `total additions + deletions > 500`:

1. **Flag the PR size** as a concern in your review summary. Large PRs are harder to review correctly and more likely to hide bugs.
2. **Prioritize ruthlessly.** Review the top 2–3 highest-risk clusters in full detail. For lower-risk clusters, do a skim review (check for obvious issues only).
3. **Explicitly state your coverage.** In the review output, note which clusters received deep review and which were skimmed:
   ```
   Deep review: Data (migrations), API (routes)
   Skim review: Frontend (components), Config
   Not reviewed: Docs (changelog only)
   ```
4. **Consider suggesting a split.** If the PR touches unrelated concerns (e.g., a bug fix + a refactor + a new feature), this is a legitimate blocker-level finding.

#### Red flags in PR scope
- More than 15 files changed — review quality drops significantly
- Changes spanning 4+ unrelated directories — likely needs splitting
- Test-to-source ratio below 0.3 for a feature PR — test coverage is likely insufficient
- Binary files or generated code mixed with source changes — pollutes the diff

### 2.4 Phase output

A cluster map:

```
Cluster: Data (🔴 highest risk)
  Files: db/migrations/20240115_add_user_roles.sql (+45 -0)
  Tests: None — ⚠️ test gap

Cluster: API (🟡 high risk)
  Files: src/api/routes/users.ts (+32 -18), src/api/middleware/auth.ts (+12 -4)
  Tests: src/api/__tests__/users.test.ts (+28 -0)

Review order: Data → API → Tests
Total: 3 clusters, 4 files, 117 additions, 22 deletions
```

---

## Phase 3 — Read Existing Review State

**Goal:** Avoid duplicating prior reviewer feedback and understand the current conversation.

If local diff mode has no imported review history, skip the fetch steps below. Record:

```
Prior reviews: unavailable in local diff mode
Active threads: unavailable
Resolved threads: unavailable
```

If the user provides copied comments, exported review threads, or bot output for the same diff, treat that material as the review state for this phase.

### 3.1 Fetch all review data

In GitHub PR mode, make these three calls (they can be parallelized):

**Get formal reviews (approvals, change requests):**

```bash
gh api repos/{owner}/{repo}/pulls/{N}/reviews --jq '.[] | {author: .user.login, state: .state, body: .body, submitted_at: .submitted_at}'
```

**Get inline review comments (comments on specific code lines):**

```bash
gh api repos/{owner}/{repo}/pulls/{N}/comments --paginate --jq '.[] | {author: .user.login, body: .body, path: .path, line: .line, created_at: .created_at, in_reply_to_id: .in_reply_to_id}'
```

**Get general PR conversation comments (not inline on code):**

```bash
gh api repos/{owner}/{repo}/issues/{N}/comments --jq '.[] | {author: .user.login, body: .body, created_at: .created_at}'
```

### 3.2 Build the already-reviewed map

For each review thread, extract and record:

| Field | Source | Purpose |
|-------|--------|---------|
| File path | Comment's `path` | Know which file was discussed |
| Line range | Comment's `line` / `original_line` | Know which code was discussed |
| Issue type | Infer from comment body | Classify: bug, style, question, suggestion |
| Resolution status | Check if `in_reply_to_id` chains end with agreement | Know if it needs attention |
| Freshness | Compare `original_line` vs current diff | Know if the code changed since |

Classify each thread into one of three states:

```
Thread is resolved (reply chain ends with author acknowledgment or fix)
  → Mark as "handled"
  → Do NOT re-raise the same issue
  → Exception: re-raise ONLY if the resolution appears incorrect
    (e.g., the fix introduced a new bug)

Thread is outdated (the file/line changed since the comment)
  → Mark as "needs recheck"
  → The code at that location changed since the comment was made
  → Verify whether the underlying issue was fixed or still exists
  → If still exists, reference the original thread in your finding

Thread is active and unresolved (no agreement in replies)
  → Mark as "open"
  → Acknowledge this thread in your review
  → Do NOT duplicate the feedback
  → If you agree with the finding, you may add supporting evidence
  → If you disagree, explain why with evidence
```

### 3.3 Summarize review state

Record the overall review posture:

```
Prior reviews: 2 (1 APPROVED by @alice, 1 CHANGES_REQUESTED by @bob)
Active threads: 3 (2 unresolved on src/api/routes.ts, 1 unresolved on db/migrations/)
Resolved threads: 5
Outdated threads: 1 (on src/utils/helpers.ts — needs recheck)
```

#### Red flags in review history
- Previous reviewer requested changes weeks ago with no follow-up — PR may be abandoned
- Multiple rounds of the same feedback — author may not understand the concern
- Reviewer approved but left unresolved threads — approval may be premature
- All comments are from bots only — no human review has occurred

---

## Phase 4 — Goal Validation

**Goal:** Verify the PR achieves its stated purpose before doing any quality review. A PR that passes every quality check but misses its goal is still a failed PR.

### 4.1 Read the full diff

```bash
gh pr diff <N> --repo owner/repo
```

Local diff mode equivalents:

```bash
# Branch diff
git diff <base>...<head>

# Working tree review
git diff --cached
git diff
```

If both committed branch changes and uncommitted work are in scope, review them as separate buckets in your notes and final output.

For large diffs, you can filter to specific files:

```bash
# Get the diff and filter to a specific file
gh pr diff <N> --repo owner/repo | awk '/^diff --git.*auth\.ts/{found=1} found{print} /^diff --git/ && found && !/auth\.ts/{found=0}'
```

Or with a local checkout:

```bash
gh pr checkout <N> --repo owner/repo
git diff $(git merge-base HEAD origin/main)..HEAD
```

### 4.2 Read full files when the diff is insufficient

When a diff hunk lacks surrounding context (common with large functions or complex control flow):

**Read the current version (head branch — what the PR proposes):**

```bash
gh api repos/{owner}/{repo}/contents/{path}?ref={head-branch} --jq '.content' | base64 -d
```

**Read the base version (what exists before the PR):**

```bash
gh api repos/{owner}/{repo}/contents/{path}?ref={base-branch} --jq '.content' | base64 -d
```

**With local checkout (faster, preferred when available):**

```bash
# Current version (PR's changes)
git show {head-branch}:{path}

# Base version (before PR)
git show {base-branch}:{path}

# Side-by-side comparison
git diff {base-branch}..{head-branch} -- {path}
```

Use head vs. base comparison when:
- The diff shows a behavioral change but the intent is unclear from the hunk alone
- You need to understand what was removed, not just what was added
- A function signature changed and you need to see all callers
- Complex control flow was restructured and the hunk context is insufficient

### 4.3 Goal validation procedure

This is the core goal-first technique. Execute these checks in order:

**Check 1 — Form the hypothesis.**
Re-read the PR body and all linked issue descriptions. Write a single sentence:

> "This PR should [accomplish X] by [changing Y in Z]."

If you cannot form this sentence, the PR description is inadequate — flag this as a finding.

**Check 2 — Verify happy paths are implemented.**
For the stated goal, identify the primary success scenario. Trace it through the diff:
- Is the core logic present?
- Does the data flow from input to output correctly?
- Are all required changes present (API + consumer + tests)?

Example of a **good** happy path trace:
> Goal: "Add CSV export to reports" → Route handler creates CSV stream → Service queries data → 
> Response sets `Content-Type: text/csv` header → Tests verify CSV output format ✅

Example of a **broken** happy path:
> Goal: "Add CSV export to reports" → Route handler exists → Service queries data → 
> But response never sets Content-Type header → Client will misinterpret the response ❌

**Check 3 — Verify failure/error paths are handled.**
For each happy path, identify at least one failure scenario:
- What happens when input is invalid?
- What happens when an external service fails?
- What happens when the database constraint is violated?
- Are errors caught, logged, and surfaced appropriately?

**Check 4 — Check for described-but-not-implemented.**
Compare the PR description bullet points (or issue acceptance criteria) against the diff. If the description promises something the diff does not deliver, this is a **🔴 blocker**:

> "PR description states [X], but the diff does not include changes to [Y]. Is this intentional or a missing implementation?"

**Check 5 — Check for implemented-but-not-described (scope creep).**
Scan the diff for changes that serve no stated purpose. Common forms:
- Refactoring unrelated code while fixing a bug
- Adding a feature not mentioned in the PR description
- Changing configuration or dependencies without explanation

Scope creep is typically a **�� important** finding, not a blocker — unless the undescribed changes are risky.

**Check 6 — Assess completeness.**
Ask: "If I merge this PR, will the stated goal be fully achieved?" Consider:
- Are database migrations included if the schema changed?
- Are API docs updated if endpoints changed?
- Are feature flags or configuration changes included if needed?
- Is backward compatibility maintained where required?

### 4.4 Phase output

A goal validation result:

```
Goal: Add role-based access control to the /users endpoint
Hypothesis: PR adds a roles column to the users table and enforces role checks in the users route middleware.

✅ Check 1 — Hypothesis formed clearly
✅ Check 2 — Happy path: admin can access all users, regular user sees only self
⚠️ Check 3 — Error path: no handling for unknown role values
✅ Check 4 — All described features are implemented
⚠️ Check 5 — Unrelated formatting changes in 3 files (scope creep, minor)
✅ Check 6 — Migration, middleware, and tests all present
```

---

## Phase 5 — Systematic Review by Cluster

**Goal:** Review each cluster in risk order, applying the review dimensions checklist with the actionability filter.

### 5.1 Cluster review loop

For each cluster, in the priority order determined in Phase 2:

**Step 1 — Read the diff hunks** for all files in the cluster. You already have the full diff from Phase 4. Focus on the files belonging to the current cluster.

**Step 2 — Read full file context** when the diff is insufficient:

```bash
# Read full file from the PR's head branch
gh api repos/{owner}/{repo}/contents/src/api/middleware/auth.ts?ref={head-branch} --jq '.content' | base64 -d
```

With local checkout:

```bash
git show {head-branch}:src/api/middleware/auth.ts
```

Read the full file when:
- A function was modified but you need to see the full function body
- New code references existing variables/functions defined elsewhere in the file
- The diff shows a partial change to a complex control flow structure
- You need to understand the file's overall architecture to evaluate the change

**Step 3 — Read the base version** when comparing behavior changes:

```bash
# Read the file as it exists before the PR
gh api repos/{owner}/{repo}/contents/src/api/middleware/auth.ts?ref={base-branch} --jq '.content' | base64 -d
```

With local checkout:

```bash
git show {base-branch}:src/api/middleware/auth.ts
```

Read the base version when:
- The diff shows a behavioral change (not just additions)
- A function's signature or return type changed
- Error handling was modified
- You need to confirm what the old behavior was

**Step 4 — Apply the review dimensions checklist.** See `references/review-dimensions.md` for the full checklist. Evaluate in priority order: Security → Correctness → Data Integrity → Performance → API Contract → Maintainability → Testing.

**Step 5 — Apply the actionability filter** to each potential finding. A finding must pass ALL of these gates:

```
┌─ Is it in scope of this PR? (not pre-existing tech debt)
│   NO → Drop it. Not this PR's problem.
│   YES ↓
├─ Is it worth the churn? (fix simpler than the problem)
│   NO → Drop it. The cure is worse than the disease.
│   YES ↓
├─ Does it match codebase conventions? (don't impose external standards)
│   NO → Drop it. Follow the project's norms.
│   YES ↓
├─ Could it be intentional? (deliberate tradeoff by the author)
│   YES → Phrase as a question, not a finding.
│   NO ↓
├─ Does it have concrete impact? (not hypothetical)
│   NO → Drop it. "In theory" is not actionable.
│   YES ↓
├─ Would a senior on this team flag it? (calibration)
│   NO → Drop it. You're being too noisy.
│   YES ↓
├─ Confidence ≥ 70%?
│   NO → Phrase as a 💡 question instead.
│   YES → Record as a finding with severity.
└
```

**Step 6 — Record findings** with full evidence:

```
**[🟡 Important] Missing null check on role lookup** — `src/api/middleware/auth.ts:47`
The `getUserRole(userId)` call can return `undefined` when the user has no
assigned role, but line 48 accesses `role.permissions` without a guard.

Evidence: `getUserRole` returns `Role | undefined` (see `src/models/user.ts:23`).
The current code will throw `TypeError: Cannot read properties of undefined`.

Suggested fix: Add a null check or default to a "viewer" role when no role is assigned.
```

### 5.2 Tracing blast radius

When a function signature, type, or API contract changes, check who depends on it:

```bash
# Search across the repo for references to the changed symbol
gh search code "getUserRole repo:owner/repo" --json path,textMatches --jq '.[] | {path: .path, matches: [.textMatches[].fragment]}'
```

With a local checkout (faster and more precise):

```bash
grep -rn "getUserRole" --include="*.ts" --include="*.tsx" src/
```

For broader dependency tracing locally:

```bash
# Find all imports of a changed module
grep -rn "from.*['\"].*auth['\"]" --include="*.ts" src/

# Find all callers of a changed function
grep -rn "getUserRole\|setUserRole\|deleteUserRole" --include="*.ts" src/
```

If callers exist outside the PR's changed files, this is a potential coordination issue — the callers may need updating too.

#### Red flags in blast radius
- Changed function has 10+ callers but only 2 are updated in the PR
- A shared type was modified but downstream consumers weren't checked
- An API response shape changed but no frontend files are in the PR
- A database column was renamed but queries in other services still use the old name

### 5.3 Reading specific files for deep context

When you need to understand a file that is not in the diff but is referenced by changed code:

```bash
gh api repos/{owner}/{repo}/contents/src/models/user.ts?ref={head-branch} --jq '.content' | base64 -d
```

With local checkout:

```bash
git show {head-branch}:src/models/user.ts
```

Common reasons to read non-diff files:
- Understanding a type or interface that changed code depends on
- Checking if a utility function handles edge cases that the caller assumes
- Verifying that a database model matches the migration being reviewed
- Confirming that an imported constant or config value is correct
- Checking if a base class or parent component enforces contracts the child relies on

---

## Phase 6 — Cross-cutting Analysis

**Goal:** Detect patterns and gaps that span multiple clusters — issues invisible when reviewing files in isolation.

### 6.1 Inconsistency detection

After reviewing all clusters, ask:
- Is the same pattern (error handling, validation, logging) done identically everywhere?
- If a new helper or utility was introduced, is it used consistently?
- Are naming conventions consistent across the changed files?

Example finding:
> `src/api/routes/users.ts:30` wraps errors in `AppError`, but `src/api/routes/roles.ts:45` throws raw `Error`. Both files were changed in this PR — they should use the same pattern.

#### What inconsistency looks like in practice
- Error handling: one route returns `{ error: "message" }`, another returns `{ message: "error" }`
- Validation: one endpoint validates input with Zod, another uses manual `if` checks
- Logging: one service logs with structured JSON, another uses `console.log`
- Naming: one file uses `userId`, another uses `user_id` for the same concept

### 6.2 Missing coordination

Check that coupled systems were updated together:

| Changed | Should also change | How to check |
|---------|--------------------|-------------|
| API endpoint signature | API consumers (frontend, CLI, SDK) | `grep -rn "/api/users" --include="*.ts" src/` |
| Database schema | ORM models, queries, seeds | `grep -rn "users\|user_roles" --include="*.ts" src/` |
| Environment variable | Docker compose, CI config, docs | `grep -rn "NEW_ENV_VAR" .` |
| Shared type/interface | All importers | `grep -rn "from.*types" --include="*.ts" src/` |
| Error code or status | Error handlers, client-side logic | `grep -rn "ERR_ROLE_INVALID" --include="*.ts" src/` |

With `gh` when you don't have local checkout:

```bash
gh search code "NEW_ENV_VAR repo:owner/repo"
```

### 6.3 Test gap analysis

For each source file that changed, check whether a corresponding test file also changed:

```
Source changed: src/api/middleware/auth.ts (+12 -4)
Test changed:   (none)
→ ⚠️ Potential test gap — auth middleware behavior changed but tests were not updated.
```

Nuance: Not every source change needs a test change. Acceptable exceptions:
- Pure refactoring that doesn't change behavior (existing tests still pass)
- Documentation or comment changes
- Configuration changes tested by CI implicitly
- Changes to code that is genuinely difficult to unit test (but integration tests should exist)

#### Red flags in test coverage
- New public API endpoint with zero test coverage
- Changed validation logic without updated test cases for edge cases
- Deleted tests without explanation
- Test assertions that only check for `200 OK` without verifying response body
- Mocked dependencies that don't reflect real behavior

### 6.4 Documentation drift

If behavior changed, check whether documentation was updated:
- README or docs/ files
- API documentation (OpenAPI specs, JSDoc, docstrings)
- Inline code comments that describe the old behavior
- CHANGELOG or migration guides

### 6.5 New dependency analysis

If `package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`, or similar files changed:
- Is the new dependency justified? (Does it solve a problem the stdlib can't?)
- Is it well-maintained? (Check stars, last commit, open issues)
- Does it have known vulnerabilities?
- Is the version pinned appropriately?
- Does the license conflict with the project's license?

#### Red flags in dependencies
- Dependency with < 100 GitHub stars and no verified publisher
- Dependency last updated 2+ years ago
- Dependency that pulls in 50+ transitive dependencies for a simple task
- Version range like `*` or `>=1.0.0` instead of a pinned or caret range
- Dependency that duplicates functionality already in the project

---

## Phase 7 — Synthesize and Output

**Goal:** Compile all findings into a clear, actionable review output. See `references/output-templates.md` for exact format templates.

### 7.1 Verdict decision

Choose the verdict based on these criteria:

```
✅ Approve — ALL of these must be true:
  ├─ Zero 🔴 blocker findings
  ├─ No more than two 🟡 important findings
  ├─ All goal validation checks pass
  └─ No critical test gaps

💬 Comment — ANY of these:
  ├─ Questions that need author answers before you can decide
  ├─ Suggestions you want to share but nothing blocks merge
  └─ More than two 🟡 important findings but zero blockers

🔄 Request Changes — ANY of these:
  ├─ One or more 🔴 blocker findings
  ├─ Goal validation failure (described but not implemented)
  ├─ More than three 🟡 important findings
  └─ Critical test gap in high-risk code
```

### 7.2 Calibration check

Before finalizing, run this self-check:

```
> 3 blockers?
  → Re-examine each one. True blockers (security, data loss, crashes) are rare.
  → If any is really 🟡 important, downgrade it.

> 10 total findings?
  → You are likely being too noisy. Re-apply the actionability filter.
  → Remove anything that fails "Would a senior on this team flag this?"

0 positive observations?
  → Add at least one. Every PR has something done well.
  → If you genuinely cannot find anything positive, the PR may need
    a conversation, not a code review.

0 questions?
  → Consider whether you truly understood everything.
  → If the PR is non-trivial, there is almost always something worth asking about.

All findings are 🟢 suggestions?
  → Consider approving. A review with only suggestions is effectively an approval
    with notes — don't request changes for non-blocking feedback.
```

### 7.3 Output structure

Use the template from `references/output-templates.md`. Key sections:

1. **Summary** — 1–2 sentences: what the PR does and whether it achieves its goal.
2. **Verdict** — ✅ / 💬 / 🔄 with one-line justification.
3. **Findings** — Grouped by severity (blockers → important → suggestions → questions).
4. **Positive observations** — At least one.
5. **Existing review threads** — Summary of prior review state from Phase 3.
   Use `Unavailable in local diff mode` when no imported review history exists.
6. **Test coverage** — Assessment of whether changes are adequately tested.
7. **Scope/size note** — If large PR, note which clusters were deeply vs. lightly reviewed.

Each finding must include:
```
**[severity] Title** — `path/to/file.ts:42`
Description of the issue.
Evidence: what the code does vs. what it should do.
Suggested fix or question.
```

### 7.4 Final assembly checklist

Before submitting the review:

- [ ] Every finding has `file:line` evidence
- [ ] No finding duplicates an existing review thread
- [ ] No finding is about style/formatting that a linter handles
- [ ] Findings are ordered by severity (most important first)
- [ ] At least one positive observation is included
- [ ] Existing review thread summary is included
- [ ] GitHub-only fields are either evidenced or marked unavailable in local diff mode
- [ ] Verdict matches the findings (no blocker → no "request changes")
- [ ] Total finding count is reasonable (<15)
- [ ] Language is constructive ("this could" not "you should")

---

## Submitting the Review

Present the review to the user first. Only submit or post it on GitHub if the user explicitly asks you to do that. If the user asked only for review findings, stop here and do not run any command in this section.

### Post a formal review with verdict

```bash
# Approve the PR
gh pr review <N> --repo owner/repo --approve --body "Review body text here"

# Request changes
gh pr review <N> --repo owner/repo --request-changes --body "Review body text here"

# Comment only (no verdict)
gh pr review <N> --repo owner/repo --comment --body "Review body text here"
```

### Post a general comment (no verdict)

When you want to add a comment to the PR conversation without submitting a formal review:

```bash
gh pr comment <N> --repo owner/repo --body "Comment text here"
```

### Post inline comments on specific code lines

For line-level feedback, use the pull request review comments API:

```bash
# Comment on a specific line in a file
gh api repos/{owner}/{repo}/pulls/{N}/comments \
  -f body="Your inline comment here" \
  -f commit_id="$(gh pr view <N> --repo owner/repo --json headRefOid --jq '.headRefOid')" \
  -f path="src/api/middleware/auth.ts" \
  -F line=47 \
  -f side="RIGHT"
```

For multi-line comments (highlighting a range):

```bash
gh api repos/{owner}/{repo}/pulls/{N}/comments \
  -f body="This entire block needs error handling" \
  -f commit_id="$(gh pr view <N> --repo owner/repo --json headRefOid --jq '.headRefOid')" \
  -f path="src/api/middleware/auth.ts" \
  -F start_line=42 \
  -F line=55 \
  -f start_side="RIGHT" \
  -f side="RIGHT"
```

### Post a review with multiple inline comments atomically

To submit a review with inline comments as a single atomic review (preferred — groups everything under one review event):

```bash
gh api repos/{owner}/{repo}/pulls/{N}/reviews \
  -f event="REQUEST_CHANGES" \
  -f body="Overall review summary here" \
  --input - << 'EOF'
{
  "comments": [
    {
      "path": "src/api/middleware/auth.ts",
      "line": 47,
      "body": "Missing null check — `getUserRole()` can return undefined"
    },
    {
      "path": "src/api/routes/users.ts",
      "line": 32,
      "body": "This endpoint doesn't validate the `role` query parameter"
    }
  ]
}
EOF
```

Valid `event` values: `APPROVE`, `REQUEST_CHANGES`, `COMMENT`.

---

## Local Checkout Workflow

When you have the repository cloned locally, many operations become faster and more powerful. Use this workflow when the agent has filesystem access.

### Checkout the PR

```bash
gh pr checkout <N> --repo owner/repo
```

This switches to the PR's head branch locally. You now have full filesystem access to the proposed changes.

### Quick orientation

```bash
# See what changed compared to the base branch
git diff --stat $(git merge-base HEAD origin/main)..HEAD

# Full diff
git diff $(git merge-base HEAD origin/main)..HEAD

# Diff for a specific file
git diff $(git merge-base HEAD origin/main)..HEAD -- src/api/middleware/auth.ts

# List only the filenames that changed
git diff --name-only $(git merge-base HEAD origin/main)..HEAD

# Show the commit log for this PR's branch
git log --oneline $(git merge-base HEAD origin/main)..HEAD
```

### Read files directly

```bash
# Current version (PR proposes this)
cat src/api/middleware/auth.ts

# Base version (what exists before the PR)
git show origin/main:src/api/middleware/auth.ts

# Compare specific functions
git diff origin/main..HEAD -- src/api/middleware/auth.ts
```

### Search the codebase

```bash
# Find all references to a changed function
grep -rn "getUserRole" --include="*.ts" --include="*.tsx" src/

# Find all files importing a changed module
grep -rn "from.*auth" --include="*.ts" src/

# Find TODO/FIXME/HACK markers in changed files
git diff --name-only origin/main..HEAD | xargs grep -n "TODO\|FIXME\|HACK"

# Find all usages of an API endpoint path
grep -rn "/api/users" --include="*.ts" --include="*.tsx" .
```

### Run tests locally

```bash
# Run the full test suite
npm test  # or pytest, go test, etc.

# Run only tests related to changed files (example for Jest)
npx jest --changedSince=origin/main

# Run a specific test file
npx jest src/api/__tests__/users.test.ts
```

### Verify build

```bash
# Check that the project compiles
npm run build  # or tsc --noEmit, go build, cargo check, etc.

# Run linter
npm run lint
```

---

## § Goal Validation

> **This section is the canonical goal validation procedure referenced by SKILL.md Phase 4.**

Goal validation is the single most important phase of a PR review. It answers: "Does this PR achieve what it set out to do?" Run this procedure after gathering context (Phase 1–3) and before any code quality review (Phase 5).

### Inputs

- PR title and body (from Phase 1)
- Linked issue descriptions (from Phase 1)
- Full diff (fetched at the start of this procedure)
- File cluster map (from Phase 2)

### Procedure

**1. Form the hypothesis.**

Combine the PR body and linked issue descriptions into a single testable statement:

> "This PR should [verb] [outcome] by [mechanism]."

Examples:
- "This PR should fix the login timeout by increasing the session TTL from 15m to 1h and adding a refresh endpoint."
- "This PR should add CSV export to the reports page by adding a download button and a backend endpoint that streams CSV."

If you cannot form this sentence, the PR description is inadequate. Report:

> **[💡 Question] PR description does not clearly state the goal**
> I cannot determine what this PR is intended to accomplish. Could you add a description of the problem being solved and the approach taken?

**2. Trace happy paths.**

For each stated capability, find the code that implements it:
- Locate the entry point (API route, UI handler, CLI command)
- Trace the data flow through the implementation
- Verify the output matches the expected behavior
- Confirm all required layers are present (route + service + model + test)

**3. Trace failure paths.**

For each happy path, identify at least one failure scenario and verify it is handled:

| Happy path | Failure scenario | What to look for |
|-----------|------------------|-----------------|
| User submits form | Invalid input | Input validation, error message |
| API calls external service | Service is down | Timeout, retry, circuit breaker |
| Database write | Constraint violation | Error catch, rollback, user feedback |
| File upload | File too large | Size check, rejection message |
| Auth check | Token expired | 401 response, redirect to login |

**4. Check for gaps.**

Compare description vs. diff:

```
Described but NOT in diff → 🔴 Blocker (missing implementation)
In diff but NOT described → 🟡 Important (scope creep, may be intentional)
Described AND in diff     → ✅ Aligned
Neither described nor implemented → Not applicable (but consider if it should be)
```

**5. Assess completeness.**

A PR is complete when merging it would fully deliver the stated goal without requiring follow-up work that is not tracked. If follow-up is needed, it should be explicitly mentioned in the PR description with linked tracking issues.

### Output

Record a goal validation scorecard:

```
Goal: [one-sentence hypothesis]
Happy paths:  [✅ | ⚠️ | ❌] [details]
Error paths:  [✅ | ⚠️ | ❌] [details]
Completeness: [✅ | ⚠️ | ❌] [details]
Scope:        [✅ aligned | ⚠️ minor creep | ❌ significant untracked work]
```

If any check is ❌, this is a **🔴 blocker**. Report it before proceeding to Phase 5.
If any check is ⚠️, record it as a **🟡 important** finding and proceed.

---

## Quick Reference — CLI Commands

| Operation | Command |
|---|---|
| Get PR metadata | `gh pr view <N> --repo owner/repo --json title,body,state,author,labels,baseRefName,headRefName,reviewDecision,statusCheckRollup,files` |
| Get PR diff | `gh pr diff <N> --repo owner/repo` |
| Get changed files | `gh api repos/{owner}/{repo}/pulls/{N}/files --paginate` |
| Get review threads | `gh api repos/{owner}/{repo}/pulls/{N}/comments --paginate` |
| Get reviews | `gh api repos/{owner}/{repo}/pulls/{N}/reviews` |
| Get general comments | `gh api repos/{owner}/{repo}/issues/{N}/comments` |
| Get check status | `gh pr checks <N> --repo owner/repo` |
| Get commits | `gh api repos/{owner}/{repo}/pulls/{N}/commits` |
| Get file (head) | `gh api repos/{owner}/{repo}/contents/{path}?ref={head}` or `git show {head}:{path}` |
| Get file (base) | `gh api repos/{owner}/{repo}/contents/{path}?ref={base}` or `git show {base}:{path}` |
| Get issue details | `gh issue view <N> --repo owner/repo --json title,body,state,labels,comments` |
| Search code | `gh search code "query repo:owner/repo"` or `grep -rn "pattern" .` |
| Get CI logs | `gh run view <run-id> --repo owner/repo --log-failed` |
| Post review *(only when explicitly asked to submit/post)* | `gh pr review <N> --repo owner/repo --approve\|--request-changes\|--comment --body "text"` |
| Post comment *(only when explicitly asked to submit/post)* | `gh pr comment <N> --repo owner/repo --body "text"` |
| Post inline comment *(only when explicitly asked to submit/post)* | `gh api repos/{owner}/{repo}/pulls/{N}/comments -f body="text" -f commit_id="sha" -f path="file" -F line=42 -f side="RIGHT"` |
| Checkout PR locally | `gh pr checkout <N> --repo owner/repo` |

## Steering notes

> These notes capture real mistakes observed during derailment testing.

1. **Phase ordering is mandatory, not suggestive.** Skipping Phase 1 (Gather Context) and jumping straight to diff analysis is the most common workflow violation. Without context, you cannot validate goals or calibrate severity -- every subsequent finding is less reliable.
2. **The phase numbering in this file is offset by 1 from SKILL.md.** SKILL.md Phase 1 (Triage) maps to pre-workflow setup. SKILL.md Phase 2 maps to this file's Phase 1 (Gather Context). Consult the Navigation table at the top of this file when cross-referencing.
3. **Goal validation (this file's Phase 4) is the most frequently skipped phase.** Agents tend to jump from context-gathering to per-file review without confirming that the PR achieves its stated goal. This leads to reviews that are technically correct but miss the biggest risk: "the PR does not do what it claims."
4. **The cross-cutting sweep (this file's Phase 6) catches issues invisible at the file level.** Schema-consumer mismatches, missing auth on new endpoints, and env-var additions without deploy config are all coordination failures that only appear when you look across clusters.

> **Cross-reference:** See SKILL.md "Default workflow" section for the 8-phase overview and `references/file-clustering.md` for how to structure the cluster review in Phases 5-6.
