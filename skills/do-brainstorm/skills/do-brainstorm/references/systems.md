# Systems Thinking — Loops and Concept Maps

Used in Step 2 or Step 3 when the problem has **dynamics over time** — feedback, compounding, resistance to change — rather than static structure. Three tools: Connection Circles for mapping, Reinforcing/Balancing Feedback for classifying loops, and Concept Map for surfacing mental models of unfamiliar systems.

## When systems thinking applies

Signals the problem needs a systems lens:

- Small interventions produce outsized effects ("we pushed one button and everything broke")
- Interventions get absorbed ("we've tried 5 fixes and the problem keeps coming back")
- Exponential trends (growth or decline that's accelerating)
- Plateaus (metric stops improving despite continued effort — something's balancing)
- Delayed effects (action now, effect in 6 months)
- Counter-intuitive behavior ("we added more engineers and velocity went down")

If none of these apply, stick to Issue Trees / Ishikawa in `decompose.md`. Systems thinking is load-bearing but overused — don't reach for it when static decomposition would do.

## Connection Circles

**When**: you've decomposed (Issue Trees / Ishikawa) and notice the causes aren't independent — they cycle back on each other.

**Mechanics**:

1. Draw a circle. Place 5-10 **elements** around it. Rules:
   - Each element must be able to increase or decrease (noun with a measurable quantity)
   - Each element must be important to changes in the system
   - Cap at ~10 — more becomes unreadable
2. Draw arrows between elements where one directly causes the other to change.
3. Label each arrow with **"+"** (if the source increases the target) or **"−"** (if the source decreases the target).
4. Look for **closed loops** — chains of arrows that cycle back to their start. Each closed loop is a feedback loop.

**Output** (inline text or mermaid):

```
Elements: unhappy_customers, bugs, response_time, support_tickets, new_features

Relationships:
  unhappy_customers  →(+) support_tickets
  support_tickets    →(+) response_time
  response_time      →(+) unhappy_customers         ← closes loop 1 (reinforcing)

  new_features       →(−) unhappy_customers          ← counteracts loop 1
  new_features       →(+) bugs
  bugs               →(+) unhappy_customers          ← undermines new_features' help

Loop 1 (reinforcing): unhappy → tickets → slow response → unhappier
Loop 2 (balancing via feature work): new features reduce unhappiness but increase bugs
```

**What it reveals**: where the **feedback loops** are — the places where leverage is highest.

**Interactions**: operates at the **Structures** level of the Iceberg Model — use Iceberg to decide *whether* to map at this level, Connection Circles to actually map it. Feeds **Reinforcing/Balancing Feedback** (below) for classifying each loop.

## Reinforcing Feedback Loops

**What**: a loop where each cycle **amplifies** the previous — exponential growth (virtuous) or exponential decline (vicious).

**Signature**:

```
Variable A increases → Variable B increases → Variable A increases further → ...
```

**Common examples**:

- **Compound interest** (positive direction): balance → more interest earned → higher balance
- **Network effects**: more users → more content → more users
- **Technical debt**: more debt → slower shipping → more pressure → more debt
- **Unhappy customers → support load → slower response → more unhappy customers** (vicious)

**What to do with a reinforcing loop**:

- If virtuous: find the inputs that accelerate it, invest in those
- If vicious: find the weakest link in the cycle; break it there
- Don't try to stop the loop by adding more of the amplifying input — you accelerate the wrong direction

**Beware**: "exponential growth looks linear until it isn't." Reinforcing loops can be invisible for a long time, then explode.

## Balancing Feedback Loops

**What**: a loop that **corrects deviations** from a target — produces stability, pushes back against change.

**Signature**:

```
Variable A moves away from goal → correction applied → Variable A returns to goal
```

**Three elements required**:
- **Goal** — the desired level (often implicit)
- **Actual level** — the measured state
- **Gap** — the difference

The loop fires whenever the gap grows. Finding the implicit **goal** is the key to understanding any balancing loop.

**Common examples**:

- **Thermostat**: room temp drifts → heater kicks on → room warms → heater off
- **Budget variance control**: spending spike → review triggered → spending cut
- **Peer review**: dip in quality → more scrutiny → quality recovers
- **Team capacity**: velocity rises → scope creeps → overload → velocity drops (stability around a medium level)

**What to do with a balancing loop**:

- If useful (stabilizing something good): don't break it; understand what it's protecting
- If resisting your intervention (you're trying to change something the loop defends): find the goal, negotiate the goal before the change, OR disable the correction mechanism

**Beware**: "why aren't my improvements sticking?" is almost always a balancing loop defending the old state.

## Systems: loops combine

Real systems have **both** loop types. Diagnose by mapping:

- Reinforcing loop alone → exponential; system eventually breaks
- Balancing loop alone → stable; system doesn't respond to input
- Both present → dynamic equilibrium (most realistic)

**Intervention strategy**:

- Identify the loop type first
- For reinforcing: accelerate virtuous, break vicious at the weakest edge
- For balancing: surface the goal; the goal is often what needs to change, not the mechanism

## Concept Map

**When**: learning or brainstorming on an unfamiliar system; workshop with multiple people whose mental models might diverge; identifying gaps in your own understanding before committing.

**Mechanics**:

1. Formulate a **focus question**: "How does X work?" / "What's the context in which Y exists?"
2. List 15-25 **entities** — people, places, organizations, actions, processes, activities.
3. Sort from most general to most specific (hierarchy hint).
4. Place on a board. Connect with lines labeled with **linking verbs**: "contributes to", "is made of", "creates", "conflicts with".
5. Rule: any two connected entities should read as a meaningful sentence (e.g., "Designer creates a concept map"). If they don't, the linking verb is wrong.
6. Iterate. Gaps in knowledge that surface must be filled before continuing.

**Output**:

```
Focus question: How do sharing permissions work in this product?

Entities + relationships:
  User  [has role]  → Permission Tier
  Permission Tier  [grants]  → Action
  Document  [belongs to]  → Workspace
  Workspace  [has]  → User[]
  Action  [applies to]  → Document
  User  [can perform]  → Action   (derived via Permission Tier + Workspace membership)
  Invitation  [elevates]  → User's Permission Tier   (temporary)
```

**What it reveals**: structure and hierarchy; gaps in the author's or team's understanding; disagreements across team members on what a term means.

**Interactions**: different from Connection Circles — Concept Map shows **static structure**; Connection Circles show **dynamics over time**. Use Concept Map when onboarding; Connection Circles when diagnosing recurring dynamic problems.

## When to use which

| Situation | Tool |
|---|---|
| Recurring problem, one-off fixes absorbed | Iceberg (`decompose.md`) → Connection Circles → classify loops |
| "We added X and the opposite of X started happening" | Connection Circles + look for reinforcing loops |
| "We keep trying but the metric plateaus" | Balancing feedback loop — find the implicit goal |
| "I don't understand this system enough to brainstorm" | Concept Map to build the model, then proceed |
| Static problem; no feedback dynamics | Skip systems thinking; stick to Issue Trees |

## Output for Fork 2 (when systems tools were used)

If you used systems tools in Step 2 instead of (or alongside) plain decomposition, surface:

```
## Decomposition (systems view)

Systems tool: <Connection Circles / Concept Map>

<Entities + relationships inline>

Loops identified:
- Loop 1 (reinforcing): <elements around the cycle>
- Loop 2 (balancing): goal=<implicit goal>, correction=<mechanism>

Priority leverage points:
- <where to intervene in Loop 1 to break/accelerate it>
- <whether the implicit goal in Loop 2 is what needs to change>

Does this capture the system dynamics? Missing relationships or loops?
```

## Common mistakes

| Mistake | Fix |
|---|---|
| Treating a loop as linear cause-effect | If tracing the arrows returns to the start, it's a loop — use systems terminology |
| Trying to break a reinforcing loop by adding more input | You accelerate the direction; break at the weakest edge instead |
| Intervening on a balancing loop without finding the goal | The loop defends the goal — changes get absorbed; surface the goal first |
| Mapping 30 elements in one Connection Circle | Cap at ~10; decompose the system into sub-systems if it's larger |
| Running Connection Circles on a static problem | Overkill; Issue Trees are lighter. Feedback loops are only useful when dynamics matter |
| Mistaking Concept Map (static) for Connection Circles (dynamic) | Different purposes: Concept Map for understanding; Connection Circles for loop-hunting |
