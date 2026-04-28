# Interactive Brainstorm Mode

User-in-the-loop variant of the core loop. The 4-phase Phase A → D structure is preserved, but each phase ends in a **fork** where the user approves, redirects, or expands. Five forks total.

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
| **Step 1** — Classify | A1 | Cynefin classifier (3 questions to user) | **Fork 1**: domain correct? Route right? |
| **Step 2** — Decompose | A2 (extended) | `frameworks/decomposition-tools.md` (Issue Trees / Ishikawa / Iceberg / Abstraction Laddering) — pick one based on problem signature | **Fork 2**: decomposition captures the problem? Branches missing? |
| **Step 3** — Explore | C1 | `frameworks/six-thinking-hats.md` / `first-principles.md` / `zwicky-box.md` / `systems-tools.md` — generate ≥3 options | **Fork 3**: options resonate? Add / drop / expand? |
| **Step 4** — Evaluate | B1 (deferred) + scoring | Hard Choice Model classifier → Decision Matrix / Impact-Effort / Eisenhower (`frameworks/decision-matrix.md`) | **Fork 4**: factors + weights right? Anything over- or under-weighted? |
| **Step 5** — Stress-test | C2 | `foundations/stress-test-trio.md` — Inversion + Ladder + Second-Order, all three | **Fork 5**: blind spots change the pick? Loop back? |
| **Step 6** — Communicate | D | `foundations/output-contract.md` — assemble the 10-section deliverable | (no fork — final output) |

Note the Phase mapping: in Interactive, calibration (B1) shifts to Step 4 because the Hard Choice classifier wraps the entire evaluation; the user explicitly weighs in on tier via the matrix.

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
| Step 5 (Stress-test) | `foundations/stress-test-trio.md` (Inversion, Ladder of Inference, Second-Order) |
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
- [ ] Decomposition approved at Fork 2
- [ ] ≥3 options presented at Fork 3
- [ ] Evaluation factors + weights approved at Fork 4
- [ ] Stress-test trio (Inversion + Ladder + Second-Order) all run at Step 5; user responded at Fork 5
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
