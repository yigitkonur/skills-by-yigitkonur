# Evaluate (Step 4 — Score and Filter)

After generating ≥3 options (Step 3), pick the right evaluation tool based on the decision's **shape**. Use the Hard Choice Model as the classifier; it routes to Decision Matrix, Impact-Effort, Eisenhower, or "just pick."

## Start with the Hard Choice Model

Two dimensions: **impact** (how significant is the outcome?) × **comparability** (how easy to compare options?).

| Impact | Comparability | Quadrant | Approach |
|---|---|---|---|
| Low | Easy | **No-brainer** | Pick quickly. Optimizing wastes time. |
| Low | Hard | **Apples & Oranges** | Pick by current priorities; don't overthink. |
| High | Easy | **Big Choice** | **Decision Matrix** — factors + weights + scores. |
| High | Hard | **Hard Choice** | **Decision Matrix** + accept there is no "right" answer; run a cheap experiment if possible. |

**Heuristic**: the bigger the impact, the more carefully you proceed. Use the time and ceremony that the stakes deserve — no more, no less.

## Decision Matrix

**When**: Big Choice or Hard Choice quadrant. Multiple options, multiple factors, factors have different weights.

**Mechanics**:

1. List the options (rows) — from Step 3, usually 3-5.
2. List the factors (columns) — the things that matter. 3-6 factors.
3. Assign **weights** to each factor (1-5 or 1-10). Explicit — not gut weighting.
4. Score each option on each factor (same scale).
5. Multiply score × weight per cell. Sum rows.
6. Highest total wins. But also: check confidence per score (see below).

**Output**:

```
## Decision Matrix

Factors (weights):
  - Latency (weight 5)
  - Operational complexity (weight 4, inverted — lower is better)
  - Cost at current scale (weight 3)
  - Migration risk (weight 4, inverted)

| Option                    | Latency (5) | OpComplex (4) | Cost (3) | MigRisk (4) | Total |
|---------------------------|-------------|---------------|----------|-------------|-------|
| Keep Postgres, tune       | 3 × 5 = 15  | 5 × 4 = 20    | 5 × 3 = 15 | 5 × 4 = 20 | 70 ◄ |
| Add read-replica          | 4 × 5 = 20  | 3 × 4 = 12    | 4 × 3 = 12 | 4 × 4 = 16 | 60   |
| Switch to Redis/Dynamo    | 5 × 5 = 25  | 2 × 4 = 8     | 3 × 3 = 9  | 2 × 4 = 8  | 50   |

Confidence notes:
- Latency scores based on benchmark X (medium confidence — benchmark is 3 months old)
- MigRisk for Dynamo scored low; unfamiliar with team's DynamoDB experience
```

**What it reveals**: the option that wins when all factors are made explicit at their true weights. The act of writing weights often changes the pick — "I thought latency was top priority, but when I weighted it I realized migration risk matters more."

**Gotcha**: the first Decision Matrix pass is often wrong. Common fixes:

- **Wrong factors** — revisit; sometimes "team familiarity" or "reversibility" should be a factor
- **Wrong weights** — commonly the weights were gut-set rather than evidence-set; revisit
- **Missing factor** — a factor that doesn't differentiate the options is worth including only if it constrains scoring ("must not violate SOC2")

## Impact-Effort Matrix

**When**: prioritization across many items (not picking between 3 options for one decision). Common in sprint planning, backlog grooming, deciding which items in a long list to tackle.

**Axes**: impact (high/low) × effort (high/low). Four quadrants:

| Quadrant | Label | Action |
|---|---|---|
| High impact, Low effort | **Quick Wins** | Tackle first. Best ROI. |
| High impact, High effort | **Major Projects** | Plan and execute after Quick Wins. |
| Low impact, Low effort | **Fill-ins** | Do in spare time; optional. |
| Low impact, High effort | **Thankless Tasks** | Avoid. |

**Mechanics**:

1. List candidates.
2. Per candidate: estimate impact (concretely — what metric moves, by how much?) and effort (developer-days, or relative t-shirt size).
3. Plot on a 2×2.
4. Execute in order: Quick Wins → Major Projects → Fill-ins. Never Thankless.

**Output**:

```
## Impact-Effort Matrix

Quick Wins (do first):
  - Add retry on 503 → stops a recurring customer complaint (impact H, effort L)
  - Fix the N+1 in /users/:id → 60ms avg latency drop (impact H, effort L)

Major Projects (plan):
  - Session-store migration to Redis (impact H, effort H)

Fill-ins (if spare time):
  - Clean up stale feature flags (impact L, effort L)

Thankless (avoid):
  - Rewrite the logging module end-to-end (impact L, effort H)
```

**What it reveals**: where effort turns into return; what to drop.

**Interactions**: Pair with **Eisenhower** for scheduling — Impact-Effort tells you *what* to do; Eisenhower tells you *when*.

## Eisenhower Matrix

**When**: scheduling subsets of the already-prioritized list. Orthogonal to Impact-Effort (which is about what to do); Eisenhower is about when / by whom.

**Axes**: urgency × importance.

| Urgent | Important | Label | Action |
|---|---|---|---|
| Yes | Yes | Q1 | **Do it now.** Crises, deadlines. |
| No | Yes | Q2 | **Schedule it.** Strategic, deep-work. |
| Yes | No | Q3 | **Delegate it** (if possible). Admin, other-people's-fires. |
| No | No | Q4 | **Don't do it.** |

**Priority order**: Q1 > Q2 > Q3 > Q4. Q2 is the classic trap — important but not urgent, gets dropped in favor of Q3 urgent-but-not-important noise.

**Mechanics**: same 2×2 assessment per candidate. Then allocate calendar time (or assign owners).

**Output** usually terse — just quadrant per item.

## Second-Order Thinking during evaluation

Decision Matrix captures first-order impact per factor. Second-order effects don't fit neatly into factor weights — they're better surfaced separately during Step 5 (stress-test). BUT: if a factor exists ("long-term maintenance cost"), weight it meaningfully — at least 25% of the total weight. Otherwise, long-term gets drowned out by short-term factors.

Rule of thumb: if you're picking between options with similar short-term scores, the second-order effects (Step 5) will be the tiebreaker.

## Confidence flagging

Every score in a Decision Matrix carries a confidence level. Classify each score as:

- **High confidence** — backed by data, measurement, or direct experience
- **Medium confidence** — informed judgment; plausible but could be wrong
- **Low confidence** — guess; worth doing research or a small experiment to raise it

If the winning option's total depends on low-confidence scores, that's a signal to:

1. Spend 30-60 minutes raising the confidence (quick benchmark, lookup, ask someone)
2. Run a cheap experiment (Hard Choice quadrant exit-ramp)
3. OR: acknowledge the uncertainty in the Step 6 output contract and pick the option most robust to being wrong on those factors

## Fork 4 output

After evaluation, surface:

```
## Evaluation

Decision shape (Hard Choice Model): <No-brainer / Apples & Oranges / Big Choice / Hard Choice>
Tool used: <Decision Matrix / Impact-Effort / Eisenhower / just-pick>

<The matrix inline>

Winner: <option X, total score>
Runner-up: <option Y, total score>
Gap: <meaningful / marginal / rounding-error>

Low-confidence scores worth raising:
- <score with low confidence + what would raise it>

Are the factors + weights right? Anything I'm undervaluing or overvaluing?
```

Wait for approval or redirect. Common redirects:

- User adjusts a weight → recompute; re-rank; winner may change
- User adds a factor → recompute
- User challenges a score → re-evaluate that score with the user's evidence
- User says "gap is marginal, let's run an experiment" → exit to Hard Choice experiment path (cheap test; define success criteria)

## Common mistakes

| Mistake | Fix |
|---|---|
| Running Decision Matrix when Hard Choice is "No-brainer" | Just pick; save the ceremony for High-impact decisions |
| Decision Matrix with weights all equal to 1 | Weights are the whole point; differentiate them |
| Factors that don't differentiate options (all get same score) | Drop those factors; they're noise |
| Scoring as gut feel without confidence flagging | Every score gets a confidence level; low-confidence scores are the ones to improve |
| Skipping Impact-Effort in favor of Decision Matrix for a backlog | Different tools: Decision Matrix = one decision among options; Impact-Effort = prioritizing many items |
| Treating Eisenhower's Q3 (delegate) as "skip" | Delegation is a real outcome — name the delegatee, define the handoff |
| Ignoring the gap size between winner and runner-up | Marginal gap = the Decision Matrix didn't really discriminate; widen the factors or run an experiment |
| Low-confidence winning score with no plan to raise confidence | Either raise it, run an experiment, or flag in Step 6 output and pick the robust option |
