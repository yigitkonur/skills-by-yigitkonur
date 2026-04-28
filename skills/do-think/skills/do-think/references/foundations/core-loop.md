# Core Loop — 4 Phases (Op-Aware)

The universal `do-think` loop. Both Solo and Interactive modes use this geometry.

Four phases. Phase A has three moves (one of which is conditional); B/C/D have two each. Phase exits are gated, not optional.

```
Phase A — Frame      A1 classify domain   ·   A2 classify operation   ·   A3 reframe (if needed)
Phase B — Calibrate  B1 effort tier       ·   B2 minimum grounding (op-aware)
Phase C — Compare    C1 op-specific output ·  C2 op-specific stress-test
Phase D — Commit     D1 choose / produce  ·   D2 verify (op-specific)
```

## Opening contract (Iron Law)

Before any analysis, emit one line:

```
Mode: <Solo|Interactive>   Op: <op>   Cynefin: <Clear|Complicated|Complex|Chaotic|Disorder>   Tier: <Low|Medium|High>
```

Where `Op` is one of: `SenseMaking | Extraction | Composition | Reshape | GroundedQA | WatchTrigger | Orchestration | SelfVerify` — see `operation-classification.md`.

This single line is non-skippable. It declares mode (no silent default-to-Solo), proves Phase A1 ran (no skipping the Cynefin classifier), proves Phase A2 ran (no defaulting to Sense-Making for everything), and locks the effort tier (no scope creep). The user can correct any of four things in one re-prompt.

## Phase A — Frame

### A1. Classify the domain
Run the Cynefin classifier from `domain-classification.md`. Pick one of: Clear, Complicated, Complex, Chaotic, Disorder. Write the domain in the opening contract.

### A2. Classify the operation
Run the cognitive-operation classifier from `operation-classification.md`. Pick one of the 8 operations. Write the operation in the opening contract.

**This is the most consequential move in Phase A** — operation selects the rest of Phase B (grounding shape) and all of Phase C (C1 output and C2 stress-test). Misclassification here is the most common upstream failure.

### A3. Reframe the real question
Default: skip. Reframe only if A1 returned **Disorder** OR the user's framing fails the why-up test ("would solving this exactly as stated actually solve their problem?"). When reframing, run Abstraction Laddering from `reframing.md`. After reframing, re-run A1 and A2 — both may change.

**Phase A exit**: opening contract written (4 fields); reframe done if needed.

## Phase B — Calibrate

### B1. Effort tier
Use the Hard Choice × Confidence-vs-Quality matrix in `effort-calibration.md`. Output: Low / Medium / High. Tier governs how deep B2 grounding goes and whether C2 stress-test is mandatory.

### B2. Gather the minimum grounding set
**Shape varies by Op** — see `operation-classification.md` for the per-op grounding focus:

- SenseMaking: direct observation + primary docs (`evidence-and-falsification.md`)
- Extraction: schema spec + sample inputs (≥3 covering edges)
- Composition: form examples + voice spec + factual context + audience
- Reshape: invariants + scope of change
- GroundedQA: corpus boundary + retrieved passages
- WatchTrigger: trigger conditions + signal definition + history baseline
- Orchestration: system contracts + idempotency keys + error modes
- SelfVerify: oracle definition + iteration budget + convergence criterion

Do not read everything to feel thorough. The minimum grounding set is the smallest evidence that can change the decision (or the smallest input that can produce a correct artifact).

**Phase B exit**: tier set; minimum evidence (op-shaped) collected.

## Phase C — Compare

C1 and C2 are **operation-specific**. Run the workflow file for the classified Op. The summaries below are routing pointers; the workflows have the procedure.

### C1. Op-specific output

NOT always "≥3 options." That's a Sense-Making move. Per-op:

| Op | C1 output |
|---|---|
| SenseMaking | ≥3 candidate verdicts/causes with falsifiers |
| Extraction | filled schema + completeness flag + ambiguity log |
| Composition | outline + assumption list (≥3 outline variants only when structural choice matters) |
| Reshape | transformation plan + invariant proofs |
| GroundedQA | retrieved evidence + scope confirmation |
| WatchTrigger | trigger spec + alert payload + escalation rules |
| Orchestration | sequence + idempotency markers + error handlers |
| SelfVerify | first attempt + first oracle reading |

If C1 generation is dry, route via the SKILL.md master table to a `frameworks/` file (e.g., `zwicky-box.md` for combinatorial generation, `six-thinking-hats.md` for perspective rotation, `decomposition-tools.md` for MECE breakdowns).

### C2. Op-specific stress-test (mandatory at Tier Medium/High)

The trio (Inversion + Ladder of Inference + Second-Order — see `stress-test-trio.md`) is for **Sense-Making**. Other ops have their own stress-test focus:

| Op | C2 stress-test |
|---|---|
| SenseMaking | Inversion + Ladder of Inference + Second-Order (the trio) |
| Extraction | coverage + edge case + schema-fit |
| Composition | form-substance match + voice fit + audience appropriateness |
| Reshape | behavior preservation + scope-creep check |
| GroundedQA | hallucination scan + citation completeness + out-of-scope flag |
| WatchTrigger | false-positive scan + missed-signal scan + signal/noise |
| Orchestration | partial-failure scan + transaction boundary check + retry safety |
| SelfVerify | loop bound + oracle accuracy + escape condition |

**Phase C exit criterion**: op-specific C1 output written AND op-specific C2 stress-test written (mandatory at Tier Medium/High; at Tier Low only the brief inversion check from `effort-calibration.md` is required). Outputs are written, not implied.

**Escalation gate**: if C2 kills all options/candidates/attempts, **switch Mode to Interactive** — do not silently pick the least-bad option.

## Phase D — Commit

### D1. Choose / produce the next move
Op-shaped: implement / produce the artifact / probe / ask one clarifying question / stop because not ready.

If more thinking would not change the next move, stop thinking.

### D2. Verify or revise
Every chosen path needs a verification check + a revision trigger. Shape varies by Op:

- SenseMaking → observable signal that confirms the verdict
- Extraction → schema validator pass + ambiguity-log human-review
- Composition → audience can make the intended decision from the artifact
- Reshape → invariants verified, behavior unchanged
- GroundedQA → cited passages can be navigated to and confirm the claims
- WatchTrigger → trigger fires on a known-good signal AND doesn't fire on a known-bad signal
- Orchestration → end-to-end run leaves the system in the expected state
- SelfVerify → oracle pass AND real-world behavior check (oracle is a proxy, not the truth)

Write the verification check before acting. Unwritten = skipped under pressure.

**Phase D exit**: chosen path stated; verification check (op-shaped) written.

## When to revisit a phase

| Discovery | Re-enter |
|---|---|
| Evidence flips an assumption you wrote in B2 | Phase A2 (re-classify op) or Phase A3 (reframe) or Phase B2 (more grounding) |
| Stress-test kills the leading C1 output / partial death (e.g., 2 of 3 SenseMaking options fail; the proposed Extraction schema fit fails; the Composition outline fails the form-substance check) | Phase C1 (regenerate the op-appropriate output) |
| Stress-test kills all C1 outputs and no operationally viable next move remains | Switch Mode to Interactive |
| Verification fails in D2 | Phase C1 with the verification result as new evidence |
| Domain shifts mid-session (e.g. Complicated → Chaotic) | Phase A1 (re-classify) and re-emit the opening contract |
| Operation shifts mid-session (e.g. Sense-Making analysis reveals it's actually Composition work) | Phase A2 (re-classify) and re-emit the opening contract |

Replanning is not failure. Sticking with a dead frame is.

## Final test

Before you act, ask:

> *Do I know enough to make the next move safer and clearer than acting immediately would be?*

If yes, act. If no, gather the smallest missing evidence first.
