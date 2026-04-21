# Remediation Workflow — Phase 2

After the audit table exists, Phase 2 executes until every in-scope row reaches a terminal status. This file is the execution recipe: order, per-status actions, discipline rules, and the termination condition.

## The core rule

**Do not stop, pause, or ask for confirmation mid-remediation unless a blocker is genuinely unresolvable.** This is an intentional divergence from obra's `executing-plans` skill, which stops and asks on every blocker. Audit-completion is designed to maximize progress through a fixed backlog; halting on every friction point defeats that.

When a blocker is encountered: document per `blocker-handling.md`, then continue with the next task.

## Priority order

Work through non-terminal statuses in this order. Not the order they appeared in the audit table.

```
1. Blockers (Blocked rows where Blocking=Yes)
   → resolve if possible; document with concrete next step if not

2. Implemented but Broken / Implemented but Outdated
   → fix the regression or update to current spec

3. Incorrectly Implemented
   → correct the misunderstanding

4. Stalled / Crashed / Timed Out
   → re-spawn and run to completion

5. Partially Implemented
   → finish the missing edges, error handling, sub-steps

6. Forgotten / Not Planned (relevant) / Planned / Queued
   → implement from zero

7. Implemented but Untested / Assumed Complete
   → run the verification; upgrade to Implemented or downgrade

8. Skipped (no valid reason)
   → either implement, or re-classify as Out of Scope with rationale

9. Ambiguous
   → disambiguate (ask, or pick with explicit justification), then execute

10. Duplicate
    → verify canonical row; mark duplicate as Superseded with canonical reference

11. Superseded
    → verify replacement is Implemented; if not, recurse on the replacement

12. Deferred to Human / Deprioritized / Cancelled
    → already terminal; confirm documentation is concrete
```

## Why this order

- **Blockers first** — unblocking may unlock multiple other tasks
- **Broken before missing** — regressions are often the root cause of other failures; fixing them first prevents chasing phantom issues
- **Regressions before net-new** — users notice regressions more acutely than missing features
- **Untested last among execution items** — verifying is cheaper than implementing; defer it until the backlog is clear

## One-at-a-time discipline

For each task in priority order:

```
1. Read the row: task, current status, Action Required
2. Execute the action (edit, run, fix, verify)
3. Verify: run the evidence-producing command tied to this task
4. Update the row: new status, new evidence citation
5. Move to the next task
```

**Do not batch** multiple remediations and verify once at the end. Two reasons:

- **Attribution** — if a single verification fails, you don't know which of the batched fixes caused it
- **Evidence per row** — the completion report requires per-row evidence; batched verification doesn't produce per-row citations

Exception: purely mechanical changes in the same file (typos, import reorderings) may be batched into one edit + one verification, as long as the evidence citation makes clear which rows were covered.

## Per-status remediation recipe

### `Blocked`

1. Re-read the blocker description
2. Check whether it's resolvable with current resources (env var, credentials, tool access)
3. If resolvable: unblock + continue
4. If unresolvable: move to `blocker-handling.md` for documentation + continue with next task

### `Implemented but Broken`

1. Re-read the failure output cited in Phase 1
2. Reproduce the failure fresh — it may have changed since the audit
3. Diagnose the root cause
4. Fix
5. Run the failing test/command again to confirm green
6. Upgrade to `Implemented` with new evidence citation

Do not declare fixed without the post-fix run.

### `Implemented but Outdated`

1. Read the updated spec cited in Phase 1
2. Identify the delta (what old spec said vs. new spec)
3. Update the code
4. Verify against the NEW spec (not the old test suite if the test was spec-locked)
5. Upgrade to `Implemented`

### `Incorrectly Implemented`

1. Re-read the original task statement
2. Compare to current behavior
3. Rewrite to match
4. Verify the new behavior matches the task
5. Upgrade to `Implemented`

### `Stalled` / `Crashed` / `Timed Out`

1. Read the abandonment point / error
2. Decide: resume from where it stopped, or restart
3. Execute to completion
4. Verify
5. Upgrade to `Implemented` (or a non-terminal status if new issues emerged)

### `Partially Implemented`

1. Read the "missing" list from Phase 1 evidence
2. Implement each missing sub-step
3. Verify each sub-step AND the overall task (adding sub-steps can break the happy path)
4. Upgrade to `Implemented`

### `Forgotten` / `Not Planned` / `Planned / Queued`

1. Read the task
2. Implement
3. Verify
4. Upgrade to `Implemented`

### `Implemented but Untested`

1. Identify the verification command (from `evidence-patterns.md`)
2. Run it
3. If passes: upgrade to `Implemented`
4. If fails: downgrade to `Implemented but Broken`; proceed to that row's recipe

### `Assumed Complete`

Same as `Implemented but Untested` — run the verification, upgrade or downgrade. Never upgrade without the run.

### `Skipped`

1. Re-read the skip decision
2. Decide: should this actually be in scope?
3. If yes: implement per the `Forgotten` recipe
4. If no: re-classify as `Out of Scope` with explicit rationale in the Evidence column

### `Ambiguous`

1. Pick an interpretation (the most likely / most compatible / most conservative)
2. State the choice + rationale
3. Implement
4. Verify
5. Upgrade to `Implemented`

If the ambiguity genuinely cannot be resolved without human input, re-classify as `Deferred to Human` and document what's needed.

### `Duplicate` / `Superseded`

1. Identify the canonical (for Duplicate) or replacement (for Superseded) task
2. Follow the canonical's remediation to terminal status
3. Mark the duplicate row: `Superseded — canonical: row #N`

### `Deferred to Human` / `Deprioritized` / `Cancelled` / `Out of Scope`

Already terminal — no remediation. Confirm the documentation is concrete:

- `Deferred to Human`: what specific question is pending?
- `Deprioritized`: what's the resumption trigger?
- `Cancelled`: what's the reason?
- `Out of Scope`: what scope boundary does it fall outside?

If any of these is vague, tighten the documentation before moving on.

## The emergent-task rule

During Phase 2, remediation may surface new tasks ("fixing the broken auth reveals an unvalidated session handler"). These emergent tasks are NOT ignored and NOT silently fixed:

1. Add them as new rows in the audit table
2. Classify (usually `Not Planned` or `Forgotten`)
3. Include them in the remediation priority order

This prevents scope creep from being invisible. The audit table grows as remediation reveals more work.

## Termination

Remediation is complete when:

- Every row in the audit table has a terminal status
- Every terminal status with a non-Implemented outcome (Blocked-unresolvable, Deferred, Deprioritized, Cancelled, Out of Scope) has concrete documentation

If you are tempted to declare Phase 2 complete with rows still at non-terminal statuses, re-read `rationalizations.md`. The answer is: either finish the row, or document it as unresolvable with a concrete next step.

## One exception to "don't pause"

You MAY pause ONCE, for a single round, if the audit reveals:

- A scope misunderstanding that would invalidate much of the remediation work
- A destructive operation that needs user authorization (file deletion outside your own work, data loss risk, pushing to shared remotes)
- A blocker whose resolution requires a credential or decision only the user can provide

In all other cases: document and continue. The single-pause rule is not a loophole; if you are using it more than once per audit, the discipline is slipping.

## After the last row

Produce the completion report per `output-format.md`. The report is the final deliverable — it transforms the audit table from "what we found" into "what was done" with per-row evidence of the transition.
