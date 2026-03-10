---
name: review-pr
description: Use skill if you are reviewing a GitHub pull request with a systematic, evidence-based workflow that clusters files, correlates existing comments, validates goals, and produces actionable findings.
---

# Review PR

Systematic pull request review grounded in the `gh` CLI and GitHub API.

## Trigger

Activate when the user asks to review a pull request, PR, or merge request on GitHub — whether by number, URL, or branch name.

## Core principles

1. **Goal-first** — verify the PR solves its stated problem before any quality check.
2. **Context before code** — read PR description, linked issues, commit messages, and CI status before touching diffs.
3. **Comment-aware** — read existing review comments and threads; never duplicate issues already flagged.
4. **Cluster then review** — group changed files by concern; review each cluster holistically, not file-by-file in isolation.
5. **Signal over noise** — every finding must pass the actionability filter before being reported.
6. **Evidence-based** — every claim needs `file:line` proof and a confidence assessment.

## Workflow

Follow these phases in order. Do not skip phases. Read `references/review-workflow.md` for the full procedure with command examples.

### Phase 1 — Gather context

Read the PR metadata, description, linked issues, and CI status. Build a mental model of **what the PR is trying to do and why** before looking at any code.

| Action | Command |
|--------|---------|
| Get PR title, body, author, base/head branches, labels | `gh pr view <N> --repo owner/repo --json title,body,state,author,labels,baseRefName,headRefName,reviewDecision` |
| Get linked issues from PR body (extract `#NNN` references) | `gh issue view <N> --repo owner/repo --json title,body,state,labels` for each linked issue |
| Get CI/check status | `gh pr checks <N> --repo owner/repo` |
| Get commit list and messages | `gh api repos/{owner}/{repo}/pulls/{N}/commits` |

**What to look for:**
- Does the PR body clearly state the problem and solution approach?
- Are there linked issues? If not, is the intent still unambiguous from the title/body?
- Commit history: is it a clean sequence of logical changes, or a messy squash-candidate with "fix typo" commits?
- CI status: any failing checks? Flaky tests vs. real failures?

**Red flags:**
- Empty PR body or generic "fix stuff" title → demand clarification before reviewing code.
- CI red with no acknowledgement in the PR body → likely the author hasn't verified the change works.
- PR targets the wrong base branch (e.g., `main` instead of `release/x.y`).
- Extremely large PR (>50 files or >1000 lines changed) with no breakdown in the description.

**Output of this phase:** A one-paragraph summary of PR intent, the problem it solves, and any red flags from CI.

### Phase 2 — Understand scope and cluster files

Get the list of changed files and group them into logical clusters before reviewing any diffs.

| Action | Command |
|--------|---------|
| Get changed file list with stats | `gh api repos/{owner}/{repo}/pulls/{N}/files` |

Read `references/file-clustering.md` for the clustering algorithm. Typical clusters:

- **API/Backend** — routes, controllers, services, middleware
- **Data** — models, schemas, migrations, seeds
- **Frontend** — components, pages, styles, assets
- **Infrastructure** — CI/CD, Docker, config, deployment
- **Tests** — test files corresponding to changed source files
- **Documentation** — README, docs, comments, changelog

For each cluster, note:
- Number of files and total lines changed
- Whether test files exist for the changed source files
- Which cluster is highest risk (largest blast radius)

**What to look for:**
- Ratio of test changes to source changes — low ratio signals potential coverage gaps.
- Files that don't belong in any cluster — could be accidental inclusions or scope creep.
- Generated files (lockfiles, compiled output, snapshots) — verify they're expected, not noise.

**Red flags:**
- Migration files with no rollback strategy or irreversible `DROP` statements.
- Config/infra changes buried among feature code — easy to miss, high blast radius.
- Renamed/moved files mixed with logic changes — makes diffs misleading.
- Test files deleted without explanation.

**Output of this phase:** A cluster map with file assignments and review priority order.

### Phase 3 — Read existing review state

Read all existing reviews and review comment threads on the PR. This prevents duplicating feedback and lets you build on prior reviewer work.

| Action | Command |
|--------|---------|
| Get all reviews (approvals, change requests, comments) | `gh api repos/{owner}/{repo}/pulls/{N}/reviews` |
| Get all review comment threads with resolution status | `gh pr view <N> --repo owner/repo --comments` and `gh api repos/{owner}/{repo}/pulls/{N}/comments` |
| Get general PR conversation comments | `gh api repos/{owner}/{repo}/issues/{N}/comments` |

Read `references/comment-correlation.md` for the correlation procedure.

For each existing review thread:
- Note the file and line range it covers
- Note whether it is resolved, outdated, or active
- Note the severity and type of issue raised
- Mark these locations as **already-reviewed** — do not raise the same issue unless you have additional evidence the reviewer missed

**What to look for:**
- Unresolved threads that the author dismissed without addressing — these need follow-up.
- Patterns in reviewer feedback: are multiple reviewers flagging the same concern?
- Outdated comments on lines that have since changed — verify the fix actually addressed the concern.

**Red flags:**
- Author force-pushed after receiving reviews without responding to comments — prior context may be lost.
- "LGTM" approvals with no substantive review on a complex PR.
- Unresolved security or correctness threads that have been open for multiple review rounds.

**Output of this phase:** A map of already-reviewed locations and a summary of unresolved threads.

### Phase 4 — Goal validation

Before any code quality review, verify the PR achieves its stated goal. Read `references/review-workflow.md` § Goal Validation for details.

| Action | Command |
|--------|---------|
| Get the full diff | `gh pr diff <N> --repo owner/repo` |
| Read key files in highest-priority cluster | `gh api repos/{owner}/{repo}/contents/{path}?ref={branch}` or `git show {branch}:{path}` |

Ask:
1. Does the diff address the problem described in the PR body and linked issues?
2. Are there happy-path and failure-path changes?
3. Is anything described in the PR body but not implemented in the diff?
4. Is anything implemented in the diff but not described in the PR body?

**What to look for:**
- Verify the fix actually covers the root cause, not just the symptom.
- Check for partial implementations — feature flags half-wired, API endpoints added but not routed.
- Confirm error/edge cases are handled, not just the golden path.

**Red flags:**
- Diff doesn't touch the files you'd expect given the PR description → possible wrong branch or incomplete work.
- PR says "fixes #123" but the linked issue describes a different problem than what the code addresses.
- New feature with zero error handling or input validation.
- Database/schema changes with no data migration for existing records.

If the PR fails goal validation, report this as a **🔴 blocker** before proceeding. A PR that passes every quality check but misses its goal is still a failed PR.

### Phase 5 — Systematic review by cluster

Review each file cluster in priority order. For each cluster, read the diff and relevant full files, then evaluate against the review dimensions.

Read `references/review-dimensions.md` for the full checklist. The dimensions in priority order:

1. **Security** — injection, auth bypass, secrets exposure, SSRF, XSS, unsafe deserialization
2. **Correctness** — logic errors, off-by-one, null/undefined handling, race conditions, error handling
3. **Data integrity** — migration safety, backward compatibility, data loss risk
4. **Performance** — N+1 queries, unbounded loops, missing pagination, memory leaks
5. **API contract** — breaking changes, missing validation, incorrect status codes
6. **Maintainability** — dead code, naming, excessive complexity, missing abstractions (only when egregious)
7. **Testing** — are the changes tested? are edge cases covered? are tests actually asserting the right things?

For each file in the cluster:

| Action | Command |
|--------|---------|
| Read the file diff (already from Phase 4) | Use the diff from `gh pr diff` |
| Read the full current file for context when needed | `gh api repos/{owner}/{repo}/contents/{path}?ref={branch}` or `git show {branch}:{path}` |
| Read the base version when comparing behavior changes | `gh api repos/{owner}/{repo}/contents/{path}?ref={base_branch}` or `git show {base_branch}:{path}` |
| Trace callers/references when evaluating blast radius | `gh search code "query repo:owner/repo"` or `grep -rn` in local checkout |

**What to look for per dimension:**
- **Security:** User input flowing into SQL/shell/template without sanitization. Auth checks missing on new endpoints. Secrets or tokens in code or logs. CORS/CSP changes that widen attack surface.
- **Correctness:** Boundary conditions (empty arrays, null, zero, max int). Async code missing `await`. Error paths that swallow exceptions silently. State mutations with no rollback on failure.
- **Performance:** Queries inside loops. Unbounded `SELECT *` without `LIMIT`. Large objects cloned unnecessarily. Missing indexes on new query patterns.
- **API contract:** Changed response shapes without versioning. Removed fields that consumers depend on. New required fields on existing endpoints.

**Red flags per dimension:**
- `eval()`, `dangerouslySetInnerHTML`, raw SQL concatenation, `chmod 777`, hardcoded credentials.
- `catch (e) {}` — empty catch blocks that silently swallow errors.
- `TODO` or `FIXME` comments added in the diff — indicates known incomplete work.
- Commented-out code submitted as part of the PR.

**Actionability filter** — before recording any finding, verify it passes ALL of these:
1. Is it in scope of this PR? (not pre-existing tech debt)
2. Is it worth the churn? (the fix is simpler than the problem)
3. Does it match codebase conventions? (don't impose external standards)
4. Is it intentional? (maybe the author made a deliberate tradeoff)
5. Does it have concrete impact? (not hypothetical)
6. Would a senior engineer on this team flag this? (calibration check)
7. Is the confidence ≥ 70%? (if not, phrase as a question instead of a finding)

### Phase 6 — Cross-cutting analysis

After reviewing all clusters, look for patterns that span multiple files:

- **Inconsistency** — same pattern handled differently in two places
- **Missing coordination** — API changed but consumer not updated
- **Test gaps** — source changed but no corresponding test changes
- **Documentation drift** — behavior changed but docs not updated
- **Dependency risks** — new dependencies added without justification

**What to look for:**
- A function signature changed in one file but callers in other files still pass old arguments.
- New environment variables referenced in code but not added to `.env.example` or deployment configs.
- Feature flags introduced but never checked in all relevant code paths.
- Error types defined but not handled by the global error handler.

**Red flags:**
- Import cycles created by the new changes.
- Shared utility functions modified without checking all consumers.
- Version bumps in `package.json` / `requirements.txt` without corresponding lockfile updates.

### Phase 7 — Synthesize and output

Compile findings into the output format. Read `references/output-templates.md` for the templates.

**Structure:**

```
## PR Review: <PR title>

### Summary
<1-2 sentence verdict: what the PR does, whether it achieves its goal>

### Verdict: <✅ Approve | 💬 Comment | 🔄 Request Changes>

### Findings

#### 🔴 Blockers (must fix before merge)
<findings that prevent merge>

#### 🟡 Important (should fix, may not block)
<findings that should be addressed but could ship>

#### 🟢 Suggestions (non-blocking improvements)
<optional improvements>

#### 💡 Questions (need author clarification)
<things that are unclear — use this instead of low-confidence findings>

#### 🎯 Positive observations
<things done well — always include at least one>

### Already-reviewed threads
<summary of existing review threads and their status>

### Test coverage assessment
<are changes adequately tested?>
```

**Each finding must include:**
```
**[severity] Title** — `path/to/file.ts:42`
<description of the issue>
<evidence: what the code does vs what it should do>
<suggested fix or question>
```

## Severity system

| Label | Icon | Meaning | Merge impact |
|-------|------|---------|-------------|
| Blocker | 🔴 | Security vulnerability, data loss, crash, goal failure | Blocks merge |
| Important | 🟡 | Bug, performance issue, missing error handling | Should fix; author decides if it blocks |
| Suggestion | 🟢 | Code improvement, better naming, simpler approach | Non-blocking |
| Question | 💡 | Unclear intent, possible issue pending clarification | Non-blocking; needs author response |
| Praise | 🎯 | Good pattern, clever solution, clean code | N/A — always include |

**Calibration rule:** If you have more than 3 blockers, re-examine each one. True blockers are rare. If you have more than 10 total findings, you are likely being too noisy — reapply the actionability filter.

## Anti-patterns

Read `references/anti-patterns.md` for the full list. The critical ones:

- **Never** review without reading the PR description and linked issues first.
- **Never** duplicate an issue already raised in an existing review thread.
- **Never** flag style/formatting issues that a linter should catch.
- **Never** suggest architectural changes that are out of scope for this PR.
- **Never** report a finding without `file:line` evidence.
- **Never** use "you should" language — use "this could" or ask questions.
- **Never** review a draft PR unless explicitly asked.
- **Never** approve without reading the full diff.

## Reference files

Load only the files needed for the current review phase.

| File | When to read |
|------|-------------|
| `references/review-workflow.md` | Read at the start of every review for the full phase-by-phase procedure with exact command syntax. |
| `references/gh-cli-reference.md` | Read when you need the exact syntax for any `gh` CLI command. |
| `references/file-clustering.md` | Read in Phase 2 when grouping changed files into review clusters. |
| `references/comment-correlation.md` | Read in Phase 3 when processing existing review comments and threads. |
| `references/review-dimensions.md` | Read in Phase 5 when doing the systematic review against the checklist. |
| `references/diff-analysis.md` | Read in Phase 5 when you need techniques for reading and understanding complex diffs. |
| `references/output-templates.md` | Read in Phase 7 when formatting the final review output. |
| `references/anti-patterns.md` | Read when you need to calibrate — especially if finding count is high. |
| `references/severity-guide.md` | Read when deciding between severity levels for a finding. |
| `references/language-specific.md` | Read when reviewing code in a specific language for language-specific patterns. |

## Guardrails

- Do not start Phase 5 (code review) before completing Phases 1-4.
- Do not report any finding that fails the actionability filter.
- Do not report more than 15 findings total without re-examining signal quality.
- Do mark the review as blocked if CI is failing — note which checks fail.
- Do always include at least one positive observation.
- Do always report the existing review thread summary so the author sees continuity.
