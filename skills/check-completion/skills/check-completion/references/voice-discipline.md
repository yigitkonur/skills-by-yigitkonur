# Voice Discipline — Writing Audit Rows and Remediation Entries

The audit table and completion report are written artifacts. The voice — word choice, phrasing, what's included, what's forbidden — is part of the discipline. Sloppy voice hides sloppy classification; precise voice forces precise thinking.

Borrowed in spirit from obra's `verification-before-completion` skill and the voice rules shared across the code-review-related skills in this pack.

## The principle

**Actions speak. The audit is not the place for narrative framing or social softening.** State the status, cite the evidence, name the action. Every word that isn't doing one of those three things is noise.

## Forbidden in audit rows / remediation log

These phrases must not appear in Status cells, Evidence cells, Action Required cells, or remediation log entries.

### Hedge language

| Forbidden | Why it fails |
|---|---|
| "Probably", "should", "seems to", "likely" | Signals absence of verification. If hedging, the status is wrong — downgrade. |
| "Mostly", "basically", "more or less" | Indicates `Partially Implemented` — use the real status. |
| "I think" | Thought is not evidence. Cite observation or downgrade. |

Example:
```
❌ Implemented — probably works since the code compiled
✅ Implemented but Untested — code at src/foo.ts:L42 compiles (build output: cargo build exit 0); no test run this session
```

### Satisfaction / completion theater

| Forbidden | Why it fails |
|---|---|
| "Great!", "Perfect!", "Done!", "All set" | Satisfaction-without-verification. Fingerprint of `Assumed Complete`. |
| "All tasks complete", "Everything Implemented" (without per-row evidence) | Summary claims without citations. Break down per row with evidence. |
| "Nothing to worry about here" | Dismissal without audit. Every row needs classification. |

### Authority laundering

| Forbidden | Why it fails |
|---|---|
| "The agent confirmed..." | Agent confirmations are claims, not verifications. Re-verify. |
| "The TodoList shows completed" | TodoList state is a toggle, not evidence. `Assumed Complete` until independently verified. |
| "The user said it was done" | User claims warrant verification, not acceptance. |

### Filler / social softening

| Forbidden | Why it fails |
|---|---|
| "Thanks for the patience" | No purpose in a technical artifact. |
| "Hope this helps" | Hope is not part of the audit. |
| "Please let me know if anything else" | If there's follow-up, state it as Action Required. |
| "Sorry for the delay" | Apologies don't appear in status reports. |

## Preferred patterns

### Status-first, then evidence

```
Status: `Implemented but Broken`
Evidence: test output: pnpm test — session.test.ts:L42 FAIL — expected "active", got "expired"
Action Required: Fix the session renewal logic at src/session.ts:L50; re-run pnpm test
```

No preamble. No "so I checked this and...". Status, then citation, then next step.

### Past tense for observation, imperative for action

```
❌ Will run the test tomorrow — will see if it passes
✅ (Evidence) test output: pnpm test — 47 passed, 0 failed
✅ (Action Required) Run pnpm test:integration; address any failures
```

Observation describes what WAS seen. Action describes what SHOULD happen. Don't mix tenses across a row.

### One sentence per cell

Each cell is one sentence. If a row's evidence or action needs more than one sentence, the row may be conflating multiple concerns — consider splitting.

Exception: `Blocked — unresolvable` rows need three things per `blocker-handling.md` (dependency, next step, owner). Three short sentences or one compound sentence with clear separators.

### Citation consistency

Use the citation style from `evidence-patterns.md` (`<source>: <quote>` format) throughout. Do not switch styles mid-audit.

## Remediation log entries

During Phase 2, each task's remediation produces a log entry (not in the final completion report, but visible as execution narration).

Format:

```
[Row N] <task> — <before-status> → <after-status>
  Action: <what was done>
  Evidence: <post-action citation>
  Notes: <optional — one line max>
```

Example:

```
[Row 4] Add session timeout — Implemented but Broken → Implemented
  Action: Added timeout check at src/session.ts:L50; reverted the accidental strict-mode change at L12
  Evidence: test output: pnpm test — 47 passed (session.test.ts now green)
  Notes: none
```

No commentary ("Great, this worked!"), no narrative ("First I thought about it, then I noticed..."), no social elements.

## The "re-read this file" rule

Before writing each audit table, scan this file. If your draft row breaks the voice discipline, rewrite it. Over time, the rules become automatic — until then, the external check is the safety net.

## Common mistakes

| Mistake | Fix |
|---|---|
| "Looks good, status Implemented" | Drop "looks good"; cite the observation that proves Implemented. If there isn't one, pick a different status. |
| "Implemented (with minor caveats)" | Caveats imply not fully Implemented. Use the correct status (`Partially Implemented`, `Implemented but Untested`, etc.). |
| "I'll verify this later" in an Action Required cell | "Later" doesn't belong. State the specific command to run and when. |
| "Needs testing" as Action Required | Name the test. "Run pnpm test" is concrete; "needs testing" is not. |
| Mixing first-person narrative ("I checked") with third-person audit style | Pick one. Audit tables are typically third-person / imperative. |

## Why this matters

The audit table is the user's basis for deciding what to ship, what to roll back, and what to plan next. If the voice is hedgy or soft, the user has to re-derive confidence per row. If the voice is crisp and evidence-cited, the user reads and decides. The skill's value is in the latter case.
