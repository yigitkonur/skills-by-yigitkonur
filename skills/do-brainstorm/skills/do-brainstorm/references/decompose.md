# Decompose (Step 2 — Surface the Real Problem)

Once classified (Step 1), decompose. This step surfaces the structure the session will work with. Four tools; pick based on the problem's signature. Do NOT run all four — one, maybe two if the first reveals a framing issue.

## Pick one

| Symptom | Tool |
|---|---|
| Why-chain problem: "why is X happening?" or "how do we solve Y?" | **Issue Trees** |
| Multi-factor root cause, suspect several interacting causes | **Ishikawa (Fishbone)** |
| Recurring issue, one-off fixes have failed, suspect structural or cultural cause | **Iceberg Model** |
| The problem statement itself feels wrong or too narrow | **Abstraction Laddering** |

## Issue Trees

**When**: A problem that decomposes naturally into sub-causes or sub-solutions via repeated "why" or "how" questions.

**Mechanics**:

1. Write the top-level problem as the tree root. Keep it neutral — not a hypothesized cause.
2. Ask **"Why?"** for a problem tree (root causes) or **"How?"** for a solution tree (remedies). Generate 3-5 branches per level.
3. Enforce **MECE** at each level:
   - **Mutually Exclusive**: no branch overlaps another
   - **Collectively Exhaustive**: branches together cover the problem
4. Stay at one abstraction level per tier. Don't mix "not enough users" with "missing OAuth redirect" at the same tier.
5. Apply the **80/20 rule**: mark the 1-2 branches most likely to carry the bulk of the cause, based on data or informed judgment.
6. Recurse on the marked branches. 2-3 levels deep is usually enough.

**Output** (inline markdown tree):

```
Problem: Users aren't adopting the new feature
├── They don't know about it
│   ├── ► Not in release notes
│   ├── No in-product promotion
│   └── No marketing email
├── They know but can't find it
│   ├── Buried in 3rd-level menu
│   └── No discoverability cue
└── They know + find it but don't use it
    ├── ► Onboarding friction
    ├── Doesn't solve their problem
    └── Existing workflow is good enough

(► = 80/20 priority branches)
```

**What it reveals**: the branches most worth investigating — the 1-2 high-leverage sub-problems.

**Interactions**: Pair with **First Principles** (Step 3) on the priority branches — "why" deep dives into foundational truths. Feeds **Decision Matrix** (Step 4) when evaluating solutions across branches.

## Ishikawa (Fishbone) Diagram

**When**: A problem where multiple categories of cause plausibly contribute. "Why is sign-ups dropping?" — could be landing page, competition, marketing, onboarding, product change.

**Mechanics**:

1. Problem on the right; draw a spine toward the left.
2. Pick 4-6 category bones. Defaults: **People / Methods / Tools / Materials / Measurement / Environment**. Customize for software: **People / Process / Code / Infrastructure / Data / External**.
3. For each category, brainstorm 2-4 specific candidate causes under the bone.
4. Per candidate, ask "why is this happening?" once to get one level deeper.
5. Analysis: identify the 2-3 most likely candidates (by evidence or team judgment); plan the test that discriminates among them.

**Output**:

```
                           People                  Process
                             │                        │
               Not enough reviewers      Retrospective never happens
                             │                        │
                             │                        │
                    ─────────┴────────────────────────┴──────────>  Shipping broken features
                             │                        │
               Test infrastructure flaky         Deploy bot silences errors
                             │                        │
                            Code              Infrastructure
```

**What it reveals**: a map of plausible causes across disjoint categories — prevents tunnel vision on one category.

**Interactions**: Complements **Iceberg Model** (Ishikawa enumerates siblings at the same level; Iceberg descends levels of abstraction). Feeds **Inversion** (Step 5) when stress-testing the picked cause.

## Iceberg Model

**When**: A recurring problem where point fixes haven't worked. "We keep shipping bugs even though we fix them." "Deploys keep breaking even though we audit after each one."

**Mechanics**: Four levels, top to bottom. Each deeper level gives more leverage.

1. **Events** — "What's happening right now?" (concrete, observable: "bug in the release yesterday")
2. **Patterns** — "What's been happening over time? What are the trends?" ("every release ships with bugs")
3. **Structures** — "What's influencing these patterns? What connections exist?" ("no dedicated QA phase; deadlines drive cuts from testing budget")
4. **Mental models** — "What values, beliefs, or assumptions shape the system?" ("we value shipping on time over quality; team lead believes QA is blocking")

**Output**:

```
Level 1 — Events: release 2024-11-02 shipped with 3 P1 bugs
Level 2 — Patterns: 4 of last 5 releases have ≥2 P1 bugs
Level 3 — Structures:
  - No pre-release QA gate
  - Testing treated as "if time permits"
  - On-call absorbs the impact (no feedback to engineering)
Level 4 — Mental models:
  - "Velocity = shipping more features"
  - "QA slows us down"
  - "Bugs are an on-call problem, not an engineering-quality problem"
```

Intervene at the deepest level you can afford. Event-level fixes (patch the bug) have lowest leverage; mental-model fixes (re-align the team's definition of "done") have highest.

**Interactions**: Sits deeper than Ishikawa — Ishikawa enumerates siblings at the Structures level; Iceberg descends. Pair with **Connection Circles** (`systems.md`) to map the feedback loops at the Structures level explicitly.

## Abstraction Laddering

**When**: The problem statement feels wrong, too narrow, too vague, or solution-shaped. Classic signal: "this is a solution pretending to be a problem."

**Mechanics**:

1. Write the current problem statement.
2. Ask **"Why?"** to climb UP one rung — produces a more abstract statement.
3. Ask **"How?"** to climb DOWN one rung — produces a more concrete statement or a solution.
4. Offer 3 rungs: original + 1 up + 1 down.
5. Ask the user which rung is the actual problem.

**Output**:

```
Up rung (why):     Make users trust the product
   ↑
Original:          Add a trust badge to the homepage
   ↓
Down rung (how):   Integrate SSL-certificate-issuer logo in the hero
```

"Add a trust badge" is a solution statement — the real problem is building trust, and the trust badge is one of many possible approaches. Going up reveals other candidates (social proof, case studies, SOC2 compliance).

**What it reveals**: alternative framings. Commonly, climbing UP unlocks better solutions; climbing DOWN validates that the user has a concrete need.

**Interactions**: Operates on problem **statements** (framing). Iceberg operates on problem **causation**. Use Laddering BEFORE decomposing — it resets what you're decomposing. Pairs with **Disorder → Classify** loop in `classify-problem.md`.

## Deciding "deep enough"

Stop decomposing when one of these holds:

- You can point at 1-2 branches/causes/rungs where an action would change the outcome
- The next level of depth isn't actionable (philosophical rather than operational)
- Budget: 2-3 levels deep is usually enough; 4+ is almost always over-decomposing

Do NOT decompose until exhaustion. The goal is insight, not completeness.

## Fork 2 output

After decomposition, surface:

```
## Decomposition

Tool used: <Issue Trees / Ishikawa / Iceberg / Abstraction Laddering>
Rationale: <one sentence why this tool>

<The tree / fishbone / iceberg / ladder inline>

Priority branches (80/20): <the 1-2 marked for Step 3 focus>

Does this decomposition capture the problem? Missing branches? Wrong level of abstraction?
```

Wait for approval. Common redirects:

- User adds a branch you missed → update the tree + re-identify priorities
- User says the priorities are wrong → re-apply 80/20 with their context
- User says the level is off → re-run Abstraction Laddering, then redo the tree
- User says the tool was wrong → switch tools (rare but legitimate)

## Common mistakes

| Mistake | Fix |
|---|---|
| Issue Tree with overlapping branches | Enforce MECE; if you can't, the categorization is off — redo |
| Ishikawa that's really an Issue Tree | Ishikawa is for multi-category; if all causes cluster in one category, use Issue Trees |
| Iceberg that stops at "Patterns" | The leverage is at Structures + Mental Models; push deeper |
| Abstraction Laddering that climbs 4+ rungs | Usually 1-2 is enough; 4+ means the real problem is well away from the stated one (legitimate, but rare) |
| Decomposing before classifying (skipping Step 1) | Decomposition choice depends on Cynefin domain; run Step 1 first |
