# Effort Calibration — Hard Choice × Confidence-vs-Quality

Phase B1. Replaces single-axis Complexity Tiers with two independent calibrations:

- **Hard Choice Model** — sets effort by impact × option-comparability
- **Confidence-vs-Quality** — sets posture (speed-first / balanced / quality-first) by problem-confidence × solution-confidence

Tier (Low / Medium / High) is the output that governs Phase B2 grounding depth and Phase C2 trio strictness. The tier appears in the opening contract.

## Hard Choice Model

Two axes: **impact** (how significant is the outcome?) × **comparability** (how easy to compare options?).

| Impact | Comparability | Quadrant | Approach | Tier |
|---|---|---|---|---|
| Low | Easy | **No-brainer** | Pick now. Optimizing wastes time. | Low |
| Low | Hard | **Apples & Oranges** | Pick by current values; don't overthink. | Low |
| High | Easy | **Big Choice** | `frameworks/decision-matrix.md`; gather information, score options. | Medium |
| High | Hard | **Hard Choice** | Decision Matrix + accept that no "right" answer exists; run a cheap experiment if reversibility allows. | High |

**Heuristic**: time-spent-thinking should match the box, not how urgent the problem feels. Most agents waste energy optimizing No-brainers and rush Hard Choices.

## Confidence-vs-Quality

Two axes: **confidence the problem matters** (evidence-based) × **confidence the solution solves it** (evidence-based).

| Problem confidence | Solution confidence | Posture |
|---|---|---|
| Low | Any | **Speed-first.** Ship the cheapest possible probe; learn fast. Quality polish is wasted on an unvalidated problem. |
| High | Low | **Balanced.** Iterate, but with rigor. Ship a small version; measure; refine. |
| High | High | **Quality-first.** The certainty earns the time. Build it right. |
| Low | Low | **Stop and reframe.** You're not ready. Re-enter Phase A2. |

Confidence is graded, not binary. "Moderately high" + "low" → lean toward speed.

## Setting the tier

Combine both calibrations:

- **Tier Low** = No-brainer / Apples-&-Oranges OR (Low problem-confidence with reversible outcome). Skip extensive grounding; one-pass thinking; optional stress-test.
- **Tier Medium** = Big Choice OR (High problem / Low solution confidence). Decision Matrix in C2; mandatory stress-test trio; standard grounding.
- **Tier High** = Hard Choice OR (High both with irreversible / one-shot outcome). Strict stress-test trio; explicit rollback path; full grounding.

Default to Medium when uncertain. Inflate to High only when the cost of being wrong is genuinely high.

## What governs Phase B2 grounding

| Tier | Grounding depth |
|---|---|
| Low | Skim the obvious files; use what's already in context. |
| Medium | Read load-bearing files; verify one critical assumption. |
| High | Read + reproduce + falsify; sanity-check assumptions against actual system behavior. |

Do not read everything to feel thorough. The minimum grounding set is the smallest evidence that can change the decision.

## What governs Phase C2 stress-test

| Tier | Stress-test |
|---|---|
| Low | Optional. Brief inversion check ("could this fail badly?"). |
| Medium | Mandatory trio: Inversion + Ladder of Inference + Second-Order. Standard depth. |
| High | Strict trio. Inversion with named mitigations baked into the plan. Explicit rollback path. Second-Order at 10-min/10-mo/10-yr scales. |

## When to re-calibrate mid-session

Tier is locked at Phase B1 by default. Re-enter calibration when:
- Phase B2 grounding reveals the impact is much smaller (or larger) than assumed
- Phase C2 stress-test exposes a previously-hidden irreversibility
- Phase D2 verification fails — recalibrate the next attempt with the failure as evidence

Re-calibration is cheap compared to running a session at the wrong tier.

## Solo mode application

Set tier silently using both matrices, write the tier in the opening contract, proceed. Re-emit the contract if tier changes mid-session.

## Interactive mode application

Tier is set via the Hard Choice classifier in `modes/interactive-brainstorm.md` Step 4 (Evaluate); see also `frameworks/decision-matrix.md` for the full Decision Matrix mechanics.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Treating every decision as Tier High | Run the matrices. Most decisions are Low. Tier inflation produces analysis paralysis and trains agents to ignore Tier signals. |
| Treating every decision as Tier Low | The opposite. Run the matrices. Hard Choices are real. Skipping them silently is how production fires happen. |
| Setting tier from urgency feeling | Urgency ≠ impact. A loud bug can be Low impact; a quiet architectural choice can be High. Use the matrices, not adrenaline. |
| Confidence as binary | Grade it. "I'm 60% sure this problem matters" → still leans speed. |
| Skipping Confidence-vs-Quality on build decisions | Build decisions especially benefit from posture clarity. Surface the posture even if briefly: "Posture: balanced — confident the problem matters; solution shape is still TBD." |
