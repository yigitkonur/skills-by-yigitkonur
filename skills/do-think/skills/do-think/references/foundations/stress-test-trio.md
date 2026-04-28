# Stress-Test Trio

Phase C2 **for Op = SenseMaking**. Mandatory at Tier Medium and High. Three tools always run together; each catches a different failure mode.

For other operations, the stress-test focus is different — see `operation-classification.md`'s "How each operation reshapes the loop" table and the corresponding workflow file (e.g., `workflows/structured-extraction.md` for Extraction, `workflows/generative-composition.md` for Composition, `workflows/grounded-qa.md` for Q&A, `workflows/iterative-self-verification.md` for SelfVerify). **Do not** copy the trio onto operations it doesn't fit.

| Tool | Catches |
|---|---|
| **Inversion** (pre-mortem) | Failure paths that optimism hid |
| **Ladder of Inference** | Jumped reasoning, skipped evidence, treated interpretation as fact |
| **Second-Order Thinking** | Long-term consequences hidden by short-term optimization |

Skipping the trio converts deep thinking into "prettier rationalization of the first plausible option." The whole point is that the trio sometimes changes the pick.

## Phase C2 exit criterion

Two requirements, both must hold:

1. **C1 input present**: three named candidate options surfaced from C1 (the prerequisite — without options, there is nothing to stress-test).
2. **Three trio outputs written for the leading option**:
   - one Inversion failure mode (with likelihood × severity)
   - one Ladder of Inference data-to-assumption walk (with at least one jumped rung named or "none found")
   - one Second-Order chain (consequence-chain or 10-min/10-mo/10-yr timeline)

The "three options" and the "three trio tools" are **independent counts** — three options come from C1; the trio runs once on the leader (each of its three tools producing one output). Outputs are written, not implied. If you cannot write all three trio outputs on the leading option, you have not stress-tested.

## Inversion — pre-mortem

**Core**: imagine the chosen option failed badly in 6-12 months. Work backward to find why.

### Procedure

1. Assume the winning option shipped. Assume it's 6-12 months later.
2. Premise: "*The project failed. What went wrong?*"
3. Generate 5-10 plausible failure modes. Don't self-censor — weird ones count.
4. Per failure mode: rate likelihood (H/M/L) × severity (H/M/L).
5. For H × H: bake a **mitigation** into the plan.
6. For the rest: name as **watch-items**, not mitigations. (Spending on every risk is over-insurance.)

### Diagnostic prompts

- "How could this go wrong?"
- "What would the opposite approach look like?"
- "What characterizes a poor solution in this space?"
- "What assumptions is this option betting on? Which of those could be false?"

### Why temporal inversion works

Listing abstract risks generates polite half-thinking. Imagining "it's 6 months later and it failed" generates concrete failure modes — the kind a postmortem would actually surface.

### Worked output

```
## Inversion (pre-mortem)

Imagine: 9 months from now, <winning option> has failed. What went wrong?

Failure modes (likelihood × severity):
1. Team lost the one engineer who understood the new stack          (M × H) — mitigate: onboard 2 engineers during Phase 1
2. Latency regression under 10x load not caught pre-prod            (M × H) — mitigate: load test in staging, not prod
3. Vendor lock-in on the managed service became painful at scale    (L × M) — watch-item, not mitigate
4. Migration ran longer than estimated; support tickets piled up    (H × M) — mitigate: phased rollout with rollback gates
5. Second-order: caused a downstream service to miss its SLO        (L × H) — surface to the downstream team
```

## Ladder of Inference — reasoning audit

Full procedure: see `evidence-and-falsification.md` (the seven rungs + the climb-down/climb-up pattern).

In the trio context: use Ladder of Inference to audit the **winning option** specifically. Common save: the selected data only supported the winner; alternative interpretations were not considered; an assumption hasn't been checked in 6 months and is no longer true.

If the audit produces a different recommendation, re-enter Phase C1 with the revised reasoning.

### Worked output

```
## Ladder of Inference — audit of <winning option>

Recommendation: <the C1 winner>
    ↑
Beliefs: <ongoing principles this reinforces>
    ↑
Conclusions: <what the data + assumptions led to>
    ↑ [CHECK] Are the assumptions defensible?
Assumptions: <what was taken as given>
    ↑
Interpretations: <what the selected data was made to mean>
    ↑ [CHECK] Most plausible interpretation?
Selected data: <what you looked at>
    ↑ [CHECK] What was excluded? Why?
Available data: <what exists that could be relevant>

Jumped rungs found: <list, or "none">
Revised recommendation (if changed): <option>
```

## Second-Order Thinking

**Core**: first-order effects are immediate. Second-order effects are what happens *after* the first-order effect settles. Most decisions optimize for first-order and get surprised by second-order.

### Method 1: Consequence chain

1. Name the immediate (first-order) effect.
2. Ask: "**And then what?**" — generate the second-order consequence.
3. Repeat for third-order until clarity diminishes.

### Method 2: Timeline analysis

Evaluate consequences at:
- **10 minutes from now** — immediate operational effect
- **10 months from now** — quarter-level downstream impact
- **10 years from now** — strategic / generational consequence

Use both methods. They surface different failure modes.

### Worked output

```
## Second-Order Thinking

Recommendation: <option>

Consequence chain:
  Immediate: <first-order impact>
  → Next: <what that causes>
    → Next: <and what that causes>
      → diminishing clarity, stop here

Timeline:
  10 minutes: <operational effect>
  10 months: <quarter-level impact>
  10 years: <strategic consequence>

Surprising effects (change the pick or require mitigation):
- <effect that wasn't obvious>
- <effect that compounds>

Effects to accept:
- <downsides worth the trade>
```

## Combining the three — synthesis

After running all three, write:

```
## Stress-test synthesis

Inversion mitigations folded into plan:
- <mitigation 1>
- <mitigation 2>

Ladder of Inference jumped rungs:
- <rung + revised thinking, or "none found">

Second-Order effects changing the pick:
- <effect>

Changes to recommendation: <what moved + why, or "no change — pick is robust">
```

## When the trio produces "no change"

Legitimate outcome — the C1 pick was robust. But: if every stress-test produces "no change" every time, suspicion: the trio is running shallow. Re-run Inversion with a harder "what if" premise.

## Escalation gate

If all three options die in the trio (every option has H × H failure modes, jumped rungs, or unacceptable second-order chains), **switch Mode to Interactive** — the user needs to be in the loop to expand the option space. Do not pick the least-bad option silently.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Skipping Inversion because "we already ran Black hat in Six Hats" | Six Hats Black is mid-generation; Inversion has the chosen option — teeth are different. Run both. |
| Ladder audit that finds no jumped rungs every time | Push harder. Shallow audits miss the real rungs. Ask "what data did I not look at?" |
| Second-Order that's just "it'll be fine" | Both methods: chain AND timeline. If both are silent, the decision probably doesn't warrant Tier Medium/High. |
| Folding every Inversion failure mode into the plan | Only H × H gets mitigations. Other items are watch-items, not plan items. Over-insurance is its own failure. |
| Treating "no change" as validation without checking trio depth | Often true; check the trio wasn't shallow. Would a harder scenario have moved the needle? |
