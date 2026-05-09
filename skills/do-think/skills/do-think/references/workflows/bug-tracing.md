# Bug Tracing

Operation: **Sense-Making** (`Op: SenseMaking`), ambiguous/post-debug bug variant. For reproducible runtime failures, use `do-debug` first. Use this workflow when `do-debug` needs a falsifiable hypothesis handoff or the failure is not reproducible enough for runtime debugging. For generic Sense-Making (research, judgment, evaluation), use `sense-making.md`. For recurring or systemic bugs where point fixes haven't worked, use `recurring-issue.md`.

Bug reasoning starts with the symptom and ends with the smallest falsification experiment or fix boundary to hand back to `do-debug`.

## Bug Trace Loop

1. capture the symptom or observed failure
2. define the exact symptom
3. trace the execution path layer by layer
4. list 2-3 plausible causes
5. falsify weak causes quickly
6. prove the surviving mechanism
7. choose the smallest diagnostic or fix boundary
8. hand back to `do-debug` with the verification check

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
- the smallest falsification experiment that tests the mechanism
- the narrowest diagnostic or fix boundary for `do-debug`

Avoid:
- broad rewrites before the mechanism is proven
- speculative cleanup mixed into the diagnostic or fix boundary
