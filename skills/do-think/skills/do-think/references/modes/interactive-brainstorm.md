# Interactive Brainstorm Mode

User-in-the-loop variant of the core loop. The 4-phase Phase A → D structure is preserved as a 6-step session with 5 user forks (steps 1-5 each end in a fork; step 6 emits the final output without a fork).

This was previously the standalone `do-brainstorm` skill; it now lives inside `do-think` as one of two operating modes.

## When to use

Switch to Interactive (from Solo's default) when any of:
- The user said "help me think", "walk through", "brainstorm", "let's figure out", "let's explore"
- The user is present AND the decision is high-stakes / hard-to-reverse
- ≥2 viable options have no obvious winner AND the user is reachable
- Solo Phase C2 stress-test killed all three options (escalation gate)
- The decision requires the user's domain knowledge / stakeholder context

## Cross-runtime requirement

Interactive needs an ask-user tool. Look up the runtime's tool name in `references/cross-runtime.md`. If the runtime has no ask-user tool, fall back to prose (template in `cross-runtime.md`). **Do not silently degrade Interactive into Solo** — the user is in the loop or they aren't; degrading without telling them breaks the contract.

## The five forks

The 4-phase loop maps to a 6-step session with 5 forks (the original `do-brainstorm` workflow, now realized inside `do-think`):

| Step | Phase | What runs | Fork question |
|---|---|---|---|
| **Step 1** — Classify + Calibrate | A1 + A2 + B1 | Cynefin classifier (3 questions to user) **plus** Op classification (1 question if not obvious from the user's prompt) **plus** Hard Choice × Confidence-vs-Quality tiering (1-2 questions). The opening contract `Mode: Interactive  Op: <op>  Cynefin: <domain>  Tier: <tier>` is emitted at the close of this step. | **Fork 1**: domain + op + tier all correct? Route right? |
| **Step 2** — Decompose (+ A3 reframe if needed) | A3 + decomposition | `frameworks/decomposition-tools.md` (Issue Trees / Ishikawa / Abstraction Laddering / Iceberg via `workflows/recurring-issue.md`) — pick one based on problem signature; if the user's framing fails the why-up test, run Abstraction Laddering first, re-emit contract if A1/A2 changed | **Fork 2**: decomposition captures the problem? Branches missing? |
| **Step 3** — Explore | C1 | Op-appropriate generators (when `Op: SenseMaking`: Six Thinking Hats / First Principles / Zwicky Box / systems-tools — generate ≥3 options. For other Ops, generate the op-appropriate C1 output: filled-schema-draft for Extraction, outline + assumption list for Composition, retrieved evidence for GroundedQA, etc.) | **Fork 3**: outputs resonate? Add / drop / expand? |
| **Step 4** — Evaluate | B2 (op-specific grounding) + scoring | When `Op: SenseMaking`: Hard Choice classifier → Decision Matrix / Impact-Effort / Eisenhower (`frameworks/decision-matrix.md`). For other Ops: op-specific evaluation per the workflow file (e.g., schema-fit verification for Extraction, form-substance match for Composition). | **Fork 4**: factors + weights right? Anything over- or under-weighted? |
| **Step 5** — Stress-test | C2 | **Op-specific stress-test** from `foundations/operation-classification.md`. When `Op: SenseMaking`: the trio in `foundations/stress-test-trio.md` (Inversion + Ladder of Inference + Second-Order). For other Ops: that op's C2 axes (Extraction → coverage + edge + schema-fit; Composition → form-substance + voice + audience; GroundedQA → hallucination scan + citation completeness + out-of-scope flag; SelfVerify → loop bound + oracle accuracy + escape condition; etc.) | **Fork 5**: blind spots change the pick? Loop back? |
| **Step 6** — Communicate | D | `foundations/output-contract.md` — assemble the 10-section deliverable | (no fork — final output) |

Note the Phase mapping: in Interactive, the opening contract's four fields (Mode/Op/Cynefin/Tier) are all set in Step 1 — A1 (Cynefin) and A2 (Op) are user-facing classifier questions, and B1 (Tier) follows from the Hard Choice × Confidence-vs-Quality answers. A3 (reframe) is conditional and runs at the start of Step 2 only when the framing fails the why-up test. B2 grounding is gathered op-specifically during Steps 2-4.

## Fork mechanics

Each fork:

- **Pause** — stop, dispatch the ask-user tool with a single, focused question (or up to 4 questions per call when truly parallel; see `references/interaction-patterns.md`).
- **Surface** — show the user the artifact for that step (the classification, the decomposition tree, the option list, the matrix, the trio synthesis).
- **Wait** — do not proceed until the user answers. Do not silently pick.
- **Redirect** — if the user wants to change something, loop back to the appropriate step.

See `references/interaction-patterns.md` for one-question-at-a-time discipline, multi-choice via ask-user-tool, and the compressed-fork patterns when the user is time-pressed.

## Skip-fork policy

The user may push to skip a fork. Response varies by fork:

| Fork | Skip-request response |
|---|---|
| Fork 1 (Classify) | **Refuse skip**. Classification is load-bearing; picking frameworks without it is operating blind. "Let me get 30 seconds of classification; it changes which tools we use." |
| Fork 2 (Decompose) | **Compress, don't skip**. Show 3-bullet decomp; ask y/n to move on. |
| Fork 3 (Explore) | **Compress, don't skip**. Show 1-line per option; ask "any missing?" |
| Fork 4 (Evaluate) | **Compress, don't skip**. Show matrix; ask "any weights wrong?" |
| Fork 5 (Stress-test) | **Refuse skip** if reversibility-cost > "fully reversible." Skipping stress-test on irreversible decisions is the skill failing. |

If the user pushes hard after a refuse-skip, comply but explicitly flag the skip in the output contract: "Note: Step 5 was skipped at user request; this recommendation has not been pre-mortemed."

## Hard gate — no implementation before output

Even "simple" brainstorms surface assumptions that change the plan. Do not skip to implementation before the output contract is produced. The session ends with a concrete next step — that next step may be implementation, but the brainstorm produces the *plan*, not the *change*.

## Output

Interactive mode produces the **10-section contract** (per `foundations/output-contract.md`):

```markdown
# <Topic>

## Approach
## Problem shape (Cynefin)
## Decomposition
## Options explored
## Evaluation
## Assumptions
## Blind spots
## Second-order effects
## Ranked summary
## Recommended next step
```

In progressive mode (default), sections emit after their step. In one-shot mode, all sections emit at the end.

Every session ends with:
- A **ranked summary** table
- A **recommended next step** with a concrete follow-on (a skill, a command, a specific decision)
- An **explicit user question** at the next fork — never "let me know what you think"

## YAGNI discipline

Every option, weight, factor, branch in the decomposition — if you cannot defend its presence, drop it. YAGNI ruthlessly. See `references/interaction-patterns.md` for signs of YAGNI violation.

## Frameworks library access (Steps 2-5)

Interactive steps 2-5 dispatch into the frameworks library:

| Step | Library files |
|---|---|
| Step 2 (Decompose) | `frameworks/decomposition-tools.md` (Issue Trees, Ishikawa) · `frameworks/systems-tools.md` (Iceberg, Connection Circles) · `foundations/reframing.md` (Abstraction Laddering) |
| Step 3 (Explore) | `frameworks/six-thinking-hats.md` · `frameworks/first-principles.md` · `frameworks/zwicky-box.md` · `frameworks/systems-tools.md` |
| Step 4 (Evaluate) | `frameworks/decision-matrix.md` (Decision Matrix, Impact-Effort, Eisenhower, Hard Choice classifier) |
| Step 5 (Stress-test) | `foundations/operation-classification.md` (per-op C2 focus) · `foundations/stress-test-trio.md` (Inversion, Ladder of Inference, Second-Order — only when `Op: SenseMaking`) |
| Step 6 (Communicate) | `foundations/output-contract.md` (Minto + 10-section) · `frameworks/interpersonal-tools.md` (SBI, Conflict Resolution Diagram — when feedback or stakeholder conflict surfaced) |

Meta-pacing for the session itself (when pacing wrong, when full execution plan needed, when speed-vs-quality posture must be explicit): `frameworks/productive-thinking-drive.md`.

## Recovery moves

| Situation | Recovery |
|---|---|
| Step 1 answers don't fit Cynefin cleanly | Run Abstraction Laddering (`foundations/reframing.md`) to reset framing, then re-classify |
| Fork 3 reveals decomposition was wrong | Loop back to Step 2 with the new understanding; don't paper over |
| Evaluation reveals no option is acceptable | Revisit Step 3 with a different generative tool (e.g., switch from Six Hats to Zwicky Box), or expand constraints |
| User pushes for implementation mid-session | Hold the gate; offer to compress remaining steps but not skip them. If user insists, comply but explicitly state which sections were skipped |
| Session crosses 60+ minutes / becomes unwieldy | Stop, produce a partial output contract covering what ran, flag incomplete sections, point at the next skill or a follow-up session |

## Final checks

Before declaring the Interactive session done, confirm:

- [ ] Cynefin classification confirmed at Fork 1
- [ ] **Op classification confirmed at Fork 1** (the most consequential setting — selects the rest of the loop)
- [ ] **Tier set at Fork 1** so the opening contract carries all four fields
- [ ] Decomposition approved at Fork 2
- [ ] Op-appropriate ≥3 outputs presented at Fork 3 (≥3 options for SenseMaking; outline + assumptions for Composition; filled-schema-draft for Extraction; etc.)
- [ ] Evaluation factors + weights approved at Fork 4
- [ ] **Op-specific stress-test** run at Step 5 (trio when `Op: SenseMaking`; per-op C2 axes otherwise); user responded at Fork 5
- [ ] Output contract includes all 10 sections (Approach / Problem shape / Decomposition / Options / Evaluation / Assumptions / Blind spots / Second-order / Ranked summary / Recommended next step)
- [ ] Recommended next step names a specific follow-on skill or concrete action
- [ ] Explicit user question at the end — not "let me know"
- [ ] No infinite-regress recommendation (don't recommend `do-think` Interactive as the next step)

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Silently resolving a fork and presenting the conclusion | Always pause at forks; compressed if pressed, never skipped if irreversible |
| Bundling 5 open-ended questions in one message | One per message for open-ended; bundle only multiple-choice via the ask-user tool |
| Skipping Step 5 because the recommendation "looks obvious" | The trio is exactly when the formulaic check catches the blind spot the intuition missed |
| Burying the conclusion in section 6 of the output | Minto: Approach + Ranked summary near the top of skim path |
| Pointing the next-step at "do-think Interactive" again | Infinite regress. Name a concrete follow-on (a `build-*` skill, `run-issue-tree`, `ask-review`, direct implementation) |
| Silently degrading Interactive into Solo when ask-user tool fails | Use the prose fallback in `cross-runtime.md`; never skip a fork |
