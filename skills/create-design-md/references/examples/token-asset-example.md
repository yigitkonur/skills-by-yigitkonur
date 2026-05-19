# Worked Example — One Token Asset Pair

A complete `.md` + `.json` pair for `references/tokens/03-color-tertiary.{md,json}` from the **Heritage Analytics** example. Use this as the structural blueprint when capturing a token.

---

## The `.md` file — `03-color-tertiary.md`

```markdown
# Color — Tertiary (Boston Clay)

> Warm clay-red reserved for the single most important action per view. The design's only accent.

**Type:** token
**Context:** tokens
**Source:** `app/globals.css` (`:root`, CSS var `--tertiary`)
**Paired JSON:** `./03-color-tertiary.json`

---

## Why

Heritage rations color severely: monochrome text on warm-white surface, with one accent. `tertiary` is that accent — a warm clay-red sometimes called "Boston Clay" — used exclusively for primary actions and active states (selected nav, focused inputs via the ring). Reserving it disciplines the visual hierarchy: where this color appears is where the user's attention should flow.

The hue (clay-red, not pure red) signals warmth rather than urgency. Destructive actions use a separate `destructive` token (#DC2626, hot red) so that `tertiary` is unambiguously a positive accent.

---

## Hierarchy

Position in the color system:

```
Surface tier:      surface     #FFFFFF    on-surface     #1A1C1E
Text tier:         primary     #1A1C1E    muted          #71717A
Interactive tier:  TERTIARY    #B8422E    secondary      #475569
Status tier:       destructive #DC2626    success        #15803D
Border tier:       border      #E4E4E7
```

`tertiary` is the **only** interactive color that fills surfaces. `primary` and `secondary` are text colors; `success` and `destructive` are status indicators with separate semantics. There is no `tertiary-foreground` because text on `tertiary` is always `surface` (white).

---

## States

This is a token, not a component. States are mode variants:

| Mode | Value |
|---|---|
| Light (default) | `#B8422E` (oklch(0.547 0.155 28.5) approx.) |
| Dark | not-implemented (Heritage is light-mode-only) |
| High-contrast | not-implemented |
| Print | not-implemented |

Opacity ladder (when used with Tailwind `/NN` modifier):

| Modifier | Use |
|---|---|
| `/100` (default) | Filled button bg. |
| `/50` | Focus rings on inputs and buttons. |
| `/30` | Sidebar item hover bg. |
| `/15` | Subtle accent backgrounds (badges, callouts). |
| `/05` | Barely-visible accent (data-state hover). |

---

## Consumers

The components and patterns that consume this token:

- `components/button-primary` — bg fill.
- `components/sidebar-item` — `/30` modifier on hover; full color on active.
- `components/badge-status` — when `variant="accent"`.
- `components/input-text` — focus ring (`/50`).
- `components/link` — text color for inline links.
- `components/chart-container` — `chart-1` series color (`tertiary`).

This list mirrors the JSON's `consumers` array.

---

## Source Evidence

```
File:    app/globals.css
Lines:   18 (light mode definition)
Selector: :root
CSS var: --tertiary

Definition:
  :root {
    --tertiary: #B8422E;
  }

Resolution chain:
  Tailwind class  bg-tertiary
  -> CSS          background-color: var(--tertiary)
  -> Literal      #B8422E
```

No dark-mode override in `.dark` selector. Confirmed via grep:

```
grep -nE 'tertiary' app/globals.css
# only one definition; no .dark override
```

---

## Cross-references

- **Used by:** every entry in the **Consumers** list above (paired component files).
- **Related to:** `../tokens/05-color-surface.md` (always paired as text-on-bg), `../elevation/03-focus-ring.md` (uses `/50` modifier).
- **Not to be confused with:** `../tokens/09-color-destructive.md` — `destructive` is a separate hot-red used only for delete/error actions.

---

## Notes

- The source defines the color in hex (`#B8422E`); the `.json` records both hex and the oklch approximation for downstream tooling that uses perceptual color space.
- Originally derived from a brand pigment ("Boston Clay") in the company's print materials. The frontend matches print to within 2 ΔE.
- The opacity ladder is observed across components; it is a convention, not a code-enforced rule. The verification pass flags new opacities that fall outside the ladder.
```

---

## The `.json` file — `03-color-tertiary.json`

```json
{
  "$id": "tokens/color-tertiary",
  "name": "Color - Tertiary (Boston Clay)",
  "type": "token",
  "tokenType": "color",
  "$type": "color",
  "$value": "#B8422E",
  "$description": "Warm clay-red. The sole interactive accent. Used for primary action backgrounds, focus rings, and active states.",
  "mode": {
    "light": "#B8422E"
  },
  "alternateFormats": {
    "oklch": "oklch(0.547 0.155 28.5)",
    "rgb":   "rgb(184 66 46)",
    "hsl":   "hsl(9 60% 45%)"
  },
  "opacityLadder": {
    "100": "default — filled button bg",
    "50":  "focus rings on inputs and buttons",
    "30":  "sidebar item hover bg",
    "15":  "subtle accent backgrounds (badges, callouts)",
    "5":   "barely-visible accent (data-state hover)"
  },
  "consumers": [
    "components/button-primary",
    "components/sidebar-item",
    "components/badge-status",
    "components/input-text",
    "components/link",
    "components/chart-container"
  ],
  "source": {
    "file": "app/globals.css",
    "selector": ":root",
    "cssVar": "--tertiary",
    "lineRange": "18"
  },
  "notes": "Light-mode only. No dark-mode override in source. Originally derived from print-material brand pigment."
}
```

---

## What to notice

1. **`$type: "color"` + `$value`** — DTCG 2025.10 compatible. A simple script can walk `references/tokens/*.json` and emit a valid DTCG token file.
2. **`alternateFormats`** — the source uses hex; the `.json` keeps hex as canonical (`$value`) but records the oklch/rgb/hsl forms for downstream tools.
3. **`opacityLadder`** is the design's discipline made machine-readable. Verification can audit a component's `tokens` block for opacity modifiers outside this ladder.
4. **`consumers`** is bidirectional with each component's `tokens` block: every component that has `"backgroundColor": "{colors.tertiary}"` (or any `{colors.tertiary}/NN` modifier) appears here.
5. **`mode.light` only** — the source has no dark-mode override. The verification pass would flag any component referencing a `mode.dark` value of this token.
6. **`source` is precise** — file, selector, cssVar, line. A maintainer can `cd app && grep -nE 'tertiary' globals.css` and find the definition.
7. **No `states` block** — tokens are not stateful. The component asset's `states` block does that work.
