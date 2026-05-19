# Extraction Cheatsheet — Token Chains, Tailwind, oklch

Practical patterns to read values out of a source. Use during Phase 4 when capturing per-asset values.

---

## Detect the styling stack (run before extracting)

```bash
# Tailwind v4 detection
grep -rl '@import.*tailwindcss' --include="*.css" . 2>/dev/null && echo "Tailwind v4"
grep -rl '@theme' --include="*.css" . 2>/dev/null && echo "Tailwind v4 (@theme blocks)"

# Tailwind v3 detection
ls tailwind.config.* 2>/dev/null && echo "Tailwind v3"

# shadcn/ui detection
ls components/ui/ 2>/dev/null && echo "shadcn/ui (root)"
ls src/components/ui/ 2>/dev/null && echo "shadcn/ui (src/)"
grep -l 'class-variance-authority' package.json && echo "CVA in use"

# CSS-in-JS detection
grep -l '"styled-components"\|"@emotion/' package.json && echo "CSS-in-JS"

# SCSS detection
find . -name "_variables.scss" -o -name "_tokens.scss" 2>/dev/null | head -3
```

Detection determines where tokens live.

---

## Resolve token chains to the literal

Tokens chain through Tailwind class → CSS variable → literal. Always resolve to the literal.

```
bg-primary
  → tailwind.config.* maps to `var(--primary)`
  → globals.css `:root { --primary: oklch(0.21 0.006 285.88); }`
  → LITERAL: oklch(0.21 0.006 285.88)
```

Multi-hop chains:

```
--sidebar-background
  → var(--sidebar)
  → :root { --sidebar: oklch(0.985 0 0); }
  → LITERAL: oklch(0.985 0 0)  /* light */
.dark { --sidebar: oklch(0.145 0 0); }
  → LITERAL: oklch(0.145 0 0)  /* dark */
```

Document the LITERAL in `$value`. Document the chain in source-evidence prose.

---

## Read oklch values

Modern shadcn (2024+) uses oklch. Format: `oklch(L C H)`.

| Component | Range | Meaning |
|---|---|---|
| L (lightness) | 0.0–1.0 | 0 = black, 1 = white. L<0.3 = dark, L>0.9 = light. |
| C (chroma) | 0.0–0.4 | 0 = pure gray, >0.1 = colored. C<0.01 = near-gray. |
| H (hue) | 0–360 | Color wheel angle. Irrelevant when C is near 0. |

Quick reads:

```
oklch(0.205 0.006 285.88)  → very dark, barely tinted (near-gray with slight cool cast) → very dark text/background
oklch(0.985 0 0)            → near-white, pure gray (no hue)                              → page surface
oklch(0.577 0.245 27.325)   → mid-tone, highly saturated, red hue                         → destructive
oklch(0.708 0.005 286.286)  → light mid-tone, near-gray                                   → ring/border
```

Convert to hex (when target system doesn't support oklch): use a culori or chroma.js based converter offline; record both the original oklch (in source evidence) and the hex (in `$value`).

---

## CSS custom property extraction

For codebase / snapshot:

```bash
# All :root custom property definitions
grep -rnE '^\s*--[a-z-]+\s*:\s*[^;]+;?' --include="*.css" --include="*.scss" .

# All var(--) usages with frequency
grep -rohE 'var\(--[a-z-]+\)' --include="*.css" --include="*.tsx" --include="*.jsx" --include="*.vue" . | sort | uniq -c | sort -rn

# Chart & sidebar token scopes
grep -rnE '--(chart|sidebar)-[a-z0-9-]+\s*:' --include="*.css" .
```

For live URL (browser computed styles): `run-agent-browser` returns the computed `var()` resolution per element. Use that.

---

## CVA (class-variance-authority) extraction

The `cva()` call IS the component's visual spec. Extract every key/value pair.

```tsx
// Source
const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md ...",
  {
    variants: {
      variant: {
        default:     "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline:     "border border-input bg-background hover:bg-accent",
        ghost:       "hover:bg-accent hover:text-accent-foreground"
      },
      size: {
        default: "h-10 px-4 py-2",
        sm:      "h-9 px-3",
        lg:      "h-11 px-8",
        icon:    "h-10 w-10"
      }
    },
    defaultVariants: {
      variant: "default",
      size:    "default"
    }
  }
)
```

Extract:

- **Base classes** — `"inline-flex items-center justify-center rounded-md ..."` applied to all variants.
- **Each variant key** — `variant`, `size`.
- **Each variant value** — `default`, `destructive`, `outline`, `ghost`; `sm`, `lg`, `icon`.
- **Default variants** — which variant/size applies with no props.
- **Compound variants** (when present) — overrides when two values combine.

Map each variant's class string to the per-asset JSON's `tokens` and `states` blocks.

---

## Tailwind-to-CSS conversion tables

### Spacing (1 unit = 4px)

| Tailwind | CSS |
|---|---|
| `p-0` | padding: 0 |
| `p-0.5` | padding: 2px |
| `p-1` | padding: 4px |
| `p-1.5` | padding: 6px |
| `p-2` | padding: 8px |
| `p-3` | padding: 12px |
| `p-4` | padding: 16px |
| `p-5` | padding: 20px |
| `p-6` | padding: 24px |
| `p-8` | padding: 32px |
| `p-10` | padding: 40px |
| `p-12` | padding: 48px |
| `gap-2` | gap: 8px |
| `gap-3` | gap: 12px |
| `gap-4` | gap: 16px |

### Sizing

| Tailwind | CSS |
|---|---|
| `h-7` | height: 28px |
| `h-8` | height: 32px |
| `h-9` | height: 36px |
| `h-10` | height: 40px |
| `h-11` | height: 44px |
| `w-full` | width: 100% |
| `size-4` | width: 16px; height: 16px |
| `size-5` | width: 20px; height: 20px |
| `size-6` | width: 24px; height: 24px |

### Border-radius

| Tailwind | CSS |
|---|---|
| `rounded-none` | border-radius: 0 |
| `rounded-sm` | border-radius: calc(var(--radius) - 4px) |
| `rounded` | border-radius: 4px |
| `rounded-md` | border-radius: calc(var(--radius) - 2px) |
| `rounded-lg` | border-radius: var(--radius) |
| `rounded-xl` | border-radius: calc(var(--radius) + 4px) |
| `rounded-2xl` | border-radius: calc(var(--radius) + 8px) |
| `rounded-full` | border-radius: 9999px |

### Typography

| Tailwind | CSS |
|---|---|
| `text-xs` | font-size: 12px; line-height: 16px |
| `text-sm` | font-size: 14px; line-height: 20px |
| `text-base` | font-size: 16px; line-height: 24px |
| `text-lg` | font-size: 18px; line-height: 28px |
| `text-xl` | font-size: 20px; line-height: 28px |
| `text-2xl` | font-size: 24px; line-height: 32px |
| `text-3xl` | font-size: 30px; line-height: 36px |
| `font-normal` | font-weight: 400 |
| `font-medium` | font-weight: 500 |
| `font-semibold` | font-weight: 600 |
| `font-bold` | font-weight: 700 |
| `tracking-tight` | letter-spacing: -0.025em |
| `tracking-wider` | letter-spacing: 0.05em |
| `leading-none` | line-height: 1 |
| `leading-tight` | line-height: 1.25 |

### Common patterns

| Tailwind | CSS |
|---|---|
| `transition-all` | transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1) |
| `transition-colors` | transition: color, background-color, border-color 150ms cubic-bezier(0.4, 0, 0.2, 1) |
| `duration-200` | transition-duration: 200ms |
| `ease-out` | transition-timing-function: cubic-bezier(0, 0, 0.2, 1) |
| `shrink-0` | flex-shrink: 0 |
| `whitespace-nowrap` | white-space: nowrap |
| `select-none` | user-select: none |
| `pointer-events-none` | pointer-events: none |
| `tabular-nums` | font-variant-numeric: tabular-nums |
| `truncate` | overflow: hidden; text-overflow: ellipsis; white-space: nowrap |
| `disabled:opacity-50` | &:disabled { opacity: 0.5 } |
| `focus-visible:ring-2` | &:focus-visible { box-shadow: 0 0 0 2px ... } |

### Opacity modifier syntax

| Tailwind | CSS |
|---|---|
| `bg-primary/90` | background-color: color-mix(in oklch, var(--primary) 90%, transparent) |
| `text-foreground/70` | color: color-mix(in oklch, var(--foreground) 70%, transparent) |
| `bg-black/50` | background-color: rgb(0 0 0 / 0.5) |

Modern Tailwind uses `color-mix` for opacity; older variants flatten to `rgb()` with alpha. Pick the form the source uses.

---

## Resolution checklist (apply to every component)

When extracting a component, walk this checklist:

- [ ] Base classes resolved to CSS.
- [ ] Every variant resolved.
- [ ] Every size resolved.
- [ ] Default variant identified.
- [ ] Default state values captured.
- [ ] Hover values captured (transitions noted).
- [ ] Focus-visible values captured (ring style).
- [ ] Active / pressed values captured (or `not-implemented`).
- [ ] Disabled values captured (opacity + pointer-events).
- [ ] Loading state captured (or `not-implemented`).
- [ ] Error / aria-invalid captured (or `not-implemented`).
- [ ] Selected / data-[state=active] captured (for toggleable; or `N/A`).
- [ ] Dark mode values captured (every property that changes).
- [ ] Internal spacing measured (padding, gap, min dimensions).
- [ ] Accessibility role, keyboard, focus mode noted.
- [ ] Composition: which siblings appear with this component.

When every box is checked or explicitly `not-implemented` / `N/A`, the asset is complete.

---

## Common failure patterns

| Pattern | Fix |
|---|---|
| Tailwind v4 missed because looking for `tailwind.config.js`. | Always grep for `@import "tailwindcss"` and `@theme` first. |
| oklch L misread as percentage. | L is 0–1, not 0–100. L=0.2 means very dark, not 20%-of-light. |
| Token chain stopped at the alias (`bg-primary` recorded, not the literal). | Always follow `var()` to the final literal. |
| CVA variants partially extracted. | Read the whole `cva()` call; extract every value of every key. |
| Hover/active conflated. | `:hover` fires on mouse-over; `:active` fires while held. They have different timings. |
| Focus and focus-visible conflated. | `:focus` fires on click + tab; `:focus-visible` is keyboard-only. Modern UIs use focus-visible only. |
| Dark mode skipped. | Always check for `.dark`, `@media prefers-color-scheme`, `data-theme=dark`. |
| Sidebar tokens missed. | `--sidebar-background`, `--sidebar-foreground`, `--sidebar-ring` are a separate token scope; grep specifically. |
