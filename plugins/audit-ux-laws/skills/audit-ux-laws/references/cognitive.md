# Cognitive

Memory limits, attention, scanning, learning, biases. Each entry: principle → takeaways → frontend code → review criteria (CRITICAL/MINOR) → related.

---

## Miller's Law

**Principle:** The average person holds ~7 (±2) items in working memory. Organize content into small, meaningful chunks rather than long unstructured lists.

**Key takeaways**
- Don't weaponize "7±2" to justify arbitrary limits — it's about chunking, not a hard cap.
- Capacity varies with prior knowledge and context.

**Frontend code implications**
- Nav grouped into ~5–9 top-level categories; overflow into sub/mega-menus, not more top links.
- Group related fields with `<fieldset>`/`<legend>`; break long forms into multi-step wizards with a progress indicator.
- Paginate / "load more" for long result sets; add category headers when showing many rows.
- Tab bars and segmented controls: 3–5 items; overflow into a "More" menu.

**Review criteria**
- CRITICAL: required cross-screen memorization (user must recall data from a prior step with no carry-over); >9 ungrouped top-level nav items.
- MINOR: long form with no grouping/steps; unformatted long data sequences.

**Related:** Chunking, Working Memory

---

## Chunking

**Principle:** Break information into grouped, meaningful units so users can scan, process, and memorize more efficiently.

**Key takeaways**
- Visually distinct groups with clear hierarchy match how people evaluate digital content.
- Chunking also communicates relationships (what belongs with what).

**Frontend code implications**
- Format sequences: phone `(XXX) XXX-XXXX`, card `XXXX XXXX XXXX XXXX`, date `MM/DD/YYYY`; use `inputmode`/`pattern`.
- Group form fields in `<fieldset>`; separate groups with `margin-bottom: 24–32px` or dividers.
- Break long lists into chunks of 3–5 with grid/flex `gap`; use `<h2>/<h3>` + whitespace for content hierarchy.
- Tables: alternating row backgrounds (`tr:nth-child(even)`), `<colgroup>`, separators between logical sections.

**Review criteria**
- CRITICAL: long sequences (phone/card/account) shown as raw unbroken strings; unrelated fields visually merged with no separation.
- MINOR: wall-of-text content with no subheads/whitespace; lists >5–7 with no sub-grouping.

**Related:** Miller's Law, Cognitive Load

---

## Cognitive Load

**Principle:** The total mental effort required to use an interface. Minimize *extraneous* load so users spend effort on their goal, not the UI.

**Key takeaways**
- Remove, defer, or offload anything not essential to the current task.
- Reuse familiar patterns so users don't relearn (ties to Jakob's Law).

**Frontend code implications**
- Eliminate redundant inputs; prefill known data; use smart defaults.
- Defer secondary settings behind progressive disclosure; show contextual help inline, not in a manual.
- Avoid jargon; one clear primary action per view.

**Review criteria**
- CRITICAL: user forced to compute/convert/remember something the system could do for them; competing primary actions with no clear priority.
- MINOR: redundant fields; unexplained jargon; help buried away from the point of need.

**Related:** Miller's Law, Tesler's Law

---

## Working Memory

**Principle:** Temporary cognitive storage for the active task is limited and fragile. Don't force users to hold information across steps or screens.

**Key takeaways**
- Carry context forward; show, don't make them recall.
- Interruptions wipe working memory — preserve state.

**Frontend code implications**
- Persist entered data across steps and on back-navigation; show a summary/review step before submit.
- Keep reference info visible while it's needed (e.g. order summary beside the form).
- Autosave drafts; restore on return.

**Review criteria**
- CRITICAL: data lost on back/refresh; user must memorize a code/value from one screen to use on another.
- MINOR: needed reference info hidden behind a tab/modal during a task.

**Related:** Miller's Law, Chunking

---

## Selective Attention

**Principle:** Users focus on a subset of stimuli — usually goal-relevant — and miss the rest (including, often, ads and unexpected changes).

**Key takeaways**
- Clear hierarchy guides the eye; don't bury critical info in visual noise.
- "Banner blindness": important things that look like ads get ignored.

**Frontend code implications**
- Give each screen one obvious focal point; use size/color/position to create attention flow.
- Don't style critical messages like promo banners; place them in the primary content path.
- De-emphasize or remove decorative noise around key actions.

**Review criteria**
- CRITICAL: essential info (errors, required steps) hidden in low-contrast or ad-like placement.
- MINOR: no clear focal point; decorative elements competing with the primary action.

**Related:** Von Restorff Effect, Cognitive Bias

---

## Serial Position Effect

**Principle:** Users best remember the first and last items in a series (primacy and recency).

**Key takeaways**
- Place the most important/least-related actions at the start and end of lists and nav.
- Middle items are weakest — don't bury anything critical there.

**Frontend code implications**
- Put key nav items first and last; least important in the middle.
- In action rows, anchor primary/destructive actions at the ends deliberately.

**Review criteria**
- CRITICAL: the single most important action buried in the middle of a long list/menu.
- MINOR: suboptimal ordering with no primacy/recency consideration.

**Related:** Von Restorff Effect, Peak-End Rule

---

## Von Restorff Effect (Isolation Effect)

**Principle:** When multiple similar objects are present, the one that differs is most likely to be noticed and remembered.

**Key takeaways**
- Make the primary CTA visually distinct — but distinction must be scarce to work.
- Don't rely on color alone (accessibility); pair with weight/size/shape.

**Frontend code implications**
- One dominant CTA per view; secondary actions visually quieter (ghost/outline).
- Highlight important info with contrast + a non-color cue (icon, weight).

**Review criteria**
- CRITICAL: primary CTA indistinguishable from secondary actions; "everything emphasized" so nothing stands out.
- MINOR: 3+ elements competing to stand out; emphasis carried by color alone.

**Related:** Serial Position Effect, Selective Attention

---

## Flow

**Principle:** The state of focused, immersive engagement that emerges when challenge and skill are balanced and friction is removed.

**Key takeaways**
- Remove interruptions and latency that break immersion (ties to Doherty Threshold).
- Match difficulty to user skill; provide clear goals and immediate feedback.

**Frontend code implications**
- Keep responses fast (<400ms perceived) and feedback immediate; avoid modal interruptions mid-task.
- Preserve context across actions; minimize context switches and reloads.

**Review criteria**
- CRITICAL: frequent blocking interruptions (modals, full reloads) during a focused task.
- MINOR: small latency or feedback gaps that nibble at immersion.

**Related:** Doherty Threshold, Goal-Gradient Effect

---

## Paradox of the Active User

**Principle:** Users don't read manuals — they jump straight in and learn by doing, even when reading first would be faster.

**Key takeaways**
- Design for exploration: make the product teach itself in context.
- Front-load value; defer documentation to the moment of need.

**Frontend code implications**
- Inline, contextual hints and empty-state guidance instead of upfront tutorials.
- Sensible defaults so a user who reads nothing still succeeds; forgiving, reversible actions (undo).

**Review criteria**
- CRITICAL: core flow unusable without reading docs first; no guidance in empty/first-run states.
- MINOR: help exists but isn't surfaced at the point of need.

**Related:** Jakob's Law, Mental Model

---

## Cognitive Bias

**Principle:** Systematic errors in thinking shape how users perceive interfaces and make decisions.

**Key takeaways**
- Anchoring, framing, loss aversion, social proof, etc. quietly steer choices — design honestly.
- Use biases to *help* users decide, not to manipulate (avoid dark patterns).

**Frontend code implications**
- Framing: present the option you genuinely recommend as the default/highlighted choice.
- Social proof: show real usage/ratings near decisions; never fabricate urgency or scarcity.
- Anchoring: order pricing so the intended reference point comes first.

**Review criteria**
- CRITICAL: dark patterns — fake scarcity/urgency, manipulative framing, hidden costs revealed late.
- MINOR: missed honest opportunity to reduce decision effort (no recommended default, no social proof where genuine).

**Related:** Selective Attention, Peak-End Rule
