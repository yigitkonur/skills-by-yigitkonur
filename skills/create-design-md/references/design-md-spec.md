# The design.md Spec — Meta-Spec for Generated design.md Files

What every generated `design.md` MUST contain, in what order, and why. This is the **meta-spec** the skill follows when producing the output for any source. Aligned with the open **DESIGN.md** format published by Google Labs (March 2026, open-sourced April 2026), extended with a references-tree contract.

> **Distinction.** This document is part of the skill's own references — `skills/create-design-md/references/design-md-spec.md`. It tells the agent how to construct the generated `design.md` at the target codebase root. The generated `design.md` itself lives at the target root, not in this repo.

---

## File anatomy

A generated `design.md` has **two parts**:

1. **YAML frontmatter** (delimited by `---`) — machine-readable design tokens. Optional fields are allowed; the parser ignores unknown keys.
2. **Markdown body** — human-readable rationale, organized into `##` sections in a fixed order. Sections that genuinely do not apply may be omitted, but present sections must appear in the canonical order below.

```markdown
---
<YAML frontmatter — machine tokens>
---

## Overview
...

## Colors
...

## ... (remaining sections in canonical order)
```

---

## Canonical section order

All section headings use `##`. **Omit only when genuinely not applicable** (e.g. `## Motion` for a wholly static design with no transitions); never skip silently — note absence with one line.

| Order | Section | Purpose | Generated references it links to |
|---|---|---|---|
| 1 | `## Overview` | Brand personality, design language, mood, density, formality, visual era. One paragraph. Answer: *what is this design's intent?* | none (it's the framing) |
| 2 | `## Colors` | Semantic role of every color token; mode (light/dark) where applicable. | `references/tokens/NN-color-*.md` |
| 3 | `## Typography` | Font families, type scale, weight scale, line-height, letter-spacing, special patterns. | `references/typography/NN-*.md` |
| 4 | `## Layout` | Grid model, spacing scale, breakpoints, density zones. | `references/spacing/`, `references/layout/` |
| 5 | `## Elevation & Depth` | Depth strategy (borders-first / shadows / layered), shadow scale, focus rings, elevation map. | `references/elevation/NN-*.md` |
| 6 | `## Shapes` | Border-radius scale, shape language, corner consistency. | `references/radius/NN-*.md` |
| 7 | `## Motion` | Transition library, duration hierarchy, easing curves, named animations. | `references/motion/NN-*.md` |
| 8 | `## Components` | One subsection per component (or component family) with link to its asset pair. | `references/components/NN-*.md` |
| 9 | `## Accessibility` | Contrast strategy, focus visibility, keyboard interaction, ARIA conventions. | references throughout |
| 10 | `## Do's and Don'ts` | Explicit guardrails. Each rule traces back to a token, scale, or composition decision. | none |
| 11 | `## References Index` | Flat list of every generated `references/[context]/NN-*.md` and `.json` file with one-line purpose. | every file |

Sections 1, 2, 3, 8, and 11 are **mandatory in every generated `design.md`**. Sections 4–7, 9, 10 may be omitted only when the source genuinely contains no evidence; if omitted, add `> This design does not implement <topic>.` under the heading and continue.

---

## YAML frontmatter — schema

The frontmatter follows the DESIGN.md token schema.

### Top-level keys

| Key | Required | Type | Purpose |
|---|---|---|---|
| `version` | optional | string | Format version. Use `"alpha"` to match the published spec until stable. |
| `name` | **required** | string | Product or design-system name. |
| `description` | optional | string | One-sentence summary of the design's intent. |
| `colors` | recommended | map<token-name, Color> | Color tokens. |
| `typography` | recommended | map<token-name, TypographyObj> | Composite typography tokens. |
| `rounded` | optional | map<scale-level, Dimension> | Border-radius scale (`xs`, `sm`, `md`, `lg`, `xl`, `full`). |
| `spacing` | optional | map<scale-level, Dimension\|number> | Spacing scale (`0`, `0.5`, `1`, `2`, `3`, `4`, `6`, `8`, `12`, `16`). |
| `components` | optional | map<component-name, ComponentProps> | Composite tokens per component, pulling from the maps above via `{path.to.token}` references. |

### Token types

| Type | Example | Notes |
|---|---|---|
| Color | `"#1A1C1E"` | Hex sRGB. The skill always resolves to a literal — never `var(--primary)`. |
| Dimension | `"16px"`, `"1rem"`, `"-0.02em"` | Number + unit (px / rem / em). |
| TypographyObj | see below | Composite. |
| Token Reference | `"{colors.primary}"` | Curly-brace path to another token in the YAML tree. References resolve to the target's `$value`. |

### TypographyObj fields

```yaml
body-md:
  fontFamily: Inter
  fontSize: 16px
  fontWeight: 400
  lineHeight: 1.5
  letterSpacing: 0em
  fontFeature: "ss01"        # optional
  fontVariation: ""          # optional
```

### Component composite — valid properties

Component-level tokens use the DESIGN.md vocabulary so a downstream agent can match `design.md` frontmatter to `references/components/*.json` one-to-one:

- `backgroundColor`
- `textColor`
- `typography` (typically a token reference)
- `rounded` (typically a token reference)
- `padding` (dimension)
- `size`, `height`, `width` (dimensions)

A component composite may reference primitive tokens only; references in component blocks may resolve to composite tokens (e.g. `typography: "{typography.label-md}"`).

### Example frontmatter (condensed)

```yaml
---
version: alpha
name: Heritage
description: Editorial-leaning publication interface with high-contrast typography.
colors:
  primary: "#1A1C1E"
  secondary: "#475569"
  tertiary: "#B8422E"
  neutral: "#F4F4F5"
  surface: "#FFFFFF"
  on-surface: "#1A1C1E"
typography:
  h1:
    fontFamily: Public Sans
    fontSize: 48px
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: -0.02em
  body-md:
    fontFamily: Public Sans
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
  label-caps:
    fontFamily: Space Grotesk
    fontSize: 12px
    fontWeight: 500
    letterSpacing: 0.08em
rounded:
  sm: 4px
  md: 8px
spacing:
  sm: 4px
  md: 8px
  lg: 16px
  xl: 24px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.surface}"
    typography: "{typography.label-caps}"
    rounded: "{rounded.md}"
    padding: 12px 24px
  button-primary-hover:
    backgroundColor: "{colors.primary}"
---
```

---

## Token-reference resolution

The skill follows two contracts when writing references:

1. **Frontmatter uses DESIGN.md curly-brace references** — `"{colors.primary}"`. References resolve to the target token's `$value`.
2. **Per-asset JSONs use the same syntax** — values in `tokens`, `states`, and component blocks point back to frontmatter token paths with `"{colors.primary}"`, `"{typography.body-md}"`, etc.

Token reference rules:
- References for color, typography, spacing, rounded MUST point at a primitive (a value in the corresponding top-level map).
- References inside a component composite block MAY point at a composite (typography token).
- Circular references are invalid.

---

## What goes in each markdown section — content guidance

### 1. `## Overview`

One paragraph (3–6 sentences). Answer:

- *What is the design's mood?* (editorial, technical, playful, formal, brutalist, etc.)
- *Who is the user?* (general consumer, internal admin, developer, data analyst)
- *What is the visual era?* (current shadcn/oklch, mid-2010s flat, neumorphic, glassmorphism)
- *What is the density?* (compact / balanced / spacious)
- *What is the formality?* (corporate / consumer / casual / playful)

Do not list tokens here — that is the job of subsequent sections.

### 2. `## Colors`

For each token in the `colors:` map, write one bullet:

```
- `primary` ({colors.primary} = #1A1C1E): CTAs and active states. Light mode only; dark mode flips to #EAEEF5. See `references/tokens/01-color-primary.{md,json}`.
```

Group by semantic purpose:
- Surface tokens (`background`, `card`, `popover`)
- Text tokens (`foreground`, `card-foreground`, `muted-foreground`)
- Interactive tokens (`primary`, `secondary`, `accent`, `destructive`)
- Control tokens (`border`, `input`, `ring`)
- Status tokens (`success`, `warning`, `info`, `destructive`)
- Chart palette (if present) — `chart-1` through `chart-N`
- App-specific scopes — `sidebar-*`, etc.

Always link the asset pair at the end of each bullet or group.

### 3. `## Typography`

State the font stack first, then the type scale, then the weight scale, then special patterns:

```markdown
**Font families:**
- Sans (Public Sans, system-ui fallback) — body and headings.
- Mono (JetBrains Mono) — code, IDs, timestamps.

**Type scale:** see `references/typography/02-type-scale.{md,json}`.
**Weight scale:** see `references/typography/03-weight-scale.{md,json}`.
**Special patterns:** tabular-nums on metrics; uppercase + tracking on section labels.
```

### 4. `## Layout`

Cover grid model, spacing scale, breakpoints, density zones. Always link `references/spacing/` and `references/layout/` asset pairs.

### 5. `## Elevation & Depth`

State the depth strategy explicitly: **borders-first**, **subtle-shadows**, **layered-shadows**, or **surface-shifts**. Then describe the shadow scale, focus ring system, and elevation map (canvas → surface → floating → overlay → backdrop). Link `references/elevation/`.

### 6. `## Shapes`

Border-radius scale and shape language. Note whether the design uses pill shapes (`full`), rounded squares (`md`/`lg`), or sharp corners. Call out asymmetric radius if present (e.g. cards with only top-left/top-right rounded). Link `references/radius/`.

### 7. `## Motion`

Transition library (CSS, framer-motion, tw-animate-css). Duration hierarchy (instant / fast / standard / slow). Easing curves. Named animations (fade-in, zoom-in-95, slide-in-from-right). Composition rules (modals layer fade + zoom). Link `references/motion/`.

### 8. `## Components`

One subsection per component family. Sort alphabetically or by importance — be consistent across runs. For each component, write a brief paragraph (anatomy, key states, where it's used) and link the asset pair:

```markdown
### Button (primary)

Filled button used for the single most important action in any view. Three sizes (`sm` 32px, `md` 36px, `lg` 40px). Hover darkens; focus shows ring; disabled drops opacity to 0.5 with pointer-events disabled. Composes with leading/trailing icons (16×16, gap 8px). See `references/components/01-button-primary.{md,json}`.
```

Mega-components (sidebar, table, dialog, command palette, form layout) should decompose into sub-component subsections, each with its own asset pair.

### 9. `## Accessibility`

Cover contrast strategy (WCAG AA / AAA targets), focus visibility (rings, outlines), keyboard interaction (which components accept which keys), ARIA conventions (roles, labels, live regions). Reference the per-component asset's `accessibility` block.

### 10. `## Do's and Don'ts`

Concrete rules that a recreating agent must follow, e.g.:

```markdown
- **Do** reserve `colors.tertiary` for the single most important action per view.
- **Don't** mix `rounded.md` and `rounded.sm` in the same composition; pick one.
- **Do** maintain a 4.5:1 contrast ratio for all body text.
- **Don't** introduce shadow tokens beyond the four in the elevation scale.
- **Do** use `typography.label-caps` exclusively for ALL-CAPS section labels.
- **Don't** animate layout properties (width, height) — use transform or opacity.
```

### 11. `## References Index`

A flat, ordered listing of every generated file. Format:

```markdown
| Path | Purpose |
|---|---|
| `references/tokens/01-color-primary.md` | Primary color token — purpose, mode, consumers. |
| `references/tokens/01-color-primary.json` | Primary color token — machine values. |
| `references/typography/01-font-families.md` | Font family inventory. |
| `references/typography/01-font-families.json` | Font family — machine values. |
| `references/components/01-button-primary.md` | Primary button — anatomy, states, composition. |
| `references/components/01-button-primary.json` | Primary button — machine values. |
| ... | ... |
```

This is the cross-reference map; the verification step (`references/verification.md`) audits this index against the actual file tree.

---

## When to deviate from the canonical structure

The DESIGN.md spec explicitly allows unknown sections and tokens to be preserved without error. The skill follows that flexibility:

- **Add new `[context]/` directories** when the source genuinely demands them (e.g. `charts/`, `density/`, `voice/`).
- **Add new sections** after `## Components` if the design has a strong identity not covered above (e.g. `## Sound`, `## Microcopy Voice`, `## Iconography`). Place them between `## Components` and `## Accessibility`.
- **Never reorder** the canonical sections. Order is normative for parser consistency.

---

## Compliance checks

A generated `design.md` is compliant when:

- [ ] Frontmatter parses as valid YAML.
- [ ] `name:` is present.
- [ ] Sections appear in canonical order.
- [ ] Mandatory sections (Overview, Colors, Typography, Components, References Index) are present.
- [ ] Every component named in `## Components` has both a `references/components/NN-*.md` and `.json` file.
- [ ] Every token in `colors:`, `typography:`, `rounded:`, `spacing:` has a paired `references/<context>/NN-*.{md,json}`.
- [ ] Every `references/[context]/NN-*` file is listed in `## References Index`.
- [ ] Token references resolve (no broken `{path.to.token}` paths).

---

## Sources of authority

This meta-spec aligns with:

- **Google Labs DESIGN.md** (open-sourced 2026): section order, frontmatter token schema, component-property vocabulary, `{path.to.token}` references.
- **W3C Design Tokens Format (DTCG 2025.10)**: optional `$type` + `$value` shape inside per-asset JSONs for downstream interoperability with Style Dictionary, Tokens Studio, Penpot, Figma export pipelines.
- **shadcn/ui semantic naming**: surface / text / interactive / control / status / chart / sidebar token groupings.
