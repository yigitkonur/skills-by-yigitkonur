# Reframing — Abstraction Laddering

Phase A2. Run when the problem statement feels wrong, too narrow, solution-shaped, or when Phase A1 returned **Disorder**.

LLMs default to accepting the user's framing as the problem to solve. Most "wrong" answers are correct answers to the wrong problem. Abstraction Laddering catches that.

The lever is **moving up and down the abstraction ladder** — *why* climbs up to the bigger problem; *how* climbs down to concrete actions.

## The ladder

```
Up rung (why):       a more abstract problem statement
   ↑
Original:            the user's stated problem
   ↓
Down rung (how):     a more concrete statement or solution
```

## Procedure

1. **Write the user's problem statement at the middle rung.** Verbatim. Do not paraphrase yet.

2. **Climb UP one rung.** Ask: "*Why* does this matter? What bigger problem does this serve?" The answer is a more abstract statement.

3. **Climb DOWN one rung.** Ask: "*How* could we satisfy this?" The answer is a more concrete statement or candidate solution.

4. **Compare the three rungs.** Pick the rung that is the *actual* problem worth solving:
   - If the up rung is a problem you would not bother solving directly, the original was correct.
   - If the up rung exposes a problem the original was a narrow approach to, the original was solution-shaped — climb up.
   - If the down rung is the only one that's actionable in the current context, climb down.

5. **Re-run Phase A1 (domain classification) on the chosen rung** — the classifier may now return a different domain than it did on the original framing. Re-emit the opening contract if it changed.

## Worked example

**Original** (user said): *Add a trust badge to the homepage.*

- Climb UP — *why?* → *Increase user trust in the product.* The user's actual problem.
- Climb DOWN — *how?* → *Embed an SSL-certificate-issuer logo in the hero.* One specific implementation of a trust badge.

The original is a solution statement, not a problem. Climbing up reveals other paths to "increase user trust" — social proof, case studies, SOC2 compliance. The skill should reframe to the up rung and reset Phase A.

## When to climb more than one rung

Usually 1 rung up + 1 rung down is enough. Climb a second rung up only when:
- The first up rung itself feels like a means to a larger end
- Multiple stakeholders disagree on which level is the actual problem

Climbing 4+ rungs is almost always over-laddering — the actual problem is well away from the stated one (legitimate, but rare).

## Solo mode application

In Solo mode, you ladder silently, pick the rung you'll operate at, and proceed. Note the chosen rung in your reasoning trace so the user can challenge it.

If laddering changes the framing meaningfully, the opening contract may need to change (especially the Cynefin domain). Re-emit the contract with the corrected domain.

## Interactive mode application

Interactive mode surfaces all three rungs to the user and asks which is the actual problem (Step 2 / Fork 2 in `modes/interactive-brainstorm.md`).

## Disorder escape hatch

If Phase A1 returned Disorder, this file is the escape. Ladder up and down from the user's stated framing; the rung you can credibly classify with Cynefin is the rung you operate at.

## When NOT to reframe

- The user's framing passes the why-up test (the up rung is something you would *not* bother solving directly — the original is the actual concern).
- The original is already concrete, scoped, and matches a clear domain.
- Repeated reframing has produced no change (signals over-laddering).

Reframing is a *check*, not a *step you always run*. Default in Phase A2: skip unless the signals above fire.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Climbing up forever, never landing | One rung up is usually enough. The up rung's value is *exposing alternatives*, not replacing the framing wholesale. |
| Climbing down into solutions and forgetting to evaluate | The down rung is one candidate, not the answer. Use it to test that the original was at the right level, not as the next move. |
| Skipping reframing when the user's prompt is solution-shaped ("Add X", "Build Y") | Solution-shaped prompts are exactly when reframing pays off. Try one why-up. |
| Reframing every problem | Reframing has cost. If the why-up test passes, save the cycles. |
