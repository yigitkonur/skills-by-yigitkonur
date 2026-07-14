# Principles

Trade-offs, simplicity, response time, input handling, motivation, conventions. Each entry: principle → takeaways → frontend code → review criteria (CRITICAL/MINOR) → related.

---

## Jakob's Law

**Principle:** Users spend most of their time on *other* sites, so they expect yours to work the same way.

**Key takeaways**
- Leverage existing conventions; familiarity lets users focus on their task, not your UI.
- Innovate on value, not on relocating the cart or reinventing the date picker.

**Frontend code implications**
- Standard placements: logo top-left links home, primary nav top, search top-right, cart/account top-right.
- Use platform-native controls and patterns; provide familiar form behaviors (Enter submits, Esc closes).

**Review criteria**
- CRITICAL: core conventions broken without reason (nav/search/cart in unexpected places, non-standard form behavior).
- MINOR: minor deviation from convention that adds small relearning cost.

**Related:** Mental Model, Law of Prägnanz

---

## Doherty Threshold

**Principle:** Productivity soars when system and user interact at a pace (<400ms) that neither has to wait for the other.

**Key takeaways**
- Keep perceived response under 400ms to maintain attention and flow.
- When work genuinely takes longer, manage *perceived* time with feedback.

**Frontend code implications**
- Optimistic UI for fast-feeling updates; skeleton screens over spinners for loads.
- Progress indicators for >1s operations; animated transitions to occupy perceived wait.
- Provide feedback within 100ms of any user action (button press state, etc.).

**Review criteria**
- CRITICAL: actions taking >400ms with no loading feedback; no acknowledgement within ~100ms of a click.
- MINOR: spinner where a skeleton/optimistic update would feel faster; abrupt content swaps.

**Related:** Flow, Fitts's Law

---

## Goal-Gradient Effect

**Principle:** Motivation to reach a goal increases as users get closer to it.

**Key takeaways**
- Show progress and the nearing finish line to pull users through.
- An artificial head-start (pre-filled progress) accelerates completion.

**Frontend code implications**
- Progress bars/steppers with current-of-total; visibly advance them after each step.
- Loyalty/onboarding: grant initial progress ("2 of 10 done" with the first granted free).

**Review criteria**
- CRITICAL: long multi-step flow with no progress indication (user can't see the end).
- MINOR: progress shown but not motivating (no sense of nearing completion, no head-start).

**Related:** Zeigarnik Effect, Flow

---

## Zeigarnik Effect

**Principle:** People remember incomplete or interrupted tasks better than completed ones — open loops nag.

**Key takeaways**
- Surface unfinished tasks to drive return and completion.
- Use checklists and progress to create satisfying closure.

**Frontend code implications**
- Onboarding/setup checklists with incomplete items visible; profile-completion meters.
- Badges/counts for pending items (drafts, unfinished steps) to prompt return.

**Review criteria**
- CRITICAL: a required incomplete task with no visible reminder anywhere.
- MINOR: missed chance to prompt completion (no checklist/meter where it would help).

**Related:** Goal-Gradient Effect, Peak-End Rule

---

## Peak-End Rule

**Principle:** People judge an experience largely by its most intense point (peak) and its end, not the average of every moment.

**Key takeaways**
- Invest in the emotional peak and a strong ending (success states, confirmations).
- A delightful finish outweighs many neutral middle moments; a bad ending poisons the whole memory.

**Frontend code implications**
- Craft success/confirmation moments (thoughtful empty-states, completion animations, clear "done").
- End flows on a high — clear confirmation, next-step suggestion, gratitude — never a dead-end.

**Review criteria**
- CRITICAL: flow ends abruptly or on an error/dead-end with no confirmation or next step.
- MINOR: functional but flat ending that misses an easy delight/peak.

**Related:** Serial Position Effect, Zeigarnik Effect

---

## Postel's Law (Robustness Principle)

**Principle:** Be liberal in what you accept, conservative in what you do — tolerate varied user input, produce predictable output.

**Key takeaways**
- Accept input in any reasonable format; normalize it for the user rather than rejecting.
- Anticipate messy input and degrade gracefully.

**Frontend code implications**
- Phone/card/date inputs: strip spaces, dashes, parens server-side/client-side; accept multiple formats.
- Trim whitespace, case-normalize emails; offer forgiving search (typo tolerance, synonyms).
- Validate helpfully (inline, specific) instead of rejecting wholesale.

**Review criteria**
- CRITICAL: valid input rejected over formatting (spaces in a card number, "+" in a phone); destructive failure on imperfect input.
- MINOR: avoidable strictness that forces users to reformat what the system could normalize.

**Related:** Jakob's Law, Tesler's Law

---

## Tesler's Law (Conservation of Complexity)

**Principle:** Every system has an irreducible amount of complexity; the only question is who absorbs it — the user or the design.

**Key takeaways**
- Don't push inherent complexity onto users; absorb it in the product where possible.
- Some complexity can't be removed — handle it with smart defaults and progressive disclosure.

**Frontend code implications**
- Smart defaults, auto-detection (locale, timezone, card type), and inference reduce user-facing complexity.
- Progressive disclosure: hide advanced complexity until a user needs it.

**Review criteria**
- CRITICAL: the product offloads work it could do itself onto every user (manual steps the system could infer/automate).
- MINOR: complexity exposed upfront that could be deferred behind progressive disclosure.

**Related:** Cognitive Load, Occam's Razor

---

## Occam's Razor

**Principle:** Among competing solutions that work, choose the one with the fewest assumptions/elements. Remove until you can't remove more without breaking function.

**Key takeaways**
- Reduce elements to the essential; every added thing has a cognitive cost.
- Simplicity is the goal, not minimalism for its own sake — don't strip needed function.

**Frontend code implications**
- Audit each element: does removing it break the task? If not, remove it.
- Collapse redundant controls; cut decorative chrome that doesn't aid the task.

**Review criteria**
- CRITICAL: essential function removed in the name of "clean" (oversimplified to unusable).
- MINOR: redundant or decorative elements that add load without function.

**Related:** Tesler's Law, Law of Prägnanz, Pareto Principle

---

## Pareto Principle (80/20 Rule)

**Principle:** Roughly 80% of effects come from 20% of causes — a minority of features/inputs drives the majority of value.

**Key takeaways**
- Identify and optimize the vital few flows users actually rely on.
- Don't spend equal polish on rarely-used features.

**Frontend code implications**
- Make the high-traffic 20% (core flows) fastest and most prominent; surface them first.
- Defer or tuck away rarely-used features; instrument to find the real vital few.

**Review criteria**
- CRITICAL: the dominant user path is buried or under-optimized while rare features take prime real estate.
- MINOR: effort spread evenly instead of concentrated on the highest-impact flows.

**Related:** Occam's Razor, Tesler's Law

---

## Parkinson's Law

**Principle:** Any task will expand to fill the time available for its completion (and, by extension, work fills the space given).

**Key takeaways**
- Constrain time/steps to speed task completion; reduce friction so the fast path is the default.
- Autofill and shortcuts compress the time a task is allowed to take.

**Frontend code implications**
- Autofill, autocomplete, and saved data to shorten task time; one-tap/express checkout.
- Reasonable defaults and limits so users don't over-deliberate; reduce required steps to the minimum.

**Review criteria**
- CRITICAL: avoidable manual steps inflate a task the system could autofill/shortcut (e.g. no autofill, no express path).
- MINOR: missing shortcuts/defaults that would compress completion time.

**Related:** Doherty Threshold, Goal-Gradient Effect
