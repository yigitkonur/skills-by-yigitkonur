# Systems Tools — Connection Circles, Reinforcing & Balancing Loops

Library entry. Routed from the SKILL.md master table, `workflows/recurring-issue.md`, or `modes/interactive-brainstorm.md` Step 2/3.

For Iceberg Model (the descend-the-levels tool that pairs with these), see `workflows/recurring-issue.md`.

## When systems thinking applies

Signals the problem needs a systems lens:

- Small interventions produce outsized effects
- Interventions get absorbed ("we've tried 5 fixes; the problem keeps coming back")
- Exponential trends (growth or decline that's accelerating)
- Plateaus (metric stops improving despite continued effort — something's balancing)
- Delayed effects (action now, effect in 6 months)
- Counter-intuitive behavior ("we added more engineers and velocity went down")

If none of these apply, stick to `decomposition-tools.md`. Systems thinking is load-bearing but overused — don't reach for it when static decomposition would do.

## Connection Circles

### Mechanics

1. Identify 5-10 system **elements** — each a noun that can increase/decrease, important to the system, expressible as a measurable quantity. Cap at ~10; more is unreadable.
2. Place elements around an imagined circle.
3. Per ordered pair, ask: does A's increase cause B to increase or decrease? Draw a signed arrow:
   - `→(+)` if source increases target
   - `→(−)` if source decreases target
4. Find **closed loops** — chains of arrows that cycle back to their start. Each closed loop is a feedback loop.

### Output (inline text)

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

### What it reveals

Where the **feedback loops** are — the places where leverage is highest. LLMs are linear by default; this tool exposes circular causality the linear model misses.

## Reinforcing Feedback Loops

### Signature

```
Variable A increases → Variable B increases → Variable A increases further → ...
```

Exponential growth (virtuous) or exponential decline (vicious). Pattern compounds at accelerating rates — humans (and LLMs) underestimate this.

### Common examples

- **Compound interest** (virtuous): balance → interest earned → higher balance
- **Network effects** (virtuous): more users → more content → more users
- **Technical debt** (vicious): more debt → slower shipping → more pressure → more debt
- **Customer churn cascade** (vicious): unhappy customers → support load → slower response → more unhappy customers

### Intervention

- **Virtuous**: find inputs that accelerate it; invest in those.
- **Vicious**: find the **weakest link** in the cycle; break it there. Do NOT try to stop the loop by adding more of the amplifying input — you accelerate the wrong direction.

### Beware

"Exponential growth looks linear until it isn't." Reinforcing loops can be invisible for a long time, then explode.

## Balancing Feedback Loops

### Signature

```
Variable A moves away from goal → correction applied → Variable A returns to goal
```

Three elements required:
- **Goal** — the desired level (often *implicit*)
- **Actual level** — the measured state
- **Gap** — the difference

The loop fires whenever the gap grows. **Finding the implicit goal is the key** to understanding any balancing loop.

### Common examples

- **Thermostat**: room temp drifts → heater kicks on → room warms → heater off
- **Budget variance control**: spending spike → review triggered → spending cut
- **Peer review**: dip in quality → more scrutiny → quality recovers
- **Team capacity**: velocity rises → scope creeps → overload → velocity drops (stability around a medium level)

### Intervention

- **Useful balancing loop** (stabilizing something good): don't break it; understand what it's protecting.
- **Resisting your intervention** (you're trying to change something the loop defends): find the goal; **negotiate the goal** before changing the mechanism. Most "improvements that don't stick" are balancing loops defending the old state.

## Loops combine in real systems

| Combination | Behavior |
|---|---|
| Reinforcing alone | Exponential; system eventually breaks |
| Balancing alone | Stable; system doesn't respond to input |
| Both present | Dynamic equilibrium (most realistic) |

### Intervention strategy

- Identify the loop type first
- For reinforcing: accelerate virtuous, break vicious at the weakest edge
- For balancing: surface the goal; the goal is often what needs to change, not the mechanism

## Interactions

- Operates at the **Structures** level of the Iceberg Model (see `workflows/recurring-issue.md`). Use Iceberg to decide whether to map at this level; Connection Circles to actually map.
- Different from `decomposition-tools.md` (Issue Trees / Ishikawa) which model static structure. Systems tools model dynamics over time.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Treating a closed loop as linear cause-effect | If tracing arrows returns to the start, it's a loop — use feedback-loop terminology, not "X causes Y." |
| Trying to break a reinforcing loop by adding more input | You accelerate the direction. Break at the weakest edge. |
| Intervening on a balancing loop without finding the goal | The loop defends the goal — your changes get absorbed. Find the goal first. |
| Mapping 30 elements in one Connection Circle | Cap at ~10. Decompose into sub-systems if larger. |
| Running Connection Circles on a static problem | Overkill. Use `decomposition-tools.md`. Systems tools are for dynamics. |
