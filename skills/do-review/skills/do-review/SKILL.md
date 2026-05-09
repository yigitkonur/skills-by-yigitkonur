---
name: do-review
description: Use skill if you are reviewing a GitHub PR (URL, number, gh pr view) or walking a branch/local diff for merge readiness with goal-grounded, evidence-based findings.
---

# Do Review

Reviewer-side merge-risk assessment for GitHub pull requests, branch diffs, and local working-tree diffs. Treat the change as a proposal with an intended outcome, not as a pile of files. Prioritize goal achievement, correctness, security, data safety, contract compatibility, test evidence, and existing review state.

## When To Use

Trigger on phrases and contexts like:

- *"review PR #123"*, *"review this PR"*, *"review github.com/owner/repo/pull/N"*
- *"is this safe to merge?"*, *"merge readiness check"*, *"give this PR a review"*
- *"walk this diff"*, *"review main...feature-branch"*, *"review origin/main...HEAD"*
- *"review my staged changes"*, *"review my working tree"*, *"review this local diff"*
- *"validate this codex-review finding against the diff"* (programmatic per-item mode)
- *"the PR already has CodeRabbit/Copilot/Greptile comments — what's left to flag?"*
- *"cluster the changed files and flag the highest-risk ones"*
- *"this PR has 40 changed files; tell me what to look at first"*

Do **NOT** use this skill for:

- *Author-side handoff* — opening a PR for your own branch, writing a self-review body, or staging your dirty tree before requesting feedback. Use `ask-review`.
- *Triaging review feedback already addressed at you* — human PR comments, bot comments already posted on a PR, markdown audit docs, multi-reviewer streams. Use `evaluate-code-review`.
- *Repo-state cleanup* — stale branches, multiple worktrees, bulk PR housekeeping. Use `run-repo-cleanup`.
- *Runtime debugging* — failing logs, repros, behavior diagnosis with no diff to judge. Use `do-debug`.
- *Style-only or formatter feedback* — defer to lint/formatter automation; do not author findings.

Boundary clarification: programmatic codex-review candidate validation inside `orchestrate-codex` stays here — that is reviewer-side merge-risk validation **before** PR handoff. Human or bot comments **already posted** on a PR are feedback triage and belong to `evaluate-code-review`.

## Invocation Contract

| Entry point | Input | Output | Mutation boundary |
|---|---|---|---|
| User-prompt mode | PR number/URL, branch comparison, local diff, or working tree | Markdown review in chat by default | No GitHub mutation unless the request explicitly says submit, post, publish, or comment |
| Skill-tool mode | PR target, local comparison, or candidate finding | Structured review/evaluation with evidence and severity | No mutation unless explicitly requested by the caller |
| Slash-command / orchestrated mode | `orchestrate-codex` review mode (or legacy `run-codex-review` shim); may pass a branch diff plus one `codex exec review` candidate item | Machine-readable per-item decision JSON | Never apply fixes; caller owns apply |

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
| GitHub PR mode | PR number/URL + repo (e.g. `owner/repo#123`, `gh pr view N`) | PR body, issues, CI, formal reviews, inline threads, bot comments |
| Local diff mode | Local git repo + base/head refs (e.g. `origin/main...HEAD`) or staged/unstaged diff | commit history, diff, file context; PR body/CI/review threads may be unavailable |

Before code review starts, name the exact comparison target on one line:
- `owner/repo#123`
- `origin/main...HEAD`
- `main...feature-branch`
- `HEAD + staged + unstaged`

If the target cannot be named in one line, stop and request the missing target before reviewing.

## Severity Calibration (Load-Bearing)

| Symbol | Tier | When to use |
|---|---|---|
| 🔴 | **Blocker** | Security flaw, data loss, common-path crash, or goal-validation miss that makes the PR unsafe to merge. |
| 🟡 | **Important** | Likely bug, contract gap, missing validation/error handling, meaningful performance issue, or missing coverage for risky behavior. |
| 🟢 | **Suggestion** | Worthwhile improvement that does not change merge safety. |
| 💡 | **Question** | Intent or behavior is unclear, or evidence is insufficient to assert a defect. |
| 🎯 | **Praise** | Specific thing done well; include at least one. |

Calibration checks:
- More than 3 blockers → reassess; blockers are rare.
- More than 10 total findings → re-apply the actionability gate.
- Same concern across several files → batch into one finding.
- Existing unresolved blocking thread on the same issue → surface it in the summary rather than duplicating it.

For boundary cases and worked examples, load `references/dimensions/severity-guide.md`.

## Evidence Contract (Load-Bearing)

Every finding must contain:

1. severity tier
2. concise title
3. exact `file:line` or line range
4. observed behavior
5. impact in this PR
6. suggested fix or clarifying question

Prefer concrete failing inputs, missing guards, contract mismatches, and phrasing from `references/output/communication.md`. Avoid style-only feedback, architecture redesigns, hypothetical chains, and approval claims without coverage notes. When the gate fails because evidence is incomplete, downgrade to a 💡 Question.

## Workflow Map

`SKILL.md` owns all 8 operational phases. Use this map when switching to deep references:

| Here (phase) | Deep reference / script |
|---|---|
| Phase 1 — Triage | SKILL.md only |
| Phase 2 — Gather context | `references/workflow/review-workflow.md`, `references/workflow/gh-cli-reference.md`, `scripts/parse-pr.sh` (`scripts/parse-pr.md` for usage) |
| Phase 3 — Scope and cluster | `references/analysis/file-clustering.md`, `scripts/cluster-files.sh` (`scripts/cluster-files.md` for usage) |
| Phase 4 — Existing review state | `references/workflow/comment-correlation.md`, `references/workflow/automation.md`, `scripts/parse-pr.sh` |
| Phase 5 — Goal validation | `references/workflow/review-workflow.md` |
| Phase 6 — Cluster review | `references/dimensions/review-dimensions.md`, `references/dimensions/security-review.md`, `references/dimensions/performance-review.md`, `references/dimensions/bug-patterns.md`, `references/dimensions/language-specific.md`, `references/analysis/diff-analysis.md` |
| Phase 7 — Cross-cutting sweep | `references/analysis/cross-cutting.md`, `references/analysis/large-pr-strategy.md` |
| Phase 8 — Synthesize output | `references/output/output-templates.md`, `references/output/communication.md`, `references/output/anti-patterns.md` |

## Workflow

### Phase 1 — Triage The Request

**Think first:** *"What exactly is being reviewed, and what judgment is requested?"*

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

**Think first:** *"What should this change accomplish, and what evidence exists before the diff?"*

Read:
- PR title, body, metadata, linked issues, and acceptance criteria
- CI/check state and commit history
- author notes, risk statements, and fixup signals

Use `scripts/parse-pr.sh` for repeatable GitHub PR gathering when shell and `gh` are available. Read `scripts/parse-pr.md` for inputs, output files, and failure modes. Use `references/workflow/gh-cli-reference.md` or MCP equivalents when the script cannot run.

Form one internal sentence: *This PR should accomplish X by changing Y in Z.*

Rules:
- If the PR body was produced by `ask-review`, treat it as the author-side self-review and declared intent/risk list. Validate it against the diff. Do not treat its weaknesses or questions as prior reviewer findings.
- Thin PR body or missing linked issue → record a context gap and carry lower confidence into goal validation.
- Local diff mode with no PR body/issues/CI → infer intent from the request, branch name, and commits; mark GitHub-only context unavailable.
- Failing CI → note failed checks, then focus on merge-risk issues not already proved by CI.
- Security scanner failure → read scan output before concluding the review. See `references/workflow/automation.md` for CI/scanner interpretation.

### Phase 3 — Scope And Cluster Files

**Think first:** *"Which changed files belong together, and where is merge risk concentrated?"*

Group changed files by concern:
- data or migrations
- security or auth
- API, routes, or contracts
- core or business logic
- frontend or user-visible behavior
- infrastructure, configuration, docs
- tests and type definitions paired with the source clusters they validate or constrain

Use `scripts/cluster-files.sh` for the initial cluster map when shell access is available. Read `scripts/cluster-files.md` for stdin, `--base/--head`, grouping rules, and output semantics. Detailed grouping rules and test/type pairing live in `references/analysis/file-clustering.md`.

Depth rules (calibrate by changed-line size):

| Changed lines | Action |
|---|---|
| < 100 | Deep review the full diff. |
| 100 – 500 | Deep review top clusters; lighter scan on low-risk clusters. |
| 500 – 1000 | Deep review highest-risk clusters; state which areas were skimmed. |
| > 1000 or incoherent mix | Flag PR size/scope and recommend specific split points. See `references/analysis/large-pr-strategy.md`. |

Recovery:
- Monorepo or unusual layout → cluster first by package/service, then by concern.
- Generated code dominates → review source definitions and note generated files lightly.
- Hunk context is insufficient → load full files and compare base versus head. See `references/analysis/diff-analysis.md`.

### Phase 4 — Read Existing Review State

**Think first:** *"What has already been found, resolved, disputed, or automated?"*

Fetch when available:
- formal reviews
- inline comment threads
- general PR conversation comments
- bot, AI, scanner, and dependency comments

Use `scripts/parse-pr.sh` for PR context artifacts, then build an already-reviewed map from the saved reviews and comments. Detailed correlation rules live in `references/workflow/comment-correlation.md`.

Classify review state:

| State | Action |
|---|---|
| **resolved** | Skip unless the bug remains or was reintroduced. |
| **active** | Acknowledge or extend; do not duplicate. |
| **outdated** | Recheck current code before re-raising. |
| **conversation-level** | Summarize as team discussion; do not map to code lines. |
| **unavailable** | State *"Existing review state: unavailable in local diff mode."* |

Do not compete with bots. Copilot, CodeRabbit, Greptile, Devin, Bito, Dependabot, CodeQL, Snyk, SonarQube, Semgrep, and similar tools count as prior review state. Read, deduplicate, verify, and recalibrate severity instead of repeating them. See `references/workflow/automation.md` for tool-specific dedupe rules.

### Phase 5 — Validate Goals

**Think first:** *"Would merging this actually deliver the stated outcome?"*

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

The detailed goal-validation procedure lives in `references/workflow/review-workflow.md`.

### Phase 6 — Review By Cluster

**Think first:** *"Within this cluster, what could make the PR unsafe to merge?"*

Apply dimensions in this order:

1. security and auth — `references/dimensions/security-review.md`
2. correctness and edge cases — `references/dimensions/bug-patterns.md`
3. data integrity and backward compatibility
4. API contract and validation
5. realistic performance impact — `references/dimensions/performance-review.md`
6. tests for changed behavior
7. maintainability only when it affects safety or comprehension

Full dimension checklist: `references/dimensions/review-dimensions.md`. Language-specific traps: `references/dimensions/language-specific.md`.

Trace blast radius for shared types, schemas, public interfaces, routes, auth boundaries, env vars, dependencies, configuration contracts, and deprecated APIs.

**Actionability gate** — report a finding only when **all** are true:

- in scope for this PR
- concrete user, system, or merge impact
- not just style, lint, formatter, or taste
- not already adequately covered by an existing thread
- consistent with repo conventions
- supported by code evidence: a specific line, missing guard, failing input, or contract mismatch

If the gate fails because evidence is incomplete, use a 💡 Question rather than a defect claim.

### Phase 7 — Cross-Cutting Sweep

**Think first:** *"Do the layers still line up after isolated cluster review?"*

Look for coordination failures:
- schema changed but API or consumers did not
- API changed but tests, docs, clients, or UI did not
- new endpoint or page without auth
- new env var or dependency without deploy/config updates
- changed source with no meaningful coverage for risky paths
- deprecated accessor or method with live call sites still using the old API
- new abstraction without migration path for existing consumers

If individual files look fine but the layers do not line up, treat that as a real review finding. Detailed cross-cluster patterns live in `references/analysis/cross-cutting.md`.

### Phase 8 — Calibrate, Synthesize, Output

**Think first:** *"Which findings survive severity calibration and what verdict follows from them?"*

Before finalizing:
- re-check severity (see Severity Calibration table above)
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

Use `references/output/output-templates.md` for full and compact templates. Use `references/output/communication.md` as the canonical wording reference. Use `references/output/anti-patterns.md` as a failure-mode checklist when review drifts toward noise.

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

## Final Checks

- [ ] exact comparison target named (URL, `owner/repo#N`, or `base...head`)
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
| File grouping, test/type pairing, initial cluster map | `references/analysis/file-clustering.md` (optionally `scripts/cluster-files.sh` and `scripts/cluster-files.md`) |
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
