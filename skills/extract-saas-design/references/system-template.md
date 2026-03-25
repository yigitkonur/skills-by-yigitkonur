# System Template

Use this template for `.design-soul/system.md` (created at the **codebase root**).

> **Target Mode Check -- Run These First**
>
> Before filling in the template, decide whether the target is a repo-backed UI or an offline snapshot. Apply the path rules in `references/extraction/target-modes.md`.
>
> Repo-backed UI examples:
> ```bash
> # Framework
> grep -l '"next"' package.json && echo "Next.js detected"
> # UI library
> ls src/components/ui/ 2>/dev/null && echo "shadcn/ui detected"
> # Styling
> grep -rl '@import.*tailwindcss' --include="*.css" src/ . 2>/dev/null && echo "Tailwind v4"
> ls tailwind.config.* 2>/dev/null && echo "Tailwind v3"
> # Icons
> grep '"lucide-react"' package.json && echo "Lucide icons"
> # Charts
> grep '"recharts"' package.json && echo "Recharts detected"
> ```
>
> Offline snapshot examples:
> ```bash
> # Inventory the captured UI files
> find . -maxdepth 2 -type f \( -name "*.html" -o -name "*.css" -o -name "*.svg" \)
> # Detect Tailwind CSS markers if the snapshot preserved them
> grep -rl '@import.*tailwindcss\|@theme' --include="*.css" .
> ```
>
> If snapshot mode applies, skip framework/package checks and fill library-specific sections with `N/A` or `not implemented` where the evidence truly does not exist.

 Fill in every section from codebase analysis. Use `[N/A]` only when genuinely not applicable — not when you haven't checked.

---

```markdown
# Design Soul

Extracted from [N] UI files across [directories].
Date: [extraction date]
Source: [repo path or name]

---

## Direction

Product type: [SaaS dashboard / Admin panel / Internal tool / Analytics platform / etc.]
Primary task: [What users do most — analyze data / manage records / configure settings / etc.]
Density: [Compact / Balanced / Spacious]
Navigation: [Sidebar / Top bar / Both / Tabs]

---

## Spacing

Base unit: [N]px

| Token | Value | Frequency | Primary usage |
|-------|-------|-----------|---------------|
| 0 | 0px | Nx | Reset |
| 0.5 | 2px | Nx | Micro gaps (badge padding) |
| 1 | 4px | Nx | Tight spacing (icon gaps) |
| 1.5 | 6px | Nx | Compact controls (small button icon-text gap) |
| 2 | 8px | Nx | PRIMARY: content gaps, inline margins |
| 3 | 12px | Nx | Input horizontal padding, card content gaps |
| 4 | 16px | Nx | Card padding, dialog padding |
| 5 | 20px | Nx | Section padding |
| 6 | 24px | Nx | Card internal padding, generous gaps |
| 8 | 32px | Nx | Section spacing |
| 10 | 40px | Nx | Major separation |
| 12 | 48px | Nx | Page-level spacing |
| 16 | 64px | Nx | Hero spacing |

Layout strategy: [Flexbox + gap / margin-based / CSS grid / mixed]
Dominant pattern: [gap-based / margin-based]

### Density Zones

| Zone | Spacing character | Where |
|------|-------------------|-------|
| Data-dense | [tight values used] | Tables, data grids, metric cards |
| Standard | [medium values used] | Forms, settings, content areas |
| Spacious | [generous values used] | Landing sections, onboarding, empty states |

---

## Radius

Base: --radius: [value]

| Token | Value | Frequency | Components |
|-------|-------|-----------|------------|
| sm | [N]px | Nx | Close buttons, checkboxes |
| default | [N]px | Nx | General elements |
| md | [N]px | Nx | Buttons, inputs, toggles |
| lg | [N]px | Nx | Cards, dialogs, containers |
| xl | [N]px | Nx | Large cards, modals |
| full | 9999px | Nx | Badges, avatars, switches, pills |

### Radius by component type

| Category | Radius | Why |
|----------|--------|-----|
| Interactive controls | [token] | [rationale] |
| Content containers | [token] | [rationale] |
| Floating overlays | [token] | [rationale] |
| Pill elements | full | Status badges, tags |
| Toggle elements | full | Circular switches and radio |

---

## Depth

Strategy: [borders-first / subtle-shadows / layered-shadows / surface-shifts]
Primary depth cue: [border / shadow / surface-color-shift]

### Shadow Scale

| Token | Value | Components |
|-------|-------|------------|
| none | none | Reset, flat elements |
| xs | [value] | Inputs, outline buttons |
| sm | [value] | Cards |
| md | [value] | Popovers, dropdowns |
| lg | [value] | Dialogs, modals |
| xl | [value] | Maximum elevation |

### Focus Ring System

| Token | Value | Usage |
|-------|-------|-------|
| ring-width | [N]px | Standard focus ring |
| ring-color | [value] | Ring color with opacity |
| ring-offset | [N]px | Gap between element and ring |

### Elevation Map

| Level | Surface | Shadow | Border | Used by |
|-------|---------|--------|--------|---------|
| 0 (canvas) | --background | none | none | Page body |
| 1 (surface) | --card | [shadow] | [border] | Cards, panels |
| 2 (floating) | --popover | [shadow] | [border] | Popovers, dropdowns |
| 3 (overlay) | --background | [shadow] | [border] | Dialogs, modals |
| 4 (backdrop) | [value] | none | none | Overlay backdrop |

---

## Typography

### Font Families

| Role | Family | Source | Usage |
|------|--------|--------|-------|
| Sans | [name] | [CDN/local/system] | App body text |
| Mono | [name] | [source] | Code, data, IDs |
| Serif | [name or none] | [source] | [usage or N/A] |

### Size Scale

| Token | Size | Frequency | Typical context |
|-------|------|-----------|-----------------|
| [10px] | 10px | Nx | Micro badges, annotations |
| xs | 12px | Nx | Labels, meta text, badges |
| sm | 14px | Nx | Body text, descriptions, table cells |
| base | 16px | Nx | Input text, comfortable body |
| lg | 18px | Nx | Dialog/card titles |
| xl | 20px | Nx | Section headers |
| 2xl | 24px | Nx | Page headings |
| 3xl | 30px | Nx | Dashboard hero metrics |

### Weight Scale

| Token | Weight | Frequency | Typical context |
|-------|--------|-----------|-----------------|
| normal | 400 | Nx | Body text, descriptions |
| medium | 500 | Nx | Buttons, labels, badges |
| semibold | 600 | Nx | Card titles, headings |
| bold | 700 | Nx | Page titles, emphasis |

### Special Typography Patterns

| Pattern | Value | Where used |
|---------|-------|------------|
| Tabular numbers | tabular-nums | Data tables, timestamps, metrics |
| Uppercase tracking | uppercase + tracking-wider | Badges, section labels |
| Tight leading | leading-none / leading-tight | Card titles, metric numbers |
| Truncation | truncate / line-clamp-N | Sidebar labels, table cells |
| Mono for data | font-mono | IDs, codes, terminal output |

---

## Color System

### Architecture

Color space: [oklch / hsl / hex / rgb] -- modern shadcn (2024+) uses oklch; older uses hsl. oklch: `oklch(lightness chroma hue)` L=0-1, C=0-0.4, H=0-360
Mode switching: [.dark class / @media prefers-color-scheme / data-theme / JS-driven]

### Surface Tokens

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| --background | [value] | [value] | Page canvas |
| --foreground | [value] | [value] | Primary text |
| --card | [value] | [value] | Card surfaces |
| --card-foreground | [value] | [value] | Card text |
| --popover | [value] | [value] | Floating surfaces |
| --popover-foreground | [value] | [value] | Floating text |

### Interactive Tokens

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| --primary | [value] | [value] | Primary buttons, accent actions |
| --primary-foreground | [value] | [value] | Text on primary |
| --secondary | [value] | [value] | Secondary actions |
| --secondary-foreground | [value] | [value] | Text on secondary |
| --accent | [value] | [value] | Hover backgrounds, active states |
| --accent-foreground | [value] | [value] | Text on accent |
| --muted | [value] | [value] | Disabled backgrounds |
| --muted-foreground | [value] | [value] | Placeholder, metadata text |

### Control Tokens

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| --input | [value] | [value] | Input borders |
| --ring | [value] | [value] | Focus ring color |

### Border Tokens

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| --border | [value] | [value] | Standard borders |
| --border-subtle | [value] | [value] | Softer separation (if exists) |

### Semantic Status

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| --destructive | [value] | [value] | Errors, delete actions |
| --success | [value] | [value] | Confirmations, positive states |
| --warning | [value] | [value] | Caution, attention needed |
| --info | [value] | [value] | Informational highlights |

### Chart / Data Visualization Palette

| Index | Color | Usage |
|-------|-------|-------|
| chart-1 | [value] | Primary data series |
| chart-2 | [value] | Secondary data series |
| chart-3 | [value] | Tertiary |
| chart-4 | [value] | Quaternary |
| chart-5 | [value] | Fifth |

### Sidebar-Specific Tokens (if applicable)

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| --sidebar-background | [value] | [value] | Sidebar canvas |
| --sidebar-foreground | [value] | [value] | Sidebar text |
| --sidebar-accent | [value] | [value] | Active item highlight |
| --sidebar-border | [value] | [value] | Sidebar borders |

### Opacity Patterns

| Modifier | Usage |
|----------|-------|
| /50 | Focus rings, hover backgrounds |
| /30 | Subtle backgrounds, dark mode input bg |
| /10 | Ghost button hover, faint highlights |
| /5 | Barely visible backgrounds |

---

## Animation

### Library

Animation source: [tw-animate-css / framer-motion / CSS native / etc.]

### Transition Defaults

| Property set | Duration | Easing | Components |
|-------------|----------|--------|------------|
| all | 150ms | ease | Buttons, badges |
| color, box-shadow | 150ms | ease | Inputs, links |
| opacity | 150ms | ease | Fade elements |
| transform | 200ms | ease-out | Scale effects |
| width, height | 300ms | ease-in-out | Sidebar collapse, accordion |

### Enter/Exit Animations

| Animation | Direction | Duration | Easing | Properties |
|-----------|-----------|----------|--------|------------|
| fade-in | Enter | [N]ms | ease-out | opacity: 0 -> 1 |
| fade-out | Exit | [N]ms | ease-in | opacity: 1 -> 0 |
| zoom-in-95 | Enter | [N]ms | ease-out | scale: 0.95 -> 1, opacity: 0 -> 1 |
| zoom-out-95 | Exit | [N]ms | ease-in | scale: 1 -> 0.95, opacity: 1 -> 0 |
| slide-in-from-right | Enter | [N]ms | ease-in-out | translateX: 100% -> 0 |
| slide-out-to-right | Exit | [N]ms | ease-in-out | translateX: 0 -> 100% |
| accordion-down | Enter | [N]ms | ease-out | height: 0 -> auto |
| accordion-up | Exit | [N]ms | ease-out | height: auto -> 0 |

### Duration Hierarchy

| Context | Enter | Exit | Why |
|---------|-------|------|-----|
| Hover states | instant | instant | Must feel responsive |
| Focus rings | 0ms | 0ms | Accessibility: immediate feedback |
| Tooltips | 150ms | 100ms | Quick information |
| Dialogs | 200ms | 150ms | Noticeable but not slow |
| Sheets/drawers | 300-500ms | 200-300ms | Physical slide feeling |

Principle: Exit faster than enter. Users closing things want it gone.

---

## Breakpoints

| Name | Width | Key layout changes |
|------|-------|-------------------|
| sm | [N]px | [what changes] |
| md | [N]px | [what changes — often sidebar collapse point] |
| lg | [N]px | [what changes] |
| xl | [N]px | [what changes] |
| 2xl | [N]px | [what changes] |

---

## Component Patterns Summary

| Component | Height | Padding | Radius | Depth | Variants |
|-----------|--------|---------|--------|-------|----------|
| Button | [N]px | [values] | [token] | [shadow] | [N] |
| Input | [N]px | [values] | [token] | [shadow] | [N] |
| Card | auto | [values] | [token] | [shadow] | [N] |
| Table Row | [N]px | [values] | none | border-bottom | [N] |
| Badge | [N]px | [values] | [token] | none | [N] |
| Dialog | auto | [values] | [token] | [shadow] | [N] |

---

## Tech Stack

- UI library: [shadcn/ui / Radix / Headless UI / MUI / Ant Design / custom]
- Styling: [Tailwind / CSS modules / styled-components / CSS-in-JS / etc.]
- Icons: [Lucide / Heroicons / Phosphor / custom / etc.]
- Animations: [tw-animate / framer-motion / CSS native / etc.]
- Charts: [Recharts / Chart.js / D3 / Tremor / etc.]
- Date handling: [date-fns / dayjs / native / etc.]
```
