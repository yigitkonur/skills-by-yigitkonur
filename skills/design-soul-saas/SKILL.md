---
name: design-soul-saas
description: "Use skill if you are documenting the visual system of a SaaS dashboard, admin panel, or internal tool."
license: MIT
metadata:
  author: yigitkonur
  version: "1.0"
---

# Design Soul — SaaS Dashboard Edition

Forensic visual DNA extraction for dashboard codebases. Read every pixel, every state, every micro-interaction. Produce documentation so complete that someone can recreate the exact look-and-feel without copying a single line of source code.

## Scope

**Use for:** SaaS dashboards, admin panels, internal tools, settings interfaces, data-heavy apps, analytics platforms, CRM interfaces, developer tools, B2B products.

**Not for:** Marketing sites, landing pages, e-commerce storefronts, blogs, portfolio sites. Those have fundamentally different design DNA — hero sections, testimonials, pricing tables. Dashboards live in a different world of density, navigation hierarchy, and persistent state.

**Works with any stack:** Tailwind, CSS modules, styled-components, CSS-in-JS, plain CSS, MUI, Ant Design, Chakra — the extraction adapts. The reference files include Tailwind-to-CSS conversion tables because Tailwind is the most common case, but for non-Tailwind codebases, read the CSS directly and document the actual property values. The output format (pixel values, hex colors, CSS recreation blocks) is framework-agnostic.

---

## Philosophy

Five principles govern this extraction. They exist because design systems lie — the stated system and the actual system diverge over time. Your job is to document what IS, not what was intended.

### 1. Document What You SEE, Not What You THINK

Never assume a class does what its name suggests. `text-primary` might resolve to any color depending on the theme configuration. Read the actual CSS variables. Resolve every token to its computed value. If you're not reading the source file, you're guessing — and guesses compound into a useless spec.

### 2. Frequency Reveals the Actual System

The design system isn't what the docs say — it's what the code uses. When you grep for spacing values and find `8px` used 193 times but `10px` used 3 times, that tells you the real scale. The 10px instances are probably bugs or exceptions. Frequency counting separates the system from the noise.

### 3. Absence Is Information

If a button has no loading state, that's a design decision worth documenting. Write "Loading: not implemented" rather than skipping the section. The person recreating this design needs to know what's deliberately missing, not just what's present. Every blank section in your output is a spec that says "build this yourself."

### 4. Recreation Is the Test

After extraction, ask: "Could a developer who has never seen the original codebase recreate a pixel-perfect version using ONLY these documents?" If the answer is "mostly, but they'd need to guess at X" — document X. This is the only quality bar that matters.

### 5. Dashboard DNA Lives in Density

SaaS dashboards have a unique visual signature: information density, persistent navigation, data-forward layouts, multi-state components, and subtle hierarchy that guides attention without decoration. When extracting, pay special attention to how the app manages density — tight spacing in data tables vs. generous spacing in settings pages. This tension IS the design system.

---

## What This Produces

```
.design-soul/
├── INDEX.md                               # Master navigation: categories, reading path, coverage summary
├── _summary.md                            # One-page snapshot: scope, key decisions, recreation estimate
├── system.md                              # Foundations: tokens, scales, strategies
└── components/
    ├── foundations/
    │   ├── 01-spacing-scale.md
    │   ├── 02-color-tokens.md
    │   ├── 03-typography-scale.md
    │   ├── 04-shadow-depth.md
    │   ├── 05-radius-scale.md
    │   ├── 06-animation-system.md
    │   └── 07-focus-and-states.md
    ├── controls/
    │   ├── 01-button.md
    │   ├── 02-input.md
    │   └── ...one file per component
    ├── containers/
    │   ├── 01-card.md
    │   ├── 02-sidebar.md
    │   └── ...
    ├── navigation/
    │   ├── 01-sidebar-nav.md
    │   ├── 02-top-bar.md
    │   ├── 03-breadcrumb.md
    │   └── ...
    ├── overlays/
    │   ├── 01-dialog.md
    │   ├── 02-command-palette.md
    │   └── ...
    ├── feedback/
    │   ├── 01-badge.md
    │   ├── 02-toast.md
    │   └── ...
    ├── data-display/
    │   ├── 01-table.md
    │   ├── 02-metric-card.md
    │   ├── 03-chart.md
    │   └── ...
    └── [app-specific]/
        └── ...custom patterns unique to this product
```

The output directory is `.design-soul/` (not `.interface-design/`). This distinguishes extraction output from a hand-authored design system.

---

## Interpreting the Request

Before starting, understand what scope the user is asking for:

| User says | What to produce | Phases to run |
|-----------|----------------|---------------|
| "Extract everything" / "full design system" / "complete visual DNA" | system.md + ALL foundation docs + ALL component docs with CSS recreation | 1→2→3→4→5→6 |
| "Extract the button and card" / specific components | system.md (minimal) + detailed docs for EACH named component | 1→2→3(scoped)→5 |
| "Just the tokens" / "foundations only" / "design tokens" | system.md + foundation docs only | 1→2→5 |

**Critical rule for focused extraction:** When the user names specific components (e.g., "button and card"), you MUST produce a separate document for EACH named component. Do not stop after the first one. If you can only go deep on some, go shallower on all rather than skipping any.

**Critical rule for full extraction:** "Everything" means Phase 2 AND Phase 3. Don't stop after system.md — the component docs with CSS recreation blocks are what make the output actually recreatable. system.md alone is the foundation, not the finished product.

---

## Execution: Six Phases

### Phase 1: Discovery

Before extracting anything, map the codebase. Dashboards have specific architectural patterns — find them.

**Step 1.1 — Identify the architecture:**

```
Answer these questions by searching the codebase:
1. Monorepo or single app?
2. Where is the component library? (packages/ui, src/components/ui, etc.)
3. Styling system? (Tailwind, CSS modules, styled-components, CSS-in-JS)
4. Component library? (shadcn/ui, Radix, Headless UI, Chakra, MUI, Ant Design, custom)
5. Where are CSS/theme files? (globals.css, theme.ts, tailwind.config)
6. Where is the dashboard-specific code? (app/dashboard, src/pages, etc.)
7. Is there a sidebar? A top bar? Both? Neither?
```

Search for these:
```
Glob: **/globals.css, **/global.css, **/theme.*, **/tokens.*
Glob: **/tailwind.config.*, **/postcss.config.*
Glob: **/components/ui/*.tsx, **/components/ui/*.jsx
Grep: "cva(" or "variants:" — CVA variant patterns
Grep: "cn(" — className merge utility (indicates shadcn/ui-like patterns)
Grep: "sidebar" — navigation architecture
Grep: "command" or "cmdk" — command palette patterns
Grep: "data-table" or "DataTable" — data display patterns
```

**Step 1.2 — Count the work:**

```
Total UI files: [count]
Shared components: [count]
Dashboard-specific components: [count]
CSS/theme files: [count]
```

**Step 1.3 — Plan execution:**

| Codebase size | Strategy |
|---------------|----------|
| < 20 components | Sequential: one agent does everything |
| 20-50 components | 3-4 agents: foundations + 2-3 component groups |
| 50-100 components | 6-8 agents: foundations + one per category |
| 100+ components | 8-12 agents: foundations + category agents + app-specific agents |

---

### Phase 2: Foundation Extraction

This phase extracts the invisible system — the tokens, scales, and strategies that hold the visual identity together. It runs FIRST because component agents need the resolved token values.

Read `references/foundations-agent.md` for the detailed agent prompt.

**What this phase produces:**
- `.design-soul/system.md` — The master token reference
- 7 foundation documents in `.design-soul/components/foundations/`

**The core technique: frequency-based discovery.**

For every visual category (spacing, colors, typography, shadows, radius, animations), grep across ALL component files and count occurrences. Sort by frequency. The most-used values reveal the actual scale.

```
Example output:
Spacing: 2px(42x), 4px(57x), 6px(67x), 8px(193x), 12px(60x), 16px(48x), 24px(26x), 32px(13x)
  → Base: 4px. Scale: 0.5, 1, 1.5, 2, 3, 4, 6, 8

Radius: 4px(51x), pill(49x), 6px(41x), 8px(26x), 12px(5x)
  → Scale: 4, 6, 8, 12, pill

Depth: borders(340x), shadow-xs(55x), shadow-sm(30x), shadow-md(15x), shadow-lg(8x)
  → Strategy: Borders-first with hierarchical shadow escalation
```

**Critical for dashboards:** Pay special attention to:
- Dense spacing patterns in data tables vs. generous spacing in settings
- Sidebar-specific token overrides (many SaaS apps have sidebar-specific colors)
- Chart/data visualization color palettes (separate from UI colors)
- Monospace font usage for data display (tabular-nums, code blocks)

See `references/system-template.md` for the exact output format.

**Micro-interaction documentation goes beyond listing transitions.** For each interactive component:
1. Document the **timing hierarchy**: micro (50-80ms for press feedback), standard (150ms for hover), slow (200-300ms for enter/exit)
2. Document **easing strategy**: which easing for hover vs. focus vs. enter vs. exit and WHY
3. Document **opacity scale semantics**: what does 0.5 mean (disabled)? What does 0.9 mean (hover darken)?
4. Document **animation composition**: floating elements often compose fade + zoom + slide — document all three layers

**Concrete output**: At the end of Phase 2, you should have created these actual files:
- `.design-soul/system.md` (use template from `references/system-template.md`)
- `.design-soul/components/foundations/01-spacing-scale.md`
- `.design-soul/components/foundations/02-color-tokens.md`
- `.design-soul/components/foundations/03-typography-scale.md`
- `.design-soul/components/foundations/04-shadow-depth.md`
- `.design-soul/components/foundations/05-radius-scale.md`
- `.design-soul/components/foundations/06-animation-system.md`
- `.design-soul/components/foundations/07-focus-and-states.md`

Create these files using the Write tool. Do not just describe what should be in them — actually write them.

---

### Phase 3: Component Extraction

For every reusable component in the codebase, create a complete visual specification following the template in `references/component-template.md`.

**Completeness is non-negotiable.** Every component gets its own `.md` file. Every file includes a CSS recreation block. If the user asked for specific components, document ALL of them — not just the first one you get to. Track what's been produced and verify nothing was missed before moving to Phase 5.

**Dashboard-specific component categories:**

| Category | Directory | What goes here |
|----------|-----------|----------------|
| Controls | `controls/` | Button, Input, Textarea, Select, Checkbox, Switch, Toggle, Radio, Slider, Date picker, Label, Form field |
| Containers | `containers/` | Card, Separator, Resizable panels, Scroll area, Accordion, Collapsible, Tabs (content variant) |
| Navigation | `navigation/` | Sidebar, Top bar, Breadcrumb, Tabs (nav variant), Workspace switcher, User menu, Mobile nav |
| Overlays | `overlays/` | Dialog, Sheet/Drawer, Popover, Tooltip, Dropdown menu, Context menu, Command palette, Alert dialog |
| Feedback | `feedback/` | Badge, Alert, Progress, Skeleton, Spinner, Toast/Notification, Empty state, Kbd |
| Data Display | `data-display/` | Table, Pagination, Calendar, Chart, Metric card, KPI, Sparkline, Carousel, Avatar, Avatar group |
| App-Specific | `[product-name]/` | AI elements (messages, tool calls, prompts), workflow builders, canvas editors, terminal UIs, or any components unique to this specific product. Identified in Phase 1 Discovery. |

Launch one agent per category. Each agent:
1. Reads EVERY source file in its assigned components
2. Follows the component template exactly (see `references/component-template.md`)
3. Writes one `.md` file per component
4. Reports: component name, variants found, states found, animations found

**State machine documentation is required for interactive components.** For every button, input, select, toggle, dialog, and sidebar menu item, document the state flow:

```
IDLE → HOVER → ACTIVE → IDLE (mouse interaction)
IDLE → FOCUS-VISIBLE → ACTIVE → IDLE (keyboard interaction)
IDLE → DISABLED (programmatic)
IDLE → LOADING → IDLE or ERROR (async interaction)
```

For each transition, document: what CSS properties change, the duration, the easing, and any visual cues (color shift, opacity, shadow, ring).

**Provide each agent with:**
- The resolved CSS variables from Phase 2
- The list of source files to read
- The component template
- The output directory path

**Concrete output**: For each component, create a file at `.design-soul/components/{category}/{NN}-{component-name}.md`. Use the Write tool. Example: `.design-soul/components/controls/01-button.md`, `.design-soul/components/data-display/01-table.md`.

After all component docs are written, create:
- `.design-soul/INDEX.md` — master navigation
- `.design-soul/_summary.md` — one-page snapshot

---

### Phase 4: Dashboard-Specific Patterns

After shared components are documented, extract patterns unique to this specific dashboard product. These are the patterns that make THIS product feel different from every other dashboard.

Read `references/dashboard-patterns.md` for the full catalog of SaaS-specific patterns to look for.

**Common dashboard-specific categories:**

| Pattern | What to look for |
|---------|-----------------|
| Dashboard layout | Main grid structure, sidebar + content proportions, responsive breakpoints |
| Metric displays | How KPIs are shown — hero numbers, sparklines, comparison deltas, trend badges |
| Data tables | Column widths, row density, sort indicators, filter bars, bulk actions, pagination |
| Settings pages | Form groups, section headers, save patterns, plan/billing display |
| Onboarding | Empty states, first-run experience, feature tours |
| Search/Command | Command palette (Cmd+K), search patterns, quick actions |
| Multi-tenant | Workspace switcher, org selector, team context |
| Loading | Skeleton patterns, progressive loading, optimistic updates |

Create a `[product-name]-patterns/` directory for anything that doesn't fit the standard categories.

---

### Phase 5: Verification

After all agents complete, verify the extraction is complete and internally consistent.

**Completeness check:**
```
For each component in the codebase:
  [ ] Has a documentation file?
  [ ] All variants documented?
  [ ] All states documented? (default, hover, focus, active, disabled, loading, error, selected)
  [ ] CSS recreation block present?
  [ ] ASCII anatomy diagram present?
```

**Cross-reference check:**
```
For each token referenced in component docs:
  [ ] Token exists in the foundation docs?
  [ ] Both light and dark values documented?

For each animation in component docs:
  [ ] Animation exists in 06-animation-system.md?
  [ ] Duration and easing match?
```

**The ultimate test:**
> Could a developer who has NEVER seen the original codebase recreate a pixel-perfect version using ONLY these documents?

If the answer is "yes, for every component" — the extraction is complete.
If the answer is "mostly, but they'd need to guess at [X]" — document [X].

See `references/quality-checklist.md` for the full verification checklist.

---

### Phase 6: Summary Report

Write two meta-files to complete the extraction:

**File 1: `.design-soul/_summary.md`** — One-page snapshot:

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
| Containers | N | N | N | N |
| Navigation | N | N | N | N |
| Overlays | N | N | N | N |
| Feedback | N | N | N | N |
| Data Display | N | N | N | N |
| [App-specific] | N | N | N | N |
| **Total** | **N** | **N** | **N** | **N** |

## Design Identity

1. Depth strategy: [borders-first / shadows / layered / surface-shifts]
2. Spacing base: [N]px with scale [...]
3. Radius personality: [sharp / medium / soft]
4. Animation philosophy: [minimal / moderate / rich]
5. Color architecture: [token-based / direct / hybrid]
6. Dark mode approach: [.dark class / media query / JS-driven]
7. Information density: [compact / balanced / spacious]
8. Navigation pattern: [sidebar / top-bar / both / tabs]

## Recreation Estimate

To recreate this design system from these docs:
- Foundations (tokens, theme): ~[N] tokens to define
- Core components: ~[N] components
- Dashboard-specific: ~[N] unique patterns
```

**File 2: `.design-soul/INDEX.md`** — Master navigation:

```markdown
# Design Soul Index

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

## Key Design Decisions

1. [Decision about depth strategy — borders vs. shadows vs. layered approach]
2. [Decision about spacing base unit and scale multipliers]
3. [Decision about color architecture — CSS variables, semantic naming]
4. [Decision about animation philosophy — when to animate, when not to]
5. [Decision about dark mode implementation — class toggle, media query, or JS]
6. [Decision about density — compact data tables vs. spacious settings pages]
7. [Decision about typography — font stacks, scale, monospace usage]
8. [Decision about responsive strategy — breakpoints, mobile nav behavior]

## Distinctive Patterns

Patterns unique to this product that distinguish it from generic dashboards:
- [Pattern 1 — e.g., AI message bubbles with streaming indicators]
- [Pattern 2 — e.g., sidebar with collapsible sub-groups and badge counts]
- [Pattern 3 — e.g., command palette with contextual action categories]

## Recommended Reading Path

1. Start with `_summary.md` for the high-level picture
2. Read `system.md` for all token values and scales
3. Read `components/foundations/` for detailed token documentation
4. Read the category most relevant to your work (usually `controls/` or `navigation/`)
5. Read `[app-specific]/` for product-unique components

## Recreation Envelope

- **Tokens to define:** ~[N] CSS custom properties
- **Components to build:** ~[N] total ([N] core + [N] app-specific)
- **Estimated effort:** [S/M/L] — based on component count and interaction complexity
```

Create both files using the Write tool.

---

## Extraction Tips for SaaS Dashboards

**Sidebar is the signature.** In most SaaS products, the sidebar IS the product's personality. Document it thoroughly — width, collapse behavior, section grouping, active indicators, mobile behavior, keyboard shortcuts.

**Data tables reveal the system.** Tables are where density, typography, spacing, and color all converge. A well-documented table specification tells you more about the design system than any other single component.

**Empty states are design.** How the app looks when there's no data is as important as how it looks with data. Document empty state patterns — they reveal the product's personality.

**Settings pages test consistency.** Settings pages are where design systems break down. They have unique layout needs (form groups, toggles, descriptions) that don't fit the main dashboard grid. Documenting settings patterns reveals how disciplined the system actually is.

**Command palette is the power-user signature.** If the app has Cmd+K or similar, document it thoroughly — it's often the most polished component in a SaaS product.

---

## Anti-Patterns: What Agents Get Wrong

These are the most common ways extraction agents fail. Read this before starting.

### 1. Guessing Instead of Reading
The agent sees `rounded-md` and writes "8px" without checking the `--radius` variable. In this codebase, `rounded-md` might be `calc(0.625rem - 2px)` = 8px, or it might be `6px` with a different base. **Always resolve the variable chain.**

### 2. Skipping "Boring" States
Agents love documenting hover states and forget about:
- **Disabled state** — opacity, pointer-events, cursor changes
- **Loading state** — even if it's "not implemented", say so
- **Error/invalid state** — `aria-invalid`, `data-[invalid]`, destructive ring
- **Selected/active state** — `data-[state=active]`, `aria-selected`
- **Empty state** — what does a table look like with no rows?

### 3. Documenting Components in Isolation
A button spec is useless if it doesn't show how the button sits inside a card footer, a dialog action bar, or a table row. **Document composition**: how this component typically pairs with others.

### 4. Flat CSS Without State Coverage
Writing `.btn { background: #171717; }` without `.btn:hover`, `.btn:focus-visible`, `.btn:disabled` is incomplete CSS. **Every CSS recreation block must include all interactive states.**

### 5. Ignoring Mega-Components
Sidebars often have 15-20 sub-components. Agents document the top-level sidebar and skip SidebarGroup, SidebarGroupLabel, SidebarMenuItem, SidebarMenuAction, SidebarMenuBadge. **Decompose mega-components into their full hierarchy.**

### 6. Missing Animation Composition
"Transition: all 0.15s ease" is not enough. Many floating elements compose multiple animations: fade-in + zoom-in + slide-in. Document the **composition**, not just individual properties.

### 7. Forgetting Dark Mode in Component Docs
Documenting tokens in system.md but not showing how each component LOOKS different in dark mode. Every component doc needs a dark mode differences section.

### 8. No Spacing Rhythm Documentation
Writing "gap: 8px" without explaining WHY 8px. Is it the standard control gap? The dense table gap? The spacious card gap? **Spacing is semantic, not arbitrary.**

---

## Reference Files

For detailed templates and checklists, read these as needed:

| File | When to read | What it contains |
|------|-------------|-----------------|
| `references/system-template.md` | Phase 2 — writing system.md | Complete token template with all categories |
| `references/component-template.md` | Phase 3 — documenting each component | Per-component structure: anatomy, variants, states, animations, CSS |
| `references/foundations-agent.md` | Phase 2 — spawning foundation agent | Detailed instructions for token extraction with frequency counting |
| `references/components-agent.md` | Phase 3 — spawning component agents | Instructions for component visual extraction, Tailwind-to-CSS tables |
| `references/dashboard-patterns.md` | Phase 4 — dashboard-specific extraction | SaaS pattern catalog: metrics, tables, settings, onboarding, search |
| `references/quality-checklist.md` | Phase 5 — verification | Full checklist: system-level, per-component, cross-reference, ultimate test |
