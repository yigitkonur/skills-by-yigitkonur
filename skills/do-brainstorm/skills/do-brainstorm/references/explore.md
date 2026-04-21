# Explore (Step 3 — Generate Options)

After decomposition, generate options. The goal is divergent thinking: ≥3 options with rationale, tradeoffs, and each option's Cynefin-fit. Premature convergence is the biggest failure mode here — if the first good-looking option gets selected without alternatives, the session hasn't brainstormed, it's rationalized.

## Pick the generative tool

| Need | Tool |
|---|---|
| Perspective diversity — want to see the decision from multiple angles | **Six Thinking Hats** |
| Reason from foundations — analogy isn't working, problem is novel | **First Principles** |
| Novel combinations — many dimensions, want to find non-obvious mixes | **Zwicky Box** |
| System with feedback loops — dynamics matter more than snapshots | See `systems.md` (Connection Circles + Feedback Loops) |

Use ONE primary tool. If the first pass produces <3 meaningful options, switch tools — don't force more options from a tool that's dry.

## Six Thinking Hats

**When**: decisions with stakeholders, tradeoffs, or emotional stakes; need structured perspective-taking before converging.

**Mechanics**: Rotate through six "hats" — each a distinct mental stance. Per hat, generate ideas or observations from that stance only.

| Hat | Stance | Ask |
|---|---|---|
| **Blue** | Process | What's our goal here? Are we on track? (Start + end with Blue.) |
| **White** | Data | What do we actually know? What data is missing? |
| **Red** | Emotions | Gut reaction? What do I feel about this without justification? |
| **Yellow** | Positivity | What are the benefits? Best-case scenarios? |
| **Black** | Downside | What could go wrong? Worst-case scenarios? |
| **Green** | Creativity | What wild ideas haven't been considered? Let it run free. |

**Order**: Blue → White → Yellow → Black → Green → Red → Blue. Start and end with Blue (orchestration); generate (Green) after risks (Black) so creativity isn't pre-filtered; Red last so emotions don't anchor analysis.

**Time-box**: 1-3 minutes per hat for a compact brainstorm; longer for deeper sessions.

**Output** (what to surface):

```
## Six Hats pass

Blue: Goal is X. Constraint is Y.
White: Data says A, B, C. We don't know D.
Yellow: If it works, we get <benefits>.
Black: Risks: <fail modes>.
Green: Wild options: <unfiltered>.
Red: Gut: feels <honest reaction>.
Blue: Close. The options that survive are <list>.
```

**What it reveals**: blind spots a single-perspective analysis misses. Yellow hat particularly catches "this option has upside we underweighted"; Black hat catches "this option has a risk we glossed over."

**Interactions**: Pair Green with **Zwicky Box** when Green gets stuck. Pair Black with **Inversion** (Step 5) — both are downside-focused, but Black is mid-brainstorm, Inversion is post-decision.

## First Principles

**When**: the problem is novel, analogies from past work are failing, you suspect you're carrying assumptions you haven't examined.

**Mechanics**:

1. State the problem.
2. Recursively ask **"Why?"** or **"What's beneath this?"** until you hit a truth that can't be broken down further — a "first principle".
3. Separate: what do we *actually know* is true (physics, math, constraints, hard data) from what we *assume* is true (convention, analogy, inherited belief).
4. Rebuild the solution from the first principles only. What does the evidence plus the hard constraints force?

**Socratic questions** to push down the ladder:

- Clarification: "What do you mean by X?"
- Probing assumptions: "What could we assume instead?"
- Probing reasons: "Why do you think this is true?"
- Implications: "What effect would that have?"
- Alternative viewpoints: "Is there another way to see this?"
- Questioning the question: "What was the point of asking this?"

**Output**:

```
## First Principles breakdown

Problem: <the stated problem>

Layer 1 (why): <immediate cause/reason>
Layer 2 (why): <upstream cause>
Layer 3 (why): <foundational constraint>
Layer 4 (why): <physical/mathematical/hard truth>  ← first principle

Assumptions we carried (not first principles):
- <assumption 1> — actually a convention from <source>
- <assumption 2> — actually an inherited belief

Rebuild:
Given only the first principles and the hard constraints, the solution space is:
<list of options, including ones the assumptions would have ruled out>
```

**What it reveals**: assumptions masquerading as constraints. Classic outcome: an option the team "couldn't do" turns out to be ruled out only by convention.

**Interactions**: Use on a priority branch from the decomposition (Step 2) — not the whole problem, which is too broad. Pairs with **Ladder of Inference** (Step 5) — both audit the reasoning chain, but First Principles generates, Ladder of Inference stress-tests.

## Zwicky Box (Morphological Analysis)

**When**: a problem with multiple independent dimensions; want to generate novel whole-system solutions, not just tweaks.

**Mechanics**:

1. Name 3-5 **dimensions** — logically independent attributes of the solution. (For an app: target audience, main function, unique feature, delivery method, revenue model.)
2. Per dimension, list 3-6 **values**. Don't filter — include implausible ones; they combine usefully.
3. Build the matrix (dimensions × values).
4. Generate **combinations**: pick one value per column. Try 3-5 systematic combinations + 2-3 random combinations.
5. Evaluate each combination as a whole solution; discard the ones that clearly don't work, keep the surprising ones.

**Output**:

```
## Zwicky Box

Problem: <problem>

Dimensions:
| Target audience | Delivery | Timing | Incentive | Format |
|---|---|---|---|---|
| Free users | Email | Weekly | None | Text |
| Paid users | In-app banner | Monthly | Discount | Video |
| Enterprise | Push notification | On event | Early access | Live workshop |
| Churned users | Sales call | One-shot | Credits | Mixed |

Combinations:
1. Churned users + Email + On event + Credits + Video
   → Personalized win-back with usage-credit for the re-engagement.

2. Enterprise + In-app banner + Weekly + Early access + Text
   → Power-user feature announcement stream.

3. Free users + Sales call + One-shot + Early access + Live workshop
   → Freemium-to-paid conversion via white-glove workshop; unusual but might work.

[3-5 more combinations]
```

**What it reveals**: non-obvious whole-system combinations. Great for breaking out of "we've always done it this way" defaults.

**Interactions**: Downstream of **First Principles** — Zwicky Box explores the solution space that First Principles opens up. Pair with **Decision Matrix** (Step 4) to score combinations.

## What "≥3 options" means

Not 3 minor variations on the same theme. Each option:

- **Labeled** (1-5 words)
- **Grounded** in a different framework or different priority branch
- **Distinguishable** in at least one meaningful dimension (risk profile, reversibility, time cost, team fit)
- **Fits a Cynefin domain** — note which option suits which domain

Example of bad options (all same):

```
1. Use Postgres with connection pooling
2. Use Postgres with a different connection pool size
3. Use Postgres with tuned connection timeouts
```

Example of good options (distinct):

```
1. Keep Postgres; tune the connection pool + add a retry layer (Complicated — known-unknown)
2. Introduce a read-replica for the hot-read path (Complicated — different architecture decision)
3. Switch to a session-store that matches the access pattern (Redis/DynamoDB) (Complex — probe first with shadow traffic)
```

## Fork 3 output

After explore, surface:

```
## Options explored

Tool(s) used: <Six Hats / First Principles / Zwicky Box / Connection Circles>

Option A: <label>
  Rationale: <2-3 sentences>
  Tradeoff: <key tension>
  Suits: <Cynefin domain>

Option B: <label>
  ...

Option C: <label>
  ...

[Optional: Option D, E if the generative tool produced them]

Which of these resonates? Should I expand one, drop one, add a new one, or widen the search with a different tool?
```

Wait for approval or redirect. Common redirects:

- User wants to add a new option → generate it + add to the list
- User wants to kill an option as non-starter → remove + rebalance (need to get back to ≥3)
- User wants to expand one option into sub-options → recurse into that option with the same or a different generative tool
- User wants a wider search → switch generative tool (e.g. from Six Hats to Zwicky Box)

## Common mistakes

| Mistake | Fix |
|---|---|
| Three options that are minor variations of the same idea | Switch generative tool; the current tool is dry |
| Presenting one strong option + two weak ones for illusion of choice | Hold yourself to ≥3 meaningfully different options; weak straw-men defeat the session |
| Skipping Six Hats because "we already know the tradeoffs" | Run it anyway for 3 minutes. Yellow/Black/Green commonly surface something missed |
| First Principles that never hits a hard constraint | Keep asking "why?" — if 4 layers in, you're still at assumptions, you haven't reached first principles |
| Zwicky Box with 8+ dimensions | Combinatorial explosion; cap at 5 dimensions. Merge or drop dimensions that aren't actually independent |
| Forgetting to tag each option's Cynefin-fit | The fit informs Step 4 (evaluation); missing it makes scoring harder |
