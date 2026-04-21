# Communicate (Step 6 — Present and Commit)

The brainstorm ends by producing structured output. This file covers how to present it — Minto Pyramid for the structure, Situation-Behavior-Impact for any feedback-shaped content, and Conflict Resolution Diagram when the brainstorm revealed stakeholder tension.

The required section order is in `output-format.md`. This file covers the voice, framing, and communication patterns.

## Minto Pyramid — conclusion first

**When**: always, for the final output contract. Busy readers skip the middle; the headline must land in the first section.

**Principle**: lead with the conclusion. Then the reasons. Then the supporting detail. BLUF ("bottom line up front").

**Mechanics**:

1. **Start with the conclusion** — what is the recommendation? (Top of the pyramid.)
2. **Key arguments** — 2-4 short summaries of *why* the recommendation holds. (Middle of the pyramid.)
3. **Supporting detail** — the evaluation matrix, decomposition tree, stress-test findings. (Bottom of the pyramid; skimmable.)

**Applied to this skill's output**:

The output-format (in `output-format.md`) is technically "approach → problem shape → decomposition → options → evaluation → assumptions → blind spots → second-order → ranked summary → recommended next step." That ORDER looks bottom-up. But Minto still applies inside each section and in the skim experience:

- **Approach section** is Minto's top layer — reads first, named chosen frameworks + why in ONE paragraph
- **Ranked summary** is the Minto conclusion — restated at the end because the journey matters too
- **Recommended next step** is the call to action — the reader's "what do I do now?"

A reader who skips everything between Approach and Ranked summary should still get the right answer.

## When to use Minto for sub-sections

For each step's output:

- **Step 1 (Classify)**: Lead with the domain. Then the evidence. Not "user said X, Y, Z, therefore Complex" — "Complex domain, because the user said X."
- **Step 2 (Decomposition)**: Lead with the priority branches. Then the full tree as supporting detail.
- **Step 3 (Options)**: Lead with the option labels + one-liner. Then the rationale per option.
- **Step 4 (Evaluation)**: Lead with the winner + total score. Then the matrix as supporting detail.
- **Step 5 (Stress-test)**: Lead with whether the pick changed. Then the artifacts.

Bury no conclusions in prose. Every section has a headline sentence at the top.

## Situation-Behavior-Impact (SBI)

**When**: the brainstorm involves feedback — on a teammate's work, on a past decision, on a process. Common when the "root cause" (Step 2 decomposition) surfaced "this team ships without QA" and the next step is a conversation.

**Structure**:

1. **Situation** — the specific context. Concrete: when, where, what meeting.
2. **Behavior** — what was observed. Observable, not inferred. "Missed three of the last four deadlines" not "doesn't care about deadlines."
3. **Impact** — what the behavior caused. On you, on the team, on downstream stakeholders. "Which made me worry…" or "Which caused the on-call team to absorb…"

**Optional extension — Intent**:

4. **Intent** — ask what their intention was. Often there's a legitimate reason you haven't seen.

**Output example** (for a brainstorm that ends with "give feedback to the release manager"):

```
## Feedback framing (SBI)

Situation: In the last four Wednesday standups (Oct-Nov 2024)...
Behavior: ...release timelines were marked green while bugs found in prod counted as post-release issues in the changelog...
Impact: ...which caused on-call pages every release night and burned 8+ engineering-hours per cycle reacting to what could have been a pre-release decision.
Intent (ask): What was the intent in marking those timelines green? Were there pressures outside the standup visibility?
```

**What it reveals**: the gap between the giver's interpretation and the actor's intent. Avoids character-based feedback; stays actionable.

**Interactions**: Pairs with Ladder of Inference (Step 5) — SBI forces you to separate observations (available data) from interpretations. If your SBI "behavior" is actually an interpretation, Ladder of Inference would have caught it.

## Conflict Resolution Diagram (Evaporating Cloud)

**When**: the brainstorm surfaced a conflict between stakeholders — "engineering wants X, product wants Y, and they're mutually exclusive." Common in architecture brainstorms where two teams have incompatible demands.

**Principle**: conflicts dissolve when you find the shared higher-level goal and the underlying needs behind each position.

**Structure**:

```
          Shared goal
         /           \
    Need A             Need B
       |                 |
  Proposal A       Proposal B (mutually exclusive)
```

**Mechanics** (right-to-left in the diagram, top-to-bottom in the conversation):

1. **Proposals** — what does each side want to do? Write both. Confirm they seem mutually exclusive.
2. **Needs** — what needs does each proposal satisfy? Underlying, not surface.
3. **Shared goal** — what higher-level objective do both need sides pursue? Both sides need to agree on this.
4. **Assumptions** — why do the two sides believe the proposals are mutually exclusive? The assumptions usually turn out to be negotiable.
5. **Reframed solution** — a new proposal that meets both underlying needs and serves the shared goal.

**Output example**:

```
## Conflict resolution (if surfaced)

Parties: engineering (X), product (Y)

Proposals:
  X: Freeze new feature work for 6 weeks; pay down debt.
  Y: Ship the holiday campaign feature on time.

Needs:
  X: Prevent cascading incidents; sustainable velocity.
  Y: Meet a customer commitment; hit quarterly revenue target.

Shared goal: Sustainable, profitable growth over the next 12 months.

Assumptions (examining):
  - X assumes all incidents trace to debt. Actually 2 of the last 4 traced to config drift.
  - Y assumes the full feature must ship on Dec 1. Minimum viable = login + 1 banner variant.

Reframed: Ship MVP version of the feature by Dec 1 (meets Y's commitment). In parallel, dedicate 30% capacity to the top 3 debt items (meets X's need). Full feature lands by Dec 20.
```

**What it reveals**: assumptions that manufactured the conflict. Most "mutually exclusive" positions aren't — they're mutually exclusive given a specific set of constraints that were never examined.

**Interactions**: Pairs with Six Thinking Hats (Step 3) — specifically Yellow (what both sides want) and Black (why the current framing fails). Also with First Principles — conflicts often dissolve when the assumed constraints aren't first principles.

## Voice rules

The output is a technical artifact. Voice rules:

| Do | Don't |
|---|---|
| Lead sections with the conclusion | Bury the conclusion in paragraph 4 |
| Cite evidence per claim | "It seems like…" |
| Flag confidence where low | Uniform confidence across all claims |
| Name the next step concretely | "Consider next steps" |
| Ask an explicit question at the end | "Let me know what you think" |
| Use tables for scoring / ranking | Prose for what's really a table |
| Keep prose dense — one idea per paragraph | Multi-paragraph rambles |

Forbidden phrases (borrowed from `evaluate-code-review/voice.md`):

- "Thanks for the great discussion"
- "Hope this helps"
- "Please feel free to"
- "You're absolutely right" (even when they are)

## Framing the "Recommended next step"

Every session ends with a next-step pointer. Make it concrete — a skill, a command, or a specific decision fork.

Good next-step formats:

- "Run `build-skills` to implement the chosen architecture as a draft."
- "Create a GitHub Issue via `run-issue-tree` with the plan and assign."
- "Open a PR for the migration with the Phase 1 changes; use `request-code-review` to generate the self-review body."
- "Schedule a 30-minute decision meeting with <stakeholders> using the Conflict Resolution Diagram above as the discussion document."
- "Raise confidence on the low-confidence scores in Step 4 by running a cheap benchmark; re-evaluate if the scores move."

Bad next-step formats:

- "Think about it and decide." (not concrete)
- "Implement it." (which skill? what's the artifact?)
- "Let me know." (not actionable)

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Conclusion buried in paragraph 6 of the output | Move to top; Minto structure |
| Next step is "consider" or "think about" | Make concrete: a command, a skill, a specific conversation |
| Final question is "let me know what you think" | Name the explicit fork: "Should we proceed with Option A or run the cheap experiment first?" |
| Feedback content in the output without SBI structure | SBI it; character-based feedback triggers defensiveness |
| Conflict surfaced but diagnosed at the proposal level | Use Conflict Resolution Diagram to go to needs + shared goal |
| Output prose reads like internal monologue | Keep internal monologue internal; surface structured artifacts |
