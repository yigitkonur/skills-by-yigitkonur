---
name: do-think
description: Use skill if you are planning, architecting, refactoring, brainstorming, or choosing under ambiguity/stakes and need Solo or user-in-the-loop deep thinking before acting.
---

# Do Think

Use this skill when acting on the first plausible answer is risky. Pick the mode FIRST, then run one core loop.

Modes: **Solo deep-think** (default; agent reasons alone, then acts) or **Interactive brainstorm** (user in the loop, 5 forks, 6-step structured session).

## Trigger boundary

Use this skill when:
- the problem is underspecified
- the right frame or decision criteria are unknown
- multiple approaches are viable and tradeoffs matter
- a refactor could change behavior, boundaries, or workflow
- the codebase or domain is unfamiliar
- the change is expensive to reverse
- the task is likely to derail after the first obstacle
- the user explicitly asked to brainstorm, walk through, or think together

Prefer another skill when:
- the task is trivial, mechanical, or fully specified
- the user gave exact steps and the main risk is execution, not reasoning
- only summarizing, translating, or relaying already-known facts
- runtime bug with a reproducible failure → `do-debug`
- reviewing a PR or branch diff → `do-review`
- evaluating received review feedback → `evaluate-code-review`
- preparing a PR/review handoff → `ask-review`
- bulk dirty-tree cleanup into PRs → `run-repo-cleanup`
- done-vs-claimed audit → `check-completion`

## Pick a mode FIRST (Iron Law #0)

Default: **Solo** for answer-or-execute requests. High stakes raise Tier first; they do not force Interactive unless the decision needs user-owned context or co-authorship.

Switch to **Interactive** by one of three gates:

- **User-flagged**: the user says "help me think", "walk through", "brainstorm", "let's figure out", "let's explore", or otherwise asks to co-author the decision.
- **Auto-detected**: stakeholder/domain context is missing, or ≥2 viable options remain equal with no agent-owned tie-breaker.
- **Escalated**: Solo Phase C2 stress-test kills all candidates/attempts.

Cross-runtime note: Interactive needs an ask-user tool. See `references/cross-runtime.md` for the runtime → tool lookup and the prose fallback. **Do not silently degrade Interactive into Solo** — surface the limitation if the runtime can't support forks.

## The opening contract (Iron Law #1)

The **first line** at the start of a `do-think` session is a single machine-checkable contract:

```
Mode: <Solo|Interactive>   Op: <op>   Cynefin: <Clear|Complicated|Complex|Chaotic|Disorder>   Tier: <Low|Medium|High>
```

Where `Op` is one of: `SenseMaking | Extraction | Composition | Reshape | GroundedQA | WatchTrigger | Orchestration | SelfVerify`.

This line is non-skippable at session start. It declares mode (no silent default-to-Solo), proves Phase A1 ran, proves Phase A2 ran, and locks the effort tier. The user can correct any field in one re-prompt. Re-emit only if Mode, Op, Cynefin, or Tier changes mid-session.

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
11. **`frameworks/` is a library** — access it from this file's table, Interactive mode, or an operation workflow that explicitly names the framework. Do not load all frameworks.

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
- **B2.** Gather the minimum grounding set. Shape varies by Op; use `references/foundations/operation-classification.md` and the workflow file.

**Phase B exit**: tier set; minimum evidence (op-shaped) collected.

### Phase C — Compare

C1 and C2 are **operation-specific**. Run the workflow for the classified Op.

- **C1.** Produce the op-shaped output. Only SenseMaking requires ≥3 candidate verdicts; other ops produce schemas, outlines, invariant plans, evidence, trigger specs, sequences, or oracle readings.
- **C2.** Stress-test before committing at Tier Medium/High. Use the trio only for SenseMaking → `references/foundations/stress-test-trio.md`; other ops use the C2 focus in `operation-classification.md`.

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
| 4 — Evaluate | B2 (op-specific grounding) + scoring | Hard Choice classifier → `frameworks/decision-matrix.md` (Tier was set in Step 1 alongside Op + Cynefin so the opening contract emits all four fields) | **Fork 4**: factors + weights right? |
| 5 — Stress-test | C2 | Op-specific stress-test from `references/foundations/operation-classification.md` (use `foundations/stress-test-trio.md` only when `Op: SenseMaking`) | **Fork 5**: blind spots change the pick? |
| 6 — Communicate | D | `foundations/output-contract.md` (10-section deliverable) | (no fork) |

Skip-fork policy and one-question-at-a-time discipline live in `references/interaction-patterns.md`.

If the Interactive artifact would exceed 3,000 words, re-scope to the highest-risk sub-problem before producing it.

## Output contract

- **Solo SenseMaking** — Minto Pyramid: first sentence = verdict, body = 3-5 evidence-backed arguments, last sentence = verification check.
- **Solo non-Sense ops** — use the classified workflow file's output contract: Extraction schema/provenance, Composition artifact/provenance, Reshape diff/invariants, GroundedQA answer/citations, WatchTrigger trigger spec, Orchestration sequence, or SelfVerify oracle log.
- **Interactive mode** — 10-section contract: Approach / Problem shape / Decomposition / Options explored / Evaluation / Assumptions / Blind spots / Second-order effects / Ranked summary / Recommended next step

Full spec: `references/foundations/output-contract.md`.

## Session completion contract

Every finished session states:
- chosen next move or produced artifact
- assumptions that matter
- risks/blind spots, plus rollback when `Tier: High`
- verification check, shaped to the Op
- handoff target when another skill should continue

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
- Reading all `frameworks/*`, or loading more than one decomposition, one generation, and one evaluation/stress tool in one pass
- Asking the user a clarifying question mid-Solo (you've hit an escalation trigger — switch to Interactive instead)

## Rationalization checks

- If classification, stress-test, or verification feels obvious, write it anyway.
- High stakes raise Tier; Interactive still needs a mode gate.
- The trio is SenseMaking-only; other ops use op-shaped C2 checks.
- If every candidate dies, switch modes or hand off. Do not pick the least-bad path silently.

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

## Escalation gates

- **Solo → Interactive** when: all candidates/attempts die in stress-test
- **Interactive → Solo** never silently — only on explicit user request
- **Out to `do-debug`** when: the task is a runtime bug with a reproducible failure, or a `do-think` session produces a testable runtime hypothesis
- **Out to `check-completion`** when: declared "done" but unsure what's actually verified
- **Do NOT recommend `do-think` as the next-step** (no infinite regress). If more thinking is needed, name the sub-topic and explicitly hand off.

### `do-debug` route-back handoff

When this session, especially one entered from `do-debug` after 3 failed fixes, produces a falsifiable runtime hypothesis, hand back to `do-debug` with:

`symptom card / observed failure`, `failed-fix summary if known`, `selected hypothesis + mechanism`, `falsification experiment`, `narrow next diagnostic or fix boundary`, and `verification check`.

## Reference routing — master table

Foundations are self-sufficient. `frameworks/` is a library accessed from this table, Interactive mode, or an operation workflow that explicitly names the framework.

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
| [`references/foundations/output-contract.md`](references/foundations/output-contract.md) | Always — SenseMaking Minto, op-shaped Solo contracts, 10-section Interactive |

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

### Frameworks (selection-capped library)

Selection rule: choose at most one decomposition tool, one generation tool, and one evaluation/stress tool per pass. In Solo mode, load no framework unless C1 generation or C2 evaluation needs it. In Interactive mode, Steps 2-5 route frameworks; each step picks one primary framework unless the user explicitly widens the session.

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

Before acting, ask: *Do I know enough to make the next move safer and clearer than acting immediately would be?* If not, gather the smallest missing evidence first.
