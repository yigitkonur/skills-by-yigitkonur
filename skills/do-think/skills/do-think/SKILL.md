---
name: do-think
description: Use skill if you are facing architectural decisions, hard tradeoffs, root-cause analysis without code, or ambiguous high-stakes choices needing structured Solo or Interactive deep thinking.
---

# Do Think

Structured deep-thinking framework for the moment **before** you act, not the act itself. Pick a **mode** (Solo or Interactive), emit the **opening contract**, run the **4-phase loop**, and apply the **mandatory stress-test** at Tier Medium/High before committing.

## When to use

Trigger on phrasings like *"think deeply"*, *"what should I do"*, *"should we…"*, *"help me decide"*, *"walk me through this"*, *"let's brainstorm"*.

Use when:

- *the problem is underspecified, the right frame is unknown, or the user is stuck on framing*
- *multiple viable approaches have non-trivial tradeoffs (architecture, API shape, dependency choice)*
- *the change is expensive to reverse — schemas, public contracts, infra, security boundaries*
- *the codebase or domain is unfamiliar and the first-plausible-answer would be a guess*
- *root-cause reasoning is needed and there is no runtime to debug against (post-mortem, design review)*
- *a refactor could change behavior, boundaries, or invariants and you need to plan before touching code*
- *the user explicitly asks to brainstorm, walk through, explore options, or co-author a decision*
- *the task is likely to derail after the first obstacle and continuous execution discipline matters*

Do **NOT** use when:

- *runtime bug with a reproducible failure → use `do-debug`* (this skill is reasoning before execution; `do-debug` is iterative diagnosis with a runtime)
- *reviewing a PR or branch diff for merge → use `do-review`*
- *evaluating received review feedback → use `evaluate-code-review`*
- *the task is fully specified and only execution risk remains — just execute*
- *only summarizing, translating, or relaying already-known facts — no decision under ambiguity, no skill needed*

## Iron Laws (non-negotiable)

1. **Pick the mode FIRST.** Default Solo for answer-or-execute requests. Switch to Interactive on a single trigger: user says "help me think"/"walk through"/"brainstorm"/"let's figure out", **or** stakeholder context is missing, **or** ≥2 viable options remain tied with no agent-owned tie-breaker, **or** Solo Phase C2 stress-test kills every candidate.
2. **Emit the opening contract on the first response** (single line, machine-checkable):
   ```
   Mode: <Solo|Interactive>   Op: <op>   Cynefin: <Clear|Complicated|Complex|Chaotic|Disorder>   Tier: <Low|Medium|High>
   ```
   Where `Op ∈ {SenseMaking, Extraction, Composition, Reshape, GroundedQA, WatchTrigger, Orchestration, SelfVerify}`. Re-emit only if any field changes mid-session.
3. **Ground before hypothesis.** Observations and mechanisms separate from judgments at every phase.
4. **Match effort to Tier** — see `references/foundations/effort-calibration.md`.
5. **Match thinking tools to Op** — `references/foundations/operation-classification.md` governs Phase C1/C2 shape.
6. **Keep ≥3 live options through Phase C only when Op = SenseMaking.** Other ops have op-shaped C1 outputs (filled schemas, outlines, retrieved evidence, trigger specs, sequences, oracle readings).
7. **Stress-test before commit** at Tier Medium or High. The trio is for SenseMaking; other ops use op-specific stress-test focus.
8. **End every session with a concrete next move + op-shaped verification check.**
9. **`frameworks/` is a library** — load on demand from the routing table, never wholesale.
10. **Never silently degrade Interactive into Solo.** If the runtime can't fork, surface the limitation (`references/cross-runtime.md`).

## The 4-phase universal core loop

```
Phase A — Frame      A1 classify domain    ·  A2 classify operation  ·  A3 reframe (if needed)
Phase B — Calibrate  B1 effort tier        ·  B2 minimum grounding (op-aware)
Phase C — Compare    C1 op-specific output ·  C2 op-specific stress-test
Phase D — Commit     D1 choose / produce   ·  D2 verify (op-specific)
```

### Phase A — Frame

- **A1.** Classify the domain (Cynefin) → `references/foundations/domain-classification.md`. Write the domain in the opening contract.
- **A2.** Classify the operation (8 cognitive operations) → `references/foundations/operation-classification.md`. Write the operation in the opening contract. **A2 selects the rest of Phase B and all of Phase C.**
- **A3.** Reframe the real question. Default: skip. Reframe only if A1 returned Disorder, **or** the user's framing fails the why-up test → `references/foundations/reframing.md` (Abstraction Laddering).

**Phase A exit:** opening contract emitted with all four fields; reframe done if needed.

### Phase B — Calibrate

- **B1.** Effort tier (Hard Choice × Confidence-vs-Quality) → `references/foundations/effort-calibration.md`. Output: Low / Medium / High in the opening contract.
- **B2.** Gather the minimum grounding set. Shape varies by Op; see `references/foundations/operation-classification.md` and the workflow file. Falsification ladder when evidence is the bottleneck → `references/foundations/evidence-and-falsification.md`.

**Phase B exit:** tier set; minimum op-shaped evidence collected.

### Phase C — Compare

C1 and C2 are **operation-specific**. Run the workflow for the classified Op.

- **C1.** Produce the op-shaped output. Only **SenseMaking** requires ≥3 candidate verdicts; other ops produce schemas, outlines, invariant plans, evidence, trigger specs, sequences, or oracle readings.
- **C2.** Stress-test before committing at Tier Medium/High. **SenseMaking → mandatory trio** at `references/foundations/stress-test-trio.md`; other ops use the op-specific C2 focus in `operation-classification.md`.

**Mandatory stress-test trio (SenseMaking only):**

| # | Tool | Asks |
|---|---|---|
| 1 | **Inversion** (pre-mortem) | "Assume this fails in 6 months — what was the failure mode?" |
| 2 | **Ladder of Inference rebuild** | "What raw observation supports each judgment? Where did I leap?" |
| 3 | **Second-order effects** | "What does this break that's not on the page? Who else depends on this?" |

If any of the three kills every live option, **escalate to Interactive** (Iron Law #1). Do not silently pick the least-bad option.

**Phase C exit:** op-specific C1 output written **AND** op-specific C2 stress-test written. Outputs are written, not implied.

### Phase D — Commit

- **D1.** Choose the next move (op-shaped): implement / produce / probe / ask one clarifying question / stop.
- **D2.** Verify or revise — every chosen path needs a verification check + a revision trigger. Shape varies by Op (verdict observation for SenseMaking; schema-validator pass for Extraction; audience-decision for Composition; oracle pass for SelfVerify; etc.). Full output contract: `references/foundations/output-contract.md`.

**Phase D exit:** chosen path stated; op-shaped verification check written.

## Mode mechanics

### Solo mode (default)

Agent reasons alone, then acts. Anti-stall and escalation triggers in `references/modes/solo-deep-think.md`. Stay autonomous through blockers via `references/workflows/continuous-execution.md`.

### Interactive mode (user in the loop)

6-step session with 5 forks. Full mechanics: `references/modes/interactive-brainstorm.md`. Fork discipline, one-question-at-a-time, YAGNI, pushback: `references/interaction-patterns.md`.

| Step | Phase | What runs | Fork |
|---|---|---|---|
| 1 — Classify | A1 | Cynefin classifier (3 questions) | **Fork 1**: domain correct? |
| 2 — Decompose | A2 (extended) | `references/frameworks/decomposition-tools.md` or `references/foundations/reframing.md` | **Fork 2**: decomposition captures the problem? |
| 3 — Explore | C1 | `references/frameworks/six-thinking-hats.md` / `references/frameworks/first-principles.md` / `references/frameworks/zwicky-box.md` / `references/frameworks/systems-tools.md` | **Fork 3**: options resonate? |
| 4 — Evaluate | B2 + scoring | Hard Choice classifier → `references/frameworks/decision-matrix.md` (Tier set in Step 1) | **Fork 4**: factors + weights right? |
| 5 — Stress-test | C2 | Op-specific stress-test from `references/foundations/operation-classification.md` (use the SenseMaking trio in `references/foundations/stress-test-trio.md` when `Op: SenseMaking`) | **Fork 5**: blind spots change the pick? |
| 6 — Communicate | D | `references/foundations/output-contract.md` (10-section deliverable) | (none) |

If the Interactive artifact would exceed 3,000 words, re-scope to the highest-risk sub-problem before producing.

## Solo routing — minimum read set by Op

Files listed are the *minimum*; add foundations as Tier escalates.

| Situation (by Op) | Read this set |
|---|---|
| Generic Sense-Making (research, judgment, evaluation) | `references/modes/solo-deep-think.md`, `references/foundations/operation-classification.md`, `references/workflows/sense-making.md`, `references/foundations/stress-test-trio.md` |
| Ambiguous / post-`do-debug` runtime hypothesis (SenseMaking, bug variant) | `references/workflows/bug-tracing.md`, `references/foundations/evidence-and-falsification.md` |
| Recurring / "we already fixed this" (SenseMaking, systemic) | `references/workflows/recurring-issue.md` |
| Structured Extraction (mess → schema) | `references/workflows/structured-extraction.md` |
| Generative Composition (artifact, doc, code feature) | `references/workflows/generative-composition.md` |
| Reshape & Repurpose — code (refactor with invariants) | `references/workflows/refactor-thinking.md` |
| Reshape & Repurpose — text/data | `references/foundations/operation-classification.md` (Op 4 inline) |
| Grounded Q&A (corpus answer with citations) | `references/workflows/grounded-qa.md` |
| Watch & Trigger (design the trigger conditions) | `references/foundations/operation-classification.md` (Op 6 inline) |
| Cross-System Orchestration (sequence design) | `references/foundations/operation-classification.md` (Op 7 inline) |
| Iterative Self-Verification (write → test → fix with oracle) | `references/workflows/iterative-self-verification.md` |
| Planning a complex task (any Op) | `references/workflows/task-planning.md`, `references/foundations/stepwise-reasoning.md` |
| Staying autonomous through blockers (any Op) | `references/workflows/continuous-execution.md` |
| Especially high-stakes / hard-to-reverse (any Op) | + `references/foundations/ultrathinking.md` |

## Output contracts

- **Solo SenseMaking** — Minto Pyramid: first sentence = verdict, body = 3–5 evidence-backed arguments, last sentence = verification check.
- **Solo non-SenseMaking ops** — use the workflow file's output contract: Extraction schema/provenance, Composition artifact/provenance, Reshape diff/invariants, GroundedQA answer/citations, WatchTrigger trigger spec, Orchestration sequence, or SelfVerify oracle log.
- **Interactive mode** — 10-section contract: Approach / Problem shape / Decomposition / Options explored / Evaluation / Assumptions / Blind spots / Second-order effects / Ranked summary / Recommended next step.

Full spec: `references/foundations/output-contract.md`.

## Voice discipline (literal forms)

- `Mode: <Solo|Interactive>`
- `Op: <SenseMaking|Extraction|Composition|Reshape|GroundedQA|WatchTrigger|Orchestration|SelfVerify>`
- `Cynefin: <domain>` · `Tier: <Low|Medium|High>`
- `Live options: 1) … 2) … 3) …` (in C1, *only* when `Op: SenseMaking`)
- `Filled schema:` / `Outline:` / `Retrieved evidence:` / `Trigger spec:` / `Sequence:` / `Oracle reading:` (in C1, op-specific)
- `Pre-mortem failure mode: …` (in C2, *only* when `Op: SenseMaking`)
- `Coverage: …` / `Form-substance match: …` / `Hallucination scan: …` / etc. (in C2, op-specific)
- `Verification check: …` (in D2)

## Session completion contract

Every finished session states:
- chosen next move or produced artifact
- assumptions that matter
- risks/blind spots, plus rollback when `Tier: High`
- op-shaped verification check
- handoff target when another skill should continue

## Anti-patterns

- Acting on the first plausible explanation
- Skipping Phase A1 (Cynefin) because the prompt feels straightforward
- Skipping Phase A2 (Op classification) and defaulting to SenseMaking for everything
- Running the SenseMaking stress-test trio on a non-SenseMaking operation
- Forcing ≥3 options on a task that isn't SenseMaking (Extraction wants completeness, Composition wants outline-fit)
- Letting one attractive option kill comparison too early (in SenseMaking)
- Treating Phase C2 as ceremonial when it's load-bearing
- Stopping after the first obstacle when better local moves still exist
- Claiming success before stating the (op-shaped) verification result
- Silently degrading Interactive into Solo
- Reading all `frameworks/*`, or loading more than one decomposition + one generation + one evaluation/stress tool in a single pass
- Asking the user a clarifying question mid-Solo (you've hit an escalation trigger — switch to Interactive instead)

## Rationalization checks

- If classification, stress-test, or verification feels obvious, write it anyway.
- High stakes raise Tier; Interactive still needs a mode gate.
- The trio is SenseMaking-only; other ops use op-shaped C2 checks.
- If every candidate dies, switch modes or hand off. Do not pick the least-bad path silently.

## Escalation gates

- **Solo → Interactive** when: all candidates/attempts die in C2 stress-test, **or** user-flagged, **or** auto-detected (missing stakeholder context, ≥2 tied options).
- **Interactive → Solo** never silently — only on explicit user request.
- **Out to `do-debug`** when: the task is a runtime bug with a reproducible failure, **or** a `do-think` session produces a testable runtime hypothesis.
- **Out to `check-completion`** when: declared "done" but unsure what's actually verified.
- **Do NOT recommend `do-think` as the next-step** (no infinite regress). If more thinking is needed, name the sub-topic and explicitly hand off.

### `do-debug` route-back handoff

When this session — especially one entered from `do-debug` after 3 failed fixes — produces a falsifiable runtime hypothesis, hand back to `do-debug` with: `symptom card / observed failure`, `failed-fix summary if known`, `selected hypothesis + mechanism`, `falsification experiment`, `narrow next diagnostic or fix boundary`, and `verification check`.

## Reference routing — master table

Foundations are self-sufficient. `frameworks/` is a library accessed from this table, Interactive mode, or an operation workflow that explicitly names the framework.

### Foundations (load-bearing primitives)

| File | Read when |
|---|---|
| [`references/foundations/core-loop.md`](references/foundations/core-loop.md) | Always — the 4-phase loop with opening contract |
| [`references/foundations/domain-classification.md`](references/foundations/domain-classification.md) | Phase A1 — Cynefin classifier |
| [`references/foundations/operation-classification.md`](references/foundations/operation-classification.md) | Phase A2 — the 8 cognitive operations + per-op routing |
| [`references/foundations/reframing.md`](references/foundations/reframing.md) | Phase A3 — Abstraction Laddering when framing is wrong or A1 returned Disorder |
| [`references/foundations/effort-calibration.md`](references/foundations/effort-calibration.md) | Phase B1 — Hard Choice × Confidence-vs-Quality |
| [`references/foundations/evidence-and-falsification.md`](references/foundations/evidence-and-falsification.md) | Phase B2 + Phase C2 — evidence ladder, falsification, Ladder of Inference rebuild |
| [`references/foundations/stepwise-reasoning.md`](references/foundations/stepwise-reasoning.md) | When tempted to leap from symptom to cause |
| [`references/foundations/stress-test-trio.md`](references/foundations/stress-test-trio.md) | Phase C2 *for SenseMaking* — Inversion + Ladder + Second-Order |
| [`references/foundations/ultrathinking.md`](references/foundations/ultrathinking.md) | Tier High — irreversible / one-shot / broad blast radius |
| [`references/foundations/output-contract.md`](references/foundations/output-contract.md) | Always — SenseMaking Minto, op-shaped Solo contracts, 10-section Interactive |

### Modes

| File | Read when |
|---|---|
| [`references/modes/solo-deep-think.md`](references/modes/solo-deep-think.md) | Mode = Solo — autonomous loop, anti-stall, escalation triggers |
| [`references/modes/interactive-brainstorm.md`](references/modes/interactive-brainstorm.md) | Mode = Interactive — 6-step + 5-fork mechanics |

### Workflows (operation-specific recipes)

| File | Op | Read when |
|---|---|---|
| [`references/workflows/sense-making.md`](references/workflows/sense-making.md) | SenseMaking | Generic research / judgment / evaluation |
| [`references/workflows/bug-tracing.md`](references/workflows/bug-tracing.md) | SenseMaking (bug variant) | Ambiguous / post-`do-debug` runtime hypothesis framing |
| [`references/workflows/recurring-issue.md`](references/workflows/recurring-issue.md) | SenseMaking (systemic) | "We already fixed this and it's back" — Iceberg + Connection Circles |
| [`references/workflows/structured-extraction.md`](references/workflows/structured-extraction.md) | Extraction | Mess → schema (transcript → todos, invoice → ledger) |
| [`references/workflows/generative-composition.md`](references/workflows/generative-composition.md) | Composition | Context + form → artifact (cover letter, RFP, deck, code feature) |
| [`references/workflows/refactor-thinking.md`](references/workflows/refactor-thinking.md) | Reshape (code) | A refactor where invariants must survive |
| [`references/workflows/grounded-qa.md`](references/workflows/grounded-qa.md) | GroundedQA | Question + corpus → cited answer |
| [`references/workflows/iterative-self-verification.md`](references/workflows/iterative-self-verification.md) | SelfVerify | Write → test → fix loop with deterministic oracle |
| [`references/workflows/task-planning.md`](references/workflows/task-planning.md) | (universal) | A large or fuzzy task that needs slicing |
| [`references/workflows/continuous-execution.md`](references/workflows/continuous-execution.md) | (universal) | Need to keep moving without frequent human checkpoint |

### Frameworks (selection-capped library)

Selection rule: at most one decomposition tool, one generation tool, and one evaluation/stress tool per pass. In Solo, load no framework unless C1 generation or C2 evaluation needs it. In Interactive, Steps 2–5 each pick one primary framework.

| File | Read when |
|---|---|
| [`references/frameworks/six-thinking-hats.md`](references/frameworks/six-thinking-hats.md) | Phase C1 needs perspective rotation; Interactive Step 3 |
| [`references/frameworks/zwicky-box.md`](references/frameworks/zwicky-box.md) | Phase C1 generator is dry — combinatorial generation |
| [`references/frameworks/first-principles.md`](references/frameworks/first-principles.md) | Analogies are failing; suspect inherited assumptions |
| [`references/frameworks/decomposition-tools.md`](references/frameworks/decomposition-tools.md) | Issue Trees / Ishikawa for problem decomposition |
| [`references/frameworks/decision-matrix.md`](references/frameworks/decision-matrix.md) | Phase C2 with ≥3 options + multiple weighted factors; Hard Choice classifier |
| [`references/frameworks/systems-tools.md`](references/frameworks/systems-tools.md) | Connection Circles + Reinforcing/Balancing Loops — feedback dynamics |
| [`references/frameworks/productive-thinking-drive.md`](references/frameworks/productive-thinking-drive.md) | Defining success criteria with the DRIVE check |
| [`references/frameworks/interpersonal-tools.md`](references/frameworks/interpersonal-tools.md) | SBI for feedback content; Conflict Resolution Diagram for stakeholder conflict |

### Cross-cutting (Interactive infrastructure)

| File | Read when |
|---|---|
| [`references/interaction-patterns.md`](references/interaction-patterns.md) | Interactive mode — fork discipline, one-question-at-a-time, YAGNI, pushback |
| [`references/cross-runtime.md`](references/cross-runtime.md) | Interactive on a non-Claude runtime — ask-user tool lookup + prose fallback |

## Final test

Before acting, ask: *Do I know enough to make the next move safer and clearer than acting immediately would be?* If not, gather the smallest missing evidence first.
