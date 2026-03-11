# Quality Checklist

Use this checklist to verify that a design soul extraction captured everything needed to recreate the visual identity of a SaaS dashboard.

---

## ⚠️ Don't Skip These (What AI Agents Miss Most)

Before running through the detailed checklist, verify these high-failure-rate items first. These are the things agents skip because they seem "obvious" or "boring":

- [ ] **Disabled states on EVERY interactive component** — opacity, pointer-events, cursor
- [ ] **Focus-visible ring** (NOT just :focus) — width, color, offset, dark mode variant
- [ ] **Loading states** — even if "Not implemented", say so explicitly
- [ ] **Error/invalid states** — `aria-invalid`, destructive ring, error message positioning
- [ ] **Empty/zero-data states** — empty table, empty chart, no results, first-time use
- [ ] **Opacity semantics** — EVERY opacity value explained (0.5 = disabled, 0.9 = hover darken)
- [ ] **Dark mode PER COMPONENT** — not just tokens in system.md, but differences in each component doc
- [ ] **Animation composition** — floating elements often compose fade + zoom + slide
- [ ] **Mega-component decomposition** — sidebar, table, form layout have 10-20+ sub-components
- [ ] **State transition documentation** — Idle → Hover → Active → Focus → Disabled
- [ ] **INDEX.md created** — master navigation with coverage table and reading path
- [ ] **_summary.md created** — one-page snapshot of the entire extraction
- [ ] **Composition patterns** — every component shown in context with at least one other component
- [ ] **Spacing rhythm WHY** — not just "8px" but "8px = dense/table gap, 16px = button padding"

---

### Steering Notes (Common Agent Failures)

1. **Tailwind v4 missed**: Agent looked for `tailwind.config.js` but the project uses `@theme` blocks in CSS.
2. **oklch values misread**: Agent treated oklch lightness as hsl lightness. In oklch, L=0.2 is dark; in hsl, L=20% is dark. Different scales.
3. **CVA variants not extracted**: Agent documented "default" variant and skipped destructive, outline, ghost, secondary.
4. **cn() class merging ignored**: With `cn()`, later classes override earlier ones via `tailwind-merge`.
5. **Dark mode only in system.md**: Each component doc needs its own "Dark Mode Differences" table.
6. **Sidebar tokens missed**: `--sidebar-background`, `--sidebar-foreground`, `--sidebar-ring` are a separate token scope.

---

## System-Level Checks

### Spacing
- [ ] Base unit identified (4px or 8px)
- [ ] Full scale documented with pixel values
- [ ] Each scale step has frequency count
- [ ] Each scale step has usage context (which components)
- [ ] Layout strategy identified (gap-based, margin-based, grid)
- [ ] Common spacing combos documented (e.g., "px-3 py-1" always on inputs)
- [ ] Dashboard density zones identified (dense areas vs. spacious areas)

### Colors
- [ ] Color space identified (hex, rgb, hsl, oklch)
- [ ] EVERY CSS custom property documented
- [ ] Light mode values listed
- [ ] Dark mode values listed
- [ ] Mode switching mechanism documented (.dark class, media query, JS)
- [ ] Semantic purpose for each token explained
- [ ] Opacity modifiers catalogued (/50, /30, etc.)
- [ ] Hardcoded colors flagged as inconsistencies
- [ ] Chart/visualization palette documented
- [ ] Sidebar-specific token overrides documented (if applicable)

### Typography
- [ ] All font families identified with source (CDN, local, system)
- [ ] Size scale with frequency counts
- [ ] Weight scale with usage contexts
- [ ] Special patterns: tabular-nums, uppercase+tracking, truncation
- [ ] Letter-spacing values documented
- [ ] Line-height values documented
- [ ] Monospace usage for data display documented

### Shadows & Depth
- [ ] Strategy identified (borders-first, shadows, layered)
- [ ] Shadow scale with exact CSS values
- [ ] Each shadow level mapped to component types
- [ ] Focus ring system documented (width, color, offset)
- [ ] Elevation map (canvas -> surface -> floating -> overlay -> backdrop)

### Radius
- [ ] Base variable documented
- [ ] Derived variables documented (calc expressions)
- [ ] Scale with Tailwind class + pixel value
- [ ] Radius-to-component mapping (md for buttons, xl for cards, etc.)

### Animations
- [ ] All named animations listed with duration + easing + properties
- [ ] Enter/exit pairs documented (fade-in/out, zoom-in/out, slide-in/out)
- [ ] Data-attribute triggers mapped (data-state, data-side)
- [ ] Duration hierarchy explained (instant -> fast -> normal -> slow)
- [ ] Easing functions listed
- [ ] Animation library identified

### States
- [ ] Standard focus pattern documented with full CSS
- [ ] Standard disabled pattern documented
- [ ] Standard error/invalid pattern documented
- [ ] Hover patterns categorized by component type
- [ ] Selected/active state patterns for toggleable components
- [ ] Data attributes used for state styling listed

---

## Per-Component Checks

For EACH component document:

### Structure
- [ ] One-line description present
- [ ] Source file path documented
- [ ] Library/dependency noted
- [ ] ASCII anatomy diagram drawn

### Variants
- [ ] EVERY variant has its own section
- [ ] Each variant lists: background, text, border, shadow (with resolved values)
- [ ] Each variant documents hover changes
- [ ] Default variant explicitly documented (not assumed)

### Sizes
- [ ] Size table with: height, padding, text size, icon size, gap
- [ ] All sizes in BOTH Tailwind classes AND pixel values
- [ ] Icon auto-sizing rule documented (e.g., SVG size-4 unless overridden)

### States
- [ ] Default/resting state — full property list
- [ ] Hover — what changes, transition timing
- [ ] Focus-visible — ring/outline details
- [ ] Active/pressed — changes or "not implemented"
- [ ] Disabled — opacity, cursor, pointer-events
- [ ] Loading — spinner details or "not implemented"
- [ ] Error/invalid — border/ring color changes or "not implemented"
- [ ] Selected/checked/active — for toggleable components

### State Transitions (NEW)
- [ ] State machine diagram showing Idle → Hover → Active → Focus → Disabled
- [ ] Each transition lists: which CSS properties change, duration, easing
- [ ] Mouse interaction flow documented
- [ ] Keyboard interaction flow documented
- [ ] Async flow documented (if applicable): Loading → Success/Error

### Anti-Patterns (NEW)
- [ ] At least 3 "don't do this" items specific to this component
- [ ] Common mistakes listed with correct approach
- [ ] Missing states explicitly called out (even if "not implemented")

### Animations
- [ ] Every animated property listed
- [ ] Duration in milliseconds
- [ ] Easing function named
- [ ] From -> To values specified
- [ ] Enter and exit animations documented separately
- [ ] Animation composition documented (fade + zoom + slide layers)
- [ ] Timing hierarchy explained (micro/standard/slow/ambient)

### Spacing
- [ ] Internal padding diagram with pixel values
- [ ] Gap between child elements
- [ ] Minimum dimensions noted
- [ ] Spacing rhythm rationale (WHY this value)

### Dark Mode
- [ ] Separate section (not inline with light mode)
- [ ] Every property that changes between modes listed
- [ ] Both resolved values shown

### Responsive
- [ ] Breakpoint changes documented
- [ ] Or "no responsive changes" stated explicitly

### Accessibility
- [ ] ARIA role noted
- [ ] Keyboard interaction documented
- [ ] Screen reader text noted (sr-only elements)

### CSS Recreation
- [ ] Complete CSS block that recreates the component
- [ ] All variants as CSS modifier classes
- [ ] All states as pseudo-classes (`:hover`, `:focus-visible`, `:disabled`, `[data-state=*]`)
- [ ] No unresolved CSS variables (or variables defined at top)
- [ ] Vendor prefixes included where needed
- [ ] A developer could copy-paste this and get a working visual

### Composition
- [ ] At least one example of how this component is used with others
- [ ] Common patterns/groupings shown
- [ ] Mega-component hierarchy documented (if 5+ sub-components)

---

## Dashboard-Specific Checks

### Layout
- [ ] Sidebar structure documented (width, collapse, mobile behavior)
- [ ] Top bar documented (if present)
- [ ] Content area layout documented (max-width, padding, grid)
- [ ] Responsive breakpoints for layout shifts documented

### Data Patterns
- [ ] Metric/KPI display patterns documented
- [ ] Data table configuration documented (sorting, filtering, pagination)
- [ ] Chart container patterns documented
- [ ] Empty states documented (at least 3 contexts)
- [ ] Loading/skeleton patterns documented

### Navigation
- [ ] Primary navigation structure documented
- [ ] Active state indicators documented
- [ ] Breadcrumb patterns documented (if present)
- [ ] Workspace/tenant switcher documented (if present)

### Settings
- [ ] Settings page layout documented (if settings exist)
- [ ] Form group patterns documented
- [ ] Save/submit patterns documented

### Search/Command
- [ ] Command palette documented (if present)
- [ ] Search patterns documented

### AI/Chat Patterns (if present)
- [ ] Message thread styling documented (user vs assistant)
- [ ] Streaming/typing state documented
- [ ] Prompt input documented (auto-grow, attachments, submit states)
- [ ] Tool call cards documented (collapsed/expanded, status indicators)
- [ ] AI-specific loading states documented (thinking, streaming, queued)

### Desktop/Platform Patterns (if applicable)
- [ ] Window chrome documented (title bar, traffic lights, drag region)
- [ ] Theme injection mechanism documented
- [ ] Terminal integration documented (if present)
- [ ] Platform-specific theme differences documented

---

## Meta-Documentation Checks (NEW)

### INDEX.md
- [ ] Extraction metadata present (source, date, scope)
- [ ] Coverage summary table (category, count, lines)
- [ ] Key design decisions (6-8 bullets)
- [ ] Distinctive patterns section
- [ ] Recommended reading path
- [ ] "Where to look by task" navigation guide

### _summary.md
- [ ] Scope section (files across categories)
- [ ] Key decisions (6 bullets max)
- [ ] Unique patterns / architectural highlights
- [ ] Recreation estimate (phased)
- [ ] Document structure explanation

---

## Cross-Reference Checks

- [ ] Every color token in component docs exists in color-tokens.md
- [ ] Every spacing value in component docs exists in spacing-scale.md
- [ ] Every shadow in component docs matches shadow-depth.md
- [ ] Every animation in component docs matches animation-system.md
- [ ] Every radius in component docs matches radius-scale.md

---

## The Ultimate Test

> Could a developer who has NEVER seen the original codebase
> recreate a pixel-perfect version using ONLY these documents?

If the answer is "yes, for every component" — the extraction is complete.

If the answer is "mostly, but they'd need to guess at [X]" — document [X].

---

## Common Gaps to Watch For

These are the things most likely to be missed:

1. **Sidebar active state** — the exact visual treatment of the currently active nav item
2. **Table hover rows** — the subtle background change on table row hover
3. **Input placeholder color** — often different from muted text color
4. **Focus ring on dark mode** — often a different opacity or color than light mode
5. **Loading skeletons** — the exact shimmer animation and matching dimensions
6. **Toast position** — which corner, offset from edges, stacking behavior
7. **Scrollbar styling** — custom scrollbar width, thumb color, track color
8. **Dropdown positioning** — which side, alignment, offset from trigger
9. **Transition timing** — the exact ms and easing on hover/focus transitions
10. **Icon sizes inside buttons** — the auto-sizing rule for SVGs nested in buttons
