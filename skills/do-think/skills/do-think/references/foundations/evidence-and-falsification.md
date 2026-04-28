# Evidence and Falsification

Reasoning quality depends more on evidence quality than on verbal sophistication. This file covers the evidence ladder, the type-separation discipline, the falsification habit, and the **Ladder of Inference rebuild** — the move that catches "confidently rationalizing a path forward."

Used in Phase B2 (grounding) and Phase C2 (stress-test).

## Evidence Ladder

Prefer stronger evidence over weaker:

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

For each live option in Phase C1, ask:
- what would prove this wrong?
- what is the cheapest way to test that?

Kill weak candidates quickly. Do not keep them alive out of politeness.

## Ladder of Inference — the rebuild move

Used in Phase C2 (stress-test trio) and any time you suspect a confidently-stated conclusion was reached without enough rungs.

The seven rungs (bottom-up):

1. **Available data** — all data that could have been relevant
2. **Selected data** — what you actually looked at
3. **Interpretations** — what you made the selected data mean
4. **Assumptions** — what you took as given to reach those interpretations
5. **Conclusions** — what the assumptions + interpretations led to
6. **Beliefs** — the ongoing principles those conclusions reinforce
7. **Actions** — the recommendation you're about to make

### Climb down — diagnostic per rung

- Action: *What alternative actions did I not seriously consider?*
- Belief: *What ongoing principles is this reinforcing? How did I form them?*
- Conclusion: *Why did I conclude this? What evidence was the conclusion based on?*
- Assumption: *Am I assuming things that aren't true? What alternative assumptions would change the conclusion?*
- Interpretation: *Is this the most plausible interpretation? What others could the data carry?*
- Selected data: *What data did I ignore? What other sources haven't I considered?*
- Available data: *What data is out there that I haven't looked at?*

Flag any rung where you cannot defend the move up. That's the *jumped rung*.

### Climb back up

Re-ascend deliberately, stating what data you now select, how you interpret it, what you assume — and only then what action follows. If the revised climb produces a different recommendation, re-enter Phase C1 with the revised reasoning.

### When to use it

- A conclusion feels confident but you cannot say *why* you reached it (you leaped a rung)
- Phase C1 produced one option that everyone seems to favor — descend the ladder; check the data selection
- Phase C2 stress-test as the standard rebuild move (one of the trio)
- You catch yourself rationalizing — descend, find the rung, rebuild

## When Evidence Is Thin

If you do not know enough, do the smallest move that improves certainty:
- read the exact file
- reproduce the failure
- inspect the command output
- compare behavior before and after the suspected boundary

Avoid large speculative rewrites when one probe could rule them out.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Citing a level-6 intuition while ignoring level-2 test output | The hunch is data; the test output is evidence. Trust the evidence. |
| Stating conclusions without naming the mechanism | If you cannot say *why* X causes Y, you have an assessment, not a mechanism. |
| Keeping a falsified candidate alive because you generated it | Kill it. Politeness toward your own hypotheses is how confirmation bias survives. |
| Climbing the Ladder once and finding "no jumped rungs" every time | Push harder. Ask "what data did I not look at?" Shallow audits miss real rungs. |
