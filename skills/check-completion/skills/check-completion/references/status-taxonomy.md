# Status Taxonomy — The 22 Statuses

Every task in the audit table gets exactly one status from this list. This file is the authoritative source for each status's definition, detection rules, and evidence patterns. Read this file when classifying a task and you are unsure which status applies.

## Contents
- [Terminal vs. non-terminal statuses](#terminal-vs-non-terminal)
- [The 22 statuses — definitions and detection](#the-22-statuses)
- [Picking between close statuses](#picking-between-close-statuses)
- [Never invent statuses](#never-invent-statuses)

## Terminal vs. non-terminal

A status is **terminal** if it is valid in the Phase 2 completion report. A status is **non-terminal** if encountering it in Phase 2 means more work is required.

| Terminal statuses | Non-terminal statuses |
|---|---|
| `Implemented` | `Partially Implemented`, `Implemented but Untested`, `Implemented but Broken`, `Implemented but Outdated`, `Assumed Complete`, `Incorrectly Implemented`, `Stalled`, `Timed Out`, `Crashed`, `Skipped`, `Forgotten`, `Blocked`, `Ambiguous`, `Planned / Queued`, `Not Planned`, `Duplicate`, `Superseded` (only if replacement is verified `Implemented`) |
| `Deferred to Human` | — |
| `Deprioritized` | — |
| `Cancelled` | — |
| `Out of Scope` | — |
| `Blocked — unresolvable` (see `blocker-handling.md`) | — |

In Phase 2, every non-terminal row must move to a terminal one. `Assumed Complete` is never terminal — it must be re-verified to become `Implemented` or downgraded.

## The 22 statuses

### `Implemented`

**Definition**: Fully complete, tested, and working as intended.

**Detection rules**:
- Code exists (file state verified)
- Verification command ran successfully in this message / session (exit 0)
- Output matches the task's stated intent
- No regressions introduced (other tests / flows still pass)

**Evidence required** (pick at least one):
- Test command output showing pass (`pytest`, `cargo test`, `pnpm test`, etc.)
- Build command output showing success (exit 0)
- Manual verification with cited observable behavior ("Ran `curl /api/foo`; got 200 with expected body")
- Commit SHA of the change + independent confirmation the commit shipped

**Borderline cases**:
- "I wrote the code but haven't run the test" → `Implemented but Untested`, not `Implemented`
- "The agent said it worked" → `Assumed Complete`, not `Implemented`
- "It used to work last week" → `Implemented but Broken` until re-run

### `Partially Implemented`

**Definition**: Core logic exists but edge cases, error handling, or sub-steps are missing.

**Detection rules**:
- Happy path exists and works
- At least one named sub-step or error path is missing
- Task description explicitly or implicitly calls for the missing parts

**Evidence required**:
- Specific list of what is present and what is missing
- File:line references for the partial implementation

### `Implemented but Untested`

**Definition**: Written but never validated or run.

**Detection rules**:
- Code exists on disk
- No test run output visible in session
- No manual verification cited

**Evidence required**: File state + statement "no verification run this session"

### `Implemented but Broken`

**Definition**: Was working, now failing due to regression or dependency change.

**Detection rules**:
- Historical evidence the code worked (git log, prior test runs)
- Current state fails (red test output, stack trace, or observed bad behavior)

**Evidence required**: Current failure output + reference to the prior passing state

### `Implemented but Outdated`

**Definition**: Done against old specs, superseded by a requirement change.

**Detection rules**:
- Code exists and runs cleanly (no broken state)
- Requirements changed after implementation
- Current behavior no longer matches updated requirements

**Evidence required**: Reference to the updated requirements + demonstration of the mismatch

### `Assumed Complete`

**Definition**: Marked done without actual verification — **treat as suspect**.

**Detection rules**:
- Task was marked done / checked off
- No verification evidence in the session supports the claim
- Common sign: agent wrote "Done" or a TodoList item toggled to `completed` without a preceding test/build/inspection

**Evidence required**: The claim-of-done + the absence of verification evidence

**This is NEVER a terminal status in the completion report.** Always re-verify to upgrade or downgrade.

### `Incorrectly Implemented`

**Definition**: Done but wrong, misunderstood, or misaligned with requirements.

**Detection rules**:
- Code exists and runs cleanly
- Behavior does not match the task's stated intent
- Common sign: agent implemented the opposite of what was asked, or a plausible-sounding variant

**Evidence required**: Task statement + observed behavior + specific mismatch

### `Stalled`

**Definition**: Started, hit a blocker, never resumed.

**Detection rules**:
- Partial progress visible (commits, tool calls, file state)
- Blocker was encountered (error, question, missing input)
- No subsequent work to resume

**Evidence required**: The partial progress + the blocker + the abandonment point

### `Timed Out`

**Definition**: Process was abandoned or killed mid-execution.

**Detection rules**:
- Long-running process was started
- No completion signal
- Common sign: session ran out of budget, context window, or user interruption

**Evidence required**: The started process + absence of completion output

### `Crashed`

**Definition**: Failed with an unhandled error.

**Detection rules**:
- Execution output shows a stack trace, non-zero exit, or terminal error
- No recovery attempt in the session

**Evidence required**: The error output or exit code

### `Skipped`

**Definition**: Bypassed intentionally without a valid reason.

**Detection rules**:
- Task was in scope
- Agent explicitly chose to skip ("I'll skip this for now")
- No justification or the justification doesn't hold up

**Evidence required**: The skip decision + why the justification doesn't hold

### `Forgotten`

**Definition**: Was in scope, never addressed, never flagged.

**Detection rules**:
- Task appeared in initial scope or plan
- No message, tool call, or commit references the task
- No acknowledgment it was set aside

**Evidence required**: Initial scope reference + absence of any subsequent trace

### `Blocked`

**Definition**: Cannot proceed — has an explicit unresolved dependency.

**Detection rules**:
- Task has a named dependency (external service, missing credentials, waiting on someone)
- Dependency is not resolved
- No workaround attempted

**Evidence required**: The specific dependency

See `blocker-handling.md` for distinguishing `Blocked` from `Blocked — unresolvable`.

### `Deferred to Human`

**Definition**: Flagged for human input and never returned to.

**Detection rules**:
- Explicit request for human decision / approval / information
- Human has not yet responded (or response was not incorporated)

**Evidence required**: The deferral message + absence of resolution

### `Deprioritized`

**Definition**: Pushed back without a clear plan to return.

**Detection rules**:
- Explicit decision to delay
- No target date / condition / trigger for resumption

**Evidence required**: The deprioritization decision + absence of resumption plan

### `Superseded`

**Definition**: Replaced by another task or approach — verify the replacement is actually done.

**Detection rules**:
- Original task was explicitly replaced (not silently dropped)
- Replacement task is named / linked

**Evidence required**: The original task + the replacement reference + replacement's own status

If replacement is not `Implemented`, flag both rows.

### `Cancelled`

**Definition**: Explicitly removed from scope — confirm this was intentional.

**Detection rules**:
- Explicit cancellation message or decision
- Rationale for cancellation (even if brief)

**Evidence required**: The cancellation decision + the rationale

### `Ambiguous`

**Definition**: Requirements were unclear — implementation may be wrong or missing.

**Detection rules**:
- Task statement has multiple plausible interpretations
- No agent or human disambiguated before work started (or after)
- Current state may or may not satisfy the task

**Evidence required**: The ambiguous statement + the interpretations

### `Duplicate`

**Definition**: Same task exists elsewhere — identify the canonical version and confirm it is complete.

**Detection rules**:
- Two or more task entries reference the same work
- No clear canonical

**Evidence required**: Both references + the choice of canonical

### `Planned / Queued`

**Definition**: Scheduled but never started.

**Detection rules**:
- Task has been named / added to a plan / TodoList
- No tool calls, commits, or messages show work begun

**Evidence required**: The plan reference + absence of execution evidence

### `Not Planned`

**Definition**: Never scoped but clearly relevant — flag for inclusion.

**Detection rules**:
- Task emerges from the audit (tool call touched something, test exposed a gap)
- Was not in the original scope / plan
- Clearly belongs in scope based on the task at hand

**Evidence required**: How the task surfaced + why it's relevant

### `Out of Scope`

**Definition**: Confirmed does not belong in this execution.

**Detection rules**:
- Task was considered and explicitly excluded
- Rationale documented

**Evidence required**: The exclusion decision + the rationale

## Picking between close statuses

Ambiguous pairings and how to resolve:

| Confused between | Rule |
|---|---|
| `Implemented` vs. `Implemented but Untested` | No verification run → always Untested. |
| `Implemented` vs. `Assumed Complete` | Agent-reported or TodoList-toggled without independent verification → Assumed Complete. |
| `Implemented but Broken` vs. `Implemented but Outdated` | Broken = same spec, now failing. Outdated = spec changed; code cleanly matches old spec. |
| `Blocked` vs. `Stalled` | Blocked has a current unresolved dependency. Stalled means the blocker existed but was abandoned without current pressure. |
| `Skipped` vs. `Deprioritized` | Skipped is a one-time decision. Deprioritized implies "later." |
| `Forgotten` vs. `Skipped` | Forgotten = silent omission. Skipped = explicit decision. |
| `Superseded` vs. `Cancelled` | Superseded has a replacement. Cancelled has no replacement. |
| `Planned / Queued` vs. `Not Planned` | Planned was in scope from the start. Not Planned emerged during audit. |
| `Ambiguous` vs. `Incorrectly Implemented` | Ambiguous means we can't tell if it's right. Incorrectly Implemented means we know it's wrong. |

**Default to the most-pessimistic status** if still unsure. Over-auditing → upgrades in Phase 2 are cheap; under-auditing → shipping with gaps is expensive.

## Never invent statuses

If a task doesn't fit any of the 22, it means:

1. The task description is ambiguous → `Ambiguous`
2. The task straddles two statuses → pick the more-pessimistic one; explain in Evidence
3. The task is genuinely novel → the taxonomy is exhaustive enough that this should never be the answer. Re-read the statuses. One fits.

Extending the taxonomy is a change to the skill, not to a single audit. Flag it as feedback to the skill author after delivering the audit with the current taxonomy.
