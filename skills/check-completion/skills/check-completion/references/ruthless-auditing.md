# Ruthless Auditing — The Discipline of Distrust

The audit succeeds only if the auditor defaults to distrust. "Looks done" is a signal to investigate, not to conclude. This file is the mindset companion to `status-taxonomy.md` + `evidence-patterns.md`.

## The core move

When classifying a task, ask:

> **"What would change my mind?"**

If the answer is "nothing I would bother to check" → you are on autopilot, not auditing. Go back to `evidence-patterns.md` and name the specific evidence that would prove the task's claimed status.

## Default to pessimistic

Given two plausible statuses, pick the more pessimistic one. This is not paranoia — it is statistically right:

- Over-auditing → Phase 2 upgrades some rows cheaply. Cost: a little re-verification time.
- Under-auditing → shipping with silent gaps. Cost: regression, trust loss, rework later.

The asymmetry favors pessimism. Rigor in Phase 1 is cheap; omissions discovered in production are not.

## The four red flags

If you see any of these in your own draft audit rows, stop and re-classify. Borrowed in spirit from `obra/verification-before-completion`.

### Red flag 1: Fuzzy language

"Probably", "should", "seems to", "mostly", "I think" — every one of these is a downgrade trigger.

```
❌ "Probably Implemented — the happy path looks fine"
✅ "Partially Implemented — happy path works (test output at message 20); error handling not verified"
```

### Red flag 2: Satisfaction language

"Done!", "Great!", "Perfect!", "All set" — satisfaction without verification is the fingerprint of `Assumed Complete`.

```
❌ "Implemented — all tasks done!"
✅ "Implemented" + specific evidence per task, or the appropriate non-terminal status
```

### Red flag 3: Authority laundering

"The agent reported success", "the TodoList says completed", "the model said it was right" — none of these is verification. The auditor verifies, not the authority.

```
❌ "Implemented (subagent confirmed complete)"
✅ "Assumed Complete — subagent reported success at message 15; no independent verification since"
```

### Red flag 4: Extrapolation

"Tests passed for X, so Y is fine too" — cross-claiming evidence across unrelated tasks is a classic audit failure.

```
❌ "Implemented — pnpm test passed (covers all the auth changes)"
✅ "Implemented for the changes in session.test.ts; Implemented but Untested for the changes in csrf.test.ts (no test referenced this file)"
```

## The "minimum viable skeptic" test

Imagine a skeptic reading your audit, asking "how do you know?" for every row. For each row:

- **`Implemented` row**: could you answer the skeptic with a specific, citable observation?
- **Non-`Implemented` row**: could you answer with the specific signal that ruled out `Implemented`?

If the answer to either is "no", the row is not ready. Re-classify.

This is not a performance — it is a design principle. The audit table is the skeptic's summary of the work. Every row is defending itself against scrutiny.

## Borderline cases — judge calls

Some tasks live on the boundary between two statuses. Common judgment zones:

### `Implemented` vs. `Implemented but Untested`

If the change is trivial enough that running a test would be ceremonial (e.g., a one-word typo fix in a comment), and the file state can be verified by inspection — `Implemented` is defensible. But **every non-trivial change requires a test run** before `Implemented`.

Trivial means: no logic, no side effects, no downstream consumers. If in doubt, it's not trivial.

### `Implemented` vs. `Assumed Complete`

The distinction is verification this session. If the test was run in a prior session (not visible in the current session's output), re-run it. Past verification does not count as current evidence.

### `Blocked` vs. `Stalled`

Ongoing pressure matters. `Blocked` implies "still trying / still waiting for the dependency"; `Stalled` implies "abandoned and moved on." If the task hasn't been touched in 10+ messages and nothing in the session is actively unblocking it, it is `Stalled`, not `Blocked`.

### `Forgotten` vs. `Skipped`

Silence is `Forgotten`. Explicit decision is `Skipped`. The distinction matters for Phase 2 — `Forgotten` needs to be executed (the user still wants it); `Skipped` may need a scope conversation first.

### `Out of Scope` vs. `Deprioritized`

Crisp rule: `Out of Scope` is permanent for this audit; `Deprioritized` is temporary with vague resumption. Don't use `Out of Scope` to hide a real deprioritization decision — be honest that it's not-now-but-later.

## When a task resists classification

If you have run through:

1. The 22 statuses in `status-taxonomy.md`
2. The close-status picking rules
3. The evidence patterns
4. The minimum-viable-skeptic test

…and still cannot classify the task, the task description itself is the problem:

- **Multiple tasks conflated into one row** → split it into separate rows
- **Task description is a goal, not a task** ("improve performance" — what specifically?) → split into concrete sub-tasks
- **Task is aspirational, not committed** → `Not Planned` (if relevant) or `Out of Scope` (if not)

An audit cannot classify a task that isn't well-defined. Fix the task, then classify.

## Guarding against upgrade drift

As Phase 2 executes, statuses change. A `Blocked` task gets unblocked and becomes `Implemented`. A discipline risk: the agent upgrades a status without going back through the Gate Function.

Every status change in Phase 2 requires fresh evidence. "I fixed it" is not evidence; the test run after the fix is.

Specifically:

- Task was `Implemented but Broken` → ran the fix → ran the test → now `Implemented`: needs the test output
- Task was `Partially Implemented` → added the missing sub-step → now `Implemented`: needs both the sub-step's verification AND the overall task verification (did adding the sub-step break the happy path?)
- Task was `Blocked` → unblocked → now needs the full `Implemented` verification, not just "the blocker is gone"

See the completion report template in `output-format.md` — every upgraded row lists both the started-status and the ended-status, with evidence for the transition.

## When you are tempted to "just declare it done"

This is the peak pressure moment. You are near the end of Phase 2, a few rows remain non-terminal, and you want to be done.

**The rule**: the audit is done when every row is at a terminal status, OR when a row is explicitly unresolvable with a concrete next step. Not before.

If you are tempted to:

- Mark a row `Implemented` without re-running the verification
- Mark a row `Out of Scope` to avoid having to finish it
- Skip a row in the completion report

…stop, re-read this file, and finish the audit properly.

The user asked for an audit because vibe-based "done" failed. Delivering vibe-based "done" at the end of an audit restores the original problem.
