# Productive Thinking Model — DRIVE Criteria

Library entry. Routed from the SKILL.md master table or `modes/interactive-brainstorm.md` Step 6 (when defining success criteria explicitly).

The full Productive Thinking Model (Tim Hurson) wraps a 6-step problem-to-execution arc around the core loop. Most of its value for `do-think` is the **DRIVE** sub-framework for defining "what success looks like." Use the rest of the 6-step model only when the deliverable is a full execution plan, not just a recommendation.

## When to use

- The brainstorm's end-state is a *plan with execution detail*, not just a decision
- Stakes are high or stakeholders multiple — generic "what does success look like?" is too thin
- You're handing off the next step to a different team / agent / skill and they need explicit success criteria
- Interactive Step 6 when the user wants the recommendation packaged with a resource plan

## DRIVE — defining success

For the chosen path, write each letter explicitly:

| Letter | Meaning | Example |
|---|---|---|
| **D** | What the solution must **D**o | "Reduce p95 latency on /users/:id from 380ms to ≤200ms" |
| **R** | **R**estrictions — what it must avoid | "No new infrastructure dependencies; no schema migration" |
| **I** | **I**nvestable resources | "1 engineer × 5 days; staging environment access; existing benchmark suite" |
| **V** | **V**alues that must be upheld | "No SLO regressions on auth flow; no degradation of error budget" |
| **E** | **E**ssential outcomes | "Pass load test at 10x current traffic for 30 min with error rate ≤0.1%" |

DRIVE is much sharper than "what does success look like?" because it forces the agent to write each axis explicitly. Missing any letter usually means the success criterion is incomplete in that dimension.

## Full 6-step model (for context)

When the user asks for "the full plan, not just the decision," wrap the core loop with these:

1. **What's going on?** — clarify problem, stakeholders, current state, target state. (Maps to Phase A1/A2.)
2. **What's success?** — DRIVE. (Augments Phase B1.)
3. **What's the question?** — formulate "How might we…?" framings to shape the option space.
4. **Generate answers.** — option generation. (Maps to Phase C1.)
5. **Forge the solution.** — score against DRIVE. (Maps to Phase C2 + D1.)
6. **Align resources.** — document required actions, owners, verification. (Augments Phase D2.)

The Phase A → D loop in `foundations/core-loop.md` is the engine; Productive Thinking adds the wrapper for execution-plan deliverables.

## How might we…? (HMW) framings

When generating options (Phase C1), prefix with "How might we…?" to widen the solution space:

- ❌ "Should we cache the user route?" → narrow, yes/no
- ✅ "How might we keep the user route fast under 10x load?" → opens cache, replica, pagination, lazy-hydration, etc.

HMW prompts feed directly into `frameworks/six-thinking-hats.md` Green hat or `frameworks/zwicky-box.md` dimension generation.

## Output

```
## DRIVE for <chosen path>

D: <what it must do, measurable>
R: <restrictions>
I: <investable resources>
V: <values to uphold>
E: <essential outcomes — measurable>

## Resource plan
- <action> — owner: <name> — verification: <check>
- <action> — owner: <name> — verification: <check>
```

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| DRIVE with all letters at "TBD" | TBD = not done. Fill each letter or admit the success criteria are not ready. |
| Skipping DRIVE because "success is obvious" | Run it anyway. Surfaces resource and value constraints that get missed. |
| Using HMW framings on Clear-domain problems | Overkill. HMW widens the option space — Clear domain doesn't need widening. |
| Treating DRIVE as a decoration ("D: build the thing") | Each letter is *measurable* and *checkable*. Vague D = no D. |
