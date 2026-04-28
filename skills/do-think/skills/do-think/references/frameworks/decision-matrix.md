# Decision Matrix (and Impact-Effort, Eisenhower, Hard Choice classifier)

Library entry. Routed from the SKILL.md master table or `modes/interactive-brainstorm.md` Step 4.

Pick the right tool by the decision's *shape*. Use the Hard Choice Model as classifier; it routes to Decision Matrix, Impact-Effort, Eisenhower, or "just pick."

## Hard Choice Model — the classifier

Two axes: **impact** × **comparability**.

| Impact | Comparability | Quadrant | Approach |
|---|---|---|---|
| Low | Easy | **No-brainer** | Pick quickly. Optimizing wastes time. |
| Low | Hard | **Apples & Oranges** | Pick by current values; don't overthink. |
| High | Easy | **Big Choice** | **Decision Matrix** below. |
| High | Hard | **Hard Choice** | **Decision Matrix** + accept no "right" answer; run a cheap experiment if reversibility allows. |

(For Tier mapping see `foundations/effort-calibration.md`.)

## Decision Matrix

### When
Big Choice or Hard Choice quadrant. Multiple options, multiple factors, factors have different weights.

### Mechanics

1. List options (rows). Usually 3-5 from Phase C1.
2. List factors (columns). 3-6 things that matter.
3. Assign **weights** to each factor (1-5 or 1-10). Explicit — not gut weighting.
4. Score each option on each factor (same scale).
5. Multiply score × weight per cell. Sum rows.
6. Highest total wins. Check confidence per score.

### Output

```
Factors (weights):
  - Latency (5)
  - Operational complexity (4, inverted — lower is better)
  - Cost at current scale (3)
  - Migration risk (4, inverted)

| Option                    | Latency (5) | OpComplex (4) | Cost (3) | MigRisk (4) | Total |
|---------------------------|-------------|---------------|----------|-------------|-------|
| Keep Postgres, tune       | 3 × 5 = 15  | 5 × 4 = 20    | 5 × 3 = 15 | 5 × 4 = 20 | 70 ◄ |
| Add read-replica          | 4 × 5 = 20  | 3 × 4 = 12    | 4 × 3 = 12 | 4 × 4 = 16 | 60   |
| Switch to Redis           | 5 × 5 = 25  | 2 × 4 = 8     | 3 × 3 = 9  | 2 × 4 = 8  | 50   |

Confidence:
- Latency scores: medium (benchmark is 3 weeks old)
- MigRisk for Redis: low (team has no production Redis experience)
```

### Gotchas

- **Wrong factors** — sometimes "team familiarity" or "reversibility" should be a factor and isn't.
- **Wrong weights** — gut-set weights produce gut-shaped winners. Set weights *before* scoring.
- **Factors that don't differentiate** — drop them; they're noise.

## Impact-Effort Matrix

### When
Prioritization across many items (not picking one option among 3-5). Sprint planning, backlog grooming.

### Quadrants

| Quadrant | Action |
|---|---|
| High impact, Low effort → **Quick Wins** | Tackle first |
| High impact, High effort → **Major Projects** | Plan + execute after Quick Wins |
| Low impact, Low effort → **Fill-ins** | Optional / spare time |
| Low impact, High effort → **Thankless Tasks** | Avoid |

### Mechanics

1. List candidates.
2. Per candidate: estimate impact (concretely — what metric moves, by how much?) + effort (developer-days).
3. Plot on a 2×2.
4. Execute order: Quick Wins → Major Projects → Fill-ins. Never Thankless.

## Eisenhower Matrix

### When
Scheduling subsets of an already-prioritized list. Orthogonal to Impact-Effort.

### Quadrants

| Urgent | Important | Label | Action |
|---|---|---|---|
| Y | Y | Q1 | Do now (crises, deadlines) |
| N | Y | Q2 | Schedule (strategic, deep work) |
| Y | N | Q3 | Delegate (admin, others' fires) |
| N | N | Q4 | Don't do |

Priority order: Q1 > Q2 > Q3 > Q4. Q2 is the classic trap — important-but-not-urgent gets dropped in favor of Q3 urgent-but-not-important noise.

## Confidence flagging

Every score in a Decision Matrix carries a confidence level:

- **High** — backed by data, measurement, or direct experience
- **Medium** — informed judgment; plausible but could be wrong
- **Low** — guess; worth research or a small experiment

If the winning option's total depends on low-confidence scores:
1. Spend 30-60 minutes raising confidence (quick benchmark, lookup, ask)
2. Run a cheap experiment (Hard Choice exit-ramp)
3. OR: acknowledge in the output and pick the option most robust to those scores being wrong

## Second-Order during evaluation

Decision Matrix captures first-order impact. Second-order effects don't fit factor weights neatly — surface them in `foundations/stress-test-trio.md` Phase C2. BUT: if a "long-term maintenance cost" factor exists, weight it ≥25% of the total; otherwise it gets drowned out.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Running Decision Matrix when Hard Choice is "No-brainer" | Just pick. Save ceremony for High-impact decisions. |
| Decision Matrix with weights all = 1 | Weights are the whole point. Differentiate them. |
| Factors that don't differentiate options (all get same score) | Drop those factors. |
| Scoring as gut feel without confidence flagging | Every score gets a confidence level. |
| Treating Eisenhower's Q3 (delegate) as "skip" | Delegation is a real outcome — name the delegatee. |
| Ignoring the gap between winner and runner-up | Marginal gap = Decision Matrix didn't really discriminate. Widen factors or run an experiment. |
