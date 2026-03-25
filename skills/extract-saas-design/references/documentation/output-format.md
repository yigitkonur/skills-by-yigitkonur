# Design Documentation Output Format

How to structure the final output of a design extraction for maximum usability.

Write the `.design-soul/` tree at the target codebase root or at a writable working copy of that codebase. Do not write it inside the skills repo or another unrelated parent directory.

For narrow extractions, create only the files required by scope. `INDEX.md` and `_summary.md` become required when the extraction spans multiple docs or categories.

---

## Output Directory Structure

```
.design-soul/
├── INDEX.md                    # Master navigation, coverage summary
├── _summary.md                 # One-page snapshot for quick orientation
├── system.md                   # Foundation tokens (spacing, colors, typography, shadows)
└── components/
    ├── foundations/
    │   ├── 01-spacing-scale.md
    │   ├── 02-color-tokens.md
    │   ├── 03-typography-scale.md
    │   ├── 04-shadow-depth.md
    │   ├── 05-radius-scale.md
    │   ├── 06-animation-system.md
    │   └── 07-focus-and-states.md
    ├── controls/               # Button, Input, Select, Checkbox, etc.
    ├── containers/             # Card, Tabs, Accordion, Separator
    ├── navigation/             # Sidebar, Breadcrumb, Top Bar
    ├── overlays/               # Dialog, Popover, Tooltip, Dropdown
    ├── feedback/               # Badge, Toast, Alert, Skeleton
    ├── data-display/           # Table, Chart, Metric Card
    └── [app-specific]/         # Product-unique components and composition patterns
```

---

## File Naming Convention

- Foundation files: `NN-{topic}.md` (e.g., `01-spacing-scale.md`)
- Component files: `NN-{component-name}.md` (e.g., `01-button.md`)
- Pattern files in `components/[app-specific]/`: `NN-{pattern-name}.md` (e.g., `01-dashboard-layout.md`)
- Number prefix controls reading order within a category
- Use kebab-case for all filenames

---

## INDEX.md Template

```markdown
# Design Soul Index

Extracted from: [repo name]
Date: [YYYY-MM-DD]
Files scanned: [N] UI files across [N] directories
Agent: [model/version used]

## Coverage Summary

| Category | Components | Files | Total Lines |
|----------|-----------|-------|-------------|
| Foundations | 7 | 7 | [N] |
| Controls | [N] | [N] | [N] |
| Containers | [N] | [N] | [N] |
| Navigation | [N] | [N] | [N] |
| Overlays | [N] | [N] | [N] |
| Feedback | [N] | [N] | [N] |
| Data Display | [N] | [N] | [N] |
| [App-specific] | [N] | [N] | [N] |
| **Total** | **[N]** | **[N]** | **[N]** |

## Key Design Decisions

1. [Depth strategy — borders-first, shadows, layered]
2. [Spacing base unit and scale]
3. [Color architecture — CSS variables, color space]
4. [Animation philosophy — minimal vs rich]
5. [Dark mode implementation]
6. [Information density strategy]
7. [Typography — font stacks, scale]
8. [Responsive strategy — breakpoints, mobile nav]

## Distinctive Patterns

- [Pattern unique to this product]
- [Another distinctive pattern]
- [Third distinctive pattern]

## Recommended Reading Path

1. `_summary.md` → high-level picture
2. `system.md` → all token values and scales
3. `components/foundations/` → detailed token documentation
4. `components/controls/` → core interactive components
5. `components/navigation/` → app structure and navigation
6. `components/[app-specific]/` → product-unique components and pattern docs

## Where to Look by Task

| Task | Read these |
|------|-----------|
| Build a form | controls/ (input, select, checkbox) + foundations/01-spacing |
| Build navigation | navigation/ (sidebar, breadcrumb) + foundations/02-colors |
| Build a modal | overlays/ (dialog, sheet) + foundations/06-animations |
| Add a data table | data-display/ (table, pagination) + app-specific pattern docs when the table is part of a broader dashboard workflow |
| Understand theming | system.md + foundations/02-color-tokens |
```

---

## _summary.md Template

```markdown
# Design Soul Extraction Summary

Extracted: [date]
Source: [repo name/path]
Files scanned: [N] UI files across [N] directories

## Scope

| Category | Components | States | Animations | Variants |
|----------|-----------|--------|------------|----------|
| Foundations | 7 docs | - | N named | - |
| Controls | N | N | N | N |
| ... | ... | ... | ... | ... |
| **Total** | **N** | **N** | **N** | **N** |

## Design Identity

1. Depth strategy: [borders-first / shadows / layered]
2. Spacing base: [N]px, scale: [list]
3. Radius personality: [sharp / medium / soft]
4. Animation philosophy: [minimal / moderate / rich]
5. Color architecture: [token-based, color space]
6. Dark mode: [.dark class / media query / JS]
7. Density: [compact / balanced / spacious]
8. Navigation: [sidebar / top-bar / both]

## Recreation Estimate

| Phase | Effort | Description |
|-------|--------|-------------|
| 1. Tokens | [time] | Define CSS custom properties |
| 2. Core components | [time] | Button, Input, Card, Badge |
| 3. Layout | [time] | Sidebar, Top Bar, Content |
| 4. Data display | [time] | Table, Charts, Metrics |
| 5. App-specific | [time] | Product-unique components |
```

---

## Per-Component Document Structure

Every component `.md` file follows this structure (see `references/component-template.md` for full template):

1. **Header** — name, one-line description, source file, library
2. **Anatomy** — ASCII diagram with dimensions
3. **Variants** — table per variant (background, text, border, shadow)
4. **Sizes** — table with height, padding, text, icon, gap
5. **States** — default, hover, focus-visible, active, disabled, loading, error
6. **State Transitions** — state machine diagram + CSS property changes
7. **Animations** — trigger, property, duration, easing, from/to
8. **Internal Spacing** — pixel-level spacing diagram
9. **Dark Mode Differences** — property-by-property light vs dark
10. **Responsive Behavior** — breakpoint changes
11. **Accessibility** — role, keyboard, screen reader, contrast
12. **Composition Patterns** — how used with other components
13. **CSS Recreation** — complete CSS to recreate the component
14. **Anti-Patterns** — what NOT to do

---

## Writing Quality Standards

### Values Must Be Resolved

```
BAD:  Background: bg-primary
GOOD: Background: oklch(0.21 0.006 285.88) — Tailwind: bg-primary
```

### States Must Be Explicit

```
BAD:  (no mention of loading state)
GOOD: Loading: Not implemented — no loading state exists in the source
```

### Spacing Must Be Semantic

```
BAD:  Padding: 16px
GOOD: Padding: 16px (p-4) — standard card content padding, matches dialog padding
```

### Dark Mode Must Be Per-Component

```
BAD:  (dark mode only in system.md)
GOOD: | Property | Light | Dark |
      | Background | white | oklch(0.21...) |
      | Border | oklch(0.92...) | white/10% |
```

---

## Storybook Integration

If the target codebase uses Storybook, cross-reference:

```bash
# Find existing Storybook stories
find src -name "*.stories.tsx" -o -name "*.stories.jsx" | head -20

# Check Storybook config
ls .storybook/
```

Map Storybook stories to extraction output:
- Each story variant → document in the Variants section
- Each story arg → document in the Sizes section
- Storybook controls → document as component props

---

## Figma Token Sync

If the project uses Figma token sync:

```bash
# Find Figma token config
find . -name "*.tokens.json" -o -name "figma-tokens*" -o -name ".tokens-studio*" | head -5

# Check for Tokens Studio config
cat .tokens-studio/config.json 2>/dev/null
```

Document the sync pipeline:
```
Figma (Tokens Studio) → .tokens.json → Style Dictionary → CSS variables → Components
```

---

## Output Checklist

- [ ] INDEX.md created with coverage summary and reading path
- [ ] _summary.md created with design identity and recreation estimate
- [ ] system.md created with all foundation tokens
- [ ] Every component has its own numbered .md file
- [ ] All values resolved (not just class names)
- [ ] All states explicit (including "not implemented")
- [ ] Dark mode documented per component
- [ ] CSS recreation block in every component doc
- [ ] Composition patterns shown for every component
