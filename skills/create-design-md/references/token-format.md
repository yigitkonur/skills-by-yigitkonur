# Per-Asset JSON Shape

The exact, machine-readable shape for every `references/[context]/NN-*.json` file. Stable so a downstream agent can ingest without parsing prose.

The shape **extends** the DESIGN.md component-property vocabulary and is **export-compatible** with the W3C Design Tokens Format (DTCG 2025.10). The skill commits to this shape.

---

## Common fields (every asset type)

| Field | Required | Type | Purpose |
|---|---|---|---|
| `$id` | yes | string | Asset identifier. Format: `<context>/<slug>`. Example: `components/button-primary`. |
| `name` | yes | string | Human-readable name. Matches the `.md`'s `# Title`. |
| `type` | yes | string | One of: `token`, `component`, `pattern`, `scale`. |
| `source` | yes | object | Where this asset came from in the source (file, selector, css var). Falsy fields allowed. |
| `notes` | optional | string | Anything important not captured in structured fields. Single paragraph. |

The `source` object:

```json
{
  "source": {
    "file": "app/globals.css",
    "selector": ":root",
    "cssVar": "--primary",
    "url": null,
    "lineRange": "12-14"
  }
}
```

If the source is a live URL, populate `url`. If a codebase, populate `file` + `selector` + (optionally) `cssVar`. If an HTML snapshot, populate `file` (snapshot path) + `selector`.

---

## Token assets — `references/tokens/`

```json
{
  "$id": "tokens/color-primary",
  "name": "Primary Color Token",
  "type": "token",
  "tokenType": "color",
  "$type": "color",
  "$value": "#1A1C1E",
  "$description": "Primary brand color for CTAs and active states.",
  "mode": {
    "light": "#1A1C1E",
    "dark":  "#EAEEF5"
  },
  "consumers": [
    "components/button-primary",
    "components/badge-status",
    "components/link"
  ],
  "source": {
    "file": "app/globals.css",
    "selector": ":root",
    "cssVar": "--primary"
  }
}
```

Field rules:

- `tokenType` — one of: `color`, `dimension`, `fontFamily`, `fontWeight`, `duration`, `cubicBezier`, `shadow`, `border`, `typography`, `radius`, `opacity`.
- `$type` — mirrors `tokenType`; provided for DTCG 2025.10 export compatibility.
- `$value` — the literal value. For colors: hex sRGB. For dimensions: `"16px"` etc. For composites (shadow, typography): the DTCG composite object.
- `$description` — one sentence on what this token is for.
- `mode` — required for color tokens that differ across light/dark. Omit for color tokens identical across modes. Add additional keys (`hc`, `print`, branded modes) when the source proves them.
- `consumers` — array of `$id`s in this output tree that reference this token. Used by the verification pass to detect orphan tokens.

### Composite token examples

**Shadow token (DTCG composite):**

```json
{
  "$id": "tokens/shadow-md",
  "name": "Medium Shadow Token",
  "type": "token",
  "tokenType": "shadow",
  "$type": "shadow",
  "$value": [
    { "color": "#0000001A", "offsetX": "0px", "offsetY": "4px", "blur":  "6px", "spread": "-1px" },
    { "color": "#0000000F", "offsetX": "0px", "offsetY": "2px", "blur":  "4px", "spread": "-2px" }
  ],
  "$description": "Default elevation for popovers and dropdowns.",
  "consumers": ["components/popover", "components/dropdown-menu"],
  "source": { "file": "app/globals.css", "selector": ":root", "cssVar": "--shadow-md" }
}
```

**Typography composite token:**

```json
{
  "$id": "typography/body-md",
  "name": "Body Medium",
  "type": "token",
  "tokenType": "typography",
  "$type": "typography",
  "$value": {
    "fontFamily": ["Public Sans", "system-ui", "sans-serif"],
    "fontSize":   { "value": 16, "unit": "px" },
    "fontWeight": 400,
    "lineHeight": 1.5,
    "letterSpacing": { "value": 0, "unit": "em" }
  },
  "$description": "Default body text for paragraphs and table cells.",
  "consumers": ["components/card-content", "components/table-cell"],
  "source": { "file": "app/globals.css", "selector": ".body", "cssVar": null }
}
```

---

## Component assets — `references/components/`

```json
{
  "$id": "components/button-primary",
  "name": "Button - Primary",
  "type": "component",
  "library": "shadcn/ui + Radix",
  "dependsOn": ["components/icon"],
  "anatomy": ["container", "icon", "label", "spinner"],
  "props": {
    "size":    { "values": ["sm", "md", "lg"], "default": "md" },
    "variant": { "values": ["solid", "outline", "ghost"], "default": "solid" },
    "disabled": { "type": "boolean", "default": false },
    "loading":  { "type": "boolean", "default": false }
  },
  "tokens": {
    "backgroundColor": "{colors.primary}",
    "textColor":       "{colors.primary-foreground}",
    "typography":      "{typography.label-md}",
    "rounded":         "{rounded.md}",
    "padding":         "8px 16px",
    "height":          "36px"
  },
  "sizes": {
    "sm": { "height": "32px", "padding": "6px 12px", "fontSize": "14px" },
    "md": { "height": "36px", "padding": "8px 16px", "fontSize": "14px" },
    "lg": { "height": "40px", "padding": "10px 20px", "fontSize": "16px" }
  },
  "states": {
    "default":  { "backgroundColor": "{colors.primary}" },
    "hover":    { "backgroundColor": "{colors.primary}", "opacity": 0.9 },
    "focus":    { "boxShadow": "0 0 0 3px {colors.ring}/50" },
    "active":   { "transform": "scale(0.98)" },
    "disabled": { "opacity": 0.5, "pointerEvents": "none", "cursor": "not-allowed" },
    "loading":  { "iconReplaced": "spinner" },
    "error":    "not-implemented"
  },
  "transitions": [
    { "property": "background-color", "duration": "150ms", "easing": "ease" },
    { "property": "transform",        "duration":  "50ms", "easing": "ease" }
  ],
  "accessibility": {
    "role": "button",
    "keyboard": ["Enter", "Space"],
    "contrast": "WCAG-AA-verified",
    "ariaPatterns": ["aria-disabled", "aria-busy"],
    "focusVisible": "ring"
  },
  "composition": [
    "Pair with secondary outline button in dialog footers (Cancel + Confirm).",
    "Single instance per view as the primary action."
  ],
  "source": {
    "file": "src/components/ui/Button.tsx",
    "selector": "button[data-variant=primary]",
    "cssVar": null
  }
}
```

Field rules:

- `anatomy` — ordered array of named parts the agent must reproduce.
- `props` — every prop the component accepts. `values` for enums; `type` + `default` for booleans/strings.
- `tokens` — the **default** composite. All values use DESIGN.md curly-brace references (`"{colors.primary}"`) or literal dimensions. Mirrors the `components.<name>` block in `design.md` frontmatter one-to-one.
- `sizes` — explicit overrides per size variant. Only fields that change.
- `states` — every state. `not-implemented` when the source does not implement it. Never `null` — be explicit.
- `transitions` — every animated property with duration and easing.
- `accessibility` — role, keyboard keys, contrast target, ARIA conventions, focus-visible mode.
- `composition` — short array of how this component is used with siblings.

---

## Scale assets — radius / spacing / motion duration

```json
{
  "$id": "radius/radius-scale",
  "name": "Border-Radius Scale",
  "type": "scale",
  "scaleType": "dimension",
  "values": {
    "none": "0px",
    "xs":   "2px",
    "sm":   "4px",
    "md":   "8px",
    "lg":   "12px",
    "xl":   "16px",
    "full": "9999px"
  },
  "$description": "Border radius scale. `md` is default for interactive controls; `lg` for cards; `full` for pills.",
  "consumers": [
    "components/button-primary",
    "components/card",
    "components/badge"
  ],
  "byComponentType": {
    "interactive": "md",
    "card":        "lg",
    "pill":        "full",
    "input":       "md"
  },
  "source": { "file": "app/globals.css", "selector": ":root", "cssVar": "--radius-*" }
}
```

---

## Pattern assets — for non-token, non-component concepts

Use when documenting things like density zones, layout patterns, or composition rules that are not a single component or single token.

```json
{
  "$id": "spacing/density-zones",
  "name": "Density Zones",
  "type": "pattern",
  "zones": [
    {
      "name": "data-dense",
      "spacingTokens": ["spacing.0.5", "spacing.1", "spacing.1.5", "spacing.2"],
      "where": ["table-cell", "sidebar-item", "metric-card", "data-grid"]
    },
    {
      "name": "standard",
      "spacingTokens": ["spacing.2", "spacing.3", "spacing.4"],
      "where": ["form-field", "settings-row", "card-content"]
    },
    {
      "name": "spacious",
      "spacingTokens": ["spacing.4", "spacing.6", "spacing.8"],
      "where": ["hero", "empty-state", "onboarding"]
    }
  ],
  "$description": "Three density zones determine which spacing tokens compose where.",
  "source": { "file": "src/", "selector": "*", "cssVar": null }
}
```

---

## Cross-references between assets

The `consumers` array (on tokens) and the `dependsOn` array (on components) form a bidirectional graph the verification pass walks:

- Every `consumers` `$id` must exist in the tree.
- Every `dependsOn` `$id` must exist in the tree.
- Every token referenced from a component's `tokens` block must have a `consumers` array containing that component's `$id`.

The verification pass (`references/verification.md`) catches drift in this graph.

---

## DTCG export compatibility

A token asset with `$type` + `$value` + `$description` is already valid DTCG 2025.10 for the field subset it covers. Composite types follow DTCG composite shapes:

- `shadow` — array of `{ color, offsetX, offsetY, blur, spread }`.
- `typography` — object with `fontFamily` (array), `fontSize` (`{value,unit}`), `fontWeight` (number), `lineHeight` (number or `{value,unit}`), `letterSpacing` (`{value,unit}`).
- `border` — `{ color, width, style }`.
- `gradient`, `transition`, `strokeStyle`, `cubicBezier` — see DTCG 2025.10 spec when needed.

A simple export script can walk `references/tokens/*.json` + `references/typography/*.json` + `references/radius/*.json` and emit a single `tokens.tokens.json` file in DTCG format. The skill does not require this export — but the shape is engineered so the export is trivial.

---

## Token-reference syntax

References use DESIGN.md curly-brace paths: `"{colors.primary}"`, `"{typography.body-md}"`, `"{rounded.md}"`. The path is the path inside the generated `design.md`'s YAML frontmatter — **not** the path inside the per-asset JSON tree.

Examples:

| Reference | Resolves to |
|---|---|
| `"{colors.primary}"` | `design.md` frontmatter → `colors.primary` (typically a literal hex). |
| `"{typography.label-md}"` | `design.md` frontmatter → `typography.label-md` (a TypographyObj). |
| `"{rounded.md}"` | `design.md` frontmatter → `rounded.md` (a dimension). |
| `"{colors.primary}/90"` | `colors.primary` with 90% opacity (skill uses the `/NN` suffix to mirror Tailwind opacity modifier syntax in the JSON when the source uses it). |

Resolution is always one hop. References do not chain through other references in `design.md` frontmatter — frontmatter values are literals.

---

## When a value resists a clean type

If a value in the source doesn't fit any standard token type, document it as a `string` with explicit notes:

```json
{
  "tokenType": "string",
  "$type": "string",
  "$value": "linear-gradient(135deg, #1A1C1E 0%, #475569 100%)",
  "$description": "Hero background gradient. Used only on landing hero. No Tailwind utility equivalent."
}
```

Prefer this over inventing a fake type. The verification pass tolerates `string` typed tokens but flags them in a low-priority list so the maintainer can choose to upgrade them later.
