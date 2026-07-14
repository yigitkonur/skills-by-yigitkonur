# Heuristics

Decision time, target acquisition, choice volume, aesthetic trust. Each entry: principle → takeaways → frontend code → review criteria (CRITICAL/MINOR) → related.

---

## Aesthetic-Usability Effect

**Principle:** Users perceive aesthetically pleasing design as more usable, and forgive minor usability issues when an interface looks good.

**Key takeaways**
- Visual polish builds trust and buys tolerance for small friction.
- It can also *mask* real usability problems in testing — don't let "it looks nice" end a review.

**Frontend code implications**
- Establish clear visual hierarchy: deliberate size/weight steps, 4–6 font sizes, 2–3 font families, a constrained palette (3–5 intentional colors).
- Consistent system tokens for shadow, radius, spacing, hover/focus states — inconsistency reads as "broken" regardless of beauty.

**Review criteria**
- CRITICAL: no visual hierarchy (all elements same weight); >3 font families or >8 font sizes; missing focus/hover states on interactive elements.
- MINOR: >6 colors without purpose; inconsistent spacing or radii; uneven shadow language.

**Related:** Von Restorff Effect, Jakob's Law

---

## Choice Overload

**Principle:** Too many options overwhelm users, causing decision paralysis and lower satisfaction (a.k.a. paradox of choice; "overchoice," Toffler 1970).

**Key takeaways**
- Reducing and organizing choices improves both decisions and how the whole experience is felt.
- When comparison is genuinely needed, enable side-by-side comparison rather than removing options.
- Prioritize what's shown at any moment (featured/recommended) and give upfront narrowing tools (search, filter).

**Frontend code implications**
- For >5–7 items, replace a plain `<select>` with a searchable/filterable combobox.
- Progressive disclosure: primary actions visible, secondary nested behind "More"/expandable panels. ≤7 top-level nav items.
- Highlight a recommended/default option (e.g. "Most Popular" badge, `border: 2px solid var(--primary)`) in plan/tier selectors.
- Lists/grids >10 items get sort + filter controls at the top.

**Review criteria**
- CRITICAL: >7 options in a dropdown/radio group with no search or grouping; pricing/plan selector with no default or recommended option highlighted.
- MINOR: 10+ item list without sort/filter/pagination; multi-step decision crammed into one screen instead of a wizard.

**Related:** Hick's Law, Doherty Threshold

---

## Fitts's Law

**Principle:** The time to acquire a target is a function of the distance to and size of the target — larger and closer targets are faster and easier to hit.

**Key takeaways**
- Make interactive elements big enough and place related actions near where the user already is.
- Screen edges/corners are effectively infinite targets (the pointer stops there).

**Frontend code implications**
- Minimum touch target 44×44px (mobile) / 24×24px (desktop pointer); pad small icons with invisible hit area via `padding` or a larger clickable wrapper.
- Place primary actions where the cursor/thumb already lives; keep destructive actions away from frequent ones.
- Group related controls close together; don't separate a label from its control by large gaps.

**Review criteria**
- CRITICAL: touch targets <44×44px on mobile; primary action >200px from where attention rests; tiny icon-only buttons with no enlarged hit area.
- MINOR: related actions slightly far apart; non-edge placement of a frequently used global action.

**Related:** Doherty Threshold, Choice Overload

---

## Hick's Law

**Principle:** The time to make a decision increases with the number and complexity of choices.

**Key takeaways**
- Minimize options when speed matters (checkout, onboarding, critical paths).
- Break complex tasks into steps so each decision is small; categorize when options can't be cut.
- Highlight recommended options to shortcut deliberation.

**Frontend code implications**
- Onboarding/checkout: one primary decision per screen; defer advanced settings.
- Categorize large option sets (grouped menus, mega-menu with headers) instead of one flat list.
- Use sensible defaults so the common path requires no choice.

**Review criteria**
- CRITICAL: speed-critical flow (checkout, signup) presenting many equally-weighted choices at once; no default on a required decision.
- MINOR: flat uncategorized menu that could be grouped; advanced options shown before basics.

**Related:** Choice Overload, Miller's Law
