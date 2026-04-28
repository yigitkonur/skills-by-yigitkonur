---
name: do-think
description: Use skill if you are facing ambiguous, high-stakes, or hard-to-reverse work — debug, refactor, plan, architect, brainstorm, choose — and need a deep-thinking framework, solo or user-in-the-loop.
---

# Do Think

The deep-thinking skill. Use it when acting on the first plausible answer is risky.

Two operating modes:

- **Solo deep-think** (default) — agent reasons alone, then acts.
- **Interactive brainstorm** — user in the loop, 5 forks, 6-step structured session.

One core loop applies to both. Pick the mode FIRST, then run the loop.

## Trigger boundary

Use this skill when:
- the problem is underspecified
- the root cause is unknown
- multiple approaches are viable and tradeoffs matter
- a refactor could change behavior, boundaries, or workflow
- the codebase or domain is unfamiliar
- the change is expensive to reverse
- the task is likely to derail if you stop after the first obstacle
- the user explicitly asked to brainstorm, walk through, or think together

Do NOT use this skill when:
- the task is trivial, mechanical, or fully specified
- the user gave exact steps and the main risk is execution, not reasoning
- you are only summarizing, translating, or relaying already-known facts
- the task is a runtime bug with a reproducible failure → use `do-debug` instead
- the task is verifying what's actually done vs. claimed → use `check-completion`

## Pick a mode FIRST (Iron Law #0)

Default: **Solo**. Switch to **Interactive** when any of:

- The user said "help me think", "walk through", "brainstorm", "let's figure out", "let's explore"
- The user is present AND the decision is high-stakes / hard-to-reverse
- ≥2 viable options have no obvious winner AND the user is reachable
- Solo's Phase C2 stress-test killed all three options (escalation gate)
- The decision requires the user's domain knowledge or stakeholder context

Cross-runtime note: Interactive needs an ask-user tool. See `references/cross-runtime.md` for the runtime → tool lookup and the prose fallback. **Do not silently degrade Interactive into Solo** — surface the limitation if the runtime can't support forks.

## The opening contract (Iron Law #1)

The **first line** of every response is a single machine-checkable contract:

```
Mode: <Solo|Interactive>   Op: <op>   Cynefin: <Clear|Complicated|Complex|Chaotic|Disorder>   Tier: <Low|Medium|High>
```

Where `Op` is one of: `SenseMaking | Extraction | Composition | Reshape | GroundedQA | WatchTrigger | Orchestration | SelfVerify`.

This line is non-skippable. It declares mode (no silent default-to-Solo), proves Phase A1 ran (no skipping the Cynefin classifier), proves Phase A2 ran (no defaulting to Sense-Making for everything), and locks the effort tier (no scope creep). The user can correct any of four things in one re-prompt. Re-emit if any field changes mid-session.

## Non-negotiable rules

1. **Iron Laws #0 + #1 are mandatory.** Mode picked, opening contract emitted (with Op + Cynefin + Tier), on the first response.
2. Ground before hypothesis.
3. Match effort to **Tier** — `references/foundations/effort-calibration.md` governs reading depth and stress-test strictness.
4. **Match thinking tools to Op** — `references/foundations/operation-classification.md` governs which Phase C1/C2 tools fit. The stress-test trio fits Sense-Making; other operations have their own stress-test focus.
5. Keep **≥3 live options** through Phase C *only when Op = SenseMaking*. Other operations have operation-specific C1 outputs (filled schemas for Extraction, outlines for Composition, retrieved evidence for GroundedQA, etc.).
6. **Stress-test before commit** at Tier Medium or High. The trio is for SenseMaking; see operation-classification.md for the per-op stress-test focus.
7. Separate observations, mechanisms, and judgments at every phase.
8. Numbered, stepwise progress instead of mental jumps.
9. Prefer the smallest next move that changes your certainty.
10. End every session with a concrete next move + verification check (shape varies by Op).
11. **Foundations are self-sufficient. `frameworks/` is library** — accessed only via the master routing table at the bottom of this file or by `modes/interactive-brainstorm.md`. Do not cross-link from foundations to frameworks.

## The universal core loop — 4 phases

```
Phase A — Frame      A1 classify domain   ·   A2 classify operation   ·   A3 reframe (if needed)
Phase B — Calibrate  B1 effort tier       ·   B2 minimum grounding (op-aware)
Phase C — Compare    C1 op-specific output ·  C2 op-specific stress-test
Phase D — Commit     D1 choose / produce  ·   D2 verify (op-specific)
```

### Phase A — Frame

- **A1.** Classify the domain (Cynefin) → `references/foundations/domain-classification.md`. Write the domain in the opening contract.
- **A2.** Classify the operation (8 cognitive operations) → `references/foundations/operation-classification.md`. Write the operation in the opening contract. **This is what selects the rest of Phase B and all of Phase C.**
- **A3.** Reframe the real question. Default: skip. Reframe only if A1 returned Disorder, OR the user's framing fails the why-up test → `references/foundations/reframing.md` (Abstraction Laddering).

**Phase A exit**: opening contract written (4 fields); reframe done if needed.

### Phase B — Calibrate

- **B1.** Effort tier (Hard Choice × Confidence-vs-Quality) → `references/foundations/effort-calibration.md`. Output: Low / Medium / High in the opening contract.
- **B2.** Gather the minimum grounding set — **shape varies by Op** (see operation-classification.md):
  - SenseMaking: direct observation + primary docs (evidence ladder)
  - Extraction: schema spec + sample inputs (≥3 covering edges)
  - Composition: form examples + voice spec + factual context + audience
  - Reshape: invariants + scope of change
  - GroundedQA: corpus boundary + retrieved passages
  - WatchTrigger: trigger conditions + signal definition + history baseline
  - Orchestration: system contracts + idempotency keys + error modes
  - SelfVerify: oracle definition + iteration budget + convergence criterion

**Phase B exit**: tier set; minimum evidence (op-shaped) collected.

### Phase C — Compare

C1 and C2 are **operation-specific**. The 4-phase loop is universal; what each phase produces depends on the operation. Run the workflow for the classified Op.

- **C1.** Op-specific output (NOT always "≥3 options"):
  - SenseMaking → ≥3 candidate verdicts with falsifiers
  - Extraction → filled schema + completeness flag + ambiguity log
  - Composition → outline + assumption list (≥3 outline variants only when structural choice matters)
  - Reshape → transformation plan + invariant proofs
  - GroundedQA → retrieved evidence + scope confirmation
  - WatchTrigger → trigger spec + alert payload + escalation rules
  - Orchestration → sequence + idempotency markers + error handlers
  - SelfVerify → first attempt + first oracle reading

- **C2.** Op-specific stress-test (mandatory at Tier Medium/High):
  - SenseMaking → Inversion + Ladder of Inference + Second-Order (the trio) → `references/foundations/stress-test-trio.md`
  - Extraction → coverage + edge case + schema-fit
  - Composition → form-substance match + voice fit + audience appropriateness
  - Reshape → behavior preservation + scope-creep check
  - GroundedQA → hallucination scan + citation completeness + out-of-scope flag
  - WatchTrigger → false-positive scan + missed-signal scan + signal/noise
  - Orchestration → partial-failure scan + transaction boundary check + retry safety
  - SelfVerify → loop bound + oracle accuracy + escape condition

**Phase C exit criterion**: op-specific C1 output written AND op-specific C2 stress-test written. Outputs are written, not implied.

**Escalation gate**: if C2 kills all options/candidates/attempts, **switch Mode to Interactive** — do not silently pick the least-bad option.

### Phase D — Commit

- **D1.** Choose the next move (op-shaped): implement / produce / probe / ask one clarifying question / stop.
- **D2.** Verify or revise — every chosen path needs a verification check + a revision trigger. Shape varies by Op (verdict observation for SenseMaking; schema validator pass for Extraction; audience decision for Composition; oracle pass for SelfVerify; etc.).

**Phase D exit**: chosen path stated; verification check (op-shaped) written.

## Solo mode — fast routing

Read the smallest set that fits the situation. Files listed are the *minimum*; add foundations as Tier escalates.

| Situation (by Op) | Read this set |
|---|---|
| Generic Sense-Making (research, judgment, evaluation) | `references/modes/solo-deep-think.md`, `references/foundations/operation-classification.md`, `references/workflows/sense-making.md`, `references/foundations/stress-test-trio.md` |
| Bug or regression (Sense-Making, bug variant) | `references/workflows/bug-tracing.md`, `references/foundations/evidence-and-falsification.md` |
| Recurring / "we already fixed this" (Sense-Making, systemic) | `references/workflows/recurring-issue.md` |
| Structured Extraction (mess → schema) | `references/workflows/structured-extraction.md` |
| Generative Composition (artifact production, code feature, doc) | `references/workflows/generative-composition.md` |
| Reshape & Repurpose — code | `references/workflows/refactor-thinking.md` |
| Reshape & Repurpose — text/data | `references/foundations/operation-classification.md` (Op 4 inline section) |
| Grounded Q&A (corpus answer with citations) | `references/workflows/grounded-qa.md` |
| Watch & Trigger (design the trigger conditions) | `references/foundations/operation-classification.md` (Op 6 inline section) |
| Cross-System Orchestration (design the sequence) | `references/foundations/operation-classification.md` (Op 7 inline section) |
| Iterative Self-Verification (write → test → fix loop with oracle) | `references/workflows/iterative-self-verification.md` |
| Planning a complex task (any Op) | `references/workflows/task-planning.md`, `references/foundations/stepwise-reasoning.md` |
| Staying autonomous through blockers (any Op) | `references/workflows/continuous-execution.md` |
| Especially high-stakes / hard-to-reverse (any Op) | + `references/foundations/ultrathinking.md` |

## Interactive mode — 6-step session, 5 forks

Full spec at `references/modes/interactive-brainstorm.md`. The 4-phase loop maps to a 6-step session with 5 forks:

| Step | Phase | What runs | Fork |
|---|---|---|---|
| 1 — Classify | A1 | Cynefin classifier (3 questions to user) | **Fork 1**: domain correct? |
| 2 — Decompose | A2 (extended) | `frameworks/decomposition-tools.md` or `foundations/reframing.md` | **Fork 2**: decomposition captures the problem? |
| 3 — Explore | C1 | `frameworks/six-thinking-hats.md` / `first-principles.md` / `zwicky-box.md` / `systems-tools.md` | **Fork 3**: options resonate? |
| 4 — Evaluate | B1 + scoring | Hard Choice classifier → `frameworks/decision-matrix.md` | **Fork 4**: factors + weights right? |
| 5 — Stress-test | C2 | `foundations/stress-test-trio.md` | **Fork 5**: blind spots change the pick? |
| 6 — Communicate | D | `foundations/output-contract.md` (10-section deliverable) | (no fork) |

Skip-fork policy and one-question-at-a-time discipline live in `references/interaction-patterns.md`.

## Output contract

- **Solo mode** — Minto Pyramid:
  - First sentence = chosen path
  - Body = 3-5 evidence-backed key arguments
  - Last sentence = verification check
  - Fast-fail: missing first sentence OR last sentence = output incomplete
- **Interactive mode** — 10-section contract: Approach / Problem shape / Decomposition / Options explored / Evaluation / Assumptions / Blind spots / Second-order effects / Ranked summary / Recommended next step

Full spec: `references/foundations/output-contract.md`.

## Anti-patterns

- Acting on the first plausible explanation
- Skipping Phase A1 (Cynefin) because the prompt feels straightforward
- Skipping Phase A2 (Op classification) and defaulting to Sense-Making for everything
- Running the Sense-Making stress-test trio on a non-Sense-Making operation
- Forcing ≥3 options on a task that isn't Sense-Making (Extraction wants completeness, Composition wants outline-fit)
- Letting one attractive option kill comparison too early (in Sense-Making)
- Treating Phase C2 stress-test as ceremonial when it's load-bearing
- Stopping after the first obstacle when better local moves still exist
- Claiming success before stating the (op-shaped) verification result
- Silently degrading Interactive into Solo
- Reading `frameworks/*` without being routed there from this master table or from `modes/interactive-brainstorm.md`
- Asking the user a clarifying question mid-Solo (you've hit an escalation trigger — switch to Interactive instead)

## Anti-rationalization table

| Rationalization | Counter |
|---|---|
| "Cynefin is overkill for this." | 30 seconds saves rerouting a 15-minute analysis. Run it. |
| "Op classification is obvious — skip it." | The most common upstream failure is op-mismatch. 30 seconds of classification saves a wrong-tools session. Write it in the contract. |
| "I already know which option wins." | Then write what would falsify it. Can't? You don't know. (Sense-Making only — other ops don't have "options.") |
| "Stress-test feels formulaic — skip." | Skipping is exactly when the formulaic check catches the blind spot the intuition missed. |
| "Three options is artificial; only two are real." | Force a third. The third is usually "do nothing" or "ask the user." Both are real. (Sense-Making only.) |
| "Solo because the user said 'just figure it out'." | Solo is the choice; "just figure it out" doesn't say it's reversible. Confirm reversibility before committing solo. |
| "Verification step is obvious — skip writing it." | Unwritten = skipped under pressure. Write it. |
| "The trio (Inversion + Ladder + Second-Order) applies to every Op." | No. The trio is for Sense-Making. Other ops have their own stress-test focus — see operation-classification.md. |

## Voice discipline

**Required forms** (use these literally in output):
- `Mode: <Solo|Interactive>`
- `Op: <SenseMaking|Extraction|Composition|Reshape|GroundedQA|WatchTrigger|Orchestration|SelfVerify>`
- `Cynefin: <domain>`
- `Tier: <Low|Medium|High>`
- `Live options: 1) … 2) … 3) …` (in C1, *only* when Op = SenseMaking)
- `Filled schema:` / `Outline:` / `Retrieved evidence:` / `Trigger spec:` / `Sequence:` / `Oracle reading:` (in C1, op-specific)
- `Pre-mortem failure mode: …` (in C2, *only* when Op = SenseMaking)
- `Coverage: …` / `Form-substance match: …` / `Hallucination scan: …` / etc. (in C2, op-specific)
- `Verification check: …` (in D2)

**Forbidden phrases**:
- "I think the best option is…" (without three named options)
- "this is straightforward" (without a Cynefin check)
- "let me know if you want me to dig deeper" (false abdication)
- "Thanks for the great discussion" / "Hope this helps" / "Please feel free to" / "You're absolutely right" (shared with the pack's review skills)

## Escalation gates

- **Solo → Interactive** when: 3 candidate options die in stress-test
- **Interactive → Solo** never silently — only on explicit user request
- **Out to `do-debug`** when: the task is a runtime bug with a reproducible failure
- **Out to `check-completion`** when: declared "done" but unsure what's actually verified
- **Do NOT recommend `do-think` as the next-step** (no infinite regress). If more thinking is needed, name the sub-topic and explicitly hand off.

## Reference routing — master table

Foundations are self-sufficient (read directly when the loop says so). `frameworks/` is library — accessed only via the rows below or via `modes/interactive-brainstorm.md`. Do not cross-link foundations into frameworks.

### Foundations (load-bearing primitives, used by every session)

| File | Read when |
|---|---|
| [`references/foundations/core-loop.md`](references/foundations/core-loop.md) | Always — the 4-phase loop with opening contract |
| [`references/foundations/domain-classification.md`](references/foundations/domain-classification.md) | Phase A1 — Cynefin classifier |
| [`references/foundations/operation-classification.md`](references/foundations/operation-classification.md) | Phase A2 — the 8 cognitive operations + per-op routing |
| [`references/foundations/reframing.md`](references/foundations/reframing.md) | Phase A3 — Abstraction Laddering when framing is wrong or A1 returned Disorder |
| [`references/foundations/effort-calibration.md`](references/foundations/effort-calibration.md) | Phase B1 — Hard Choice × Confidence-vs-Quality |
| [`references/foundations/evidence-and-falsification.md`](references/foundations/evidence-and-falsification.md) | Phase B2 + Phase C2 — evidence ladder, falsification, Ladder of Inference rebuild |
| [`references/foundations/stepwise-reasoning.md`](references/foundations/stepwise-reasoning.md) | When tempted to leap from symptom to cause |
| [`references/foundations/stress-test-trio.md`](references/foundations/stress-test-trio.md) | Phase C2 *for SenseMaking* — Inversion + Ladder + Second-Order (other ops use op-specific stress-test from operation-classification.md) |
| [`references/foundations/ultrathinking.md`](references/foundations/ultrathinking.md) | Tier High — irreversible / one-shot / broad blast radius |
| [`references/foundations/output-contract.md`](references/foundations/output-contract.md) | Always — Minto for Solo, 10-section for Interactive (op-shaped variations inside) |

### Modes (how the skill operates)

| File | Read when |
|---|---|
| [`references/modes/solo-deep-think.md`](references/modes/solo-deep-think.md) | Mode = Solo — autonomous loop, anti-stall, escalation triggers |
| [`references/modes/interactive-brainstorm.md`](references/modes/interactive-brainstorm.md) | Mode = Interactive — 6-step + 5-fork mechanics |

### Workflows (operation-specific recipes)

| File | Op | Read when |
|---|---|---|
| [`references/workflows/sense-making.md`](references/workflows/sense-making.md) | SenseMaking | Generic research / judgment / evaluation (non-bug, non-systemic) |
| [`references/workflows/bug-tracing.md`](references/workflows/bug-tracing.md) | SenseMaking (bug variant) | A specific bug with a known symptom |
| [`references/workflows/recurring-issue.md`](references/workflows/recurring-issue.md) | SenseMaking (systemic variant) | "We already fixed this and it's back" — Iceberg + Connection Circles |
| [`references/workflows/structured-extraction.md`](references/workflows/structured-extraction.md) | Extraction | Mess → schema (transcript → todos, invoice → ledger, email → CRM) |
| [`references/workflows/generative-composition.md`](references/workflows/generative-composition.md) | Composition | Context + form → artifact (cover letter, RFP, deck, code feature) |
| [`references/workflows/refactor-thinking.md`](references/workflows/refactor-thinking.md) | Reshape (code variant) | A refactor where invariants must survive |
| [`references/workflows/grounded-qa.md`](references/workflows/grounded-qa.md) | GroundedQA | Question + corpus → cited answer (HR Q&A, codebase Q&A, support FAQ) |
| [`references/workflows/iterative-self-verification.md`](references/workflows/iterative-self-verification.md) | SelfVerify | Write → test → fix loop with deterministic oracle |
| [`references/workflows/task-planning.md`](references/workflows/task-planning.md) | (universal) | A large or fuzzy task that needs slicing |
| [`references/workflows/continuous-execution.md`](references/workflows/continuous-execution.md) | (universal) | Need to keep moving without frequent human checkpoint |

### Frameworks (library — accessed only from this table or from Interactive Steps 2-5)

| File | Read when |
|---|---|
| [`references/frameworks/six-thinking-hats.md`](references/frameworks/six-thinking-hats.md) | Phase C1 needs perspective rotation; Interactive Step 3 |
| [`references/frameworks/zwicky-box.md`](references/frameworks/zwicky-box.md) | Phase C1 generator is dry — combinatorial generation across dimensions |
| [`references/frameworks/first-principles.md`](references/frameworks/first-principles.md) | Analogies are failing; suspect inherited assumptions |
| [`references/frameworks/decomposition-tools.md`](references/frameworks/decomposition-tools.md) | Issue Trees / Ishikawa for problem decomposition |
| [`references/frameworks/decision-matrix.md`](references/frameworks/decision-matrix.md) | Phase C2 with ≥3 options + multiple weighted factors; Hard Choice classifier |
| [`references/frameworks/systems-tools.md`](references/frameworks/systems-tools.md) | Connection Circles + Reinforcing/Balancing Loops — feedback dynamics |
| [`references/frameworks/productive-thinking-drive.md`](references/frameworks/productive-thinking-drive.md) | Defining success criteria with the DRIVE check |
| [`references/frameworks/interpersonal-tools.md`](references/frameworks/interpersonal-tools.md) | SBI for feedback content; Conflict Resolution Diagram for stakeholder conflict |

### Cross-cutting (Interactive mode infrastructure)

| File | Read when |
|---|---|
| [`references/interaction-patterns.md`](references/interaction-patterns.md) | Interactive mode — fork discipline, one-question-at-a-time, YAGNI, pushback |
| [`references/cross-runtime.md`](references/cross-runtime.md) | Interactive on a non-Claude runtime — ask-user tool lookup + prose fallback |

## Final test

Before you act, ask:

> *Do I know enough to make the next move safer and clearer than acting immediately would be?*

If yes, act. If no, gather the smallest missing evidence first.
