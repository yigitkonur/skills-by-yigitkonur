# Continuous Execution

Use this workflow when the task should keep moving without frequent human intervention.

## Core Rule

Do not stop early just because the first path got harder than expected.

Keep moving until one of these is true:
- the task is actually complete
- the next move requires real external approval
- the next move depends on information you cannot discover locally or verify safely

## Continuous Execution Loop

1. state the next objective
2. attempt the highest-signal local move
3. inspect the result
4. if blocked, choose the next best local move
5. escalate only after local options are exhausted

## What Counts as a Real Blocker

- missing credentials or permissions you cannot infer
- destructive or high-risk action that needs approval
- unavailable external system or service
- ambiguity that cannot be reduced from local context

## What Does Not Count as a Real Blocker

- first attempt failed
- code path was unfamiliar
- tool output was noisy
- one hypothesis was wrong
- the plan needs revision

## Anti-Stall Discipline

When blocked, ask:
- what can I verify locally?
- what assumption can I test?
- what smaller move would narrow the uncertainty?
- what evidence would make the next question sharper?

Stopping is correct only when autonomy would become reckless, not when it becomes inconvenient.
