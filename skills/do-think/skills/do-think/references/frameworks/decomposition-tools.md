# Decomposition Tools — Issue Trees and Ishikawa

Library entry. Routed from the SKILL.md master table, `workflows/task-planning.md` (MECE check), or `modes/interactive-brainstorm.md` Step 2.

Two tools, pick by problem signature. Do NOT run both. If the first reveals a framing issue, switch to `foundations/reframing.md` (Abstraction Laddering).

| Symptom | Tool |
|---|---|
| Why-chain problem: "why is X happening?" or "how do we solve Y?" | **Issue Trees** |
| Multi-factor root cause, suspect several interacting causes | **Ishikawa (Fishbone)** |

## Issue Trees

### When
A problem that decomposes naturally into sub-causes (problem tree) or sub-solutions (solution tree) via repeated "why" or "how" questions.

### Mechanics

1. Write the top-level problem as the tree root. Keep it neutral — not a hypothesized cause.
2. Ask **"Why?"** for a problem tree, **"How?"** for a solution tree. Generate 3-5 branches per level.
3. Enforce **MECE** at each level:
   - **Mutually Exclusive**: no branch overlaps another
   - **Collectively Exhaustive**: branches together cover the problem
4. Stay at one abstraction level per tier. Don't mix "not enough users" with "missing OAuth redirect" at the same tier.
5. Apply the **80/20 rule**: mark the 1-2 branches most likely to carry the bulk of the cause.
6. Recurse on the marked branches. 2-3 levels deep is usually enough.

### Output (inline markdown tree)

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

### What it reveals

The 1-2 high-leverage sub-problems worth deeper investigation.

## Ishikawa (Fishbone) Diagram

### When
A problem where multiple categories of cause plausibly contribute. "Why are sign-ups dropping?" — could be landing page, competition, marketing, onboarding, product change.

### Mechanics

1. Problem on the right; draw a spine toward the left.
2. Pick 4-6 category bones. Defaults: People / Methods / Tools / Materials / Measurement / Environment. Software-adapted: **People / Process / Code / Infrastructure / Data / External**.
3. For each category, brainstorm 2-4 specific candidate causes under the bone.
4. Per candidate, ask "why is this happening?" once to get one level deeper.
5. Identify the 2-3 most likely candidates by evidence; design the test that discriminates among them.

### Output

```
                           People                  Process
                             │                        │
               Not enough reviewers      Retrospective never happens
                             │                        │
                    ─────────┴────────────────────────┴──────────>  Shipping broken features
                             │                        │
               Test infrastructure flaky         Deploy bot silences errors
                             │                        │
                            Code              Infrastructure
```

### What it reveals

A map of plausible causes across disjoint categories — prevents tunnel vision on one category.

## Deciding "deep enough"

Stop decomposing when one of these holds:

- You can point at 1-2 branches/causes where an action would change the outcome
- The next level of depth isn't actionable (philosophical rather than operational)
- Budget: 2-3 levels deep is usually enough; 4+ is almost always over-decomposing

## Interactions

- Issue Trees: pair with `first-principles.md` on the priority branches; feed `decision-matrix.md` to evaluate solutions across branches.
- Ishikawa: complements `frameworks/systems-tools.md` Iceberg Model — Ishikawa enumerates siblings at the same level; Iceberg descends levels.
- If the problem statement itself feels wrong, route to `foundations/reframing.md` (Abstraction Laddering) before decomposing.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Issue Tree with overlapping branches | Enforce MECE; if you can't, the categorization is off — redo. |
| Ishikawa that's really an Issue Tree | Ishikawa is for *multi-category*; if all causes cluster in one category, switch to Issue Trees. |
| Decomposing before classifying domain | Decomposition choice depends on Cynefin domain (`foundations/domain-classification.md`). Classify first. |
| Decomposing to 4+ levels | Over-decomposition. The goal is insight, not completeness. |
