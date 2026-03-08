---
name: planning
description: Use skill if you need structured planning, prioritization, option analysis, or root-cause framing before acting.
---

# Planning Skill

Use this skill to create plans that are clear, testable, and adaptable.

## Core Promise

You are not writing a task list. You are building decision quality.

1. Frame the right problem.
2. Use the right thinking method for the context.
3. Deliver an execution path with verification and pivot signals.

## Audience & Tone

Write like you are guiding a smart junior teammate.

- Start simple, then add depth.
- Explain why each step exists.
- Define specialized terms in one line.
- Prefer concrete actions over abstract slogans.

## Operating Rules

1. Do not propose solutions before framing.
2. Do not recommend architecture/process changes without evidence.
3. If confidence is low and impact is high, research first.
4. Separate facts, assumptions, and interpretations.
5. Show trade-offs and alternatives.
6. Every plan must contain a verification step.
7. For technical work, explore current system behavior before structural recommendations.

## Reference routing

Load only the files needed for the task.

1. `references/01-intake-and-framing.md`
   - Read when the request is vague, broad, or conflicting.
   - Read when people are proposing solutions before defining the problem.
   - Read when planning quality is low because goals are unclear.

2. `references/02-root-cause-and-problem-solving.md`
   - Read when the same issue keeps recurring.
   - Read when teams disagree on causes.
   - Read when symptoms are repeatedly patched without durable improvement.

3. `references/03-option-design-and-decision-quality.md`
   - Read when multiple options exist.
   - Read when trade-offs are unclear.
   - Read when discussion is preference-driven instead of criteria-driven.

4. `references/04-prioritization-and-sequencing.md`
   - Read when there is more work than capacity.
   - Read when deadlines create pressure and decision fatigue.
   - Read when stakeholders want everything prioritized.

5. `references/05-systems-thinking.md`
   - Read when local fixes create side effects.
   - Read when outcomes emerge from cross-team/tool interactions.
   - Read when problems keep returning in different forms.

6. `references/06-technical-strategy-and-architecture.md`
   - Read when choosing architecture for a new system or major feature.
   - Read when considering structural changes in an existing system.
   - Read when unsure whether complexity is justified.

7. `references/07-communication-and-alignment.md`
   - Read when decisions are made but not understood.
   - Read when stakeholder buy-in is weak.
   - Read when feedback triggers defensiveness.

8. `references/08-execution-risk-and-learning.md`
   - Read when delivery conditions are changing.
   - Read when the plan includes high uncertainty.
   - Read when controlled adaptation is needed instead of rigid execution.

9. `references/09-thinking-methods-catalog.md`
   - Read when methods need to be selected intentionally instead of guessing.
   - Read when better planning quality is needed under uncertainty.
   - Read when brief, use-case-driven guidance is needed for each method.

## Default Workflow

### Step 1) Clarify the mission
Capture:
- target outcome
- constraints
- non-negotiables
- success criteria

Mission sentence format:
“We need to ___ so that ___ within ___ constraints.”

### Step 2) Frame before fix
Use one framing method first:
- First principles
- Abstraction laddering
- Issue trees

Output: problem map, not solution map.

### Step 3) Build evidence
Use three evidence lanes:
1. local context (artifacts, prior attempts, observed behavior)
2. direct signals (current outcomes, bottlenecks, failure signatures)
3. external references (when uncertainty is material)

For technical tasks, explore in this order:
1. map current boundaries
2. trace real flow end-to-end
3. identify constraints and conventions
4. propose changes only after evidence

### Step 4) Diagnose root causes
Use methods such as:
- Ishikawa Diagram
- Iceberg Model
- Inversion
- Ladder of Inference

Output: top likely causes with confidence ratings.

### Step 5) Design options
Create 2-4 viable options.
Use:
- Zwicky box
- Productive Thinking Model
- Conflict Resolution Diagram

Output: options with effort, impact, risk, reversibility.

### Step 6) Decide with trade-offs
Pick decision methods by situation:
- Decision matrix
- Hard choice model
- Second-order thinking
- Cynefin framework
- Six Thinking Hats
- Confidence determines speed vs. quality

Output: chosen option + why alternatives were not selected.

### Step 7) Plan execution
Include:
- phases
- dependencies
- owners
- checkpoints
- verification criteria
- pivot triggers

Use OODA loop when context is volatile.

### Step 8) Align stakeholders
Use:
- Minto Pyramid for decision narrative
- Situation-Behavior-Impact for feedback

Deliver two layers:
1. one-screen summary
2. full execution details

### Step 9) Monitor and learn
Track both:
- balancing loops (stability forces)
- reinforcing loops (amplifying forces)

Adapt scope or sequence when signals change.

## Method Triads by Use Case

Use these quick stacks when speed matters:

- **Ambiguous request** -> First principles + Abstraction laddering + Issue trees
- **Recurring issue** -> Ishikawa + Iceberg + Inversion
- **Hard decision** -> Decision matrix + Second-order thinking + Hard choice model
- **Urgent delivery** -> Impact-Effort + OODA + Confidence determines speed vs. quality
- **Cross-team tension** -> Six Thinking Hats + Conflict Resolution Diagram + SBI
- **Complex ecosystem** -> Concept map + Connection circles + feedback loops

## Output Contract

Unless user asks otherwise, output this structure:

1. Mission Snapshot
2. Problem Framing
3. Evidence and Assumptions
4. Root Causes or Decision Context
5. Options Considered
6. Decision Rationale
7. Execution Plan
8. Risks, Triggers, Contingencies
9. Immediate Next Actions

## Final Quality Gate (Always run before final answer)

- Are we solving the right problem?
- Are assumptions explicit?
- Are method choices justified?
- Are trade-offs visible?
- Is verification concrete?
- Can a junior teammate execute this plan?

If any answer is “no,” revise before finalizing.
