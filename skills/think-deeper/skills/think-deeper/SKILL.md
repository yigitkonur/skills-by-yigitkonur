---
name: think-deeper
description: "Use skill if you are handling ambiguous, high-stakes, or hard-to-reverse work and need a generic deep-thinking framework for debugging, refactoring, planning, or choosing an approach."
---

# Think Deeper

Use this skill when the task is important enough that acting on the first plausible answer is risky.

This is a tool-agnostic reasoning framework. It is not a request to narrate more thoughts. It is a way to gather better evidence, slow down premature commitment, and hand off a clearer next move before acting.

## Trigger Boundary

Use this skill when:

- the problem is underspecified
- the root cause is unknown
- multiple approaches are viable and the tradeoffs matter
- a refactor could change behavior, boundaries, or workflow
- the codebase or domain is unfamiliar
- the change is expensive to reverse
- the task is likely to derail if you stop after the first obstacle

Do not use this skill when:

- the task is trivial, mechanical, or fully specified
- the user gave exact steps and the main risk is execution, not reasoning
- you are only summarizing, translating, or relaying already-known facts

## Non-Negotiable Rules

1. Ground before hypothesis.
2. Match effort to complexity.
3. Keep 2-3 live options or causes for medium and high complexity until evidence kills them.
4. Separate observations, mechanisms, and judgments.
5. Use numbered, stepwise progress instead of mental jumps.
6. Prefer the smallest next move that changes your certainty.
7. Do not stop early just because the first path got harder than expected.
8. End thinking with a concrete execution or verification move.
9. Keep detailed inner reasoning private unless the user explicitly asks for it.

## Core Loop

Always start with the generic loop in [references/foundations/core-loop.md](references/foundations/core-loop.md).

The loop is:
1. frame the real question
2. gather the minimum grounding set
3. classify the task shape
4. keep live options long enough to compare them
5. apply filters before committing
6. choose the next move
7. verify or revise

Support the loop with:
- [references/foundations/evidence-and-falsification.md](references/foundations/evidence-and-falsification.md) for evidence quality
- [references/foundations/stepwise-reasoning.md](references/foundations/stepwise-reasoning.md) for sequential thought discipline
- [references/foundations/ultrathinking.md](references/foundations/ultrathinking.md) for high-stakes reasoning

## Fast Routing

Read the smallest set that fits the situation:

| Situation | Read this set |
|---|---|
| generic hard decision | [references/foundations/core-loop.md](references/foundations/core-loop.md), [references/foundations/evidence-and-falsification.md](references/foundations/evidence-and-falsification.md), [references/foundations/stepwise-reasoning.md](references/foundations/stepwise-reasoning.md) |
| especially high-stakes or hard-to-reverse work | [references/foundations/core-loop.md](references/foundations/core-loop.md), [references/foundations/ultrathinking.md](references/foundations/ultrathinking.md), [references/workflows/task-planning.md](references/workflows/task-planning.md) |
| bug or regression | [references/workflows/bug-tracing.md](references/workflows/bug-tracing.md), [references/foundations/evidence-and-falsification.md](references/foundations/evidence-and-falsification.md), [references/foundations/stepwise-reasoning.md](references/foundations/stepwise-reasoning.md) |
| refactor or redesign | [references/workflows/refactor-thinking.md](references/workflows/refactor-thinking.md), [references/workflows/task-planning.md](references/workflows/task-planning.md), [references/foundations/ultrathinking.md](references/foundations/ultrathinking.md) |
| planning a complex task | [references/workflows/task-planning.md](references/workflows/task-planning.md), [references/foundations/core-loop.md](references/foundations/core-loop.md), [references/foundations/stepwise-reasoning.md](references/foundations/stepwise-reasoning.md) |
| staying autonomous through blockers | [references/workflows/continuous-execution.md](references/workflows/continuous-execution.md), [references/foundations/core-loop.md](references/foundations/core-loop.md), [references/foundations/evidence-and-falsification.md](references/foundations/evidence-and-falsification.md) |

## Complexity Tiers

| Tier | Use when | Reasoning expectation |
|---|---|---|
| Low | The path is mostly clear and the main risk is forgetting one important constraint | Brief framing, one quick evidence pass, then act |
| Medium | Several plausible paths exist or the blast radius is meaningful | Keep multiple options alive, compare tradeoffs, then choose |
| High | Root cause is unclear, reversibility is poor, or the change could alter architecture or workflow | Gather stronger evidence, test assumptions, run a stricter handoff before acting |

Do not inflate the tier just because the prompt is vague. Raise it only when the cost of being wrong is genuinely high.

## Case Guidance

### Bug Cases

Use [references/workflows/bug-tracing.md](references/workflows/bug-tracing.md).

Focus on:
- reproducing the symptom
- tracing the failing path layer by layer
- separating symptom from cause
- falsifying weak theories early
- fixing the smallest causal point
- adding a regression guard

### Refactor Cases

Use [references/workflows/refactor-thinking.md](references/workflows/refactor-thinking.md).

Focus on:
- naming the invariants that must survive
- finding seams before moving code
- changing one axis at a time
- preserving behavior while improving structure
- keeping rollback paths visible

### Planning Cases

Use [references/workflows/task-planning.md](references/workflows/task-planning.md).

Focus on:
- desired outcome
- constraints and unknowns
- ordered work slices
- one active step at a time
- updating the plan when evidence changes it

### Continuous Execution Cases

Use [references/workflows/continuous-execution.md](references/workflows/continuous-execution.md).

Focus on:
- not stopping at the first solvable blocker
- exhausting high-signal local moves before escalating
- resolving uncertainty with evidence instead of asking too early
- pausing only for real external blockers or approval boundaries

## Output Contract

Before acting, be able to state:

- the actual problem
- the evidence already checked
- the live options or candidate causes
- the chosen path and why it wins
- the verification step

When writing to the user, compress the reasoning into decisions, evidence, tradeoffs, and next actions. Do not dump raw thought logs.

## Anti-Patterns

Avoid these:

- acting on the first plausible explanation
- overplanning when a quick probe would answer the question
- continuing to think after the next move is already obvious
- confusing observations with interpretations
- letting one attractive option kill comparison too early
- stopping after the first obstacle when better local moves still exist
- claiming success before stating the verification result

## Final Test

Before you act, ask:

`Do I know enough to make the next move safer and clearer than acting immediately would be?`

If yes, act. If no, gather the smallest missing evidence first.
