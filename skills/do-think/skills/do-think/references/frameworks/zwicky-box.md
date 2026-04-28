# Zwicky Box (Morphological Analysis)

Library entry. Routed from the SKILL.md master table, `workflows/refactor-thinking.md` (when option generation is dry), or `modes/interactive-brainstorm.md` Step 3.

## Essence

Define the design space as a matrix of independent dimensions × possible values. Generate combinations systematically. Forces non-obvious whole-system options that single-axis brainstorming misses.

## When to use

- Phase C1 produces only minor variations on the same idea (generator is dry)
- Refactor or architecture decisions with multiple independent axes
- "We've always done it this way" is the default and you want to break it
- Interactive Step 3 when novel combinations matter more than expert analysis

## Procedure

1. **Name 3-5 dimensions** — logically independent attributes of the solution. Example for a cache: storage tier, eviction policy, key strategy, invalidation trigger, consistency level.
2. **Per dimension, list 3-6 values.** Don't filter for feasibility yet — implausible values combine usefully.
3. **Build the matrix** (dimensions × values).
4. **Generate combinations**: pick one value per column. Aim for 3-5 systematic combinations + 2-3 deliberately strange combinations.
5. **Evaluate each combination as a whole solution.** Discard the ones that clearly don't work, keep the surprising ones.

## Worked example

Problem: design a re-engagement campaign for churned users.

| Target | Delivery | Timing | Incentive | Format |
|---|---|---|---|---|
| Free users | Email | Weekly | None | Text |
| Paid users | In-app banner | Monthly | Discount | Video |
| Enterprise | Push notification | On-event | Early access | Live workshop |
| Churned users | Sales call | One-shot | Credits | Mixed |

Combinations:
1. **Churned users + Email + On-event + Credits + Video** → personalized win-back triggered by usage signal, with credits to lower the re-engage friction.
2. **Enterprise + In-app banner + Weekly + Early access + Text** → power-user feature stream.
3. **Free users + Sales call + One-shot + Early access + Live workshop** → freemium-to-paid conversion via white-glove workshop. Strange but might convert at high rate.

## What it reveals

Whole-system options that didn't appear in linear brainstorming. The constraint of "pick one per column" forces you out of comfortable defaults.

## Interactions

- Downstream of `first-principles.md` — first-principles opens the dimension space; Zwicky Box explores it.
- Feeds `decision-matrix.md` for scoring the surviving combinations.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| 8+ dimensions | Combinatorial explosion. Cap at 5. Merge or drop dimensions that aren't actually independent. |
| Filtering values for feasibility before combining | Feasibility check is *after* combination. Filtering early loses the non-obvious good ones. |
| Generating only "systematic" combinations | Include 2-3 *strange* combinations. The surprises are where the value is. |
| Treating Zwicky Box output as final answer | It's option generation. Combinations still go through the calling workflow's op-specific evaluation and stress-test (Decision Matrix + the trio when `Op: SenseMaking`; per-op C2 from `operation-classification.md` otherwise). |
