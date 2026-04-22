# Evidence and Falsification

Reasoning quality depends more on evidence quality than on verbal sophistication.

## Evidence Ladder

Prefer stronger evidence over weaker evidence:

1. direct observation from the current system
2. reproducible command or test output
3. exact code or config in the repo
4. primary docs or specs
5. inference from patterns
6. intuition or analogy

Do not let a level-6 hunch overrule level-1 or level-2 evidence.

## Separate These Explicitly

| Type | Example |
|---|---|
| Observation | `The failing test throws in auth middleware` |
| Mechanism | `The middleware reads a null session token` |
| Assessment | `The token hydration path is broken` |

Collapse them too early and you start defending a story instead of testing a cause.

## Falsification Habit

For each live option, ask:
- what would prove this wrong?
- what is the cheapest way to test that?

Kill weak candidates quickly. Do not keep them alive out of politeness.

## When Evidence Is Thin

If you do not know enough, do the smallest move that improves certainty:
- read the exact file
- reproduce the failure
- inspect the command output
- compare behavior before and after the suspected boundary

Avoid large speculative rewrites when one probe could rule them out.
