# Sense-Making — Generic Research / Judgment / Evaluation

Operation: **Sense-Making & Judgment** (`Op: SenseMaking`).

The default cognitive operation: take fragmented context, apply a mental model, produce a position. Use this workflow for research, judgment, evaluation, and analysis tasks that are NOT bug investigations (`bug-tracing.md`) or recurring-systemic issues (`recurring-issue.md`).

## Triggers

- Research: "What's happening in our sector this week?", "How do competitors handle X?"
- Judgment: "Is this contract clause risky?", "Should we approve this?", "Is this lead qualified?"
- Evaluation: "Score this resume against the JD", "Triage these tickets by priority", "Which customer is at churn risk?"
- Analysis: "What's driving this metric?", "Why are these reviews trending negative?"

If the task is a *runtime* bug → `bug-tracing.md`. If symptoms recur after fixes → `recurring-issue.md`. Otherwise: this file.

## Phase A — Frame

- **A1** (Cynefin): usually Complicated (analysis will resolve) or Complex (probe required).
- **A2** (Op): SenseMaking.
- **A3** (Reframe, if needed): the user's question may be solution-shaped — climb up via `foundations/reframing.md`.

## Phase B — Calibrate

- **B1** (Tier): set by `foundations/effort-calibration.md`. Most judgment tasks are Medium; analysis affecting downstream commitments is High.
- **B2** (Grounding): the **evidence ladder** governs (`foundations/evidence-and-falsification.md`). For SenseMaking specifically:
  - **Direct observation** of the system / artifact / corpus — first
  - **Primary docs** (the contract itself, the call recording, the source data) — second
  - **Inference from patterns** — third
  - Resist the temptation to skip to the conclusion before reading the source.

## Phase C — Compare

### C1. Hold ≥3 candidate verdicts (or candidate causes)

Generate three positions on the question. The third is often "do nothing" or "ask the user" — both legitimate.

For each, write:
- **What it claims** (the verdict)
- **What supports it** (evidence cited from B2)
- **What would falsify it** (the cheapest test that could kill this position)

If only two candidates emerge after honest effort, force a third — frequently the obvious-but-unstated-answer is missing because everyone assumed it. Use the SKILL.md routing to reach `frameworks/six-thinking-hats.md` (perspective rotation) or `frameworks/first-principles.md` (assumption stripping) when generation is dry.

### C2. Stress-test trio (mandatory at Tier Medium/High)

Run all three from `foundations/stress-test-trio.md`. Sense-Making is the operation the trio was designed for:

- **Inversion** — assume the chosen verdict is wrong six months from now. What evidence convinces a future-you that today's pick was misguided?
- **Ladder of Inference** — descend from the verdict to the raw data. Where did selection bias enter? Which interpretations had alternatives?
- **Second-Order** — if the verdict is acted upon, what happens *after* the first-order effect? 10-min / 10-mo / 10-yr.

**Phase C exit criterion**: 3 verdicts surfaced + 3 stress-test outputs written.

**Escalation gate**: if all three verdicts die in the trio, switch to Interactive — the user needs to expand the option space.

## Phase D — Commit

- **D1**: state the chosen verdict (or "no verdict — gather more evidence first" if grounding was thin).
- **D2**: state the **verification check** — what observable signal will confirm the verdict was correct? Lead-qualified-but-doesn't-buy-in-30-days → falsified. Contract-flagged-as-risky-but-the-deal-closes-without-incident → may have been overcautious.

## Output contract

Per `foundations/output-contract.md`, Solo Minto Pyramid:

```
Verdict: <the position>.

Evidence (in evidence-ladder order, strongest first):
- <observation 1>
- <observation 2>
- <inference, flagged as inference>

Stress-test passes:
- Inversion: <main failure mode + mitigation or "accepted">
- Ladder: <jumped rung found, or "none — selection was clean">
- Second-Order: <key downstream effect>

Verification: <what we'll observe to confirm the verdict>.
```

Interactive mode: full 10-section deliverable per `foundations/output-contract.md`.

## Per-domain examples

| Domain | The verdict shape |
|---|---|
| Legal contract review | "This clause is risky because X / acceptable because Y / requires renegotiation on Z" |
| Lead qualification | "Lead score N / 100 — qualified because X, disqualified because Y, neutral because Z" |
| Resume filtering | "Match: strong/medium/weak — driven by X (matches), Y (gaps), Z (signals)" |
| Customer churn risk | "Churn probability: high/medium/low — driven by usage pattern X, support history Y, billing Z" |
| Market research | "Three takeaways: A (with evidence), B (with evidence), C (with evidence). Recommended action: …" |
| Architecture judgment | "Recommend pattern X over Y because of constraints Z; rollback plan: revert to Y if metric W moves" |

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| One-option output ("the answer is X") without three-option exploration | Force ≥3. The third is often "do nothing" — write it down. |
| Verdict before evidence in the output | Minto: verdict first IS correct. But the *internal* reasoning runs evidence → verdict, not the reverse. The output is the artifact, not the reasoning trace. |
| Treating "stress-test passed unchanged" as proof of robust verdict every time | If the trio NEVER changes the pick, it's running shallow. Re-run Inversion with a harder premise. |
| Conflating "I read the source" with "I have evidence" | Evidence is the specific cited observation. Reading without citing is preparation, not grounding. |
| Skipping verification check because "the verdict is obviously right" | Unwritten = skipped. Future-you needs the check to know whether to revise. |
| Inflating Tier for routine evaluations | A weekly market scan is Tier Low. Daily lead qualification is Tier Low. Save Tier High for verdicts with downstream commitment. |
