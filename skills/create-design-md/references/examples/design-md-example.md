# Worked Example — `design.md`

A complete worked example of a generated `design.md` for a fictional SaaS dashboard called **Heritage Analytics**. The references tree it links to is described conceptually at the bottom; you don't need to produce the tree to read this example.

Use this as the structural blueprint for any generated `design.md`. The body length here (~80 lines of prose) is a healthy target — long enough to ground every section, short enough to scan.

---

```markdown
---
version: alpha
name: Heritage Analytics
description: Editorial-leaning analytics dashboard with high-contrast typography and a single accent color reserved for the most important action.
colors:
  primary: "#1A1C1E"
  secondary: "#475569"
  tertiary: "#B8422E"
  neutral: "#F4F4F5"
  surface: "#FFFFFF"
  on-surface: "#1A1C1E"
  muted: "#71717A"
  border: "#E4E4E7"
  destructive: "#DC2626"
  success: "#15803D"
  chart-1: "#B8422E"
  chart-2: "#475569"
  chart-3: "#15803D"
  chart-4: "#A855F7"
  chart-5: "#0EA5E9"
typography:
  h1:
    fontFamily: Public Sans
    fontSize: 48px
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: -0.02em
  h2:
    fontFamily: Public Sans
    fontSize: 24px
    fontWeight: 600
    lineHeight: 1.25
  body-md:
    fontFamily: Public Sans
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
  body-sm:
    fontFamily: Public Sans
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.45
  label-caps:
    fontFamily: Space Grotesk
    fontSize: 12px
    fontWeight: 500
    letterSpacing: 0.08em
  mono-sm:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: 400
rounded:
  none: 0px
  sm: 4px
  md: 8px
  lg: 12px
  full: 9999px
spacing:
  0: 0px
  1: 4px
  2: 8px
  3: 12px
  4: 16px
  6: 24px
  8: 32px
  12: 48px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.surface}"
    typography: "{typography.label-caps}"
    rounded: "{rounded.md}"
    padding: 12px 24px
    height: 40px
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    typography: "{typography.label-caps}"
    rounded: "{rounded.md}"
    padding: 12px 24px
    height: 40px
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.lg}"
    padding: 24px
  input-text:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: 10px 12px
    height: 40px
---

# Heritage Analytics — Design System

## Overview

Heritage Analytics is an editorial-leaning analytics dashboard for content publishers. The mood is **considered, calm, and confident**: a near-black primary text on warm-white surface, a single warm-clay accent (`tertiary`) reserved for the most important action in any view, and a typeface (Public Sans) that reads like a long-form publication. Density is **balanced** — neither data-dense like a trading terminal nor spacious like a marketing site. The visual era is **2024+ shadcn/oklch** flattened to hex for portability. Formality is **professional with editorial restraint**.

## Colors

Surface and text are deliberately monochrome; color is rationed to the single `tertiary` accent and the chart palette.

- `primary` (`#1A1C1E`): page text, dark UI surfaces. See `references/tokens/01-color-primary.{md,json}`.
- `secondary` (`#475569`): secondary text, low-emphasis controls. See `references/tokens/02-color-secondary.{md,json}`.
- `tertiary` (`#B8422E`): the SOLE primary-action accent. One per view. See `references/tokens/03-color-tertiary.{md,json}`.
- `neutral` (`#F4F4F5`): low-emphasis backgrounds (card alt, hover). See `references/tokens/04-color-neutral.{md,json}`.
- `surface` (`#FFFFFF`): card backgrounds, page canvas. See `references/tokens/05-color-surface.{md,json}`.
- `on-surface` (`#1A1C1E`): default text on surface. See `references/tokens/06-color-on-surface.{md,json}`.
- `muted` (`#71717A`): metadata, timestamps, placeholders. See `references/tokens/07-color-muted.{md,json}`.
- `border` (`#E4E4E7`): standard hairline borders. See `references/tokens/08-color-border.{md,json}`.
- `destructive` (`#DC2626`): delete confirmations, error rings. See `references/tokens/09-color-destructive.{md,json}`.
- `success` (`#15803D`): positive trend indicators. See `references/tokens/10-color-success.{md,json}`.
- Chart palette `chart-1` … `chart-5`: data visualization. See `references/tokens/11-color-chart.{md,json}`.

Dark mode: not implemented in this design.

## Typography

**Font families:** Public Sans (body/headings), Space Grotesk (uppercase labels), JetBrains Mono (timestamps, IDs, terminal output). See `references/typography/01-font-families.{md,json}`.

**Type scale:** `h1` 48px → `h2` 24px → `body-md` 16px → `body-sm` 14px → `label-caps` 12px → `mono-sm` 13px. See `references/typography/02-type-scale.{md,json}`.

**Weight scale:** `400` (body), `500` (labels), `600` (headings). No `700+`. See `references/typography/03-weight-scale.{md,json}`.

**Special patterns:** tabular-nums on every metric and table number column; `label-caps` ALL-CAPS for section labels with 0.08em tracking; mono for IDs and timestamps. See `references/typography/04-special-patterns.{md,json}`.

## Layout

Fluid grid on mobile; fixed max-width 1200px on desktop. Sidebar collapses below the `md` breakpoint (768px). Strict 8px spacing scale with a 4px half-step for micro-adjustments (badge padding, icon-to-text gaps). See `references/spacing/01-base-unit.{md,json}` and `references/layout/01-grid.{md,json}`, `references/layout/02-breakpoints.{md,json}`.

Density zones: data-dense (tables, sidebar), standard (forms, settings), spacious (empty states, onboarding). See `references/spacing/03-density-zones.{md,json}`.

## Elevation & Depth

Strategy: **borders-first**. The design avoids shadows except for floating overlays (popovers, dropdowns). Borders carry depth on cards, inputs, and tabs. See `references/elevation/01-depth-strategy.{md,json}`.

Shadow scale: only two — `shadow-md` for popovers/dropdowns, `shadow-lg` for dialogs. See `references/elevation/02-shadow-scale.{md,json}`.

Focus rings: 3px outset ring in `tertiary`/50% on every focus-visible. See `references/elevation/03-focus-ring.{md,json}`.

Elevation map: 0 (page canvas, white) → 1 (card, white + border) → 2 (popover, white + shadow-md) → 3 (dialog, white + shadow-lg). See `references/elevation/04-elevation-map.{md,json}`.

## Shapes

Border-radius scale: `none` 0px → `sm` 4px → `md` 8px → `lg` 12px → `full` 9999px. Interactive controls use `md`; cards use `lg`; badges/avatars use `full`. The design avoids mixing `md` and `sm` in the same composition. See `references/radius/01-radius-scale.{md,json}` and `references/radius/02-radius-by-component.{md,json}`.

## Motion

Transition library: CSS-native (no framer-motion). Duration hierarchy: hover/focus 150ms ease, modal/dialog 200ms ease, sidebar collapse 300ms ease-in-out. See `references/motion/01-transition-defaults.{md,json}` and `references/motion/02-duration-hierarchy.{md,json}`.

Named animations: `fade-in` 150ms ease-out, `slide-in-from-right` 300ms ease-in-out (sidebar), `zoom-in-95` 200ms ease-out (popover). Composition: popovers and dialogs layer `fade-in` + `zoom-in-95`. See `references/motion/03-named-animations.{md,json}`.

## Components

### Button (primary)

Filled clay button used for the single most important action per view. Sizes: `sm` 32px / `md` 40px (default) / `lg` 44px. States: hover darkens to `colors.primary`; focus shows 3px `tertiary`/50% ring; disabled drops opacity 0.5 with pointer-events disabled. Composes with leading/trailing 16×16 icons at 8px gap. See `references/components/01-button-primary.{md,json}`.

### Button (secondary)

White surface with `primary` border for low-emphasis actions. Hover fills `neutral`. Same sizes and structure as primary. See `references/components/02-button-secondary.{md,json}`.

### Card

White surface, 1px `border` hairline, 12px `lg` radius, 24px internal padding. No shadow. Composes with `CardHeader` (title + description) and `CardFooter` (right-aligned actions). See `references/components/03-card.{md,json}`.

### Input (text)

White surface, 1px `border` hairline, `md` radius, 12px horizontal padding, 40px tall. Focus shows `tertiary` ring. Error state replaces border with `destructive`. See `references/components/04-input-text.{md,json}`.

### Sidebar (full decomposition)

Sidebar is a mega-component. Decomposed into `sidebar-shell` (256px width, white surface), `sidebar-group` (uppercase `label-caps` heading), `sidebar-item` (40px row, 12px horizontal padding, hover `neutral`, active `primary` background + `surface` text), `sidebar-collapse-toggle`. See `references/components/05-sidebar-shell.{md,json}`, `references/components/06-sidebar-group.{md,json}`, `references/components/07-sidebar-item.{md,json}`, `references/components/08-sidebar-collapse-toggle.{md,json}`.

### Table

Plain hairline borders between rows; `header` row uses `label-caps` typography; numeric cells use `tabular-nums`. Row hover reveals `neutral` background. See `references/components/09-table-shell.{md,json}` and `references/components/10-table-row.{md,json}`.

### Dialog / Modal

White surface, 16px `lg` radius, 32px padding, `shadow-lg`. Backdrop is `primary`/40% scrim with `fade-in` 200ms. See `references/components/11-dialog.{md,json}`.

### Badge

`full` radius pill. Three variants: `default` (neutral bg + primary text), `success`, `destructive`. Always `label-caps` typography. See `references/components/12-badge.{md,json}`.

### Metric Card

`Card` shell + large number in `h1` typography + `body-sm` description below + trend indicator (`success` or `destructive` arrow). Numbers always `tabular-nums`. See `references/components/13-metric-card.{md,json}`.

### Chart Container

`Card` shell + 24px padding + `label-caps` title row + chart body. Uses `chart-1`…`chart-5` palette in series order. See `references/components/14-chart-container.{md,json}`.

## Accessibility

All text meets WCAG AA contrast (4.5:1 minimum) against its surface. Focus is keyboard-driven only — `:focus-visible` shows the 3px `tertiary`/50% ring; `:focus` alone is suppressed. Sidebar items expose `aria-current="page"` on the active route. Dialogs trap focus and restore on close (Esc to close). Table headers use `<th scope="col">`. Charts pair every visual with a screen-reader summary. See per-component asset `accessibility` blocks for keyboard and ARIA details.

## Do's and Don'ts

- **Do** reserve `colors.tertiary` for the single most important action per view. One CTA color, one CTA per view.
- **Do** maintain WCAG AA contrast (4.5:1) for body text and 3:1 for large text.
- **Do** use `typography.label-caps` exclusively for ALL-CAPS section labels and badges.
- **Do** use tabular-nums on every metric and numeric table column.
- **Don't** mix `rounded.md` and `rounded.sm` in the same composition.
- **Don't** introduce shadow tokens beyond `shadow-md` and `shadow-lg`. The system is borders-first.
- **Don't** animate `width` or `height` — use `transform` and `opacity` only.
- **Don't** introduce a second accent color. The design's identity rests on a single accent.

## References Index

| Path | Purpose |
|---|---|
| `references/tokens/01-color-primary.md` | Primary color — purpose, mode, consumers. |
| `references/tokens/01-color-primary.json` | Primary color — machine values. |
| `references/tokens/02-color-secondary.md` | Secondary color — purpose, consumers. |
| `references/tokens/02-color-secondary.json` | Secondary color — machine values. |
| ... | ... |
| `references/typography/01-font-families.md` | Font families and fallback stack. |
| `references/typography/01-font-families.json` | Font families — machine values. |
| ... | ... |
| `references/components/01-button-primary.md` | Primary button — anatomy, states, composition. |
| `references/components/01-button-primary.json` | Primary button — machine values. |
| ... | ... |
```

---

## Notes on this example

- **Body length** is intentionally lean (~75 lines of body, plus a long References Index). Most depth lives in the per-asset `references/[context]/NN-*.md` files. `design.md` is routing + framing.
- **Frontmatter `name`** matches the product name. The product's design system inherits the name.
- **Every component named under `## Components`** has a corresponding `references/components/NN-*.md` and `.json`.
- **Every token in `colors:`** has a corresponding `references/tokens/NN-*.md` and `.json` (or shares an asset when grouped — e.g. `11-color-chart.{md,json}` covers `chart-1` through `chart-5`).
- **Section "Layout"** links into both `spacing/` and `layout/` because the layout topic spans both contexts.
- **Dark mode "not implemented"** is stated explicitly in `## Colors` — never silent.
