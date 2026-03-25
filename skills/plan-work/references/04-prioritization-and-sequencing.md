# Prioritization and Sequencing

## Read this if
- There is more work than capacity.
- Deadlines create pressure and decision fatigue.
- Stakeholders want everything prioritized.
- You need a defensible, repeatable way to say "not now" to good ideas.
- Sequencing decisions keep getting revisited without resolution.

## Planning vision for this stage
Think in constrained optimization: maximize useful outcomes under limited attention and time.
Every "yes" is an implicit "no" to something else. Make those trade-offs explicit and traceable.

## Prioritization flow

1. List all candidate tasks.
2. Estimate impact, urgency, effort, and risk.
3. Rank with explicit method (see frameworks below).
4. Commit to what is deferred — write it down, communicate it.
5. Build dependency-aware sequence.
6. Set WIP limits to protect throughput.
7. Review and re-rank at a fixed cadence.

---

## Provisional sequencing fallback

Use this when the user needs an ordering now, the work is still reversible, and the framing step still has open gaps.

1. Return the gap list first.
2. State the assumptions that make the ordering valid.
3. Force-rank by:
   - dependency and unblock value
   - reversibility
   - learning value
   - time-sensitivity that is grounded in real constraints
4. Name the signal that would move any item up or down.

Do not use RICE, ICE, or weighted scores with invented inputs. If the evidence is thin, use a forced-rank or High/Medium/Low tiers and explain the basis.

### Provisional sequence template

| Rank | Item | Why now | Assumptions | What would move it |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

## Prioritization frameworks

### Eisenhower Matrix
Best for urgency vs importance separation.
- Thinking posture: "Protect important work from urgent noise."

| | **Urgent** | **Not Urgent** |
|---|---|---|
| **Important** | Do now — crises, deadlines, blockers | Schedule — strategy, prevention, growth |
| **Not Important** | Delegate — interrupts, most emails, some meetings | Drop — busywork, low-value habits |

**How to use it:**
1. Place every candidate task into one of the four quadrants.
2. Timebox Quadrant 1 (urgent + important) — if everything lives here, your system is reactive.
3. Protect Quadrant 2 (important + not urgent) — this is where leverage lives.
4. Actively push Quadrant 3 work to others or batch it into fixed windows.
5. Eliminate Quadrant 4 ruthlessly.

**Anti-patterns:**
- Everything classified as urgent + important → you have a prioritization problem, not a capacity problem.
- Quadrant 2 is always empty → you are firefighting and never investing.

---

### Impact-Effort Matrix
Best for backlog shaping.
- Thinking posture: "Quick wins first, strategic bets phased, low-value work cut."

| | **Low Effort** | **High Effort** |
|---|---|---|
| **High Impact** | **Quick Wins** — do first | **Big Bets** — plan and phase |
| **Low Impact** | **Fill-ins** — do if capacity allows | **Money Pit** — avoid or kill |

**Scoring guide:**

| Impact Level | Description | Example |
|---|---|---|
| High | Moves a key metric ≥10%, unblocks multiple teams, or is required for a milestone | Launch payment integration |
| Medium | Improves workflow, reduces friction, or addresses a known pain point | Add bulk export feature |
| Low | Cosmetic, marginal improvement, or benefits a tiny audience | Rename internal admin labels |

| Effort Level | Description | Example |
|---|---|---|
| Low | ≤2 days, one person, no cross-team coordination | Fix typo in error message |
| Medium | 3–10 days, may need design or review | Build new API endpoint |
| High | >2 weeks, multi-team, needs architecture or migration | Re-platform search infrastructure |

---

### RICE Scoring Framework
Best for comparing a large backlog of features or initiatives with quantitative rigor.
- Thinking posture: "Score objectively, compare apples to apples, debate the inputs not the ranking."

**Formula:**

```
RICE Score = (Reach × Impact × Confidence) / Effort
```

| Component | Definition | Scale |
|---|---|---|
| **Reach** | Number of users/customers affected per quarter | Actual number (e.g., 500, 10000) |
| **Impact** | How much this moves the needle per user | 3 = massive, 2 = high, 1 = medium, 0.5 = low, 0.25 = minimal |
| **Confidence** | How sure you are about the estimates | 1.0 = high (100%), 0.8 = medium (80%), 0.5 = low (50%) |
| **Effort** | Person-months of work required | Decimal (e.g., 0.5, 1, 3, 6) |

**Worked example:**

| Item | Reach (users/qtr) | Impact | Confidence | Effort (person-mo) | RICE Score |
|---|---|---|---|---|---|
| Onboarding redesign | 5000 | 2 | 0.8 | 3 | **2667** |
| API rate limit alerts | 200 | 3 | 1.0 | 0.5 | **1200** |
| Dark mode | 8000 | 0.5 | 0.8 | 2 | **1600** |
| SSO integration | 300 | 3 | 0.8 | 4 | **180** |
| In-app changelog | 4000 | 0.25 | 0.5 | 0.5 | **1000** |

**Interpretation:** Onboarding redesign scores highest despite being the most effort because it reaches 5000 users with high impact. SSO scores lowest per-unit-effort — consider deferring or finding a lighter implementation.

**When RICE works well:** Product teams comparing 10+ feature candidates. Cross-functional prioritization where "gut feel" causes conflict.

**When RICE breaks down:** All items have similar reach (use ICE instead). Effort estimates are unreliable. Strategic alignment matters more than score.

---

### ICE Scoring
Best for fast, lightweight prioritization when reach is uniform or unknown.
- Thinking posture: "Simple scores, fast decisions, revisit often."

**Formula:**

```
ICE Score = Impact × Confidence × Ease
```

All three dimensions scored on a 1–10 scale.

| Component | 1 (Low) | 5 (Medium) | 10 (High) |
|---|---|---|---|
| **Impact** | Negligible improvement | Noticeable improvement | Transformative |
| **Confidence** | Pure guess | Some data or precedent | Strong evidence |
| **Ease** | Months of work, high risk | Weeks, moderate complexity | Days, straightforward |

**ICE vs RICE — when to use which:**

| Dimension | ICE | RICE |
|---|---|---|
| Speed | Fast — three subjective scores | Slower — needs reach data |
| Reach awareness | No — assumes uniform reach | Yes — explicit reach dimension |
| Best for | Growth experiments, A/B test backlog, internal tools | Product roadmaps, cross-team prioritization |
| Risk | Bias toward easy wins | Can over-index on reach |
| Team size | Solo or small team | Larger teams needing shared framework |

---

### MoSCoW Method
Best for scope negotiation within a fixed timebox (sprint, release, quarter).
- Thinking posture: "Protect the core, negotiate the edges, name what's out."

| Category | Definition | Budget Target |
|---|---|---|
| **Must have** | Core requirements — delivery fails without these | ~60% of capacity |
| **Should have** | Important but the release is viable without them | ~20% of capacity |
| **Could have** | Nice-to-have, included only if time permits | ~20% of capacity |
| **Won't have (this time)** | Explicitly out of scope for this cycle | 0% — but documented |

**Rules:**
1. Every item must be categorized — no "uncategorized" pile.
2. "Won't have" is mandatory — if nothing is in Won't, you haven't prioritized.
3. Must-haves are non-negotiable on scope but negotiable on approach (simplify, phase, reduce fidelity).
4. Should-haves are the first to defer if Must-haves slip.
5. Re-evaluate at mid-cycle: promote Shoulds if ahead, demote Coulds if behind.

**Anti-patterns:**

| Anti-pattern | Symptom | Fix |
|---|---|---|
| Everything is Must | 90%+ items in Must category | Force-rank Musts, move bottom 30% to Should |
| No Won't category | Stakeholders refuse to defer anything | Require at least 3 Won't items per cycle |
| Static lists | MoSCoW set once, never revisited | Review at every sprint boundary |
| Category inflation | "Should" used as polite "Must" | Define clear consequences: "If this drops, what breaks?" |

---

### Weighted Scoring Model
Best for multi-criteria decisions where different factors matter differently to different stakeholders.
- Thinking posture: "Make the criteria and weights explicit so debates are productive."

**Template:**

1. Define 3–5 scoring criteria.
2. Assign weights (must sum to 100%).
3. Score each item 1–5 on each criterion.
4. Multiply scores by weights and sum.

**Example — prioritizing platform investments:**

| Criterion | Weight | Item A: Cache Layer | Item B: Auth Revamp | Item C: Admin Dashboard |
|---|---|---|---|---|
| Revenue impact | 30% | 4 (1.2) | 3 (0.9) | 2 (0.6) |
| User satisfaction | 25% | 3 (0.75) | 5 (1.25) | 4 (1.0) |
| Engineering cost | 20% | 5 (1.0) | 2 (0.4) | 3 (0.6) |
| Strategic alignment | 15% | 3 (0.45) | 5 (0.75) | 2 (0.3) |
| Risk reduction | 10% | 2 (0.2) | 4 (0.4) | 3 (0.3) |
| **Weighted Total** | **100%** | **3.60** | **3.70** | **2.80** |

Scores in parentheses = raw score × weight. Auth Revamp edges out Cache Layer despite higher engineering cost because of strong user satisfaction and strategic alignment.

---

### Confidence determines speed vs. quality
Best for selecting delivery posture.
- Thinking posture: "High uncertainty → learn faster; high certainty → execute cleaner."

| Confidence | Posture | Approach |
|---|---|---|
| Low (<40%) | Explore | Spike, prototype, user interview — spend effort on learning, not building |
| Medium (40–70%) | Iterate | Ship MVP, measure, adjust — accept rework as the cost of learning |
| High (>70%) | Execute | Full build, optimize for quality — rework here is waste |

---

### OODA Loop
Best for dynamic contexts where conditions change faster than plan cycles.
- Thinking posture: "Short cycles, fast corrections."

**Observe → Orient → Decide → Act**, then repeat.

| Phase | Action | Example |
|---|---|---|
| **Observe** | Gather fresh data — metrics, user feedback, competitor moves | "Churn spiked 15% this week" |
| **Orient** | Interpret in context — what changed, what matters | "Spike correlates with pricing page update" |
| **Decide** | Choose response — commit to one path | "Revert pricing page, run A/B test" |
| **Act** | Execute with a defined timebox | "Ship revert today, design test by Thursday" |

**Cycle length guidance:**
- Crisis / incident: minutes to hours
- Growth experiments: 1–2 weeks
- Product planning: 2–4 weeks
- Strategy: quarterly

---

### Second-order thinking (sequencing guard)
Best for avoiding local optimization.
- Thinking posture: "How does this priority choice affect future optionality?"

**Questions to ask before committing to a sequence:**
1. If we do A first, does it make B easier or harder?
2. What doors close if we defer C another quarter?
3. Does this create a dependency that constrains future choices?
4. Are we optimizing for this sprint at the cost of next quarter?

---

## WIP Limits

Limiting work-in-progress is the single highest-leverage process improvement for most teams.

**Why WIP limits work:**
- Context switching has a ~20% overhead per additional concurrent task.
- Finishing one thing is worth more than starting three things.
- Bottlenecks become visible when WIP is constrained.

**Little's Law:**

```
Cycle Time = WIP / Throughput
```

If your team completes 5 items/week (throughput) and has 15 items in progress (WIP), average cycle time is 3 weeks. Cut WIP to 10 → cycle time drops to 2 weeks with the same throughput.

**Recommended WIP limits:**

| Team Size | Per-Person WIP | Team WIP | Notes |
|---|---|---|---|
| 1 (solo) | 1–2 | 1–2 | Focus is your only advantage |
| 2–4 (small) | 1–2 | 3–6 | Allow one "blocked" slot per person |
| 5–8 (medium) | 1–2 | 5–10 | Pair on complex items to reduce WIP further |
| 9+ (large) | 1 | 8–12 | Sub-teams with independent WIP limits |

**Implementation:**
1. Count current WIP (everything "in progress" right now).
2. Set limit at current WIP minus 20% — uncomfortable but achievable.
3. When at limit: finish something before starting something new.
4. Reduce limit by 1 every 2 weeks until pain emerges, then hold.

---

## Dependency Mapping

Unmanaged dependencies are the #1 cause of sequencing failures.

**Dependency identification checklist:**
- Does this task need output from another task?
- Does this task need a specific person, team, or external vendor?
- Does this task need an environment, dataset, or access grant?
- Does this task block other high-priority work?

**Dependency map template:**

```
[A: Design API spec]
    → [B: Implement endpoints] (blocked by A)
    → [C: Write API docs] (blocked by A)
        → [D: Partner integration] (blocked by B + C)
[E: Provision staging env] (independent)
    → [D: Partner integration] (also blocked by E)
```

**Dependency classification:**

| Type | Description | Mitigation |
|---|---|---|
| **Hard** | Cannot start without predecessor completing | Sequence strictly; surface early |
| **Soft** | Could start but would require rework | Start with stub/mock; accept some rework |
| **External** | Depends on a team or vendor you don't control | Add buffer; identify fallback; escalate early |
| **Resource** | Same person needed for multiple tasks | Stagger; cross-train; reduce WIP |

**Rule:** Any task with 3+ dependencies is high-risk. Break it down or re-sequence to reduce coupling.

---

## Now / Next / Later Framework

A lightweight alternative to full backlog grooming. Three buckets, clear rules.

| Bucket | Time Horizon | Criteria | Detail Level |
|---|---|---|---|
| **Now** | This sprint / week | Fully scoped, dependencies resolved, assignee identified | User stories with acceptance criteria |
| **Next** | Next 1–2 sprints | Roughly scoped, dependencies identified, effort estimated | Brief descriptions with open questions |
| **Later** | This quarter or beyond | Idea-stage, not yet estimated, may require research | One-liners or themes |

**Movement rules:**
- Items move Now → Done, or back to Next if blocked.
- Items move Next → Now only when fully scoped and dependencies are clear.
- Items move Later → Next after a research spike or stakeholder decision.
- Items can be removed from Later at any time without ceremony.

**Capacity rule:** Now should contain no more work than the team can finish in the current cycle.

---

## Estimation Guidance

Estimation exists to support prioritization, not to create commitments. Use the lightest method that gives enough signal.

**Method comparison:**

| Method | Scale | Best For | Accuracy | Speed |
|---|---|---|---|---|
| **T-shirt sizing** | XS, S, M, L, XL | Early-stage backlog, roadmap planning | Low — relative only | Very fast |
| **Story points** | Fibonacci (1,2,3,5,8,13,21) | Sprint planning, velocity tracking | Medium — calibrated over time | Moderate |
| **Time-based** | Hours or days | Maintenance, well-understood tasks | High — for familiar work | Slow |

**T-shirt sizing guide:**

| Size | Relative Effort | Typical Duration | Risk |
|---|---|---|---|
| XS | Trivial | < half day | None |
| S | Small | 1–2 days | Low |
| M | Medium | 3–5 days | Moderate — may have unknowns |
| L | Large | 1–2 weeks | High — break it down |
| XL | Very large | 2+ weeks | Very high — must decompose before committing |

**Estimation anti-patterns:**

| Anti-pattern | Problem | Fix |
|---|---|---|
| Precision theater | Estimating in hours for work months away | Use T-shirt sizes for anything >2 sprints out |
| Anchoring | First estimate biases all subsequent discussion | Use blind estimation (planning poker) |
| No re-estimation | Estimates never updated as scope evolves | Re-estimate when scope changes >20% |
| Conflating estimate with commitment | "3 days" becomes a deadline | Separate estimation from scheduling |

---

## Use-case bundles

| Situation | Recommended Combination |
|---|---|
| Overloaded roadmap | RICE scoring + MoSCoW for scope cuts |
| Comparing 20+ feature ideas | RICE or ICE scoring → Impact-Effort matrix for visualization |
| High-pressure incident recovery | OODA loop + Confidence-speed-quality |
| Strategic sequencing choice | Second-order thinking + Dependency mapping |
| Sprint planning | MoSCoW + T-shirt sizing + WIP limits |
| Stakeholder negotiation | Weighted scoring model (make criteria transparent) |
| Early-stage product | Now/Next/Later + ICE scoring |

## Output template
- Priority criteria (which framework, why)
- Ranked list (Now / Next / Later)
- Scoring table or provisional forced-rank rationale (depending on method)
- WIP limit for current cycle
- Dependencies and blockers (mapped and classified)
- Assumptions and invalidation triggers (required in provisional mode)
- Deferred items and why (Won't Have list)
- Estimation summary (method and key estimates)
- Review cadence (when to re-prioritize)


## Common traps

### MoSCoW inflation -- everything is "Must"
**What happens:** Agent categorizes 8 out of 10 items as "Must Have." The prioritization exercise produces no useful trade-offs.
**Why it happens:** Without a forcing function, every item feels important. The requester's urgency language gets mapped directly to Must.
**Prevention:** Apply the 60 percent rule: if more than 60 percent of items are Must, rework the categories. Ask for each Must: "If this slipped one sprint, would the release fail?" If no, it is a Should.

### RICE scores calculated with fictional data
**What happens:** Agent scores Reach and Impact for items where no usage data exists. The scores look precise (Reach: 5000 users) but are made up.
**Why it happens:** RICE requires quantitative inputs. When data does not exist, agents invent plausible numbers rather than flagging the gap.
**Prevention:** If Reach or Impact cannot be grounded in real data (analytics, user counts, support tickets), use qualitative tiers (High/Med/Low) instead of fake numbers. Label the tier basis.

### Dependencies ignored in sequencing
**What happens:** The priority list ranks items independently. Item 3 actually blocks items 1 and 2, but this is not visible until execution starts.
**Why it happens:** Prioritization frameworks (RICE, ICE) score items in isolation. They do not model dependencies.
**Prevention:** After scoring, draw a dependency graph. If any lower-ranked item blocks a higher-ranked one, promote it or note the dependency explicitly in the sequence.

### Heavy scoring applied to small lists
**What happens:** Agent builds a full RICE scoring spreadsheet for a 4-item backlog. The overhead of scoring exceeds the value of the prioritization.
**Why it happens:** The skill recommends RICE without qualifying when it is worth the effort.
**Prevention:** For lists of 5 or fewer items, use a simple forced-rank instead of RICE. Ask: "If you could only do one, which?" Repeat until ranked. Reserve RICE for 10+ items where intuitive ranking breaks down.
