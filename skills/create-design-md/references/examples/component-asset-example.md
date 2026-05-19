# Worked Example — One Component Asset Pair

A complete `.md` + `.json` pair for `references/components/01-button-primary.{md,json}` from the **Heritage Analytics** example. Use this as the structural blueprint when capturing a component.

---

## The `.md` file — `01-button-primary.md`

```markdown
# Button — Primary

> Filled clay button used for the single most important action per view. Heritage uses a one-CTA-per-view discipline; this component is reserved for it.

**Type:** component
**Context:** components
**Source:** `src/components/ui/Button.tsx` (`button[data-variant=primary]`)
**Paired JSON:** `./01-button-primary.json`

---

## Why

The Heritage design rations color: monochrome text on warm-white surface, with `tertiary` (clay) reserved for the single most important action. Button-primary is the only component that defaults to filling with `tertiary`. Its prominence is intentional — there should be exactly one per view.

---

## Anatomy

```
+-- container ---------------------------------------------+
|                                                          |
|  +--[icon 16x16]--+  [label]  +--[trailing-icon 16x16]+ |
|  |   optional     |   text    |       optional         | |
|  +----------------+  <-- 8px-->+----------------------+ |
|                                                          |
|  <-- 40px tall, 12px vertical, 24px horizontal -->       |
+----------------------------------------------------------+
```

Parts: `container`, `icon` (optional leading), `label`, `trailing-icon` (optional), `spinner` (replaces icon when `loading=true`).

---

## States

| State | Behavior |
|---|---|
| Default | bg `colors.tertiary` (#B8422E), text `colors.surface` (#FFFFFF), border none |
| Hover | bg darkens to `colors.primary` (#1A1C1E), 150ms ease |
| Focus-visible | 3px outset ring `colors.tertiary`/50%, no offset |
| Active / Pressed | transform `scale(0.98)`, 50ms ease |
| Disabled | opacity 0.5, pointer-events none, cursor not-allowed |
| Loading | icon replaced by spinner; label remains; container same |
| Error / aria-invalid | not-implemented (button rarely carries error state in this design) |
| Selected / data-[state=active] | N/A (button is not toggleable) |

---

## Composition

- **Dialog footer:** paired with a `Button (secondary)` Cancel on the left.

  ```
  <DialogFooter>
    <Button variant="secondary">Cancel</Button>
    <Button>Save</Button>  // <-- this asset
  </DialogFooter>
  ```

- **Card footer:** right-aligned, last child of a `Card` composition.

- **Hero CTA:** used standalone, centered, as a single action below the hero copy.

Discipline: never more than one button-primary visible in a viewport. If two screens both need a primary action, they are separate views.

---

## Source Evidence

```
File:      src/components/ui/Button.tsx
Lines:     12-72 (cva block) + 84-110 (component render)
Selector:  button[data-variant=primary]
CSS var:   uses var(--tertiary) -> resolves to #B8422E
```

CVA call (verbatim from source):

```tsx
const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium uppercase tracking-wider transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary:   "bg-tertiary text-surface hover:bg-primary",
        secondary: "bg-surface text-primary border border-primary hover:bg-neutral",
        ghost:     "hover:bg-neutral hover:text-primary"
      },
      size: {
        sm:      "h-8 px-3",
        default: "h-10 px-6",
        lg:      "h-11 px-8"
      }
    },
    defaultVariants: { variant: "primary", size: "default" }
  }
)
```

---

## Cross-references

- **Depends on:**
  - `../tokens/03-color-tertiary.md` — the bg color.
  - `../tokens/05-color-surface.md` — the text color.
  - `../tokens/01-color-primary.md` — the hover bg.
  - `../typography/04-special-patterns.md` — uppercase + tracking pattern.
  - `../radius/01-radius-scale.md` — `md` radius.
  - `../motion/01-transition-defaults.md` — 150ms ease default.
  - `../elevation/03-focus-ring.md` — 3px outset ring pattern.
- **Depended on by:**
  - `../components/11-dialog.md` — used in DialogFooter.
  - `../components/03-card.md` — used in CardFooter.

---

## Notes

- The source labels this variant `"primary"` in the CVA `variants.variant.primary` block. The semantic name in `design.md` frontmatter is `button-primary` — disambiguated from `button-secondary` and `button-ghost` peers.
- `transform: scale(0.98)` on `:active` is observable in the live DOM but not in the CVA call; it comes from `globals.css` `.button:active { transform: scale(0.98) }`. The source-evidence section above is incomplete — see the live runtime to confirm.
- No icon spacing rule in the CVA call; the 8px gap is `gap-2` applied as a base class.
```

---

## The `.json` file — `01-button-primary.json`

```json
{
  "$id": "components/button-primary",
  "name": "Button - Primary",
  "type": "component",
  "library": "shadcn/ui + Radix Slot",
  "dependsOn": [
    "tokens/color-tertiary",
    "tokens/color-surface",
    "tokens/color-primary",
    "typography/special-patterns",
    "radius/radius-scale",
    "motion/transition-defaults",
    "elevation/focus-ring"
  ],
  "anatomy": ["container", "icon", "label", "trailing-icon", "spinner"],
  "props": {
    "size":     { "values": ["sm", "default", "lg"], "default": "default" },
    "variant":  { "values": ["primary"],            "default": "primary" },
    "disabled": { "type":   "boolean",              "default": false },
    "loading":  { "type":   "boolean",              "default": false },
    "leadingIcon":  { "type": "ReactNode",          "default": null },
    "trailingIcon": { "type": "ReactNode",          "default": null }
  },
  "tokens": {
    "backgroundColor": "{colors.tertiary}",
    "textColor":       "{colors.surface}",
    "typography":      "{typography.label-caps}",
    "rounded":         "{rounded.md}",
    "padding":         "12px 24px",
    "height":          "40px"
  },
  "sizes": {
    "sm":      { "height": "32px", "padding": "8px 12px",  "fontSize": "12px" },
    "default": { "height": "40px", "padding": "12px 24px", "fontSize": "12px" },
    "lg":      { "height": "44px", "padding": "14px 32px", "fontSize": "14px" }
  },
  "states": {
    "default":  { "backgroundColor": "{colors.tertiary}",  "textColor": "{colors.surface}" },
    "hover":    { "backgroundColor": "{colors.primary}",   "textColor": "{colors.surface}" },
    "focus":    { "boxShadow": "0 0 0 3px {colors.tertiary}/50" },
    "active":   { "transform": "scale(0.98)" },
    "disabled": { "opacity": 0.5, "pointerEvents": "none", "cursor": "not-allowed" },
    "loading":  { "iconReplaced": "spinner", "label": "preserved" },
    "error":    "not-implemented",
    "selected": "N/A"
  },
  "transitions": [
    { "property": "background-color", "duration": "150ms", "easing": "ease" },
    { "property": "transform",        "duration":  "50ms", "easing": "ease" },
    { "property": "box-shadow",       "duration":   "0ms", "easing": "step-start" }
  ],
  "accessibility": {
    "role": "button",
    "keyboard": ["Enter", "Space"],
    "contrast": "WCAG-AA-verified",
    "ariaPatterns": ["aria-disabled", "aria-busy"],
    "focusVisible": "ring",
    "screenReader": "Announces the visible label"
  },
  "composition": [
    "Pair with Button - Secondary 'Cancel' in dialog footers, right-aligned, gap 8px.",
    "Used as the single right-aligned action in CardFooter compositions.",
    "Used standalone as hero CTAs.",
    "Discipline: never more than one button-primary visible per viewport."
  ],
  "source": {
    "file": "src/components/ui/Button.tsx",
    "selector": "button[data-variant=primary]",
    "cssVar": null,
    "lineRange": "12-110"
  },
  "notes": "transform: scale(0.98) on :active comes from globals.css, not the CVA block. icon-to-text gap of 8px is from base class gap-2."
}
```

---

## What to notice

1. **Both files cover the same component from two angles.** The `.md` carries prose, anatomy, composition examples, and source evidence narrative. The `.json` carries the machine values that another agent ingests.
2. **No information is duplicated** — the `.md`'s **Cross-references** section names dependencies; the `.json`'s `dependsOn` array names the same dependencies; the two are intentionally **redundant for verification** but not duplicated as prose.
3. **States are explicit.** Every row in the States table is filled or marked `not-implemented` / `N/A`. The JSON mirrors this; missing keys would fail verification.
4. **Token references use DESIGN.md syntax** — `"{colors.tertiary}"`. This matches the frontmatter of the generated `design.md`.
5. **The `tokens` block in the JSON** is identical to the `components.button-primary` block in `design.md` frontmatter. The JSON is the single source of truth; the frontmatter is built from it.
6. **`composition` is content-shaped** — short bullet points naming concrete compositions, not generic UI advice.
7. **`source` always records the file path + selector** — the audit trail that lets a reproducer (or maintainer) verify the captured values.
