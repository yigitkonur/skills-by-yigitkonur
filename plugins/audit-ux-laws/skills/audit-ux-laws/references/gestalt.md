# Gestalt & Mental Models

Visual grouping, layout relationships, shape simplification, expectations. Each entry: principle → takeaways → frontend code → review criteria (CRITICAL/MINOR) → related.

---

## Law of Proximity

**Principle:** Objects near each other are perceived as a group.

**Key takeaways**
- Spacing communicates relationship more strongly than borders or color.
- The gap *between* groups must exceed the gap *within* a group.

**Frontend code implications**
- Tighten spacing within a group, widen it between groups (e.g. `gap: 8px` inside, `32px` between).
- Keep labels close to their inputs; keep an action close to the object it acts on.

**Review criteria**
- CRITICAL: a label/control or item/action so far apart users can't tell what belongs to what; uniform spacing that erases all grouping.
- MINOR: within-group gap nearly equal to between-group gap (weak grouping signal).

**Related:** Common Region, Similarity

---

## Law of Similarity

**Principle:** Elements that look alike (color, shape, size) are perceived as related, even when separated.

**Key takeaways**
- Consistent styling signals "same kind/role"; differing style signals "different role."
- Make links/buttons look like links/buttons everywhere.

**Frontend code implications**
- One consistent visual language per element role (all primary buttons identical; all links styled the same).
- Don't style a non-interactive element like an interactive one (false affordance).

**Review criteria**
- CRITICAL: interactive and static elements share identical styling (users can't tell what's clickable).
- MINOR: same-role elements styled inconsistently across views.

**Related:** Proximity, Uniform Connectedness

---

## Law of Common Region

**Principle:** Elements within a shared boundary (a container/background) are perceived as grouped.

**Key takeaways**
- A card, panel, or background block is a strong grouping device — stronger than proximity alone.
- Use it to separate logically distinct sections.

**Frontend code implications**
- Wrap related content in a card (`background`, `border`, `border-radius`, padding) to bind it.
- Separate sections with distinct background regions rather than relying on spacing only.

**Review criteria**
- CRITICAL: a container visually encloses unrelated items, implying a false relationship.
- MINOR: related items would read more clearly inside a shared region but aren't.

**Related:** Proximity, Uniform Connectedness

---

## Law of Uniform Connectedness

**Principle:** Elements visually connected (by a line, shared color region, or container) are perceived as more related than elements merely near or similar.

**Key takeaways**
- The strongest Gestalt grouping cue — explicit connection beats proximity and similarity.
- Use connectors for steps, relationships, and flows.

**Frontend code implications**
- Connect stepper/wizard nodes with a line; group toolbar actions in a connected segmented control.
- Use a shared header band or connecting element to bind a control to its content.

**Review criteria**
- CRITICAL: a connecting line/region links items that aren't actually related.
- MINOR: a sequence/flow shown as loose items where a connector would clarify order.

**Related:** Common Region, Similarity

---

## Law of Prägnanz (Simplicity)

**Principle:** People interpret ambiguous or complex images in the simplest form possible, because it takes the least cognitive effort.

**Key takeaways**
- Favor simple, clean shapes and layouts the eye resolves instantly.
- Complex or irregular forms increase processing effort and error.

**Frontend code implications**
- Prefer simple geometric shapes and regular grids; avoid gratuitously complex layouts.
- Reduce visual clutter so structure is read at a glance.

**Review criteria**
- CRITICAL: layout so visually complex/irregular that structure is unreadable at a glance.
- MINOR: ornamental complexity that adds processing cost without function.

**Related:** Occam's Razor, Similarity

---

## Mental Model

**Principle:** Users come with a prebuilt belief — from prior products and the real world — about how your system should work. Friction comes from a mismatch between their model and yours.

**Key takeaways**
- Meet existing expectations; align labels, icons, and flows with what users already know.
- When you must break a convention, signal it clearly and explain.

**Frontend code implications**
- Use conventional icons/labels (cart, gear = settings, magnifier = search) for their conventional meaning.
- Match real-world metaphors (folders, trash) where they fit; don't repurpose familiar icons for new meanings.

**Review criteria**
- CRITICAL: a familiar pattern/icon repurposed for an unexpected action (violates the user's model).
- MINOR: novel pattern used where a conventional one would be understood instantly.

**Related:** Jakob's Law, Paradox of the Active User
