---
name: audit-completion
description: Use skill if you are verifying claimed-done work, auditing session/plan/branch completion, finding partial or assumed-complete tasks, or answering "are we done?" with evidence.
---

# Check Completion

Two-phase audit-and-remediate skill. **Phase 1 — Audit:** scan task / session / plan / branch claims, classify every item into one of 22 statuses with cited evidence, deliver a markdown table. **Phase 2 — Remediate:** drive every in-scope row to a **terminal** status — `Implemented` for finished work, or a deliberate-stop terminal (`Deferred to Human`, `Deprioritized`, `Cancelled`, `Out of Scope`, `Superseded` with replacement verified, or `Blocked — unresolvable` with concrete next step). No mid-task pauses. No defaulting to `Implemented` on faith.

## When to use

- *"are we done?" / "what's left?" / "did we actually finish X?"*
- *verifying a claimed-done session, plan, branch, or PR before declaring complete*
- *producing a status report on a multi-step task with evidence per item*
- *catching silent gaps — tasks that were started, assumed complete, deferred, or forgotten*
- *recovering from a crashed / interrupted / half-finished execution by enumerating what remains*
- *converting a casual "I think we're good" into a rigorous completion audit*
- *triaging a TodoList where statuses drifted from reality*

Do NOT use when:

- verifying a single claim before making it — use the Gate Function inline as a local verification gate, not the full audit
- evaluating reviewer comments, bot comments, or external review docs → `review-feedback`
- planning *upcoming* work from GitHub issues → the `gh` CLI directly (the run-issue-tree skill was retired)
- reviewing someone else's PR or branch diff → `review-pr`
- debugging a runtime failure → `debug-runtime`

## The 22-status taxonomy (load-bearing)

Every task gets exactly one status. If tempted to invent a 23rd, don't — pick the closest existing one and explain the borderline in the Evidence column. Full definitions, detection rules, evidence patterns, and borderline examples live in `references/status-taxonomy.md`.

| Status | Shape |
|---|---|
| `Implemented` | Fully complete, tested, working as intended (terminal) |
| `Partially Implemented` | Core logic exists; edges / error-handling / sub-steps missing |
| `Implemented but Untested` | Written; never validated or run |
| `Implemented but Broken` | Was working; now failing due to regression / dependency change |
| `Implemented but Outdated` | Done against old specs; superseded by a requirement change |
| `Assumed Complete` | Marked done without actual verification — **treat as suspect** |
| `Incorrectly Implemented` | Done but wrong, misunderstood, or misaligned with requirements |
| `Stalled` | Started; hit a blocker; never resumed |
| `Timed Out` | Process abandoned or killed mid-execution |
| `Crashed` | Failed with an unhandled error |
| `Skipped` | Bypassed intentionally without a valid reason |
| `Forgotten` | In scope; never addressed; never flagged |
| `Blocked` | Cannot proceed — explicit unresolved dependency |
| `Deferred to Human` | Flagged for human input; never returned to (terminal) |
| `Deprioritized` | Pushed back without a clear plan to return (terminal) |
| `Superseded` | Replaced by another task — **verify the replacement is `Implemented`** (terminal) |
| `Cancelled` | Explicitly removed from scope — confirm intentional (terminal) |
| `Ambiguous` | Requirements were unclear — implementation may be wrong or missing |
| `Duplicate` | Same task exists elsewhere — identify canonical version, confirm complete |
| `Planned / Queued` | Scheduled but never started |
| `Not Planned` | Never scoped but clearly relevant — flag for inclusion |
| `Out of Scope` | Confirmed does not belong (terminal) |

**Terminal statuses** (allowed in the Phase 2 completion report): `Implemented`, `Deferred to Human`, `Deprioritized`, `Cancelled`, `Out of Scope`, `Superseded` (replacement verified), `Blocked — unresolvable` (with concrete next step). Any other status in the final report is a failure of this skill.

## Non-negotiable rules

1. **Two phases, not one.** The audit table is a discrete artifact delivered before any remediation begins. Quietly fixing things while auditing defeats the audit.
2. **Never default to `Implemented`.** Any doubt → not `Implemented`. Pick the most-pessimistic applicable status.
3. **`Assumed Complete` is suspect.** Every `Assumed Complete` row gets a follow-up verification or a status downgrade.
4. **Every non-`Implemented` row has a concrete `Action Required`.** "Revisit later" is a failure — state what to run, what to check, what to decide.
5. **Evidence before status.** Each `Implemented` row names specific evidence (test output, commit SHA, file state, observed behavior). No evidence → no `Implemented`.
6. **Remediation order is blockers → broken → missing → untested.** Not the order tasks were written.
7. **Never pause mid-Phase-2 for confirmation.** Halt only when the work is complete or a blocker is genuinely unresolvable and documented with a concrete next step.
8. **Total terminal coverage.** Every in-scope row ends at a terminal status. Rows left at `Partially Implemented`, `Stalled`, etc. in the completion report are a failure.

## Required workflow

### Phase 1 — Audit

#### Step 1. Disambiguate scope

State what "in scope" means for this audit before enumerating tasks. See `references/scope-disambiguation.md` for picking when the user's ask is broad.

Options: **session** (everything this conversation has been asked to do) · **plan** (tasks in a specific plan/TodoList) · **branch** (everything on the current git branch since divergence) · **PR** (commits + TODO comments + linked issues on an open PR) · **custom** (explicit list).

If no scope was named, pick the most comprehensive that still produces a finite list, and state the choice.

#### Step 2. Enumerate tasks from all six sources

Scan every source — silent sources become silent gaps. Extraction recipes per source are in `references/audit-sources.md`.

| Source | What it reveals |
|---|---|
| Conversation messages | User asks; agent promises; "I'll do X next" never done |
| Tool-call history (Edit/Write/Bash) | What was actually modified; what was attempted and failed |
| TodoList state | Explicit task list with statuses the agent kept |
| Git log + diff | Committed work, commit boundaries, rename/delete operations |
| Test output / CI | Pass/fail per test; regressions since last known-good |
| Bash history | `rm` / `mv` / `touch` operations invisible to git until committed |

Combine into a deduplicated flat list.

#### Step 3. Classify each task with the Gate Function

```
For status = `Implemented`:
  1. IDENTIFY what evidence would prove this task is complete
  2. RUN the verification (or locate existing evidence in this session)
  3. READ the output / diff / state
  4. VERIFY the evidence matches the task
  5. ONLY THEN assign `Implemented`

For any other status:
  - Pick the most-pessimistic applicable status
  - Cite the specific evidence that rules out `Implemented`
```

What "real evidence" looks like per status class is in `references/evidence-patterns.md`. The discipline of distrust — when to downgrade vs. upgrade, borderline cases — is in `references/ruthless-auditing.md`.

#### Step 4. Deliver the audit table

```markdown
## Audit

Scope: <which scope + source list>
Sources scanned: <6 sources with one-line summary each>

| # | Task | Status | Evidence | Blocking? | Action Required |
|---|------|--------|----------|-----------|-----------------|
| 1 | <task> | `Implemented` | <evidence citation> | No | — |
| 2 | <task> | `Implemented but Broken` | <evidence + what broke> | No | Fix <failure>; re-run <command> |
| 3 | <task> | `Blocked` | <what's blocking> | Yes | <concrete next step to unblock> |
```

Every non-`Implemented` row MUST have `Action Required`. Rows with `Yes` in Blocking rise to top of Phase 2. Full formatting rules and citation style live in `references/output-format.md`.

If the audit is saved to a markdown file, run `bash scripts/check-task-status.sh <audit.md>` before Phase 2. The checker reports status counts, invented statuses, and non-`Implemented` rows missing `Action Required`. Usage and exit codes are in `scripts/check-task-status.md`.

### Phase 2 — Remediate

#### Step 5. Execute in priority order

```
1.  Blockers — resolve, or document why unresolvable
2.  `Implemented but Broken` / `Implemented but Outdated` — fix regressions
3.  `Incorrectly Implemented` — correct misunderstandings
4.  `Stalled` / `Crashed` / `Timed Out` — re-spawn and complete
5.  `Partially Implemented` — finish edge cases, error handling, sub-steps
6.  `Forgotten` / `Not Planned` (relevant) / `Planned / Queued` — implement
7.  `Implemented but Untested` / `Assumed Complete` — verify (retest, re-run, confirm)
8.  `Skipped` (no valid reason) — implement or change to `Out of Scope` with rationale
9.  `Ambiguous` — resolve the ambiguity (ask or pick with justification) then execute
10. `Duplicate` — verify canonical is `Implemented`; mark duplicate `Superseded` with reference
11. `Superseded` — verify replacement is `Implemented`; if not, recurse on replacement
12. `Deferred to Human` / `Deprioritized` / `Cancelled` / `Out of Scope` — terminal; document
```

Full one-at-a-time remediation discipline and per-status recipes are in `references/remediation-workflow.md`.

#### Step 6. Handle blockers surgically

A blocker that cannot be resolved does not justify halting remediation. Document it and continue. Criteria for "genuinely unresolvable" vs. "I just don't want to deal with it," and the documentation format, are in `references/blocker-handling.md`.

#### Step 7. Deliver the completion report

```markdown
## Completion Report

Started: <N tasks audited, M rows needing remediation>
Status totals: audited=<N>; remediation rows=<M>; remediated to `Implemented`=<X>; terminal non-`Implemented`=<Y>; non-terminal remaining=0

| # | Task | Started | Ended | Evidence |
|---|------|---------|-------|----------|
| 1 | <task> | `Implemented but Broken` | `Implemented` | <test output green> |
| 2 | <task> | `Blocked` | `Blocked — unresolvable` | <next step documented> |
| 3 | <task> | `Deferred to Human` | `Deferred to Human` | <named open question + owner> |
```

Every row ends at a terminal status. If the report is saved, run `bash scripts/check-task-status.sh <report.md>` before declaring done — the checker fails if any `Ended` value is invented or non-terminal.

## Output contract

Produce these artifacts in order — no batching, no skipping:

1. Scope declaration (after Step 1)
2. Source-scan summary (after Step 2) — one line per source with counts or "no results"
3. **Phase 1 audit table** (after Step 4) — discrete artifact before any remediation
4. Remediation log (during Steps 5–6) — per-task "Fixed X by Y, evidence: Z" entries
5. Blocker documentation (as they arise in Step 6)
6. **Phase 2 completion report** (after Step 7) — final table, every row terminal

Artifacts 3 and 6 are the headline deliverables. Everything else is supporting.

## Rationalizations to counter

Agents under pressure default to `Implemented`. High-signal counters:

| Rationalization | Counter |
|---|---|
| "Everything looks done, it's probably fine" | "Probably" is not a status. Run the Gate Function per task. |
| "The agent reported success earlier" | Agent reports are not evidence. Re-verify independently. |
| "I'll audit later; let me fix the one obvious thing first" | No. Audit first. Fixing while auditing defeats the audit. |

Full table and pressure scenarios live in `references/rationalizations.md`. Forbidden phrases ("probably fine", "looks good") and preferred phrasing live in `references/voice-discipline.md`.

## Guardrails and recovery

- Do not deliver the completion report without the audit table preceding it.
- Do not claim `Implemented` without running the specific verification this message.
- Do not default `Assumed Complete` rows to `Implemented` when retesting — pick the actual terminal state.
- Do not leave rows at non-terminal statuses in the completion report.
- Do not pause mid-Phase-2 for confirmation; resolve blockers or document and continue.

Recovery moves:

- **Source scan taking too long** — set a per-source budget (e.g., 10 min). Noise with no signal → document and move on.
- **100+ tasks** — re-disambiguate scope; split into sub-audits.
- **Audit revealed the scope itself was wrong** — pause once, re-scope, restart Phase 1.
- **Remediation surfacing new tasks** — add each as a new row with a status; do not let scope creep silently.

## Reference routing

| File | Read when |
|---|---|
| `references/status-taxonomy.md` | Classifying — full definitions, detection rules, evidence patterns, borderline examples for all 22 statuses |
| `references/audit-sources.md` | Step 2 — extraction recipes per source (messages / tool trace / TodoList / git / tests / bash) |
| `references/evidence-patterns.md` | Step 3 — what "real evidence" looks like per status class; what is NOT evidence |
| `references/ruthless-auditing.md` | Mid-Phase-1 — discipline of distrust; when to downgrade vs. upgrade; borderline cases |
| `references/remediation-workflow.md` | Phase 2 — priority order, one-at-a-time discipline, per-status remediation recipe |
| `references/blocker-handling.md` | Phase 2 blocker — "unresolvable" criteria, documentation format, when to escalate |
| `references/output-format.md` | Formatting audit table or completion report — column rules, evidence citation style, terminal-state requirements |
| `references/rationalizations.md` | RED baseline — excuses that bypass audit rigor; pressure scenarios |
| `references/scope-disambiguation.md` | Step 1 — picking the right scope; session vs. plan vs. branch vs. PR |
| `references/voice-discipline.md` | Writing rows and log entries — forbidden phrases, preferred phrasing, citation style |
| `scripts/check-task-status.sh` | Deterministic table check for saved markdown — counts, unknown statuses, missing actions, non-terminal endings |
| `scripts/check-task-status.md` | Usage, input shapes, output fields, exit codes for the checker |

## Final checks

- [ ] scope declared and matches the user's ask
- [ ] all 6 audit sources scanned (or explicitly marked unavailable)
- [ ] audit table delivered as discrete artifact before any remediation
- [ ] every row has exactly one of the 22 statuses (no invented statuses, no multi-status cells)
- [ ] every non-`Implemented` row has a concrete `Action Required`
- [ ] every `Implemented` row cites specific evidence
- [ ] blockers documented with concrete next steps; remediation did not halt on first blocker
- [ ] completion report shows every row at a terminal status
- [ ] non-terminal rows remaining = 0
- [ ] saved markdown passes `bash scripts/check-task-status.sh <file>`
- [ ] zero forbidden phrases (grep-checked)
- [ ] rationalizations table consulted before declaring "everything looks done"
