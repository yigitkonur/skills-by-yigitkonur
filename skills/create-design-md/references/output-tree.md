# Generated Output Tree

The exact directory contract the skill produces, per run, at the target codebase root (or a writable working directory beside it). This is the **generated** tree — not the skill's own references.

---

## Top-level layout

```
<target-root>/
├── design.md                  # master spec (DESIGN.md format)
└── references/                # paired per-asset evidence
    ├── tokens/                # primitives — color, semantic, etc.
    ├── typography/            # font families, type scale, weight scale
    ├── spacing/               # base unit, scale, density zones
    ├── radius/                # border-radius scale and shape language
    ├── elevation/             # shadow scale, focus rings, elevation map
    ├── motion/                # transitions, durations, named animations
    ├── layout/                # grid, breakpoints, content widths
    ├── components/            # one pair per component
    └── <domain>/              # optional contexts: charts/, sidebar/, density/
```

Per-context directory has the same shape:

```
references/<context>/
├── 01-<slug>.md
├── 01-<slug>.json
├── 02-<slug>.md
├── 02-<slug>.json
├── 03-<slug>.md
├── 03-<slug>.json
└── ...
```

---

## Naming rules

| Rule | Detail |
|---|---|
| Pair | Every `.md` has a `.json`; every `.json` has a `.md`. |
| Stem | Shared across the pair. `01-button-primary.md` + `01-button-primary.json`. |
| Ordinal | `NN-` zero-padded. Controls reading order within a context. |
| Slug | `kebab-case`. Specific noun: `button-primary`, not `button` or `primary-button-component`. |
| Encoding | UTF-8, LF line endings. |
| Header | The `.md`'s `# Title` matches the JSON's `name:` field. |

---

## Canonical contexts and their typical contents

Use this canonical set first. Add a new `[context]/` directory only when the source warrants.

### `tokens/`

Primitive design tokens — the foundational vocabulary other contexts reference.

Typical asset pairs:

- `01-color-primary` — primary brand color (or surface for cooler systems).
- `02-color-semantic` — semantic status (`success`, `warning`, `info`, `destructive`).
- `03-color-neutral` — gray/neutral scale.
- `04-color-chart` — visualization palette (if a dashboard).
- `05-color-sidebar` — sidebar-scoped tokens (if a sidebar-led layout).
- `06-color-opacity-scale` — `/5`, `/10`, `/30`, `/50`, `/90` semantic ladder.

### `typography/`

- `01-font-families` — every family with source (Google Fonts, local, system) and fallback.
- `02-type-scale` — every size token (`xs`, `sm`, `base`, `lg`, `xl`, `2xl`, `3xl`) with pixel value, line-height, and contexts.
- `03-weight-scale` — every weight (`normal`, `medium`, `semibold`, `bold`) and where used.
- `04-line-height` — leading values used and their contexts.
- `05-letter-spacing` — tracking values and contexts (uppercase + tracking pattern).
- `06-special-patterns` — `tabular-nums`, `font-mono` for data, truncation strategies, line-clamp.
- `07-heading-hierarchy` — `h1`–`h6` mapping to actual usage.

### `spacing/`

- `01-base-unit` — the 4px or 8px base. Justification.
- `02-spacing-scale` — every value used, frequency, primary usage.
- `03-density-zones` — data-dense vs. balanced vs. spacious.
- `04-layout-strategy` — flex+gap vs margin vs grid. Dominant pattern.

### `radius/`

- `01-radius-scale` — `xs`, `sm`, `md`, `lg`, `xl`, `full` with values.
- `02-radius-by-component` — which component categories use which radius.

### `elevation/`

- `01-depth-strategy` — borders-first / subtle-shadows / layered-shadows / surface-shifts.
- `02-shadow-scale` — every shadow value and which components use it.
- `03-focus-ring` — focus-visible ring width, color, offset, dark-mode variant.
- `04-elevation-map` — level 0 (canvas) through level N (backdrop).

### `motion/`

- `01-transition-defaults` — default duration + easing for hover/focus changes.
- `02-named-animations` — fade-in, zoom-in-95, slide-in-from-right with from/to.
- `03-duration-hierarchy` — instant / fast / standard / slow tiers and what each covers.
- `04-easing-functions` — every named easing curve used.

### `layout/`

- `01-grid` — grid model (fluid, fixed-max, mixed).
- `02-breakpoints` — `sm`, `md`, `lg`, `xl`, `2xl` with widths and what changes at each.
- `03-content-widths` — page max-width, sidebar width(s), main column constraints.
- `04-responsive-patterns` — sidebar-collapse point, hamburger emergence, mobile nav.

### `components/`

One pair per component (or sub-component when decomposed). Typical inventory for a dashboard:

- Controls: `button-primary`, `button-secondary`, `button-ghost`, `button-icon`, `input-text`, `input-search`, `select`, `checkbox`, `radio`, `switch`, `slider`, `textarea`.
- Containers: `card`, `tabs`, `accordion`, `separator`, `scroll-area`.
- Navigation: `sidebar-shell`, `sidebar-item`, `sidebar-group`, `breadcrumb`, `top-bar`.
- Overlays: `dialog`, `sheet`, `popover`, `tooltip`, `dropdown-menu`, `command-palette`.
- Feedback: `badge`, `alert`, `toast`, `skeleton`, `progress`.
- Data display: `table-shell`, `table-row`, `table-cell`, `chart-container`, `metric-card`.

Mega-components (sidebar, table, dialog) decompose into multiple component asset pairs — never compressed into a single asset.

### Optional contexts

- `charts/` — chart-specific patterns: tooltip, axis, legend, empty state.
- `sidebar/` — full sidebar decomposition for sidebar-dominant designs.
- `density/` — explicit density modes if the design exposes multiple.
- `voice/` — copywriting tone, microcopy patterns.
- `iconography/` — icon library, sizes, stroke widths.

---

## File ordering within a context

`NN-` ordinals reflect **reading order**, not creation order. Earlier numbers are more foundational; later numbers depend on earlier ones. Example:

```
typography/
├── 01-font-families.md        # foundational: what fonts ship
├── 02-type-scale.md           # depends on families
├── 03-weight-scale.md         # depends on families
├── 04-line-height.md          # tied to scale
├── 05-letter-spacing.md       # tied to scale
├── 06-special-patterns.md     # composes earlier patterns
└── 07-heading-hierarchy.md    # final synthesis
```

When inserting a new asset between existing ones, prefer renumbering downstream files to keep ordinals dense. Validation in `references/verification.md` flags sparse or duplicate ordinals.

---

## End-to-end example path

```
my-saas/
├── design.md
└── references/
    ├── tokens/
    │   ├── 01-color-primary.md
    │   ├── 01-color-primary.json
    │   ├── 02-color-semantic.md
    │   ├── 02-color-semantic.json
    │   ├── 03-color-neutral.md
    │   └── 03-color-neutral.json
    ├── typography/
    │   ├── 01-font-families.md
    │   ├── 01-font-families.json
    │   ├── 02-type-scale.md
    │   └── 02-type-scale.json
    ├── spacing/
    │   ├── 01-base-unit.md
    │   └── 01-base-unit.json
    ├── radius/
    │   ├── 01-radius-scale.md
    │   └── 01-radius-scale.json
    ├── elevation/
    │   ├── 01-depth-strategy.md
    │   ├── 01-depth-strategy.json
    │   ├── 02-shadow-scale.md
    │   └── 02-shadow-scale.json
    ├── motion/
    │   ├── 01-transition-defaults.md
    │   └── 01-transition-defaults.json
    ├── layout/
    │   ├── 01-grid.md
    │   ├── 01-grid.json
    │   ├── 02-breakpoints.md
    │   └── 02-breakpoints.json
    └── components/
        ├── 01-button-primary.md
        ├── 01-button-primary.json
        ├── 02-button-secondary.md
        ├── 02-button-secondary.json
        ├── 03-input-text.md
        ├── 03-input-text.json
        ├── 04-card.md
        ├── 04-card.json
        ├── 05-dialog.md
        └── 05-dialog.json
```

`design.md` links every one of these files. The `## References Index` section at the bottom of `design.md` lists them with one-line purposes — that index is the durable cross-reference.

---

## Scope reductions

Not every run produces every context. Common reduced shapes:

| Scope | Mandatory contexts | Optional |
|---|---|---|
| Full extraction | tokens, typography, spacing, radius, elevation, motion, layout, components | charts, sidebar, density |
| Foundations only | tokens, typography, spacing, radius, elevation, motion | layout |
| Specific components | tokens (minimal — only colors used by the in-scope components), components | typography (subset) |
| Tokens only | tokens | none |

Smaller scope still requires a `design.md` at the root with a `## References Index` for what was produced. Never write per-asset files without an accompanying `design.md`.

---

## What to do when uncertain

- **Asset doesn't fit a context cleanly?** Pick the closest canonical context; do not invent a new one until at least one other asset would also live there.
- **Two contexts contend for the same asset?** Place the asset in the more foundational one (e.g. focus-ring values live in `elevation/`, not `motion/`).
- **Source uses non-standard naming?** Preserve the source's names in the `.md`'s prose, but map to the canonical context vocabulary in the JSON's keys.
- **Source has overlapping or conflicting tokens?** Document the dominant pattern in the asset; list exceptions in the asset's prose with file paths.
