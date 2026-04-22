---
name: do-brainstorm
description: Use skill if you are brainstorming before committing — architecture decisions, debugging direction, scoping research, prioritization, or exploring a solution space with the user in the loop.
---

# Do Brainstorm

A framework-aware, user-in-the-loop brainstorming session. Not a feature-design linear flow (see obra/brainstorming) and not solo reasoning (see the repo's `do-think` skill). This skill classifies the problem first (Cynefin), then routes to the right combination of 25 mental-model frameworks, pausing at forks to bring the user along.

## Trigger boundary

Use this skill when the task is to:

- **architect a decision** — two or more plausible designs; tradeoffs matter
- **find a direction in a stuck debug** — the next step isn't obvious
- **scope an ambiguous task** — unclear where to start, what's in/out
- **prioritize under constraint** — more options than bandwidth
- **explore a solution space** before committing to implementation
- **root-cause a recurring problem** — one-off fixes haven't worked

Prefer another skill when:

- a specific design is already agreed → go implement (`build-*`, `develop-*`)
- a PR exists to evaluate → `do-review` (or the companion `evaluate-code-review` skill if installed)
- the task is narrowly "design this feature before coding it" with no exploration needed → direct design + skip this skill
- the agent is reasoning alone with no user in the loop → `do-think`
- the work is executing pre-decided tasks at scale → `run-issue-tree`

## Non-negotiable rules

1. **HARD GATE** — do not skip to implementation before the session produces its output contract. Even "simple" brainstorms surface assumptions that change the plan.
2. **Classify before routing.** Step 1 (Cynefin) runs first, always. Frameworks selected in Steps 2-5 depend on the classification.
3. **Pause at every fork.** Five fork points total (end of Steps 1-5). User approves or redirects at each. Do not silently resolve forks unilaterally.
4. **One question at a time** when asking open-ended. Bundle multiple-choice questions via the runtime's ask-user tool (see `references/cross-runtime.md`) — up to 4 per call, 2-4 options each, `(Recommended)` first.
5. **Deep passes run internally; structured output surfaces.** Apply frameworks inside each step; show the user the artifacts (tree, options, evaluation table, pre-mortem) — not your internal monologue.
6. **YAGNI ruthlessly.** Every option, weight, or constraint must earn its place. If you cannot justify why something is in the session, drop it.
7. **Surface assumptions, blind spots, second-order effects.** These are required sections in the output contract — not optional flourishes.
8. **Every session ends with a concrete next step + an explicit user question.** Not "let me know what you think" — name the fork.

## The two output modes

| Mode | Trigger phrasing | Produces |
|---|---|---|
| **Interactive** (default) | "Let's brainstorm X", "Help me think through Y" | Full 6-step session with pauses; output emitted progressively |
| **One-shot** | "Give me a brainstorm doc on X", "Run the full brainstorm and hand me the result" | Runs Steps 1-6 without pauses; produces the full output contract as a single markdown deliverable; user reviews at the end instead of at each fork |

Default to interactive. Switch to one-shot only when the user explicitly asks for a deliverable without mid-session involvement.

## Required workflow

### 1. Classify the problem (Cynefin first)

Before picking tools, classify. Dispatch **one** ask-user-tool call with up to 3 questions:

- "What shape is this problem?" — options: design decision / root-cause hunt / prioritization / novel exploration / stabilizing a crisis
- "How clear is cause-effect here?" — options: fully understood / multiple plausible paths / unknown unknowns / genuinely chaotic
- "How reversible is the outcome?" — options: fully reversible / adjustable / costly to reverse / one-shot

Map answers to Cynefin domain. See `references/classify-problem.md` for the full decision table.

| Domain | Routes to |
|---|---|
| **Clear** — known best practice applies | Decline politely: "This has a standard answer — recommend X. Brainstorm not needed." |
| **Complicated** — multiple known-unknowns, analysis will resolve | Step 2 (decompose → analyze) |
| **Complex** — unknown unknowns, probe to learn | Steps 2 lite + 3 (explore → iterate) |
| **Chaotic** — in crisis, stabilize first | Step 2 lite + Step 4 (triage with Hard Choice Model) |
| **Disorder** — you can't tell which domain | Run Abstraction Laddering first, then re-classify |

**FORK 1:** Show the user the classification + proposed route. Ask: "Does this read right? Anything that changes the shape?"

### 2. Decompose (surface the real problem)

Pick the decomposition tool based on the Cynefin domain + problem symptoms. See `references/decompose.md`.

| Symptom | Tool |
|---|---|
| Problem is a why/how chain | **Issue Trees** (MECE; ask why for problem, ask how for solutions) |
| Multi-factor root cause across categories | **Ishikawa** (fishbone; people/methods/tools/environment) |
| Recurring issue, surface fixes failed | **Iceberg Model** (events → patterns → structures → mental models) |
| Problem statement feels wrong | **Abstraction Laddering** (climb up with "why", down with "how") |

Surface the decomposition inline as markdown (tree, table, or bulleted hierarchy).

**FORK 2:** "Does this decomposition capture the problem? Missing branches? Wrong level of abstraction?"

### 3. Explore (generate options)

Pick generative tools based on what the session needs. See `references/explore.md` (and `references/systems.md` for systems-specific problems).

| Need | Tool |
|---|---|
| Perspective diversity | **Six Thinking Hats** (White/Red/Black/Yellow/Green/Blue — use Blue to orchestrate, Green to generate, Black to attack) |
| Reason from foundations, escape analogy traps | **First Principles** + Socratic questioning |
| Novel combinations across multiple dimensions | **Zwicky Box** (morphological analysis — dimensions × values → combinations) |
| System / feedback-loop dynamics | **Connection Circles** + **Reinforcing/Balancing Feedback** (see `systems.md`) |

Generate **≥3 options**. Each option gets: one-line label, 2-3 sentence rationale, key tradeoff, and which Cynefin domain it suits best.

**FORK 3:** "Which of these resonates? Should I expand one, drop one, add a new one, or widen the search?"

### 4. Evaluate (score + filter)

Use `references/evaluate.md`. First classify the decision shape with the Hard Choice Model:

| Impact | Comparability | Approach |
|---|---|---|
| Low | Easy | Just pick — optimizing wastes time |
| Low | Hard | Pick by current priorities; don't overthink |
| High | Easy | **Decision Matrix** — factors + weights + scores |
| High | Hard | **Decision Matrix** + run a cheap experiment; accept there is no "right" answer |

For prioritization across many options: **Impact-Effort Matrix** (quick wins → major projects → fill-ins → thankless); **Eisenhower Matrix** for time-allocation subsets.

Emit an evaluation table. Scores explicit. Weights explicit. Confidence flagged.

**FORK 4:** "Are the factors + weights right? Anything I'm undervaluing or overvaluing?"

### 5. Stress-test (blind spots + second-order)

Always run all three. See `references/stress-test.md`.

- **Inversion** (pre-mortem): "If this fails in 6 months, what went wrong?" List the plausible failures, then propose mitigations.
- **Ladder of Inference**: climb down from the recommendation to the raw observations, then back up. What data was selected? What was interpreted? What was assumed?
- **Second-Order Thinking**: 10-minute / 10-month / 10-year timeline. What happens *after* the first-order win?

Surface: **Assumptions**, **Blind spots**, **Second-order effects** as explicit sections — required in the output contract.

**FORK 5:** "Any of these change the pick? Should we revisit an earlier step?"

### 6. Communicate + commit (Minto structure)

Produce the full output (see `references/output-format.md`). Minto-style: conclusion + ranking near the end AFTER the full thinking, but **Approach** section at the top gives the fast skim.

Every session ends with:

- A **ranked summary** table
- A **recommended next step** with the right next-skill or action pointer (e.g., `build-skills` to implement, `run-issue-tree` to plan, `run-research` to gather more evidence, direct implementation, or the companion `ask-review` skill if installed)
- An **explicit user question** naming the next fork — not "let me know what you think"

## Output contract

Every session produces this structure. In interactive mode, sections emit progressively (after their step). In one-shot mode, all at once.

```markdown
# <Brainstorm topic>

## Approach
Chosen frameworks: <list>. Why: <one-sentence rationale per>.

## Problem shape (Cynefin)
Domain: <Clear / Complicated / Complex / Chaotic / Disorder>
Evidence: <what the user said in Step 1>.

## Decomposition
<tree / table / hierarchy from Step 2>

## Options explored
<list of ≥3 options with rationale and tradeoffs from Step 3>

## Evaluation
<table with factors, weights, scores, confidence from Step 4>

## Assumptions
- <explicit, load-bearing>
- ...

## Blind spots
- <what the process likely missed>
- ...

## Second-order effects
- 10 minutes: <...>
- 10 months: <...>
- 10 years: <...>

## Ranked summary
| # | Option | Score / Rationale | Confidence | Notes |

## Recommended next step
<Concrete action + which skill or tool to use next>.
**Your input needed on:** <specific question at the next fork>.
```

## Do this, not that

| Do this | Not that |
|---|---|
| classify with Cynefin first, always | pick a framework because it's your favorite |
| pause at the 5 forks, show the user the output of each step | silently resolve forks and present the conclusion |
| generate ≥3 options before converging | propose one option and ask if it's good |
| always run Inversion + Ladder of Inference + Second-Order | skip stress-testing because the recommendation "looks obvious" |
| surface assumptions explicitly as a section | bury assumptions in prose |
| point to the right follow-on skill at the end | end with "let me know what you think" |
| bundle clarifying questions via the ask-user tool, ≤4 per call | fire 10 open-ended questions in one message |
| scale section detail to complexity | 500 words on a 2-line decision |
| deep-pass frameworks internally, surface structured output | narrate your internal monologue as the output |

## Guardrails and recovery

- Do not pick frameworks before the Cynefin classification is confirmed at Fork 1.
- Do not compress the 5 forks into fewer. If the user explicitly asks for one-shot, honor it — otherwise pause at each.
- Do not skip Step 5 (stress-test). Every session runs Inversion + Ladder of Inference + Second-Order.
- Do not terminate without a named next-step skill or action.
- Do not propose `do-brainstorm` again as the next step — that's infinite regress. If more brainstorming is truly needed, name the sub-topic and explicitly hand off.

Recovery moves:

- **User's Step 1 answers don't fit Cynefin cleanly** — run Abstraction Laddering first to reframe, then re-classify. Say so explicitly.
- **Fork 3 reveals the decomposition was wrong** — loop back to Step 2 with the new understanding, don't paper over.
- **Evaluation reveals no option is acceptable** — revisit Step 3 with a different generative tool (if Six Hats was used, try Zwicky Box), or expand the constraints.
- **User pushes for implementation mid-session** — hold the gate; offer to compress remaining steps but not skip them. If they insist, comply but explicitly state which sections were skipped.
- **Session crosses 60+ minutes or becomes unwieldy** — stop, produce a partial output contract covering what ran, flag incomplete sections, point at the next skill or a follow-up session.

## Reference routing

| File | Read when |
|---|---|
| `references/classify-problem.md` | Running Step 1 — Cynefin classification questions + decision table + Disorder → Abstraction-Laddering escape |
| `references/decompose.md` | Running Step 2 — Issue Trees / Ishikawa / Iceberg / Abstraction Laddering; picking the right tool for the problem's shape |
| `references/explore.md` | Running Step 3 — Six Thinking Hats / First Principles / Zwicky Box; generating ≥3 options |
| `references/systems.md` | Step 2 or 3 when the problem has feedback dynamics — Connection Circles + Reinforcing/Balancing Feedback + Concept Map |
| `references/evaluate.md` | Running Step 4 — Hard Choice Model classifier + Decision Matrix + Impact-Effort + Eisenhower |
| `references/stress-test.md` | Running Step 5 — Inversion (pre-mortem) + Ladder of Inference + Second-Order Thinking |
| `references/communicate.md` | Running Step 6 — Minto Pyramid output structure + Situation-Behavior-Impact for feedback situations + Conflict Resolution Diagram for stakeholder conflicts |
| `references/meta.md` | When the session itself needs adjustment — OODA Loop for pacing + Productive Thinking Model for innovation tasks + Confidence-determines-Speed/Quality for speed-vs-quality calls |
| `references/interaction-patterns.md` | Unsure when to pause, how to phrase a question, or whether to push back when the user wants to skip a fork — includes the "one question at a time" discipline |
| `references/output-format.md` | Writing the final deliverable — exact section templates, Minto ordering, ranked-summary column rules |
| `references/cross-runtime.md` | Running on a non-Claude runtime — compact ask-user-tool table, portability notes, and prose fallback; mirrors the lookup convention from the sibling `enhance-prompt` skill |

## Final checks

Before declaring the session done, confirm:

- [ ] Cynefin classification confirmed at Fork 1
- [ ] Decomposition approved at Fork 2
- [ ] ≥3 options presented at Fork 3
- [ ] Evaluation factors + weights approved at Fork 4
- [ ] Inversion + Ladder of Inference + Second-Order all run at Step 5; user responded at Fork 5
- [ ] Output contract includes Approach / Problem shape / Decomposition / Options / Evaluation / Assumptions / Blind spots / Second-order / Ranked summary / Recommended next step
- [ ] Recommended next step names a specific follow-on skill or concrete action
- [ ] Explicit user question at the end — not "let me know"
- [ ] No infinite-regress recommendation (don't recommend `do-brainstorm` as the next step)
