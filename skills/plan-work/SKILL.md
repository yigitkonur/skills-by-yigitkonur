---
name: plan-work
description: Use skill if you are framing a vague request, comparing approaches, prioritizing a backlog, or defining risks, checkpoints, and decision criteria before acting.
---

# Plan Work

Use this skill to turn ambiguous or high-stakes work into a decision, sequence, or safe-to-learn experiment.

## Trigger boundaries

Use it when the main deliverable is:
- a clearer problem frame
- a decision with trade-offs
- a ranked or sequenced backlog
- a risk-aware execution plan
- a root-cause hypothesis for a recurring issue

Do not use it as a substitute for:
- external information gathering (`run-research`)
- code writing or refactoring (`build-*`, `develop-*`)
- PR review (`review-*`)
- debugging or verification (`debug-*`, `test-*`)

If another skill owns execution, use this skill to structure the decision first, then hand off.

## Operating stance

1. Frame before fix.
2. Use the smallest method stack that improves clarity.
3. Match analysis depth to reversibility, evidence quality, and blast radius.
4. Prefer a concrete recommendation or next experiment over abstract discussion.
5. Always separate facts, assumptions, unknowns, and preferences.

## Reference router

Start with one file. Add a second only when it answers a different question.

| Need | Start with | Add only if |
|---|---|---|
| Vague, broad, or conflicting request | `references/01-intake-and-framing.md` | `references/09-thinking-methods-catalog.md` if method choice is unclear |
| Recurring failure or root-cause dispute | `references/02-root-cause-and-problem-solving.md` | `references/05-systems-thinking.md` if system effects dominate |
| Comparing options, technology, or architecture | `references/03-option-design-and-decision-quality.md` | `references/06-technical-strategy-and-architecture.md` for ADRs or technical strategy |
| Backlog overload or sequencing | `references/04-prioritization-and-sequencing.md` | `references/08-execution-risk-and-learning.md` if changing conditions threaten delivery |
| Side effects across teams or systems | `references/05-systems-thinking.md` | `references/07-communication-and-alignment.md` if alignment is the real bottleneck |
| Stakeholder alignment or decision communication | `references/07-communication-and-alignment.md` | `references/01-intake-and-framing.md` if goals or scope are still fuzzy |
| Execution risk, checkpoints, retros, or pivot triggers | `references/08-execution-risk-and-learning.md` | `references/04-prioritization-and-sequencing.md` if scope cuts or re-sequencing are needed |
| Unsure which thinking method fits | `references/09-thinking-methods-catalog.md` | the single domain file that matches the actual planning job |

## Default workflow

### 1. Classify the planning job

Pick one dominant job first:
- frame the problem
- diagnose a cause
- compare options
- prioritize work
- align people
- de-risk execution

State it explicitly: `This is primarily a ___ decision/problem.`

Do not try to run every planning mode at once.

### 2. Frame the mission before proposing solutions

Capture:
- mission sentence: `We need to ___ so that ___ within ___ constraints.`
- success criteria and failure signals
- constraints and non-negotiables
- facts vs. assumptions
- scope: in / out / unknown

Stop here and do not recommend a plan yet if any of these are true:
- the decision-maker is unknown
- success cannot be observed
- 3+ core 5W2H questions are unanswered
- critical unknowns have no owner or resolve-by date

If blocked, return a decision-ready gap list instead of pretending the plan is ready.

### 3. Choose the smallest useful method

Use one primary method. Add one companion only if it closes a clear gap.

| Situation | Use | Avoid |
|---|---|---|
| Several measurable options | Decision matrix | Hard choice model unless the real conflict is values |
| Values or principles conflict | Hard choice model | Fake precision with weighted scores |
| Single incident | 5 Whys | Full systems mapping unless evidence says the cause is systemic |
| Recurring or multi-cause issue | Iceberg / Ishikawa / hypothesis-driven RCA | Stopping at `human error` or `bad communication` |
| Backlog overload | RICE or Impact-Effort, then MoSCoW for scope | Heavy scoring when the list is small or the data is fictional |
| Fast-changing execution | OODA + confidence-based pacing | Long upfront optimization loops |
| Executive communication | Minto Pyramid | Leading with background instead of the recommendation |

Method rule: if the first method already makes the choice clear, stop. Do not stack extra frameworks just to look rigorous.

### 4. Build enough evidence, not maximum evidence

Use evidence in this order:
1. local context (artifacts, prior attempts, observed behavior)
2. direct signals (current outcomes, constraints, failure signatures)
3. external research only when it can change the decision

Depth rules:
- **Type 2 / reversible / low-blast-radius decisions:** bias to action. Recommend the simplest safe experiment and a short feedback loop.
- **Type 1 / hard-to-reverse / high-blast-radius decisions:** require 2-4 viable options, explicit criteria, risks, fallback, and a review date.
- **Urgent but unclear situations:** make bounded assumptions, label them, and choose the smallest reversible step that will generate better evidence.
- If new evidence is not changing the recommendation, stop researching.

For technical work, understand current system behavior before recommending structural change.

### 5. Decide, prioritize, or diagnose

Apply the output shape that matches the job:
- **Decision:** include the selected option, why it wins, and why the others do not.
- **Prioritization:** force trade-offs. If more than 60% of items are `Must`, rework the categories.
- **Root cause:** trace to a system cause that can be changed, not just a symptom or person.
- **Execution planning:** define phases, dependencies, owners, checkpoints, verification, and pivot triggers.

Always include a minimal or fallback option.

### 6. Package the answer for action

Deliver two layers unless the user asks otherwise:
1. **Decision brief:** recommendation, why now, biggest trade-off, immediate next step.
2. **Execution detail:** phases, owners, dependencies, verification, risk controls, and review cadence.

Lead with the recommendation for decision-makers. Lead with sequence and ownership for executors.

## Anti-derail guardrails

| Do this | Not that |
|---|---|
| Start with one reference file and one method | Load all references or stack 4 methods up front |
| Label assumptions and unknowns explicitly | Smuggle guesses in as facts |
| Use reversibility to decide how much analysis is enough | Wait for certainty on a reversible decision |
| Timebox framing and comparison work | Research forever because one more artifact might appear |
| Switch to a simpler method when a framework adds no clarity | Keep a method running because you already started it |
| End with checkpoints, pivot triggers, and verification | End with vague advice like `monitor progress` |
| Hand off to the execution skill once the plan is decision-ready | Keep planning after the useful planning work is done |

## Recovery paths

- If the request stays vague after framing, return:
  - a mission draft
  - the top missing inputs
  - the next best questions
  - the reference file to open first
- If options remain tied, use reversibility as the tiebreaker and choose the easier-to-undo path.
- If debate is really about values, stop scoring and switch to the hard choice model.
- If conditions change faster than the plan, shift into OODA + checkpoint/pivot mode via `references/08-execution-risk-and-learning.md`.
- If a plan depends on unknowns you cannot resolve yet, recommend a safe-to-learn experiment or an explicit research task instead of a fake commitment.

## Output contract

Unless the user asks otherwise, respond in this order:

1. Mission Snapshot
2. Planning Job + Chosen Method(s)
3. Facts, Assumptions, and Unknowns
4. Root Cause, Decision Frame, or Priority Logic
5. Options or Ranked Work
6. Recommendation and Why Not the Alternatives
7. Execution Plan
8. Risks, Checkpoints, Pivot Triggers, and Verification
9. Immediate Next Actions or Open Questions

## Done conditions

Planning is complete when:
- the problem or decision is stated in one sentence
- the chosen method is justified
- the recommendation or next experiment is clear
- trade-offs are visible
- verification and revisit conditions exist
- unresolved unknowns are explicit, owned, and time-bounded

If you cannot meet those conditions, stop with a decision-ready gap list instead of pretending the plan is complete.

## Final quality gate

Before finalizing, check:

- [ ] Are we solving the right problem?
- [ ] Did we choose the smallest useful method?
- [ ] Are facts, assumptions, and unknowns clearly separated?
- [ ] Did we match analysis depth to reversibility and risk?
- [ ] Are trade-offs and rejected alternatives visible?
- [ ] Does the answer include verification, checkpoints, and pivot triggers where needed?
- [ ] Is the plan communicated in the right order for the audience?

If any answer is `no`, revise before finalizing.

## Final reminder

Do not load every reference by default. Start with the single best-matching file above, add one more only if it answers a new question, and stop planning once the next action is decision-ready.
