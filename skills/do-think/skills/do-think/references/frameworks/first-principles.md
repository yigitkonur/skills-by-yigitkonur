# First Principles

Library entry. Routed from the SKILL.md master table, `foundations/ultrathinking.md`, or `modes/interactive-brainstorm.md` Step 3.

## Essence

Break the problem down to its most basic truths — the things that *cannot* be decomposed further (physics, math, hard constraints) — then rebuild the solution from those foundations only. Strips inherited assumptions disguised as constraints.

## When to use

- Analogies from past work are failing
- The agent suspects it's carrying assumptions it hasn't examined
- Novel problem; no clear precedent
- Refactor or architecture work where the "current way" is being defended without reasoning
- Interactive Step 3 when the option set is constrained by inherited belief

## Procedure

1. **State the problem.** Plain language.
2. **Strip the analogies.** What beliefs are you carrying because that's how it's "always done"? Surface them.
3. **Recursively ask "Why?" or "What's beneath this?"** until you hit a truth that can't be broken down further — a *first principle* (physics, math, hard data, regulatory hard limit).
4. **Separate explicitly:**
   - What you *actually know* is true (first principles + hard data)
   - What you *assume* is true (convention, analogy, inherited belief)
5. **Rebuild the solution from the first principles only.** What does the evidence + hard constraints *force*?

## Socratic questions to push down the ladder

| Type | Prompt |
|---|---|
| Clarification | "What do I mean by X?" |
| Probing assumptions | "What could I assume instead?" |
| Probing reasons | "Why do I think this is true?" |
| Implications | "What effect would that have?" |
| Alternative viewpoints | "Is there another way to see this?" |
| Questioning the question | "What was the point of asking this?" |

## Output

```
## First Principles breakdown

Problem: <stated problem>

Layer 1 (why): <immediate cause/reason>
Layer 2 (why): <upstream cause>
Layer 3 (why): <foundational constraint>
Layer 4 (why): <physical/mathematical/hard truth>  ← first principle

Assumptions we carried (NOT first principles):
- <assumption 1> — actually a convention from <source>
- <assumption 2> — actually an inherited belief

Rebuild:
Given only the first principles + hard constraints, the solution space is:
<list of options, including ones the assumptions would have ruled out>
```

## What it reveals

Assumptions masquerading as constraints. Classic outcome: an option the team "couldn't do" was ruled out only by convention, not by physics.

## Interactions

- Use on a *priority branch* from decomposition (`decomposition-tools.md`), not the whole problem (too broad).
- Pairs with `foundations/evidence-and-falsification.md`'s Ladder of Inference — both audit the reasoning chain; first-principles generates new options, Ladder of Inference stress-tests existing reasoning.
- Feeds `zwicky-box.md` — first-principles defines the dimension space, Zwicky Box explores it.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Asking "why?" until you hit a vague answer and calling it a first principle | First principles are physics/math/hard data, not philosophy. If you're 4 layers in and still at assumptions, you haven't reached first principles. |
| Rebuilding while still carrying the original assumptions | The whole point is to discard them. If your "rebuilt" solution looks like the starting point, the assumption strip didn't happen. |
| Running first-principles on every problem | High cost; reserve for problems where analogies have actually failed. For Complicated-domain problems with known patterns, `decomposition-tools.md` is lighter. |
