# Stress-Test (Step 5 — Blind Spots and Second-Order)

Step 5 is not optional. Every session runs all three tools: Inversion, Ladder of Inference, Second-Order Thinking. Skipping it converts the brainstorm from "rigorous exploration" to "prettier rationalization of the first plausible option." The whole point of the skill is that Step 5 sometimes changes the pick.

## Always run all three

Each tool catches a different failure mode:

| Tool | Catches |
|---|---|
| **Inversion** (pre-mortem) | Failure paths the Yellow/Green hat optimism hid |
| **Ladder of Inference** | Jumped reasoning, skipped evidence, treated interpretation as fact |
| **Second-Order Thinking** | Long-term consequences hidden by short-term optimization |

## Inversion — Pre-mortem

**Core idea**: imagine the chosen option failed badly in 6-12 months. Work backward to find why.

**Mechanics**:

1. Assume the winning option shipped. Assume it's 6-12 months later.
2. Premise: "The project failed. What went wrong?"
3. Generate 5-10 plausible failure modes. Don't self-censor — weird ones count.
4. For each failure mode: rate likelihood (H/M/L) and severity (H/M/L).
5. For High likelihood × High severity: surface a **mitigation** baked into the plan.
6. For the rest: name as watch-items, not mitigations. (Spending on every risk is over-insurance.)

**Diagnostic prompts**:

- "How could this go wrong?"
- "What would the opposite approach look like?"
- "What characterizes a poor solution in this space?"
- "What assumptions is this option betting on? Which of those are false?"

**Output**:

```
## Inversion (Pre-mortem)

Imagine: 9 months from now, <winning option> has failed. What went wrong?

Failure modes (likelihood × severity):
1. Team lost the one engineer who understood the new stack          (M × H) — mitigate: onboard 2 engineers during Phase 1
2. Latency regression under 10x load not caught pre-prod            (M × H) — mitigate: load test in staging, not prod
3. Vendor lock-in on the managed service became painful at scale    (L × M) — watch-item, not mitigate
4. Migration ran longer than estimated; support tickets piled up    (H × M) — mitigate: phased rollout with rollback gates
5. Second-order: caused a downstream service to miss its SLO        (L × H) — surface to the downstream team
```

**What it reveals**: failure paths the Yellow hat's optimism skipped. Classic save: finds a "how could we have missed this?" that's cheap to prevent now, expensive to fix later.

**Interactions**: Black Hat in Six Thinking Hats is mid-brainstorm; Inversion is post-decision. Both downside-focused but Inversion has teeth because the option is already chosen.

## Ladder of Inference — Reasoning Audit

**Core idea**: trace how you got from raw data to this recommendation. Every rung is a chance to have jumped incorrectly. Climb down (to the evidence), then climb back up (deliberately).

**The seven rungs** (bottom-up):

1. **Available data** — all data that could have been relevant
2. **Selected data** — what you actually looked at
3. **Interpretations** — what you made the selected data mean
4. **Assumptions** — what you took as given to reach those interpretations
5. **Conclusions** — what the assumptions + interpretations led to
6. **Beliefs** — the ongoing principles that conclusions reinforce
7. **Actions** — the recommendation you're about to make

**Diagnostic questions per rung** (climb down):

- Actions: *Why is this the right action? What alternatives did I not take seriously?*
- Beliefs: *What beliefs am I carrying into this? How did I form them?*
- Conclusions: *Why did I conclude this? What evidence is the conclusion based on?*
- Assumptions: *Am I assuming things that aren't true? What alternative assumptions would change the conclusion?*
- Interpretations: *Am I looking at the data objectively? What other meanings could it have?*
- Selected data: *What data did I ignore? What other sources haven't I considered?*
- Available data: *What data is out there that I haven't looked at?*

**Mechanics**:

1. State the recommendation (top of ladder).
2. Climb down — at each rung, answer the diagnostic. Write each rung's content.
3. Flag any rung where you can't defend the move up. That's the jumped rung.
4. Climb back up, revising the jumped-rung content.
5. If the revised climb produces a different recommendation, re-run Step 4 (evaluation) with the new reasoning.

**Output**:

```
## Ladder of Inference — audit

Recommendation: <winning option from Step 4>
    ↑
Beliefs: <the ongoing principles this reinforces>
    ↑
Conclusions: <what the data + assumptions led to>
    ↑ [CHECK] Are the assumptions defensible? If not, climb down further
Assumptions: <what was taken as given>
    ↑
Interpretations: <what the selected data was made to mean>
    ↑ [CHECK] Is this the most plausible interpretation?
Selected data: <what you looked at>
    ↑ [CHECK] What was excluded? Why?
Available data: <what exists that could be relevant>

Jumped rungs found: <list, or "none">
Revised recommendation (if changed): <option>
```

**What it reveals**: the rung you jumped. Common failures: selected data that only supports the winning option; an interpretation that's one of three plausible but the others weren't considered; an assumption you haven't checked in 6 months that's no longer true.

**Interactions**: Ladder of Inference operates on *reasoning*; Inversion operates on *outcomes*. Run Inversion for "what could go wrong in the future?" and Ladder of Inference for "was my thinking sound to get here?"

## Second-Order Thinking

**Core idea**: first-order effects are the immediate consequences. Second-order effects are what happens *after* the first-order effect settles. Most decisions optimize for first-order and get surprised by second-order.

**Two methods** (use both):

### Method 1: Consequence chain

1. Name the immediate (first-order) effect of the decision.
2. Ask: **"And then what?"** — generate the second-order consequence.
3. Ask "and then what?" again — third-order.
4. Repeat until consequences become too speculative to reason about.

### Method 2: Timeline analysis

Evaluate consequences at:

- **10 minutes from now** — immediate operational effect
- **10 months from now** — downstream impact at typical-quarter scale
- **10 years from now** — generational or strategic consequence

**Mechanics**:

1. State the recommendation.
2. Run both methods.
3. Surface consequences that are surprising, that change the pick, or that require mitigation.

**Output**:

```
## Second-Order Thinking

Recommendation: <option>

Consequence chain:
  Immediate: <first-order impact>
  → Next: <what that causes>
    → Next: <and what that causes>
      → Next: <diminishing clarity — stop here>

Timeline analysis:
  10 minutes: <operational effect — code shipped, dashboard updated, etc.>
  10 months: <team / process / user / dependency impact at the quarter level>
  10 years: <strategic consequence — market position, culture, architecture drift>

Surprising effects (change the pick or require mitigation):
- <effect that wasn't obvious>
- <effect that compounds over time>

Effects to accept:
- <downsides that are worth the trade>
```

**What it reveals**: long-term consequences that first-order optimization hides. Classic save: "the quick win at 10 minutes creates a maintenance burden at 10 months that outweighs it."

**Interactions**: Complements Inversion — Inversion asks "what if it fails?"; Second-Order asks "what if it succeeds but then?" Both are required for high-reversibility-cost decisions.

## Combining the three

For each of the three, produce a short artifact. Then synthesize:

```
## Stress-test synthesis

Inversion mitigations (now part of the plan):
- <mitigation 1>
- <mitigation 2>

Ladder of Inference — jumped rungs found:
- <rung + revised thinking>

Second-Order effects changing the pick:
- <effect>

Changes to the recommendation (if any): <what moved + why>
```

If the stress-test produces NO changes, that's a legitimate outcome — the Step 4 pick was robust. But if every stress-test produces no changes every time, suspicion: the stress-test is running shallow. Re-run Inversion with a harder "what if" premise.

## Fork 5 output

After stress-test, surface:

```
## Stress-test results

<Inversion pre-mortem inline>
<Ladder of Inference audit inline>
<Second-Order analysis inline>

Synthesis:
- Mitigations folded into the plan: <list>
- Jumped-rung revisions: <list or "none">
- Second-order concerns: <list>

Updated recommendation (if changed): <option or "no change">

Any of these change the pick? Should we revisit Step 3 (more options) or Step 4 (re-evaluate)?
```

Wait for approval or redirect. Common redirects:

- User sees a new failure mode → add to Inversion + mitigate
- User says a jumped rung is bigger than flagged → revisit Step 4 with revised reasoning
- User says second-order is a non-issue → acknowledge, note the dissent, move on
- User wants to add an option in light of stress-test → loop back to Step 3

## Common mistakes

| Mistake | Fix |
|---|---|
| Skipping Inversion because "we already did Black hat" | Black hat was during generation; Inversion has the chosen option — teeth are different |
| Ladder of Inference that doesn't find any jumped rungs | Push harder — ask "what data did I not look at?" Shallow audits miss real rungs |
| Second-Order that's just "it'll be fine" | Both methods: consequence chain AND timeline. If both are silent, the decision probably doesn't warrant this skill |
| Running stress-tests on every option instead of the winner | Only the winner gets full stress-test; other options get Inversion-lite if they're close runners-up |
| Treating "no change" as "stress-test validated the pick" | Often true, but check the stress-test wasn't shallow — would a harder scenario have moved the needle? |
| Folding every Inversion failure mode into the plan | Only H × H failures get mitigations; everything else is a watch-item, not a plan item |
