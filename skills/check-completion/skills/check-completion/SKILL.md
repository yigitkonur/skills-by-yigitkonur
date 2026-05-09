---
name: check-completion
description: Use skill if you are auditing task, session, plan, or branch completion claims - classify each item with the 22-status taxonomy, then remediate to terminal status.
---

# Check Completion

Two-phase skill. **Phase 1 — Audit**: scan task, session, plan, or branch completion claims, classify every item into one of 22 statuses, deliver a markdown audit table with evidence per row. **Phase 2 — Remediate**: execute against the audit until every in-scope task reaches a **terminal status** — `Implemented` for work finished, or one of the deliberate-stop statuses (`Deferred to Human`, `Deprioritized`, `Cancelled`, `Out of Scope`, `Superseded` with replacement verified, or `Blocked — unresolvable` with a concrete next step). No mid-task pauses. No defaulting to `Implemented` on faith.

## Trigger boundary

Use this skill when the task is to audit internal completion state for tasks, plans, sessions, or branches:

- audit what's been done vs. what was claimed done at the end of a session, a plan, or a branch of work
- produce a status-report on a project / sprint / multi-step task, with evidence per item
- convert a casual "are we done?" question into a rigorous completion audit
- catch silent gaps — tasks that were started, assumed complete, deferred, or forgotten
- recover from a crashed / interrupted / half-finished execution by enumerating what remains

Prefer another skill when:

- verifying a single claim before making it → use the Gate Function inline as a local verification gate
- evaluating external review feedback, reviewer comments, bot comments, or review docs → `evaluate-code-review`
- planning upcoming work from GitHub issues or sub-issues → `run-issue-tree`
- planning upcoming work without an issue tree → use the repo's planning workflow
- debugging runtime failures → `do-debug`
- reviewing someone else's PR or branch diff → `do-review`

## Non-negotiable rules (discipline)

1. **Two phases, not one.** The audit table is produced first, as a discrete artifact. Remediation starts only after the table exists. Do not quietly fix things while auditing — that defeats the audit.
2. **Never default to `Implemented`.** If there is any doubt, the task is not `Implemented`. Pick the most-pessimistic applicable status from `references/status-taxonomy.md`.
3. **`Assumed Complete` is not safe.** Treat it as suspect. Every `Assumed Complete` row requires a follow-up verification or a status downgrade.
4. **Every non-`Implemented` row has a concrete action required.** Vague follow-ups ("revisit later") are failures. State what to run, what to check, what to decide.
5. **Evidence before status.** Each `Implemented` row names the specific evidence (test output, commit SHA, file state, observed behavior). No evidence → no `Implemented`.
6. **Remediation order is blockers → broken → missing → untested.** Not the order the tasks were written.
7. **Remediation does not pause mid-task for confirmation.** The only halt conditions: (a) the work is complete, (b) a blocker is genuinely unresolvable and has been documented with a concrete next step.
8. **Terminal state is total coverage.** Every in-scope task ends at a terminal status per `status-taxonomy.md`: `Implemented` (work done with evidence), `Deferred to Human` / `Deprioritized` / `Cancelled` / `Out of Scope` (deliberate stop with rationale), `Superseded` (replacement verified `Implemented`), or `Blocked — unresolvable` (with concrete next step per `blocker-handling.md`). Rows left at non-terminal statuses (e.g., `Partially Implemented`, `Stalled`) are a failure of this skill.

## The 22-status taxonomy

Every task gets exactly one status from this list. Full definitions + detection rules + evidence patterns are in `references/status-taxonomy.md`.

| Status | Shape |
|---|---|
| `Implemented` | Fully complete, tested, working as intended |
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
| `Deferred to Human` | Flagged for human input; never returned to |
| `Deprioritized` | Pushed back without a clear plan to return |
| `Superseded` | Replaced by another task/approach — **verify the replacement is actually done** |
| `Cancelled` | Explicitly removed from scope — confirm this was intentional |
| `Ambiguous` | Requirements were unclear — implementation may be wrong or missing |
| `Duplicate` | Same task exists elsewhere — identify the canonical version and confirm it is complete |
| `Planned / Queued` | Scheduled but never started |
| `Not Planned` | Never scoped but clearly relevant — flag for inclusion |
| `Out of Scope` | Confirmed does not belong in this execution |

If tempted to invent a status: don't. Pick the closest existing one and explain the borderline in the Evidence column.

## Required workflow

### Phase 1 — Audit

#### 1. Disambiguate scope

Before enumerating tasks, state clearly what "in scope" means for this audit. See `references/scope-disambiguation.md`.

Options:
- **Session scope** — everything this conversation has been asked to do
- **Plan scope** — the tasks in a specific plan file or TodoList
- **Branch scope** — everything on the current git branch since it diverged
- **PR scope** — the commits + TODO comments + linked issues on an open PR
- **Custom scope** — an explicit list the user provided

If the user did not name a scope, pick the most comprehensive one that still produces a finite task list, and state the choice.

#### 2. Enumerate tasks from all sources

Scan the six audit sources. See `references/audit-sources.md` for extraction recipes per source.

| Source | What it reveals |
|---|---|
| Conversation messages | User asks; agent promises; "I'll do X next" that was never done |
| Tool-call history (Edit/Write/Bash) | What was actually modified; what was attempted and failed |
| TodoList state | Explicit task list with statuses the agent kept |
| Git log + diff | Committed work, commit boundaries, rename/delete operations |
| Test output / CI | Pass/fail per test; regressions since last known-good |
| Bash history | `rm` / `mv` / `touch` operations invisible to git until committed |

Combine the extractions into a deduplicated flat list. Do not skip any source — silent sources become silent gaps.

#### 3. Classify each task

For each task, run the Gate Function:

```
For status = `Implemented`:
  1. IDENTIFY what evidence would prove this task is complete
  2. RUN the verification (or locate the existing evidence in this session)
  3. READ the output / diff / state
  4. VERIFY the evidence matches the task
  5. ONLY THEN assign `Implemented`

For any other status:
  - Pick the most-pessimistic applicable status
  - Cite the specific evidence that rules out `Implemented`
```

See `references/evidence-patterns.md` for what "real evidence" looks like per status class. See `references/ruthless-auditing.md` for the discipline of distrust.

#### 4. Deliver the audit table

Output format:

```markdown
## Audit

Scope: <which scope + source list>
Sources scanned: <6 sources with one-line summary each>

| # | Task | Status | Evidence | Blocking? | Action Required |
|---|------|--------|----------|-----------|-----------------|
| 1 | <task> | `Implemented` | <evidence citation> | No | — |
| 2 | <task> | `Implemented but Broken` | <evidence + what broke> | No | Fix <specific failure>; re-run <command> |
| 3 | <task> | `Blocked` | <what's blocking> | Yes | <concrete next step to unblock> |
| … | … | … | … | … | … |
```

**Every non-`Implemented` row MUST have an `Action Required`.** Blocking tasks (`Yes` in Blocking column) rise to the top of Phase 2.

See `references/output-format.md` for full formatting rules.

### Phase 2 — Remediate

#### 5. Execute in priority order

```
1. Blockers — resolve, or document why unresolvable
2. `Implemented but Broken` / `Implemented but Outdated` — fix regressions
3. `Incorrectly Implemented` — correct misunderstandings
4. `Stalled` / `Crashed` / `Timed Out` — re-spawn and complete
5. `Partially Implemented` — finish edge cases, error handling, sub-steps
6. `Forgotten` / `Not Planned` (relevant) / `Planned / Queued` — implement
7. `Implemented but Untested` / `Assumed Complete` — verify (retest, re-run, confirm)
8. `Skipped` (no valid reason) — either implement or change status to `Out of Scope` with rationale
9. `Ambiguous` — resolve the ambiguity (ask or pick with justification) then execute
10. `Duplicate` — verify the canonical version is `Implemented`; mark the duplicate as `Superseded` with the canonical reference
11. `Superseded` — verify replacement is `Implemented`; if not, recurse on the replacement
12. `Deferred to Human` / `Deprioritized` / `Cancelled` / `Out of Scope` — document and leave as terminal
```

See `references/remediation-workflow.md` for the full order + one-at-a-time discipline.

#### 6. Handle blockers surgically

A blocker that cannot be resolved does not justify halting remediation. Document it, then continue with everything else.

See `references/blocker-handling.md` for the blocker-documentation format and how to judge "genuinely unresolvable" vs. "I just don't want to deal with it."

#### 7. Deliver the completion report

After remediation, produce the completion report — the audit table with every row updated to its terminal status.

```markdown
## Completion Report

Started: <N tasks audited, M rows needing remediation at Phase 1>
Status totals: audited tasks=<N>; Phase 1 rows needing remediation=<M>; rows remediated to `Implemented`=<X>; terminal non-`Implemented` rows=<Y>; non-terminal rows remaining=0

| # | Task | Started | Ended | Evidence |
|---|------|---------|-------|----------|
| 1 | <task> | `Implemented but Broken` | `Implemented` | <test output showing green> |
| 2 | <task> | `Blocked` | `Blocked — unresolvable` | <next step documented> |
| 3 | <task> | `Deferred to Human` | `Deferred to Human` | <named open question + owner> |
| … | … | … | … | … |
```

Every row ends at a terminal status: `Implemented`, `Deferred to Human`, `Deprioritized`, `Cancelled`, `Out of Scope`, `Superseded` with the replacement verified `Implemented`, or `Blocked — unresolvable` with a concrete next step.

## Output contract

Produce artifacts in this order — no batching, no skipping:

1. Scope declaration (after Step 1)
2. Source-scan summary (after Step 2) — one line per source with counts or "no results"
3. **Phase 1 audit table** (after Step 4) — the full markdown table, delivered as a discrete artifact before any remediation begins
4. Remediation log (during Step 5-6) — per-task "Fixed X by Y, evidence: Z" entries
5. Blocker documentation (as they arise in Step 6)
6. **Phase 2 completion report** (after Step 7) — the final table with every row at its terminal status

Phase 1 (artifact 3) and Phase 2 (artifact 6) are the two headline deliverables. Everything else is supporting.

## Rationalizations to counter (RED baseline, abridged)

Agents under pressure default to `Implemented`. The counters:

| Rationalization | Counter |
|---|---|
| "Everything looks done, it's probably fine" | "Probably" is not a status. Run the Gate Function per task. |
| "The agent reported success earlier" | Agent reports are not evidence. Re-verify independently. |
| "I wrote the code, so it's Implemented" | `Implemented but Untested` until you ran it. Exit code 0 beats "I wrote it." |
| "It was Implemented last week" | `Implemented but Broken` is a real status. Re-run now. |
| "I'll audit later; let me just fix the one obvious thing first" | No. Audit first. Fixing while auditing defeats the audit. |
| "Not finding evidence means there isn't any" | Not finding it means you didn't find it. Scan all 6 sources, then conclude. |
| "This is just a quick audit, I can skip the table" | The table is the audit. No table, no audit. |

Full table + pressure scenarios: `references/rationalizations.md`.

## Do this, not that

| Do this | Not that |
|---|---|
| scan all 6 audit sources before classifying | enumerate from memory and skip the source scan |
| produce the audit table as a discrete artifact before remediation | silently start fixing things while "auditing" |
| pick the most-pessimistic applicable status when in doubt | default to `Implemented` and hope |
| cite specific evidence per row | mark `Implemented` with "looks good" |
| document blockers with a concrete next step and continue | halt remediation on the first blocker |
| run the task-specific Gate Function per status | treat all `Implemented` candidates as equivalent |
| finish every in-scope task or explicitly flag unresolvable | leave rows in ambiguous states at end |
| use all 22 statuses; pick the closest if a task is borderline | invent new statuses |

## Guardrails and recovery

- Do not deliver the completion report without the audit table preceding it.
- Do not claim `Implemented` without running the specific verification this message.
- Do not default `Assumed Complete` rows to `Implemented` when retesting — pick the actual terminal state.
- Do not leave rows at non-terminal statuses (`Partially Implemented`, `Stalled`, etc.) in the completion report.
- Do not pause mid-Phase-2 for confirmation; resolve blockers or document and continue.

Recovery moves:

- **Source scan is taking too long** — set a budget (e.g., 10 minutes per source). If a source is producing noise with no signal, document and move on.
- **Too many tasks** (100+) — re-disambiguate scope; split into sub-audits if truly that many.
- **Audit revealed the scope itself was wrong** — pause once, re-scope, restart Phase 1.
- **Remediation keeps surfacing new tasks** — each new task gets added as a new row in the audit table with a status; then continues through remediation. Do not let scope creep silently.

## Reference routing

| File | Read when |
|---|---|
| `references/status-taxonomy.md` | Classifying a task — full definitions, detection rules, evidence patterns, borderline examples for all 22 statuses |
| `references/audit-sources.md` | Phase 1 Step 2 — extraction recipes per source (messages / tool trace / TodoList / git / tests / bash) |
| `references/evidence-patterns.md` | Step 3 classification — what "real evidence" looks like per status class; what is NOT evidence |
| `references/ruthless-auditing.md` | Mid-Phase-1 — the discipline of distrust; when to downgrade vs. upgrade status; borderline cases |
| `references/remediation-workflow.md` | Phase 2 — priority order, one-at-a-time discipline, per-status remediation recipe |
| `references/blocker-handling.md` | Phase 2 encounters a blocker — "unresolvable" criteria, documentation format, when to escalate |
| `references/output-format.md` | Formatting the audit table or the completion report — column rules, evidence citation style, terminal-state requirements |
| `references/rationalizations.md` | RED baseline — excuses that bypass audit rigor; pressure scenario to confirm discipline holds |
| `references/scope-disambiguation.md` | Step 1 — picking the right scope when the user's ask is broad; session vs. plan vs. branch vs. PR |
| `references/voice-discipline.md` | Writing audit rows and remediation log entries — forbidden phrases ("probably fine", "looks good"), preferred phrasing, citation style |

## Final checks

Before declaring done, confirm:

- [ ] scope declared and matches the user's ask
- [ ] all 6 audit sources scanned (or explicitly marked unavailable)
- [ ] audit table delivered as a discrete artifact before any remediation
- [ ] every row has exactly one of the 22 statuses (no invented statuses, no multi-status cells)
- [ ] every non-`Implemented` row has a concrete `Action Required`
- [ ] every `Implemented` row cites specific evidence (command output, commit SHA, file state, observable behavior)
- [ ] blockers documented with concrete next steps; remediation did not halt on first blocker
- [ ] completion report shows every row at a terminal status
- [ ] completion report status totals show non-terminal rows remaining = 0
- [ ] zero forbidden phrases in the report (grep-checked)
- [ ] rationalizations table consulted before declaring "everything looks done"
