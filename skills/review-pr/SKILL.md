---
name: review-pr
description: Use skill if you are reviewing a GitHub pull request with a systematic, evidence-based workflow that clusters files, correlates existing comments, validates goals, and produces actionable findings.
---

# Review PR

Systematic pull request review grounded in the `gh` CLI and GitHub API. Uses a 7-phase evidence-based workflow: gather context → cluster files → read existing reviews → validate goals → review by cluster → cross-cutting analysis → synthesize findings. Every finding must pass an actionability filter and include `file:line` evidence.

## Trigger

Activate when the user asks to review a pull request, PR, or merge request on GitHub — whether by number, URL, or branch name. Also activate when asked to check code changes, evaluate a diff, or assess merge readiness.

## Decision tree

```
What kind of review?
│
├── Standard PR review (most common)
│   ├── Full 7-phase workflow ───────────────► Workflow (below)
│   ├── Phase-by-phase CLI commands ─────────► references/review-workflow.md
│   ├── gh CLI syntax reference ─────────────► references/gh-cli-reference.md
│   └── Output format and templates ─────────► references/output-templates.md
│
├── What to check in the code
│   ├── Security vulnerabilities ────────────► references/security-review.md
│   ├── Performance anti-patterns ───────────► references/performance-review.md
│   ├── Common bug patterns ─────────────────► references/bug-patterns.md
│   ├── Full review dimensions checklist ────► references/review-dimensions.md
│   ├── Language-specific patterns ──────────► references/language-specific.md
│   └── Cross-file coordination gaps ────────► references/cross-cutting.md
│
├── How to organize the review
│   ├── Grouping files into clusters ────────► references/file-clustering.md
│   ├── Handling large PRs (500+ lines) ─────► references/large-pr-strategy.md
│   └── Reading and understanding diffs ─────► references/diff-analysis.md
│
├── Working with existing reviews
│   ├── Correlating with prior comments ─────► references/comment-correlation.md
│   └── Avoiding duplicate findings ─────────► references/comment-correlation.md § Rule 1
│
├── Writing good review comments
│   ├── Actionable comment structure ────────► references/communication.md
│   ├── Tone and phrasing guide ─────────────► references/communication.md § Language and Tone
│   └── Severity classification ─────────────► references/severity-guide.md
│
├── Working with automation
│   ├── CI/CD integration ───────────────────► references/automation.md
│   ├── Static analysis tools ───────────────► references/automation.md § Static Analysis
│   └── AI review tool integration ──────────► references/automation.md § AI Review Tools
│
└── Anti-patterns to avoid
    └── Full anti-pattern reference ─────────► references/anti-patterns.md
```

## Core principles

1. **Goal-first** — verify the PR solves its stated problem before any quality check.
2. **Context before code** — read PR description, linked issues, commit messages, and CI status before touching diffs.
3. **Comment-aware** — read existing review comments and threads; never duplicate issues already flagged.
4. **Cluster then review** — group changed files by concern; review each cluster holistically.
5. **Signal over noise** — every finding must pass the actionability filter before being reported.
6. **Evidence-based** — every claim needs `file:line` proof and a confidence assessment.

## Workflow

Follow these phases in order. Do not skip phases. Read `references/review-workflow.md` for the full procedure with command examples.

### Phase 1 — Gather context

Read PR metadata, description, linked issues, and CI status. Build a mental model of **what the PR is trying to do and why** before looking at any code.

| Action | Command |
|--------|---------|
| PR metadata | `gh pr view <N> --repo owner/repo --json title,body,state,author,labels,baseRefName,headRefName,reviewDecision` |
| Linked issues | `gh issue view <N> --repo owner/repo --json title,body,state,labels` |
| CI status | `gh pr checks <N> --repo owner/repo` |
| Commit messages | `gh api repos/{owner}/{repo}/pulls/{N}/commits` |

**What to look for:**
- Does the PR body clearly state the problem and solution approach?
- Are there linked issues? If not, is the intent unambiguous from the title/body?
- Commit history: clean logical sequence or messy fixup commits?
- CI status: any failing checks? Flaky tests vs. real failures?

**Red flags:** Empty PR body, failing CI, wrong base branch, extremely large scope (>50 files), draft state without explicit review request.

**Output:** One-paragraph summary of PR intent, the problem it solves, and any red flags.

### Phase 2 — Cluster files

Get changed files, group by concern, and set review priority order. Read `references/file-clustering.md` for the clustering algorithm.

| Cluster | Priority | Focus |
|---------|----------|-------|
| Data/Migration | 🔴 Highest | Rollback safety, backward compatibility, data loss |
| Security/Auth | 🔴 Highest | Auth bypass, permission escalation, secrets |
| API/Routes | 🟡 High | Input validation, breaking changes, error handling |
| Core Logic | 🟡 High | Correctness, race conditions, edge cases |
| Frontend | 🟢 Medium | State management, XSS, accessibility |
| Infrastructure | 🟢 Medium | Deploy safety, secret management |
| Config/Docs | ⚪ Low | Quick scan for accuracy |

For large PRs (>500 lines), read `references/large-pr-strategy.md` for chunking strategies and depth tiers.

### Phase 3 — Read existing review state

Fetch reviews, comment threads, and conversation. Build an already-reviewed map. Read `references/comment-correlation.md` for the full procedure.

**Rules:** Do not duplicate resolved threads. Acknowledge active threads. Recheck outdated threads.

### Phase 4 — Goal validation

Verify the PR achieves its stated purpose. Read `references/review-workflow.md` § Goal Validation.

1. Form hypothesis: "This PR should [accomplish X] by [changing Y]"
2. Verify happy paths are implemented
3. Verify failure/error paths are handled
4. Check for described-but-not-implemented (🔴 blocker)
5. Check for implemented-but-not-described (scope creep)
6. Assess completeness

A PR that passes every quality check but misses its goal is still a failed PR.

### Phase 5 — Systematic review by cluster

Review each cluster in priority order against the review dimensions. Read `references/review-dimensions.md` for the full checklist.

**Dimensions in priority order:**
1. **Security** — injection, auth bypass, secrets exposure → `references/security-review.md`
2. **Correctness** — logic errors, null handling, race conditions → `references/bug-patterns.md`
3. **Data integrity** — migration safety, backward compatibility, data loss
4. **Performance** — N+1 queries, unbounded loops, missing pagination → `references/performance-review.md`
5. **API contract** — breaking changes, missing validation, incorrect status codes
6. **Maintainability** — dead code, naming, complexity (only flag egregious issues)
7. **Testing** — are changes tested? are edge cases covered? are assertions meaningful?

For each file in the cluster:

| Action | Command |
|--------|---------|
| Read the file diff | Use the diff from `gh pr diff` (already fetched in Phase 4) |
| Read full file for context | `gh api repos/{owner}/{repo}/contents/{path}?ref={branch}` |
| Read base version for comparison | `gh api repos/{owner}/{repo}/contents/{path}?ref={base_branch}` |
| Trace callers/blast radius | `gh search code "query repo:owner/repo"` or `grep -rn` locally |

**Actionability filter** — before recording any finding, verify it passes ALL:
1. In scope of this PR? (not pre-existing tech debt)
2. Worth the churn? (fix simpler than the problem)
3. Matches codebase conventions? (don't impose external standards)
4. Could be intentional? (if so, phrase as question)
5. Concrete impact? (not hypothetical)
6. Would a senior on this team flag it? (calibration)
7. Confidence ≥ 70%? (if not, use 💡 question)

### Phase 6 — Cross-cutting analysis

Detect patterns spanning clusters. Read `references/cross-cutting.md` for the full coordination checklist.

Key checks: API changed but consumer not updated, new env var not in deploy config, shared type changed without updating importers, test gaps for changed source files.

### Phase 7 — Synthesize and output

Compile findings into structured output. Read `references/output-templates.md` for templates.

**Each finding must include:**
```
**[🟡 Important] Title** — `path/to/file.ts:42`
Description of the issue.
Evidence: what the code does vs what it should do.
Suggested fix or question.
```

**Output structure:**
```
## PR Review: <title> (#<number>)
### Summary — 1-2 sentence verdict
### Verdict: ✅ Approve | 💬 Comment | 🔄 Request Changes
### 🔴 Blockers (must fix) / 🟡 Important (should fix) / 🟢 Suggestions
### 💡 Questions (need author clarification)
### 🎯 Positive observations (always include at least one)
### Existing review threads summary
### File clusters reviewed (with review depth per cluster)
### Test coverage assessment
```

## Verdict decision matrix

| Condition | Verdict |
|-----------|---------|
| No blockers, ≤2 important, goal achieved | ✅ Approve |
| No blockers, has questions needing answers | 💬 Comment |
| No blockers, >2 important findings | 💬 Comment (lean toward Request Changes) |
| Any blockers | 🔄 Request Changes |
| Goal validation failed | 🔄 Request Changes |
| CI failing on critical checks | 🔄 Request Changes |
| All findings are 🟢 suggestions only | ✅ Approve (with notes) |

## Severity system

| Label | Icon | Meaning | Merge impact |
|-------|------|---------|-------------|
| Blocker | 🔴 | Security vuln, data loss, crash, goal failure | Blocks merge |
| Important | 🟡 | Bug, performance issue, missing error handling | Should fix |
| Suggestion | 🟢 | Code improvement, better naming, simpler approach | Non-blocking |
| Question | 💡 | Unclear intent, needs clarification | Non-blocking |
| Praise | 🎯 | Good pattern, clever solution, clean code | Always include |

**Calibration:** >3 blockers → re-examine. >10 findings total → re-apply actionability filter. 0 positive observations → add at least one.

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

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Reviewing without reading PR description | Always complete Phase 1 before looking at code. |
| Duplicating issues from existing review threads | Complete Phase 3 and check already-reviewed map before every finding. |
| Flagging style/formatting issues | If a linter should catch it, skip it. Read `references/automation.md`. |
| Too many findings (>15) | Re-apply actionability filter. Consider PR is too large, not too buggy. |
| No positive feedback | Always include ≥1 praise. Read `references/communication.md`. |
| "You should" language | Use "This could" or ask questions. Never directive. |
| Suggesting out-of-scope architecture changes | Note as 💡 Question for separate discussion, not a finding. |
| Low-confidence findings stated as facts | If confidence <70%, phrase as 💡 Question instead. |
| Reviewing draft PRs uninvited | Only review drafts when explicitly asked. |
| Approving without reading full diff | Always state what you reviewed vs skimmed. |
| Missing cross-file coordination bugs | Always run Phase 6 cross-cutting checks. |
| Ignoring AI/bot review comments | Read existing AI reviews in Phase 3; don't duplicate. |

## Reference files

Load only the files needed for the current review phase.

| File | When to read |
|------|-------------|
| `references/review-workflow.md` | Start of every review — full phase-by-phase procedure with CLI commands. |
| `references/gh-cli-reference.md` | When you need exact `gh` CLI syntax for any operation. |
| `references/file-clustering.md` | Phase 2 — grouping changed files into review clusters. |
| `references/comment-correlation.md` | Phase 3 — processing existing review comments and threads. |
| `references/review-dimensions.md` | Phase 5 — systematic review against the quality checklist. |
| `references/security-review.md` | Phase 5 — security-focused review with STRIDE and vulnerability patterns. |
| `references/performance-review.md` | Phase 5 — performance review with N+1, memory, and complexity patterns. |
| `references/bug-patterns.md` | Phase 5 — common bugs: race conditions, error handling, off-by-one. |
| `references/cross-cutting.md` | Phase 6 — cross-file coordination gaps and missing updates. |
| `references/large-pr-strategy.md` | Phase 2 — chunking and depth tiers for large PRs (500+ lines). |
| `references/diff-analysis.md` | Phase 5 — techniques for reading complex diffs. |
| `references/output-templates.md` | Phase 7 — formatting the final review output. |
| `references/communication.md` | Phase 7 — writing actionable comments with good tone. |
| `references/anti-patterns.md` | Calibration — when finding count is high or quality is uncertain. |
| `references/severity-guide.md` | When deciding between severity levels for a finding. |
| `references/language-specific.md` | When reviewing code in a specific language for language-specific patterns. |
| `references/automation.md` | When working with CI, static analysis, or AI review tools. |

## Minimal reading sets

### "I need to review a standard PR"

- `references/review-workflow.md`
- `references/file-clustering.md`
- `references/comment-correlation.md`
- `references/output-templates.md`

### "I need to do a security-focused review"

- `references/security-review.md`
- `references/review-dimensions.md` § Security
- `references/review-workflow.md`
- `references/severity-guide.md`

### "I need to review a large PR (500+ lines)"

- `references/large-pr-strategy.md`
- `references/file-clustering.md`
- `references/review-workflow.md`
- `references/cross-cutting.md`

### "I need help writing good review comments"

- `references/communication.md`
- `references/severity-guide.md`
- `references/anti-patterns.md`

### "I need to review for performance issues"

- `references/performance-review.md`
- `references/review-dimensions.md` § Performance
- `references/bug-patterns.md`

### "I need to check for common bugs"

- `references/bug-patterns.md`
- `references/review-dimensions.md` § Correctness
- `references/language-specific.md`

### "I need to work with CI and automated tools"

- `references/automation.md`
- `references/gh-cli-reference.md`

### "I need the complete review dimensions checklist"

- `references/review-dimensions.md`
- `references/security-review.md`
- `references/performance-review.md`
- `references/bug-patterns.md`
- `references/language-specific.md`

## Guardrails

- Do not start Phase 5 (code review) before completing Phases 1-4.
- Do not report any finding that fails the actionability filter.
- Do not report more than 15 findings total without re-examining signal quality.
- Do mark the review as blocked if CI is failing — note which checks fail.
- Do always include at least one positive observation.
- Do always report the existing review thread summary so the author sees continuity.

## Final reminder

This skill is split into many focused reference files organized by domain. Do not load everything at once. Start with the smallest relevant reading set above, then expand into neighboring references only when the task actually requires them. Every reference file in `references/` is explicitly routed from the decision tree above.
