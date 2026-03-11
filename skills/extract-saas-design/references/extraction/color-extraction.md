# Color Extraction Methodology

Extract every color from a codebase — CSS variables, Tailwind classes, hardcoded values — and map them to a structured token system.

---

## Step 1: Locate All Color Sources

### CSS Custom Properties

```bash
# Find all CSS variable definitions
grep -rn '--[a-z-]*:\s*#\|--[a-z-]*:\s*rgb\|--[a-z-]*:\s*hsl\|--[a-z-]*:\s*oklch' \
  --include="*.css" --include="*.scss" --include="*.less" src/

# Find all CSS variable usages
grep -rn 'var(--' --include="*.css" --include="*.tsx" --include="*.jsx" src/
```

### Tailwind Config Colors

```bash
# Check tailwind.config for theme extensions
grep -A 50 'colors:' tailwind.config.*
grep -A 50 'extend:' tailwind.config.*

# Find CSS variable-based Tailwind colors
grep -rn 'hsl(var(--\|oklch(var(--\|rgb(var(--' --include="*.css" src/
```

### Hardcoded Colors (Inconsistencies)

```bash
# Find inline hex colors in components
grep -rn '#[0-9a-fA-F]\{3,8\}' --include="*.tsx" --include="*.jsx" --include="*.css" src/

# Find inline rgb/hsl in components
grep -rn 'rgb(\|rgba(\|hsl(\|hsla(' --include="*.tsx" --include="*.jsx" src/
```

---

## Step 2: Resolve the Token Chain

Colors in modern apps follow a resolution chain:

```
Tailwind class → CSS variable → Computed value
    bg-primary  →  var(--primary)  →  oklch(0.21 0.006 285.88)
```

### Resolution Process

1. **Read the Tailwind class** from the component: `bg-primary`
2. **Find the CSS variable** it maps to: check `tailwind.config` or `globals.css`
3. **Resolve to computed value**: follow `var()` references until you reach a literal
4. **Document both modes**: light value AND dark value

### Example Resolution

```css
/* globals.css */
:root {
  --primary: oklch(0.21 0.006 285.88);        /* Near-black */
  --primary-foreground: oklch(0.985 0 0);       /* Near-white */
}

.dark {
  --primary: oklch(0.92 0.004 286.32);          /* Near-white */
  --primary-foreground: oklch(0.21 0.006 285.88); /* Near-black */
}
```

**Document as:**

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| --primary | oklch(0.21 0.006 285.88) | oklch(0.92 0.004 286.32) | Primary buttons, accent links |
| --primary-foreground | oklch(0.985 0 0) | oklch(0.21 0.006 285.88) | Text on primary |

---

## Step 3: Categorize by Semantic Purpose

### Surface Tokens (backgrounds)

| Token | Purpose | Example Component |
|-------|---------|-------------------|
| --background | Page canvas | `<body>`, main content area |
| --card | Elevated surface | Card, panel backgrounds |
| --popover | Floating surface | Dropdowns, tooltips, popovers |
| --sidebar-background | Sidebar canvas | Navigation sidebar |

### Text Tokens (foregrounds)

| Token | Purpose | Example Component |
|-------|---------|-------------------|
| --foreground | Primary text | Body text, headings |
| --muted-foreground | Secondary text | Descriptions, timestamps, labels |
| --card-foreground | Card text | Text inside cards |

### Interactive Tokens

| Token | Purpose | Example Component |
|-------|---------|-------------------|
| --primary | Primary actions | CTA buttons, active nav |
| --secondary | Secondary actions | Cancel buttons, toggles |
| --accent | Hover/active backgrounds | Menu item hover, selection |
| --destructive | Danger actions | Delete buttons, error alerts |

### Border & Control Tokens

| Token | Purpose | Example Component |
|-------|---------|-------------------|
| --border | Standard borders | Card borders, dividers |
| --input | Input borders | Text input, select trigger |
| --ring | Focus ring color | Focus-visible indicator |

### Semantic Status Colors

| Token | Purpose | Example |
|-------|---------|---------|
| --success | Positive feedback | Success toast, trend-up indicator |
| --warning | Caution | Warning alert, approaching limit |
| --info | Informational | Info badge, help tooltip |
| --destructive | Error/danger | Error toast, delete confirmation |

---

## Step 4: Document Opacity Patterns

Opacity modifiers are semantic. Document what each means:

```bash
# Find opacity modifier usage
grep -rn '/[0-9]\+' --include="*.tsx" --include="*.jsx" src/ | \
  grep -o 'bg-[a-z-]*/[0-9]\+\|text-[a-z-]*/[0-9]\+'  | sort | uniq -c | sort -rn
```

### Common Opacity Scale

| Modifier | Opacity | Semantic Meaning | Example Usage |
|----------|---------|-----------------|---------------|
| /5 | 5% | Barely visible background | Ghost button hover |
| /10 | 10% | Subtle tint | Dark mode borders, faint highlight |
| /15 | 15% | Surface-adaptive borders | Dark mode card borders |
| /30 | 30% | Soft background | Dark mode input background |
| /50 | 50% | Half presence | Focus rings, disabled elements |
| /70 | 70% | Prominent overlay | Backdrop behind modals |
| /80 | 80% | Strong presence | Secondary hover states |
| /90 | 90% | Near-full | Primary button hover darken |

---

## Step 5: Chart/Visualization Palette

Dashboard apps always have a separate chart palette. Find it:

```bash
# Look for chart-specific colors
grep -rn 'chart\|--chart\|chartColors\|CHART_COLORS' \
  --include="*.css" --include="*.ts" --include="*.tsx" src/

# Look for Recharts/D3 color configs
grep -rn 'fill="\|stroke="\|color:\s*\[' --include="*.tsx" --include="*.jsx" src/
```

### Document Chart Colors

| Index | Token | Light Value | Dark Value | Series Purpose |
|-------|-------|-------------|------------|----------------|
| 1 | --chart-1 | hsl(12 76% 61%) | hsl(220 70% 50%) | Primary data series |
| 2 | --chart-2 | hsl(173 58% 39%) | hsl(160 60% 45%) | Secondary data series |
| 3 | --chart-3 | hsl(197 37% 24%) | hsl(30 80% 55%) | Tertiary |
| 4 | --chart-4 | hsl(43 74% 66%) | hsl(280 65% 60%) | Quaternary |
| 5 | --chart-5 | hsl(27 87% 67%) | hsl(340 75% 55%) | Fifth |

---

## Step 6: Identify Color Space

The color space matters for interpolation and manipulation:

| Color Space | Syntax | Pros | Cons |
|-------------|--------|------|------|
| hex | #1a1a1a | Compact, universal | No alpha, poor interpolation |
| rgb/rgba | rgb(26 26 26) | Alpha support | Perceptually non-uniform |
| hsl/hsla | hsl(0 0% 10%) | Human-readable hue | Poor perceptual uniformity |
| oklch | oklch(0.21 0.006 285) | Perceptually uniform, wide gamut | Newer, less tooling |

**Detection:**
```bash
# Determine which color space the codebase uses
grep -c 'oklch\|hsl\|rgb\|#[0-9a-f]' globals.css
```

---

## Step 7: Mode Switching Mechanism

Document HOW dark mode works:

| Mechanism | Detection | Example |
|-----------|-----------|---------|
| `.dark` class | `grep 'class.*dark\|\.dark'` on `<html>` | next-themes, class toggle |
| `data-theme` | `grep 'data-theme'` | daisyUI, custom themes |
| `@media prefers-color-scheme` | `grep '@media.*prefers-color-scheme'` | OS-level only |
| JS runtime | `grep 'setTheme\|toggleTheme'` | Custom implementation |

---

## Output Checklist

After extraction, verify:

- [ ] Every CSS variable documented with both light and dark values
- [ ] Every semantic purpose explained (not just "primary" but "primary buttons, active nav")
- [ ] Opacity modifiers cataloged with semantic meaning
- [ ] Chart/visualization palette documented separately from UI colors
- [ ] Sidebar-specific tokens documented (if they exist)
- [ ] Hardcoded colors flagged as inconsistencies
- [ ] Color space identified and documented
- [ ] Mode switching mechanism documented
- [ ] All tokens grouped by semantic purpose (surface, text, interactive, border, status)
