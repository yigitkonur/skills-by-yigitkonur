---
name: audit-ux-laws
description: "Use if building or auditing UI against the 30 Laws of UX (Fitts, Hick, Gestalt, cognitive load)."
---

# Audit UX Laws

Self-contained reference for the **30 Laws of UX** (based on lawsofux.com by Jon Yablonski), tuned for an agent to find the relevant law, apply it to real code, and flag violations by severity. No live fetch — all law content is bundled in `references/`.

This skill does two jobs: **proactive design** (pick the right law while building UI) and **review** (audit an interface and report violations as CRITICAL / MINOR with concrete fixes). It works on UI only — components, layouts, navigation, forms, interactions, perceived performance. It is not a visual/CSS-correctness pass and it does not redesign brand or content.

The agent owns one decision: *which laws are relevant to the thing in front of me?* Everything downstream — the takeaway, the code pattern, the severity threshold — lives in the routed reference file. Read the router, open the **one** category file you need, apply it.

## When to Use

Trigger on phrases and contexts like:

- *"is this good UX?"*, *"review this interface"*, *"what's wrong with this design?"*
- building or editing components, pages, layouts, navigation, menus, dropdowns, forms
- *"too many options"*, *"this feels overwhelming"*, decision points, pricing tiers
- touch-target sizing, click areas, spacing, visual grouping, hierarchy, what stands out
- loading states, response time, perceived performance, animation timing
- any named law: Fitts's, Hick's, Miller's, Jakob's, Doherty Threshold, Gestalt, Von Restorff, choice overload, chunking, cognitive load, Tesler's, Postel's, Pareto, Occam's, Zeigarnik, peak-end, goal-gradient, serial position

### Do NOT use when

- The work is backend / API / data-layer with no user-facing surface.
- The ask is pure visual polish (exact colors, shadows, brand) — that is a CSS/design-system pass.
- You need a full persona-driven usability audit with saved findings → use `audit-ux-and-save-files`.
- You need a visual UI bug audit across pages with screenshots → use `audit-ui-and-save-files`.

## Step 1 — Route the symptom to a law

Match what you see to a row; open only the reference file in the last column.

| What you're checking | Laws | Reference file |
|---|---|---|
| **Too many options** (menus, dropdowns, nav, plans) | Hick's Law, Choice Overload | `references/heuristics.md` |
| **Touch targets** too small / far apart / hard to hit | Fitts's Law | `references/heuristics.md` |
| **Beautiful-but-is-it-usable** / first-impression trust | Aesthetic-Usability Effect | `references/heuristics.md` |
| **Too much info on screen** / dense forms / long lists | Miller's Law, Cognitive Load, Chunking, Working Memory | `references/cognitive.md` |
| **What stands out** / CTA emphasis / scanning order | Von Restorff, Serial Position, Selective Attention | `references/cognitive.md` |
| **Onboarding / first-time users skip instructions** | Paradox of the Active User, Cognitive Bias, Flow | `references/cognitive.md` |
| **Grouping / spacing / layout relationships** | Proximity, Similarity, Common Region, Uniform Connectedness, Prägnanz | `references/gestalt.md` |
| **Users confused by an unfamiliar pattern** | Jakob's Law, Mental Model | `references/gestalt.md` (Mental Model), `references/principles.md` (Jakob's) |
| **Response time / loading / perceived speed** | Doherty Threshold | `references/principles.md` |
| **Forms too long / complexity** | Tesler's Law, Parkinson's Law, Occam's Razor, Pareto | `references/principles.md` |
| **Input handling / error tolerance** | Postel's Law | `references/principles.md` |
| **Motivation / progress / completion / memorable ending** | Goal-Gradient, Zeigarnik, Peak-End Rule | `references/principles.md` |

If more than one row matches, open each named file once and apply every relevant law.

## Step 2 — Apply or review

**Designing (proactive):** read the law's *Key Takeaways* + *Frontend Code Implications*, then build to them.

**Reviewing (audit):** walk the law's *Review Criteria*, classify each violation, and report it with the fix. Severity scale:

- **CRITICAL** — breaks usability, accessibility, or trust. Fix before ship. (e.g. touch target <44×44px mobile; >7 ungrouped options; primary CTA indistinguishable from secondary; no loading feedback >400ms; required cross-screen memorization.)
- **MINOR** — polish / optimization. (e.g. >6 colors, inconsistent spacing, missing smart default, no progress indicator, suboptimal CTA placement.)

Always connect the finding to the *why* (the psychological principle) and give a **concrete, actionable fix** — code pattern or specific change, never "improve the UX."

## Step 3 — Follow Related links when warranted

Each law entry ends with **Related** pointers (e.g. Choice Overload → Hick's Law → Doherty Threshold). Follow them only when the current law's fix creates a new question the related law answers.

## Quick Reference — all 30 laws

| Law | Category | One-liner | Related |
|---|---|---|---|
| Aesthetic-Usability Effect | Heuristic | Beautiful design is perceived as more usable | Von Restorff, Jakob's |
| Choice Overload | Heuristic | Too many options cause decision paralysis | Hick's, Doherty |
| Fitts's Law | Heuristic | Larger, closer targets are faster to hit | Doherty, Choice Overload |
| Hick's Law | Heuristic | Decision time grows with number of choices | Choice Overload, Miller's |
| Chunking | Cognitive | Group info into meaningful units | Miller's, Cognitive Load |
| Cognitive Bias | Cognitive | Systematic thinking errors shape decisions | Selective Attention, Peak-End |
| Cognitive Load | Cognitive | Minimize mental effort to use the interface | Miller's, Tesler's |
| Miller's Law | Cognitive | Working memory holds ~7±2 items | Chunking, Working Memory |
| Working Memory | Cognitive | Don't force recall across steps/screens | Miller's, Chunking |
| Selective Attention | Cognitive | Users filter to goal-relevant stimuli | Von Restorff, Cognitive Bias |
| Serial Position Effect | Cognitive | First and last items remembered best | Von Restorff, Peak-End |
| Von Restorff Effect | Cognitive | The distinct item stands out — use for CTAs | Serial Position, Selective Attention |
| Flow | Cognitive | Balance challenge & skill; remove friction | Doherty, Goal-Gradient |
| Paradox of the Active User | Cognitive | Users skip manuals and learn by doing | Jakob's, Mental Model |
| Law of Proximity | Gestalt | Near elements are perceived as grouped | Common Region, Similarity |
| Law of Similarity | Gestalt | Similar-looking elements are seen as related | Proximity, Uniform Connectedness |
| Law of Common Region | Gestalt | A shared boundary groups elements | Proximity, Uniform Connectedness |
| Law of Uniform Connectedness | Gestalt | Visually connected elements are most related | Common Region, Similarity |
| Law of Prägnanz | Gestalt | Users read complex shapes in their simplest form | Occam's, Similarity |
| Mental Model | Gestalt | Users carry prebuilt expectations from other products | Jakob's, Paradox of Active User |
| Jakob's Law | Principle | Users expect your site to work like the others they know | Mental Model, Prägnanz |
| Doherty Threshold | Principle | Keep response <400ms to hold attention & flow | Flow, Fitts's |
| Goal-Gradient Effect | Principle | Motivation rises as the goal nears — show progress | Zeigarnik, Flow |
| Zeigarnik Effect | Principle | Incomplete tasks are remembered — use progress cues | Goal-Gradient, Peak-End |
| Peak-End Rule | Principle | Experiences are judged by their peak and ending | Serial Position, Zeigarnik |
| Postel's Law | Principle | Be liberal in what you accept, strict in what you output | Jakob's, Tesler's |
| Tesler's Law | Principle | Irreducible complexity must live in design, not the user | Cognitive Load, Occam's |
| Occam's Razor | Principle | Remove elements until you can't without breaking function | Tesler's, Prägnanz, Pareto |
| Pareto Principle | Principle | ~80% of effects come from ~20% of causes | Occam's, Tesler's |
| Parkinson's Law | Principle | Work expands to fill available time/space — constrain it | Doherty, Goal-Gradient |

## Reference routing

Load only the file for the category you routed to in Step 1.

| File | Read when |
|---|---|
| `references/heuristics.md` | Decision time, target acquisition, choice volume, aesthetic trust. |
| `references/cognitive.md` | Memory limits, attention, scanning, learning, biases. |
| `references/gestalt.md` | Visual grouping, layout relationships, shape simplification, expectations. |
| `references/principles.md` | Trade-offs, simplicity, response time, input handling, motivation, conventions. |

## Guardrails

- Self-contained: never fetch lawsofux.com at runtime; bundled references are the source of truth.
- Don't load all four category files for every request — route, then apply only what's relevant.
- Every review finding needs a severity (CRITICAL/MINOR), a *why* (the law), and a concrete fix.
- Don't invent thresholds; use the numbers in the reference files.
- Severity numbers are usability heuristics, not a substitute for WCAG accessibility testing.
