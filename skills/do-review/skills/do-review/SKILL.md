---
name: do-review
description: "Use skill if you are reviewing a GitHub pull request or branch diff for merge readiness with high-signal findings grounded in stated goals and changed-file clusters."
---

# Do Review

Reviewer-side merge-risk assessment for GitHub pull requests, branch diffs, and local diffs. Treat the change as a proposal with an intended outcome, not as a pile of files. Prioritize goal achievement, correctness, security, data safety, contract compatibility, test evidence, and existing review state.

## Trigger Boundary

Use this skill when the task is to:
- review a PR, pull request, branch diff, local comparison, or working-tree diff
- decide whether a change is safe to merge
- validate a candidate review finding against the actual diff
- review a PR that already has human, bot, or AI comments
- triage a large diff by grouping changed files into review clusters

Prefer sibling skills when:
- author-side PR handoff, self-review body, or reviewer prompt preparation → `ask-review`
- received human/bot review comments already posted on a PR → `evaluate-code-review`
- messy repo state, multiple worktrees, stale branches, or bulk PR cleanup → `run-repo-cleanup`
- codex fleet execution or per-branch review-loop orchestration → `orchestrate-codex` or the legacy `run-codex-review` shim
- runtime diagnosis with logs, repros, or failing behavior → `do-debug`
- single-purpose test execution with no review judgment → use the repo's test workflow directly
- formatting, lint, or style-only feedback → skip or rely on automation

Boundary with `evaluate-code-review`: programmatic codex-review candidate validation inside `orchestrate-codex` still belongs here because it is reviewer-side merge-risk validation before PR handoff. Human or bot comments already posted on a PR are feedback triage and belong to `evaluate-code-review`.

## Invocation Contract

| Entry point | Input | Output | Mutation boundary |
|---|---|---|---|
| User-prompt mode | PR number/URL, branch comparison, local diff, or working tree | Markdown review in chat by default | No GitHub mutation unless the request explicitly says submit, post, publish, or comment |
| Skill-tool mode | PR target, local comparison, or candidate finding | Structured review/evaluation with evidence and severity | No mutation unless explicitly requested by the caller |
| Slash-command / orchestrated mode | `orchestrate-codex` review mode or legacy `run-codex-review`; may pass a branch diff plus one `codex exec review` candidate item | Machine-readable per-item decision JSON | Never apply fixes; caller owns apply |

Programmatic per-item shape:

```json
{
  "decision": "accepted|rejected|ambiguous",
  "severity": "blocker|important|suggestion|question",
  "evidence": ["file:line"],
  "rationale": "Why the item does or does not survive review.",
  "intended_fix_shape": "Optional only for accepted items."
}
```

For per-item mode, return only the JSON object unless the caller asks for explanatory markdown.

## Review Stance

1. **Goal first** — a PR that misses its stated outcome fails even when the code looks clean.
2. **Context before diff** — read why the change exists before judging how it is implemented.
3. **Conversation-aware** — human reviewers, bots, scanners, and author replies are evidence.
4. **Cluster before depth** — review related files together and start with highest-risk clusters.
5. **Evidence before opinion** — every finding needs `file:line`, observed behavior, impact, and a suggested fix or question.
6. **Questions before speculation** — if evidence is incomplete, ask instead of asserting.
7. **Signal over volume** — fewer high-confidence findings beat long nit lists.

## Target Modes

| Mode | Required target | Context available |
|---|---|---|
| GitHub PR mode | PR number/URL + repo | PR body, issues, CI, formal reviews, inline threads, bot comments |
| Local diff mode | Local git repo + base/head refs or staged/unstaged diff | commit history, diff, file context; PR body/CI/review threads may be unavailable |

Before code review starts, name the exact comparison target:
- `owner/repo#123`
- `origin/main...HEAD`
- `main...feature-branch`
- `HEAD + staged + unstaged`

If the target cannot be named in one line, stop and request the missing target before reviewing.

## Workflow Map

`SKILL.md` owns all 8 operational phases. The deeper procedure in `references/workflow/review-workflow.md` uses matching names and notes that its detailed sections start after target triage. Use this map when switching between files:

| Here | Deep reference |
|---|---|
| Phase 1 — Triage | SKILL.md only |
| Phase 2 — Gather context | `references/workflow/review-workflow.md` / `scripts/parse-pr.sh` |
| Phase 3 — Scope and cluster | `references/analysis/file-clustering.md` / `scripts/cluster-files.sh` |
| Phase 4 — Existing review state | `references/workflow/comment-correlation.md` / `scripts/parse-pr.sh` |
| Phase 5 — Goal validation | `references/workflow/review-workflow.md` |
| Phase 6 — Cluster review | `references/dimensions/review-dimensions.md` |
| Phase 7 — Cross-cutting sweep | `references/analysis/cross-cutting.md` |
| Phase 8 — Synthesize output | `references/output/output-templates.md` |

## Workflow

### Phase 1 — Triage The Request

**Think first:** "What exactly is being reviewed, and what judgment is requested?"

Identify:
- PR number, URL, branch, repo, and comparison target
- local diff base/head refs, staged/unstaged scope, or working-tree scope
- full review versus targeted review
- draft versus ready state
- merge-readiness, security-only, performance-only, or general review

Default to **general merge-readiness review** when the request does not specify a dimension.

Decision rules:
- Draft PR without an explicit deep-review request → stop after a readiness note or keep feedback high-level.
- Targeted request such as security on PR 42 → still gather context, cluster files, and read review state before going deep.
- No GitHub PR target but a local repo + diff range exists → switch to local diff mode.
- No clear target and no local diff → request the target before reviewing code.
- Refactor, deprecation, or behavioral-change PR → weight call-site impact, backwards compatibility, and migration path.

### Phase 2 — Gather Context Before Code

**Think first:** "What should this change accomplish, and what evidence exists before the diff?"

Read:
- PR title, body, metadata, linked issues, and acceptance criteria
- CI/check state and commit history
- author notes, risk statements, and fixup signals

Use `scripts/parse-pr.sh` for repeatable GitHub PR gathering when shell and `gh` are available. Read `scripts/parse-pr.md` for inputs, output files, and failure modes. Use `references/workflow/gh-cli-reference.md` or MCP equivalents when the script cannot run.

Create one internal sentence:
`This PR should accomplish X by changing Y in Z.`

Rules:
- If the PR body was produced by `ask-review`, treat it as the author-side self-review and declared intent/risk list. Validate it against the diff. Do not treat its weaknesses or questions as prior reviewer findings.
- Thin PR body or missing linked issue → record a context gap and carry lower confidence into goal validation.
- Local diff mode with no PR body/issues/CI → infer intent from the request, branch name, and commits; mark GitHub-only context unavailable.
- Failing CI → note failed checks, then focus on merge-risk issues not already proved by CI.
- Security scanner failure → read scan output before concluding the review.

### Phase 3 — Scope And Cluster Files

**Think first:** "Which changed files belong together, and where is merge risk concentrated?"

Group changed files by concern:
- data or migrations
- security or auth
- API, routes, or contracts
- core or business logic
- frontend or user-visible behavior
- infrastructure, configuration, docs
- tests and type definitions paired with the source clusters they validate or constrain

Use `scripts/cluster-files.sh` for the initial cluster map when shell access is available. Read `scripts/cluster-files.md` for stdin, `--base/--head`, grouping rules, and output semantics.

Depth rules:
- Under 100 changed lines → deep review the full diff.
- 100 to 500 changed lines → deep review top clusters; lighter scan on low-risk clusters.
- 500 to 1000 changed lines → deep review highest-risk clusters and state skimmed areas.
- More than 1000 changed lines or incoherent mixed concerns → flag PR size/scope and recommend specific split points.

Recovery:
- Monorepo or unusual layout → cluster first by package/service, then by concern.
- Generated code dominates → review source definitions and note generated files lightly.
- Hunk context is insufficient → load full files and compare base versus head.

### Phase 4 — Read Existing Review State

**Think first:** "What has already been found, resolved, disputed, or automated?"

Fetch when available:
- formal reviews
- inline comment threads
- general PR conversation comments
- bot, AI, scanner, and dependency comments

Use `scripts/parse-pr.sh` for PR context artifacts, then build an already-reviewed map from the saved reviews and comments.

Classify review state:
- **resolved** → skip unless the bug remains or was reintroduced
- **active** → acknowledge or extend; do not duplicate
- **outdated** → recheck current code before re-raising
- **conversation-level** → summarize as team discussion; do not map to code lines
- **unavailable** → state `Existing review state: unavailable in local diff mode`

Do not compete with bots. Copilot, CodeRabbit, Greptile, Devin, Bito, Dependabot, CodeQL, Snyk, SonarQube, Semgrep, and similar tools count as prior review state. Read, deduplicate, verify, and recalibrate severity instead of repeating them.

### Phase 5 — Validate Goals

**Think first:** "Would merging this actually deliver the stated outcome?"

Check in order:
1. happy path exists end to end
2. failure and error paths are handled
3. described behavior appears in the diff
4. risky extra scope is explained
5. supporting changes exist where needed: tests, docs, config, consumers, type definitions, migrations

Immediate escalation:
- described-but-not-implemented behavior → likely 🔴 Blocker
- implemented-but-not-described risky scope → at least 🟡 Important
- success criteria cannot be explained → raise the context/goal gap before deeper review

### Phase 6 — Review By Cluster

**Think first:** "Within this cluster, what could make the PR unsafe to merge?"

Apply dimensions in this order:
1. security and auth
2. correctness and edge cases
3. data integrity and backward compatibility
4. API contract and validation
5. realistic performance impact
6. tests for changed behavior
7. maintainability only when it affects safety or comprehension

Trace blast radius for shared types, schemas, public interfaces, routes, auth boundaries, env vars, dependencies, configuration contracts, and deprecated APIs.

Actionability gate — report a finding only when all are true:
- in scope for this PR
- concrete user, system, or merge impact
- not just style, lint, formatter, or taste
- not already adequately covered by an existing thread
- consistent with repo conventions
- supported by code evidence: a specific line, missing guard, failing input, or contract mismatch

If the gate fails because evidence is incomplete, use a 💡 Question rather than a defect claim.

### Phase 7 — Cross-Cutting Sweep

**Think first:** "Do the layers still line up after isolated cluster review?"

Look for coordination failures:
- schema changed but API or consumers did not
- API changed but tests, docs, clients, or UI did not
- new endpoint or page without auth
- new env var or dependency without deploy/config updates
- changed source with no meaningful coverage for risky paths
- deprecated accessor or method with live call sites still using the old API
- new abstraction without migration path for existing consumers

If individual files look fine but the layers do not line up, treat that as a real review finding.

### Phase 8 — Calibrate, Synthesize, Output

**Think first:** "Which findings survive severity calibration and what verdict follows from them?"

Before finalizing:
- re-check severity
- remove duplicates
- batch repeated issues into one finding
- cut speculative, stylistic, or low-value comments
- include at least one specific positive observation
- summarize existing review state, or mark it unavailable
- state which clusters were deep-reviewed versus skimmed
- note CI/check state and test coverage for risky paths

Verdict ladder:
- **✅ Approve** — no blockers, goal achieved, only minor issues or questions remain
- **💬 Comment** — non-blocking issues or open questions remain
- **🔄 Request Changes** — blocker, goal failure, or risky unaddressed gap

Only suggestions → do not request changes.

## Severity Calibration

- **🔴 Blocker** — security flaw, data loss, common-path crash, or goal-validation miss that makes the PR unsafe to merge
- **🟡 Important** — likely bug, contract gap, missing validation/error handling, meaningful performance issue, or missing coverage for risky behavior
- **🟢 Suggestion** — worthwhile improvement that does not change merge safety
- **💡 Question** — intent or behavior is unclear, or evidence is insufficient
- **🎯 Praise** — specific thing done well; include at least one

Calibration checks:
- More than 3 blockers → reassess; blockers are rare.
- More than 10 total findings → re-apply the actionability gate.
- Same concern across several files → batch into one finding.
- Existing unresolved blocking thread on the same issue → surface it in the summary rather than duplicating it.

## Evidence Contract

Every finding must contain:
1. severity
2. concise title
3. exact `file:line` or line range
4. observed behavior
5. impact in this PR
6. suggested fix or clarifying question

Prefer concrete failing inputs, missing guards, contract mismatches, and phrasing from `references/output/communication.md`. Avoid style-only feedback, architecture redesigns, hypothetical chains, and approval claims without coverage notes.

## Output Contract

Default output is markdown/chat. GitHub mutation is allowed only when the request explicitly says submit, post, publish, or comment.

| Mode | Trigger | Required output |
|---|---|---|
| Markdown review mode | Default | verdict, findings, specific positive observation, review-state summary, coverage, checks/CI state, and test/verification notes |
| Formal GitHub review mode | Explicit submit/post/publish request | one `gh pr review` verdict with body; no surprise inline comments |
| Inline comment mode | Explicit inline-comment request + line metadata | batch comments into one review event when possible |
| Programmatic per-item mode | `orchestrate-codex` or legacy shim | JSON decision only; no posting or fixes |

Compact output still must state:
- comparison target
- existing review state or unavailable
- clusters deep-reviewed versus skimmed
- checks/CI state
- at least one specific positive observation

Use `references/output/output-templates.md` for full and compact templates. Use `references/output/communication.md` as the canonical wording reference. Keep `references/output/anti-patterns.md` as a failure-mode checklist, not a phrase table.

## Final Checks
- [ ] exact comparison target named
- [ ] goal hypothesis formed or context gap stated
- [ ] changed files clustered before deep review
- [ ] existing review state read or marked unavailable
- [ ] bot/scanner findings deduplicated
- [ ] goal validation completed before quality review
- [ ] each finding passes the actionability gate
- [ ] severity count recalibrated
- [ ] verdict follows from findings
- [ ] compact output includes target, review state, coverage, checks/CI, and praise
- [ ] no GitHub mutation occurred unless explicitly requested
## Reference And Script Routing

Load the smallest set needed for the current phase.

| Need | Load |
|---|---|
| End-to-end review procedure and goal validation | `references/workflow/review-workflow.md` |
| Exact GitHub CLI and MCP equivalents | `references/workflow/gh-cli-reference.md` |
| CI, static analysis, bot/scanner interpretation | `references/workflow/automation.md` |
| Existing review threads, bot dedupe, team discussion state | `references/workflow/comment-correlation.md` |
| File grouping, test/type pairing, initial cluster map | `references/analysis/file-clustering.md`; optionally `scripts/cluster-files.sh` and `scripts/cluster-files.md` |
| Deep diff interpretation and base/head comparison | `references/analysis/diff-analysis.md` |
| Large PR depth tiers and split suggestions | `references/analysis/large-pr-strategy.md` |
| Cross-cluster coordination gaps | `references/analysis/cross-cutting.md` |
| Full review dimension checklist | `references/dimensions/review-dimensions.md` |
| Security-focused review | `references/dimensions/security-review.md` |
| Performance-focused review | `references/dimensions/performance-review.md` |
| Common correctness traps | `references/dimensions/bug-patterns.md` |
| Language-specific pitfalls | `references/dimensions/language-specific.md` |
| Severity examples and boundary cases | `references/dimensions/severity-guide.md` |
| Output templates and verdict formats | `references/output/output-templates.md` |
| Comment wording, batching, and positive observations | `references/output/communication.md` |
| Anti-noise checklist when review drifts | `references/output/anti-patterns.md` |
| Read-only PR context collection | `scripts/parse-pr.sh` and `scripts/parse-pr.md` |
