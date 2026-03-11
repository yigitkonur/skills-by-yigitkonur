---
name: extract-saas-design
description: Use skill if you are extracting the visual system of a SaaS dashboard, admin panel, or internal tool into structured design documentation.
---

# Extract SaaS Design

Forensic visual extraction for dashboard codebases. Read every pixel, every state, every micro-interaction. Produce documentation so complete that someone can recreate the exact look-and-feel without copying a single line of source code.

**Use for:** SaaS dashboards, admin panels, internal tools, analytics platforms, CRM interfaces, developer tools, B2B products — any data-heavy application with persistent navigation and multi-state components.

**Not for:** Marketing sites, landing pages, e-commerce storefronts, blogs. Those have fundamentally different design DNA.

## Decision tree

```
What do you need?
│
├── Full design extraction ("extract everything")
│   ├── Where to start ──────────────────────► Quick start (below)
│   ├── Phase 1: Discovery ──────────────────► Discovery steps (below)
│   ├── Phase 2: Foundations ────────────────► Foundation extraction (below)
│   └── Phase 3: Components ─────────────────► Component extraction (below)
│
├── Extract foundations / tokens
│   ├── Color tokens ────────────────────────► references/extraction/color-extraction.md
│   ├── Typography scale ────────────────────► references/extraction/typography-extraction.md
│   ├── Spacing scale ───────────────────────► references/extraction/spacing-extraction.md
│   ├── Icons & assets ──────────────────────► references/extraction/icons-and-assets.md
│   └── System template ────────────────────► references/system-template.md
│
├── Extract specific components
│   ├── Component template ──────────────────► references/component-template.md
│   ├── Component agent prompt ──────────────► references/components-agent.md
│   └── Foundation agent prompt ─────────────► references/foundations-agent.md
│
├── Dashboard-specific patterns
│   ├── Layout, metrics, tables, settings ──► references/dashboard-patterns.md
│   └── Grid & responsive layout ───────────► references/layout/grid-and-responsive.md
│
├── Token formats & naming
│   ├── W3C DTCG, Style Dictionary, CSS ────► references/tokens/token-formats.md
│   └── Naming conventions ─────────────────► references/tokens/naming-conventions.md
│
├── Output & documentation
│   ├── Output format & templates ──────────► references/documentation/output-format.md
│   └── System template ────────────────────► references/system-template.md
│
└── Quality & audit
    ├── Quality checklist ───────────────────► references/quality-checklist.md
    ├── Consistency audit ───────────────────► references/audit/consistency-checklist.md
    └── Accessibility review ────────────────► references/audit/accessibility-review.md
```

## Quick start

### Interpreting the request

| User says | What to produce | Phases |
|-----------|----------------|--------|
| "Extract everything" / "full design system" | system.md + ALL foundation docs + ALL component docs | 1→2→3→4 |
| "Extract the button and card" | system.md (minimal) + detailed docs for EACH named component | 1→2→3(scoped) |
| "Just the tokens" / "foundations only" | system.md + 7 foundation docs only | 1→2 |
| "Audit the design consistency" | Run extraction verification against existing codebase | Audit only |
| "Extract dark mode" | system.md with mode differences + per-component dark mode sections | 1→2→3 |

### First 5 minutes

1. **Identify the styling approach**: Tailwind? CSS Modules? styled-components? CSS-in-JS? Check `package.json` and the first 3 component files.
2. **Find the token source**: `globals.css`, `tailwind.config.ts`, `theme.ts`, or `tokens.json`. This is ground truth for every value you'll extract.
3. **Resolve one token chain end-to-end**: Pick `--primary` or `bg-primary`. Trace it from usage → CSS variable → HSL/hex value. If you can resolve one, you can resolve them all.
4. **Count components**: `find src -name "*.tsx" -path "*/components/*" | wc -l`. This determines your parallelization strategy.
5. **Create `.design-soul/` directory** and start `INDEX.md`.

### Output structure

```
.design-soul/
├── INDEX.md                    # Master navigation
├── _summary.md                 # One-page snapshot
├── system.md                   # All foundation tokens
└── components/
    ├── foundations/             # 7 docs: spacing, colors, typography, shadows, radius, animations, states
    ├── controls/               # Button, Input, Select, Checkbox, etc.
    ├── containers/             # Card, Tabs, Accordion, Separator
    ├── navigation/             # Sidebar, Breadcrumb, Top Bar
    ├── overlays/               # Dialog, Popover, Tooltip, Dropdown
    ├── feedback/               # Badge, Toast, Alert, Skeleton
    ├── data-display/           # Table, Chart, Metric Card
    └── [app-specific]/         # Product-unique components
```

## Key patterns

### Phase 1: Discovery

Before extracting anything, map the codebase:

```bash
# Architecture
find . -name "globals.css" -o -name "tailwind.config.*" -o -name "theme.*"
find . -path "*/components/ui/*.tsx" | head -20
grep -rn 'cva(\|cn(' --include="*.tsx" src/ | head -5

# Count the work
echo "UI files:"; find src -name "*.tsx" -path "*/components/*" | wc -l
echo "CSS files:"; find src -name "*.css" | wc -l
```

| Codebase size | Strategy |
|---------------|----------|
| < 20 components | Sequential: one agent does everything |
| 20–50 | 3–4 agents: foundations + 2–3 component groups |
| 50–100 | 6–8 agents: foundations + one per category |
| 100+ | 8–12 agents: foundations + category agents + app-specific |

### Phase 2: Foundation extraction

The core technique is **frequency-based discovery**. For each visual property, grep all files, count occurrences, sort by frequency. The most-used values reveal the actual scale.

```bash
# Spacing scale — find the actual system
grep -roh 'p-[0-9.]*\|gap-[0-9.]*\|m-[0-9.]*' --include="*.tsx" src/ | sort | uniq -c | sort -rn

# Color tokens — map the full palette
grep -rn 'var(--' --include="*.css" src/ | grep -oh '--[a-z-]*' | sort | uniq -c | sort -rn

# Typography — identify the type scale
grep -roh 'text-\(xs\|sm\|base\|lg\|xl\)' --include="*.tsx" src/ | sort | uniq -c | sort -rn

# Shadows — enumerate elevation levels
grep -roh 'shadow-[a-z]*' --include="*.tsx" src/ | sort | uniq -c | sort -rn

# Border radius — map the shape scale
grep -roh 'rounded-[a-z]*' --include="*.tsx" src/ | sort | uniq -c | sort -rn
```

**Token chain resolution** — the critical technique:

```
Usage:        className="bg-primary"
↓ Tailwind:   bg-primary → var(--primary)
↓ CSS:        --primary: 222.2 47.4% 11.2%
↓ Resolved:   hsl(222.2, 47.4%, 11.2%) = #0f172a
```

Always resolve to the final computed value. Never document an alias without its resolved value.

**Seven foundation documents** to produce:
1. **Spacing** — base unit, scale, density zones (compact/default/relaxed)
2. **Colors** — primitives, semantic mapping, chart palette, dark mode overrides
3. **Typography** — font families, size scale, weight scale, line-height rules
4. **Shadows** — elevation levels with exact CSS values
5. **Border radius** — shape scale with component mapping
6. **Animations** — duration scale, easing functions, transition patterns
7. **Interactive states** — hover/focus/active/disabled/loading conventions

Templates: `references/system-template.md` for system.md, `references/foundations-agent.md` for agent prompts.

### Phase 3: Component extraction

For every reusable component, create a visual spec following `references/component-template.md`. Each doc includes:

1. **ASCII anatomy** — spatial layout with dimensions and slot names
2. **Variants table** — background, text, border, shadow per variant (default, destructive, outline, ghost, link)
3. **Sizes table** — height, padding-x, padding-y, font-size, icon-size, gap
4. **States** — default, hover, focus-visible, active, disabled, loading, error
5. **State transitions** — state machine diagram with exact CSS property changes and timing
6. **CSS recreation block** — copy-pasteable CSS that produces pixel-perfect recreation
7. **Dark mode differences** — property-by-property comparison table (light value → dark value)
8. **Composition** — how the component appears inside other components (button in dialog footer, badge in table cell)

**Component anatomy example:**

```
┌─ Button ─────────────────────────────────┐
│  [Icon 16×16]  [Label]  [Icon 16×16]     │
│  ├─ gap: 8px ──┤        ├─ gap: 8px ──┤  │
│  ├──── padding: 16px ─────────────────┤  │
└──────────────────────────────────────────┘
height: 36px (sm) | 40px (default) | 44px (lg)
```

**Multi-agent strategy for components:**

| Agent | Scope | Reads |
|-------|-------|-------|
| Controls agent | Button, Input, Select, Toggle, Checkbox, Radio | `references/component-template.md` |
| Container agent | Card, Tabs, Accordion, Sheet, Separator | `references/component-template.md` |
| Navigation agent | Sidebar, Breadcrumb, Pagination, Top Bar | `references/component-template.md` + `references/dashboard-patterns.md` |
| Overlay agent | Dialog, Popover, Tooltip, Dropdown, Command | `references/component-template.md` |
| Feedback agent | Badge, Toast, Alert, Progress, Skeleton | `references/component-template.md` |
| Data display agent | Table, Chart, Metric, List | `references/component-template.md` + `references/dashboard-patterns.md` |

### Phase 4: Dashboard-specific patterns

After shared components, extract product-unique patterns (see `references/dashboard-patterns.md`):

| Pattern | Key things to document |
|---------|----------------------|
| Dashboard layout | Sidebar width, collapse behavior, content area max-width |
| Metric displays | Number formatting, trend indicators, sparklines |
| Data tables | Column types, sort/filter/pagination, empty & loading states |
| Settings pages | Form groups, save patterns, dangerous zone styling |
| Command palette | Trigger, result grouping, keyboard hints |
| Empty states | Icon style, CTA placement, first-run vs filtered-empty |

### Five extraction principles

1. **Document what you SEE, not what you THINK.** `text-primary` might be any color. Resolve every token to its computed value.
2. **Frequency reveals the actual system.** 8px used 193 times vs 10px used 3 times. The 10px is probably a bug.
3. **Absence is information.** No loading state on a button? Write "Loading: not implemented."
4. **Recreation is the test.** Could someone recreate pixel-perfect UI from ONLY your docs?
5. **Dashboard DNA lives in density.** Tight spacing in tables vs generous spacing in settings — document the tension.

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Guessing instead of reading | `rounded-md` might be 6px or 8px depending on `--radius`. Always resolve the variable chain. |
| Skipping "boring" states | Disabled (opacity + pointer-events), loading, error/invalid — document ALL of them, even as "not implemented." |
| Documenting components in isolation | A button spec without showing it in a card footer or dialog action bar is useless. Document composition. |
| Flat CSS without state coverage | `.btn { background: blue }` is incomplete. Include `:hover`, `:focus-visible`, `:disabled`, `[data-loading]`. |
| Ignoring mega-components | Sidebars have 15+ sub-components. Document the full hierarchy, not just the top-level wrapper. |
| Missing animation composition | Floating elements compose fade + zoom + slide. Document all three layers, not just `transition: all 0.15s`. |
| Dark mode only in system.md | Every component doc needs its own dark mode differences section. |
| Spacing without semantics | Not just "gap: 8px" but "8px = dense table gap" vs "16px = card padding." Spacing is semantic. |
| Missing opacity semantics | 0.5 = disabled, 0.9 = hover darken, 0.35 = muted text. Document the scale. |
| Forgetting chart colors | Data visualization palette is separate from UI colors. Always extract it. |

## Minimal reading sets

### "I need to extract just the design tokens"

- `references/extraction/color-extraction.md`
- `references/extraction/typography-extraction.md`
- `references/extraction/spacing-extraction.md`
- `references/system-template.md`

### "I need to extract a full design system"

- `references/foundations-agent.md`
- `references/components-agent.md`
- `references/component-template.md`
- `references/system-template.md`
- `references/quality-checklist.md`
- `references/documentation/output-format.md`

### "I need to document specific components"

- `references/component-template.md`
- `references/components-agent.md`
- `references/extraction/icons-and-assets.md`

### "I need dashboard-specific patterns"

- `references/dashboard-patterns.md`
- `references/layout/grid-and-responsive.md`

### "I need to understand token formats"

- `references/tokens/token-formats.md`
- `references/tokens/naming-conventions.md`

### "I need to audit the extraction quality"

- `references/quality-checklist.md`
- `references/audit/consistency-checklist.md`
- `references/audit/accessibility-review.md`

### "I need to structure the output"

- `references/documentation/output-format.md`
- `references/system-template.md`
- `references/component-template.md`

## All reference files

| Directory | File | Purpose |
|-----------|------|---------|
| `references/` | `system-template.md` | Template for system.md (all foundation tokens) |
| `references/` | `component-template.md` | Template for individual component documentation |
| `references/` | `foundations-agent.md` | Agent prompt for foundation extraction |
| `references/` | `components-agent.md` | Agent prompt for component extraction |
| `references/` | `dashboard-patterns.md` | SaaS dashboard-specific patterns (metrics, tables, settings) |
| `references/` | `quality-checklist.md` | Extraction quality verification checklist |
| `references/extraction/` | `color-extraction.md` | Color extraction methodology with grep commands |
| `references/extraction/` | `typography-extraction.md` | Typography scale extraction methodology |
| `references/extraction/` | `spacing-extraction.md` | Spacing scale extraction with frequency analysis |
| `references/extraction/` | `icons-and-assets.md` | Icon library, sizing, SVG patterns, avatars |
| `references/tokens/` | `token-formats.md` | W3C DTCG, CSS variables, Tailwind, Style Dictionary |
| `references/tokens/` | `naming-conventions.md` | Semantic, scale, and component token naming |
| `references/layout/` | `grid-and-responsive.md` | Dashboard grid, sidebar, responsive breakpoints |
| `references/documentation/` | `output-format.md` | .design-soul/ structure and document templates |
| `references/audit/` | `consistency-checklist.md` | Token and component consistency audit |
| `references/audit/` | `accessibility-review.md` | WCAG compliance, contrast, keyboard, ARIA |

## Final reminder

This skill is split into many focused reference files organized by domain. Do not load everything at once. Start with the smallest relevant reading set above, then expand into neighboring references only when the task actually requires them. Every reference file in `references/` is explicitly routed from the decision tree above.
