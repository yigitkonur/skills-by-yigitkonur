# Bug Tracing

Operation: **Sense-Making** (`Op: SenseMaking`), bug variant. For generic Sense-Making (research, judgment, evaluation), use `sense-making.md`. For recurring or systemic bugs where point fixes haven't worked, use `recurring-issue.md`.

Bug reasoning starts with the symptom and ends at the smallest causal fix.

## Bug Trace Loop

1. reproduce the bug
2. define the exact symptom
3. trace the execution path layer by layer
4. list 2-3 plausible causes
5. falsify weak causes quickly
6. prove the surviving mechanism
7. fix the smallest causal point
8. add a regression guard

## Symptom Discipline

Write the symptom precisely:
- where it appears
- when it appears
- what was expected
- what actually happened

If you cannot state the symptom cleanly, you are still debugging the story, not the system.

## Trace by Boundaries

Walk through the boundaries in order:
- input
- validation
- transformation
- state change
- output

At each boundary, ask: `What is the last thing I know is correct?`

## Cause Discipline

Do not confuse:
- the first file that looks suspicious
- the last file that threw
- the real causal point

The real cause is the earliest point where the system stopped meeting the assumptions required for the expected behavior.

## Fix Discipline

Prefer:
- the smallest fix that restores the broken assumption
- the narrowest regression guard that proves the bug stays fixed

Avoid:
- broad rewrites before the mechanism is proven
- speculative cleanup mixed into the bug fix
