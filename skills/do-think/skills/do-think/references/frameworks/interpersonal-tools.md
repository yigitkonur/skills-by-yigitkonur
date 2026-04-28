# Interpersonal Tools — SBI and Conflict Resolution Diagram

Library entry. Routed from the SKILL.md master table or `modes/interactive-brainstorm.md` Step 6 (when feedback content or stakeholder conflict surfaces).

These are niche tools for `do-think` — most thinking sessions don't need them. Reach when the brainstorm's deliverable is a **conversation** with someone, not a code change.

## Situation-Behavior-Impact (SBI)

### When

The brainstorm involves feedback — on a teammate's work, on a past decision, on a process. Common when Step 2 (decompose) surfaced "this team ships without QA" and the next step is a conversation, not a fix.

### Structure

1. **Situation** — the specific context. Concrete: when, where, what meeting.
2. **Behavior** — what was *observed*. Observable, not inferred. ("Missed three of the last four deadlines" not "doesn't care about deadlines.")
3. **Impact** — what the behavior caused. On you, on the team, on downstream stakeholders.
4. **Intent** (optional but recommended) — ask what their intention was. Often there's a legitimate reason you haven't seen.

### Output

```
## Feedback framing (SBI)

Situation: In the last four Wednesday standups (Oct-Nov 2024)…
Behavior: …release timelines were marked green while bugs found in prod counted as
          post-release issues in the changelog…
Impact: …which caused on-call pages every release night and burned 8+ engineering-hours
        per cycle reacting to what could have been a pre-release decision.
Intent (ask): What was the intent in marking those timelines green? Were there pressures
              outside the standup visibility?
```

### What it reveals

The gap between the giver's interpretation and the actor's intent. Avoids character-based feedback; stays actionable.

### Interactions

Pairs with `foundations/evidence-and-falsification.md` Ladder of Inference — SBI forces you to separate observations (available data) from interpretations. If your SBI "behavior" is actually an interpretation, the Ladder would have caught it.

## Conflict Resolution Diagram (Evaporating Cloud)

### When

The brainstorm surfaces a conflict between stakeholders — "engineering wants X, product wants Y, and they're mutually exclusive." Common in architecture brainstorms where two teams have incompatible demands.

### Principle

Conflicts dissolve when you find the **shared higher-level goal** and the **underlying needs** behind each position. Most "mutually exclusive" positions aren't — they're mutually exclusive given a specific set of constraints that were never examined.

### Structure (right-to-left in the diagram, top-to-bottom in the conversation)

```
         Shared goal
        /           \
   Need A             Need B
      |                 |
 Proposal A       Proposal B (mutually exclusive)
```

### Mechanics

1. **Proposals** — what each side wants to do. Confirm they seem mutually exclusive.
2. **Needs** — what needs does each proposal satisfy? Underlying, not surface.
3. **Shared goal** — what higher-level objective do both need-sides pursue? Both must agree.
4. **Assumptions** — why do the two sides believe the proposals are mutually exclusive? Examine each.
5. **Reframed solution** — a new proposal that meets both underlying needs and serves the shared goal.

### Output

```
## Conflict resolution

Parties: engineering (X), product (Y)

Proposals:
  X: Freeze new feature work for 6 weeks; pay down debt.
  Y: Ship the holiday campaign feature on time.

Needs:
  X: Prevent cascading incidents; sustainable velocity.
  Y: Meet a customer commitment; hit quarterly revenue target.

Shared goal: Sustainable, profitable growth over the next 12 months.

Assumptions (examining):
  - X assumes all incidents trace to debt. Actually 2 of 4 traced to config drift.
  - Y assumes the full feature must ship on Dec 1. Minimum viable = login + 1 banner variant.

Reframed: Ship MVP version of the feature by Dec 1 (meets Y's commitment). In parallel,
dedicate 30% capacity to top 3 debt items (meets X's need). Full feature lands by Dec 20.
```

### What it reveals

Assumptions that *manufactured* the conflict. The shared goal usually exists; the assumptions made it invisible.

### Interactions

Pairs with `frameworks/six-thinking-hats.md` (Yellow + Black) — both surface what each side wants and why the current framing fails. Also with `frameworks/first-principles.md` — conflicts often dissolve when assumed constraints aren't first principles.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| SBI with "behavior" that's actually interpretation | "Behavior" is observable. "Doesn't care" is interpretation; "missed three deadlines" is behavior. |
| Conflict diagram diagnosed at the proposal level | Go to needs + shared goal. Proposal-level argument loops. |
| Giving feedback in the abstract ("be more careful") | SBI it. Specific situation + specific behavior + specific impact. Generic feedback triggers defensiveness without action. |
| Reframing a conflict by splitting the difference | Splitting ≠ reframing. The reframed solution must meet *both* underlying needs, not compromise on the proposals. |
