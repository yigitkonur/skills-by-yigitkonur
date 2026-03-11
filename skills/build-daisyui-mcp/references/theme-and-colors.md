# Theme and Color Reference

> Definitive reference for daisyUI 5 theming: semantic colors, oklch format, custom themes, shape variables, built-in themes, and design patterns.
>
> See also: `references/component-catalog.md` for components, `workflow/05-theme-generation-workflow.md` for creating themes from brand assets.

---

## Semantic Color System

daisyUI uses semantic color names instead of raw hex/Tailwind palette colors. Every theme defines these 20 CSS custom properties. They adapt automatically when the active theme changes — **no `dark:` prefix needed**.

### The 20 Required Color Variables

| # | Variable | Content Pair | Purpose |
|---|----------|-------------|---------|
| 1 | `--color-primary` | `--color-primary-content` | Brand primary — buttons, links, active states, CTAs |
| 2 | `--color-secondary` | `--color-secondary-content` | Brand secondary — supporting actions, less prominent UI |
| 3 | `--color-accent` | `--color-accent-content` | Accent/highlight — badges, eye-catching elements |
| 4 | `--color-neutral` | `--color-neutral-content` | Neutral tone — dark backgrounds, emphasis areas |
| 5 | `--color-base-100` | `--color-base-content` | Page background (lightest) + default text color |
| 6 | `--color-base-200` | *(shares base-content)* | Slightly darker — cards, elevated surfaces |
| 7 | `--color-base-300` | *(shares base-content)* | Even darker — borders, dividers, subtle backgrounds |
| 8 | `--color-info` | `--color-info-content` | Informational — help messages, info badges |
| 9 | `--color-success` | `--color-success-content` | Success state — confirmations, completed steps |
| 10 | `--color-warning` | `--color-warning-content` | Warning state — caution messages, pending actions |
| 11 | `--color-error` | `--color-error-content` | Error state — errors, destructive actions, danger |

### How Semantic Colors Work in Utility Classes

```html
<!-- daisyUI semantic colors — adapt per theme -->
<div class="bg-primary text-primary-content">Themed button</div>
<div class="bg-base-100 text-base-content">Themed page</div>

<!-- Tailwind raw colors — SAME on all themes (avoid for theming) -->
<div class="bg-blue-500 text-white">Always blue, breaks on dark theme</div>
```

### Color Design Rules

1. Use `base-*` colors for the majority of the page
2. Use `primary` for the most important interactive elements
3. Use `secondary` and `accent` sparingly for visual hierarchy
4. Use status colors (`info`, `success`, `warning`, `error`) only for their semantic purpose
5. Every `-content` color must have sufficient contrast against its parent color
6. Never use Tailwind palette colors (e.g. `text-gray-800`) on semantic backgrounds — they won't adapt to dark themes
7. All Tailwind utilities (`bg-`, `text-`, `border-`, `ring-`, `outline-`, `shadow-`) accept daisyUI color names
8. Opacity modifiers work: `bg-primary/50` gives 50% opacity primary background

---

## oklch Color Format

daisyUI 5 uses oklch as the preferred color format. It provides perceptually uniform lightness, making it easy to create accessible color pairs.

### Format

```
oklch(lightness% chroma hue)
```

| Component | Range | Description |
|-----------|-------|-------------|
| **Lightness** | `0%` (black) to `100%` (white) | Perceived brightness — perceptually uniform |
| **Chroma** | `0` (gray) to `~0.4` (maximum vivid) | Color intensity / saturation |
| **Hue** | `0` to `360` degrees | Position on color wheel |

### Hue Wheel Reference

```
  0° = Red          60° = Orange/Yellow
 90° = Yellow      120° = Yellow-Green
150° = Green       180° = Cyan
210° = Sky Blue    240° = Blue
270° = Violet      300° = Magenta/Purple
330° = Pink        360° = Red (wraps)
```

### Common Hex → oklch Conversions

| Color | Hex | oklch | L% | C | H |
|-------|-----|-------|----|---|---|
| Pure White | `#ffffff` | `oklch(100% 0 0)` | 100 | 0 | 0 |
| Pure Black | `#000000` | `oklch(0% 0 0)` | 0 | 0 | 0 |
| Light Gray | `#f3f4f6` | `oklch(96% 0.01 260)` | 96 | 0.01 | 260 |
| Medium Gray | `#6b7280` | `oklch(55% 0.02 260)` | 55 | 0.02 | 260 |
| Dark Gray | `#1f2937` | `oklch(27% 0.02 260)` | 27 | 0.02 | 260 |
| **Red** | `#ef4444` | `oklch(58% 0.22 25)` | 58 | 0.22 | 25 |
| **Orange** | `#f97316` | `oklch(70% 0.19 50)` | 70 | 0.19 | 50 |
| **Amber** | `#f59e0b` | `oklch(77% 0.17 75)` | 77 | 0.17 | 75 |
| **Yellow** | `#eab308` | `oklch(80% 0.18 95)` | 80 | 0.18 | 95 |
| **Green** | `#22c55e` | `oklch(72% 0.19 150)` | 72 | 0.19 | 150 |
| **Teal** | `#14b8a6` | `oklch(70% 0.14 180)` | 70 | 0.14 | 180 |
| **Cyan** | `#06b6d4` | `oklch(68% 0.13 210)` | 68 | 0.13 | 210 |
| **Blue** | `#3b82f6` | `oklch(62% 0.19 260)` | 62 | 0.19 | 260 |
| **Indigo** | `#6366f1` | `oklch(55% 0.22 275)` | 55 | 0.22 | 275 |
| **Purple** | `#8b5cf6` | `oklch(55% 0.22 290)` | 55 | 0.22 | 290 |
| **Pink** | `#ec4899` | `oklch(60% 0.22 345)` | 60 | 0.22 | 345 |

### Brand Color Ranges → oklch

| Brand Style | Primary oklch | Typical L% | Typical C | Hue Range |
|-------------|--------------|------------|-----------|-----------|
| Corporate Blue | `oklch(55% 0.2 250)` | 45–60% | 0.15–0.25 | 240–260 |
| Startup Green | `oklch(65% 0.2 150)` | 60–72% | 0.15–0.25 | 140–165 |
| Creative Purple | `oklch(50% 0.25 290)` | 45–60% | 0.2–0.3 | 280–310 |
| Warm Orange | `oklch(70% 0.18 55)` | 65–75% | 0.15–0.2 | 40–70 |
| Elegant Red | `oklch(55% 0.22 25)` | 50–60% | 0.18–0.25 | 15–35 |
| Tech Cyan | `oklch(68% 0.14 210)` | 60–72% | 0.1–0.18 | 195–220 |
| Luxury Gold | `oklch(75% 0.15 85)` | 70–80% | 0.12–0.18 | 75–95 |

> **Tip:** You can also use hex values directly — `--color-primary: #3b82f6;` — but oklch makes it easier to create consistent palettes and verify contrast.

---

## Complete Theme CSS Template

Every custom theme must define **all 26 variables** (20 colors + 6 shape/effect). Below is the complete template with real oklch values and explanatory comments.

```css
@import "tailwindcss";
@plugin "daisyui";

@plugin "daisyui/theme" {
  name: "mytheme";
  default: true;            /* Set as the default active theme */
  prefersdark: false;       /* Set true to activate via prefers-color-scheme: dark */
  color-scheme: light;      /* Tells the browser UI (scrollbars, etc.) to use light or dark chrome */

  /* ─────────────────────────────────────────────
     BASE COLORS — Page backgrounds & default text
     base-100 is lightest (page), base-300 is darkest (borders)
     ───────────────────────────────────────────── */
  --color-base-100: oklch(98% 0.02 240);        /* Page background — lightest surface */
  --color-base-200: oklch(95% 0.03 240);        /* Card/section background — slightly darker */
  --color-base-300: oklch(92% 0.04 240);        /* Borders, dividers, subtle backgrounds */
  --color-base-content: oklch(20% 0.05 240);    /* Default text color on all base backgrounds */

  /* ─────────────────────────────────────────────
     PRIMARY — Main brand / CTA color
     Used for: buttons, links, active states, primary actions
     ───────────────────────────────────────────── */
  --color-primary: oklch(55% 0.3 240);          /* Brand primary color */
  --color-primary-content: oklch(98% 0.01 240); /* Text/icons on primary background */

  /* ─────────────────────────────────────────────
     SECONDARY — Supporting brand color
     Used for: secondary buttons, less prominent actions
     ───────────────────────────────────────────── */
  --color-secondary: oklch(70% 0.25 200);       /* Brand secondary color */
  --color-secondary-content: oklch(98% 0.01 200); /* Text/icons on secondary background */

  /* ─────────────────────────────────────────────
     ACCENT — Highlight / pop color
     Used for: badges, highlights, attention-grabbing elements
     ───────────────────────────────────────────── */
  --color-accent: oklch(65% 0.25 160);          /* Accent / highlight color */
  --color-accent-content: oklch(98% 0.01 160);  /* Text/icons on accent background */

  /* ─────────────────────────────────────────────
     NEUTRAL — Dark neutral tone
     Used for: dark backgrounds, navbar, footer, emphasis areas
     ───────────────────────────────────────────── */
  --color-neutral: oklch(50% 0.05 240);         /* Neutral dark color (low chroma) */
  --color-neutral-content: oklch(98% 0.01 240); /* Text/icons on neutral background */

  /* ─────────────────────────────────────────────
     STATUS COLORS — Informational states
     Used for: alerts, toasts, badges, form validation
     ───────────────────────────────────────────── */
  --color-info: oklch(70% 0.2 220);             /* Informational — blue tone */
  --color-info-content: oklch(98% 0.01 220);    /* Text on info background */

  --color-success: oklch(65% 0.25 140);         /* Success — green tone */
  --color-success-content: oklch(98% 0.01 140); /* Text on success background */

  --color-warning: oklch(80% 0.25 80);          /* Warning — amber tone */
  --color-warning-content: oklch(20% 0.05 80);  /* Text on warning (dark, because bg is light) */

  --color-error: oklch(65% 0.3 30);             /* Error — red tone */
  --color-error-content: oklch(98% 0.01 30);    /* Text on error background */

  /* ─────────────────────────────────────────────
     BORDER RADIUS — Roundness of UI elements
     Preferred values: 0rem, 0.25rem, 0.5rem, 1rem, 2rem
     ───────────────────────────────────────────── */
  --radius-selector: 1rem;    /* Checkboxes, toggles, radio buttons, badges */
  --radius-field: 0.25rem;    /* Buttons, inputs, selects, tabs */
  --radius-box: 0.5rem;       /* Cards, modals, drawers, alerts */

  /* ─────────────────────────────────────────────
     SIZE — Base sizing scale for interactive elements
     Default: 0.25rem. Increase for larger UI, decrease for compact
     ───────────────────────────────────────────── */
  --size-selector: 0.25rem;   /* Size scale for checkboxes, toggles, badges */
  --size-field: 0.25rem;      /* Size scale for buttons, inputs, selects, tabs */

  /* ─────────────────────────────────────────────
     EFFECTS — Borders, shadows, and texture
     ───────────────────────────────────────────── */
  --border: 1px;              /* Default border width. Typical: 1px, 1.5px, or 2px */
  --depth: 1;                 /* 0 = flat (no shadows), 1 = elevated (shadows + 3D) */
  --noise: 0;                 /* 0 = clean surfaces, 1 = subtle grain/noise texture */
}
```

### Variable Summary Table

| Variable | Type | Required | Values |
|----------|------|----------|--------|
| `name` | Theme metadata | Yes | Valid CSS identifier string |
| `default` | Theme metadata | No | `true` or `false` |
| `prefersdark` | Theme metadata | No | `true` or `false` |
| `color-scheme` | Theme metadata | No | `light` or `dark` |
| `--color-base-100` | Color | Yes | oklch or hex |
| `--color-base-200` | Color | Yes | oklch or hex |
| `--color-base-300` | Color | Yes | oklch or hex |
| `--color-base-content` | Color | Yes | oklch or hex |
| `--color-primary` | Color | Yes | oklch or hex |
| `--color-primary-content` | Color | Yes | oklch or hex |
| `--color-secondary` | Color | Yes | oklch or hex |
| `--color-secondary-content` | Color | Yes | oklch or hex |
| `--color-accent` | Color | Yes | oklch or hex |
| `--color-accent-content` | Color | Yes | oklch or hex |
| `--color-neutral` | Color | Yes | oklch or hex |
| `--color-neutral-content` | Color | Yes | oklch or hex |
| `--color-info` | Color | Yes | oklch or hex |
| `--color-info-content` | Color | Yes | oklch or hex |
| `--color-success` | Color | Yes | oklch or hex |
| `--color-success-content` | Color | Yes | oklch or hex |
| `--color-warning` | Color | Yes | oklch or hex |
| `--color-warning-content` | Color | Yes | oklch or hex |
| `--color-error` | Color | Yes | oklch or hex |
| `--color-error-content` | Color | Yes | oklch or hex |
| `--radius-selector` | Shape | Yes | CSS length (`0rem`–`2rem`) |
| `--radius-field` | Shape | Yes | CSS length (`0rem`–`1rem`) |
| `--radius-box` | Shape | Yes | CSS length (`0rem`–`1.5rem`) |
| `--size-selector` | Size | Yes | CSS length (default `0.25rem`) |
| `--size-field` | Size | Yes | CSS length (default `0.25rem`) |
| `--border` | Effect | Yes | CSS length (`0.5px`, `1px`, `1.5px`, `2px`) |
| `--depth` | Effect | Yes | `0` or `1` only |
| `--noise` | Effect | Yes | `0` or `1` only |

---

## Shape Variables Explained

| Variable | Applies To | Example Values | Visual Effect |
|----------|-----------|----------------|---------------|
| `--radius-selector` | Checkboxes, toggles, radio buttons, badges | `0rem` (square) → `0.25rem` (subtle) → `1rem` (rounded) → `2rem` (pill) | Controls roundness of small selectable elements |
| `--radius-field` | Buttons, inputs, selects, textareas, tabs | `0rem` (sharp) → `0.25rem` (default) → `0.5rem` (soft) → `1rem` (very round) | Controls roundness of form controls |
| `--radius-box` | Cards, modals, drawers, alerts, dropdowns | `0rem` (sharp) → `0.5rem` (default) → `1rem` (rounded) → `1.5rem` (very round) | Controls roundness of container elements |
| `--size-selector` | Checkbox, toggle, badge sizing | `0.1875rem` (compact) → `0.25rem` (default) → `0.3125rem` (larger) | Makes selectable elements smaller or larger |
| `--size-field` | Button, input, select, tab sizing | `0.1875rem` (compact) → `0.25rem` (default) → `0.3125rem` (larger) | Makes form controls smaller or larger |
| `--border` | All bordered components | `0.5px` (thin) → `1px` (default) → `1.5px` → `2px` (bold) | Controls default border thickness |
| `--depth` | Shadow/elevation on all components | `0` = flat, no shadows / `1` = subtle shadow + 3D depth | Binary toggle for elevation style |
| `--noise` | Texture overlay on surfaces | `0` = clean, smooth surfaces / `1` = subtle grain texture | Binary toggle for organic/textured feel |

### Preferred `--radius-*` Values

```
0rem      → square / sharp edges
0.25rem   → barely rounded (corporate, minimal)
0.5rem    → softly rounded (modern default)
1rem      → noticeably rounded (friendly)
2rem      → pill-shaped (playful, bold)
```

### Preferred `--size-*` Values

```
0.1875rem → compact / dense UI
0.21875rem → slightly compact
0.25rem   → default / standard
0.28125rem → slightly larger
0.3125rem → larger / spacious UI
```

---

## WCAG AA Contrast Rules for -content Colors

Every `-content` color must be readable against its parent color. daisyUI uses oklch lightness to determine contrast.

### Quick Rules

| Parent Color Lightness | Content Color Lightness | Example |
|-----------------------|------------------------|---------|
| **> 65%** (light bg) | **< 25%** (dark text) | Warning bg `80%` → content `20%` |
| **< 45%** (dark bg) | **> 85%** (light text) | Primary bg `55%` → content `98%` |
| **45%–65%** (medium bg) | Test both — pick higher contrast | Check both `15%` and `98%` |

### Detailed Guidelines

1. **Minimum lightness gap:** At least 40 percentage points between base and content lightness
2. **Content chroma:** Keep `-content` chroma very low (< `0.05`) for maximum readability
3. **Hue alignment:** Keep content hue close to its parent hue for visual harmony, or use `0` for neutral
4. **Warning is special:** Warning colors are typically light (`~80%` lightness) — they need **dark** content text, unlike other status colors
5. **Test at both extremes:** For borderline cases, render text at both `oklch(98% 0.01 H)` and `oklch(15% 0.02 H)` and choose the one with better contrast

### Content Color Templates

```
Dark text on light bg:  oklch(20% 0.05 {hue})   — for warning, light accent
Light text on dark bg:  oklch(98% 0.01 {hue})   — for primary, secondary, neutral, error, info, success
Near-black text:        oklch(15% 0.02 0)        — maximum contrast on any light bg
Near-white text:        oklch(98% 0.01 0)        — maximum contrast on any dark bg
```

---

## 35 Built-in Themes

daisyUI ships with 35 pre-built themes. Use these before creating custom ones.

### Light Themes (18)

| Theme | Vibe | Best For |
|-------|------|----------|
| `light` | Clean default, neutral gray-blue | General purpose, default fallback |
| `cupcake` | Soft pastels, pink-purple | Friendly apps, playful UI |
| `bumblebee` | Warm yellow/amber | Energetic, attention-grabbing |
| `emerald` | Fresh green nature | Health, eco, nature-themed |
| `corporate` | Professional blue/gray | B2B, enterprise, dashboards |
| `retro` | Vintage warm cream | Nostalgic, creative portfolios |
| `cyberpunk` | Neon yellow/pink, futuristic | Gaming, tech, edgy branding |
| `valentine` | Romantic pink tones | Seasonal, fashion, lifestyle |
| `garden` | Natural greens, earth tones | Organic, gardening, outdoor |
| `lofi` | Minimal, low-contrast | Minimalist, zen, reading |
| `pastel` | Soft pastel rainbow | Kids, education, playful |
| `fantasy` | Purple/magical tones | Creative, gaming, storytelling |
| `wireframe` | Monochrome wireframe look | Prototyping, MVPs |
| `cmyk` | Bold print-inspired | Creative agencies, design |
| `autumn` | Warm fall oranges | Seasonal, cozy, warm |
| `acid` | Vibrant neon/lime | Bold, experimental, youth |
| `lemonade` | Fresh citrus yellow-green | Fresh, clean, summer |
| `winter` | Cool icy blues | Seasonal, calm, professional |

### Dark Themes (17)

| Theme | Vibe | Best For |
|-------|------|----------|
| `dark` | Clean default dark | General purpose dark mode |
| `synthwave` | 80s retro neon purple | Music, gaming, creative |
| `halloween` | Spooky orange/purple | Seasonal, horror, dark fun |
| `forest` | Deep forest greens | Nature, eco, deep green |
| `aqua` | Teal/aqua underwater | Ocean, water, cool tones |
| `black` | Pure OLED black | Ultra-minimal, OLED screens |
| `luxury` | Gold on dark | Premium, finance, upscale |
| `dracula` | Popular dev color scheme | Developer tools, coding |
| `business` | Professional dark | Enterprise dark mode |
| `night` | Deep blue night sky | Evening, calm, space |
| `coffee` | Rich coffee/brown | Warm dark, café, reading |
| `dim` | Muted, low-contrast dark | Easy on eyes, long reading |
| `nord` | Nordic cool palette | Developer-friendly, calm |
| `sunset` | Warm sunset orange-purple | Creative, warm evening |
| `caramellatte` | Warm caramel tones | Cozy, warm, light-dark |
| `abyss` | Deep dark ocean blue | Deep focus, immersive |
| `silk` | Soft elegant muted | Refined, premium, subtle |

### How to Apply Themes

```html
<!-- Set theme globally -->
<html data-theme="light">

<!-- Override for a specific section -->
<div data-theme="dark">
  <!-- This section uses dark theme regardless of page theme -->
</div>
```

### How to Configure Available Themes

```css
/* Default: light + dark */
@plugin "daisyui";

/* Specific themes with defaults */
@plugin "daisyui" {
  themes: light --default, dark --prefersdark, cupcake, dracula;
}

/* All 35 themes */
@plugin "daisyui" {
  themes: all;
}

/* Custom default + dark fallback */
@plugin "daisyui" {
  themes: nord --default, dracula --prefersdark, synthwave;
}

/* Disable all built-in themes (for fully custom) */
@plugin "daisyui" {
  themes: false;
}
```

### Customizing a Built-in Theme

Override specific variables of any built-in theme:

```css
@plugin "daisyui" {
  themes: light --default, dark --prefersdark;
}

/* Override dark theme's primary and secondary colors */
@plugin "daisyui/theme" {
  name: "dark";
  default: false;
  prefersdark: true;
  --color-primary: oklch(65% 0.25 250);
  --color-secondary: oklch(70% 0.2 180);
}
```

---

## Dark Theme Design Tips

### What to Do

1. **Never use `dark:` prefix for daisyUI semantic colors** — they adapt automatically when the theme changes
2. **`dark:` is only for custom Tailwind utilities** outside the daisyUI color system (e.g. `dark:border-gray-700` for a hardcoded Tailwind color)
3. **Design with `base-100` → `base-200` → `base-300`** (lightest to darkest) — they invert automatically in dark themes
4. **Set `color-scheme: dark`** so browser-rendered UI (scrollbars, form controls) matches
5. **Set `prefersdark: true`** to auto-activate via `prefers-color-scheme: dark`

### Dark-Specific Adjustments

| Property | Light Theme | Dark Theme | Why |
|----------|------------|------------|-----|
| `--color-base-100` | `oklch(98% ...)` (near white) | `oklch(18% ...)` (near black) | Flip background luminance |
| `--color-base-content` | `oklch(20% ...)` (dark text) | `oklch(90% ...)` (light text) | Maintain text readability |
| Brand color chroma | Full saturation | Reduce 10–20% | Vivid colors look harsh on dark bg |
| Brand color lightness | Standard | Increase 5–10% | Need more brightness to stand out |
| `--depth` | `0` or `1` | `0` preferred | Shadows look unnatural on dark backgrounds |
| `--noise` | `0` | `0` or `1` | Slight noise can add welcome texture to flat dark surfaces |

### Dark Theme Template

```css
@plugin "daisyui/theme" {
  name: "mydark";
  default: false;
  prefersdark: true;
  color-scheme: dark;

  --color-base-100: oklch(18% 0.02 260);
  --color-base-200: oklch(22% 0.02 260);
  --color-base-300: oklch(28% 0.03 260);
  --color-base-content: oklch(90% 0.01 260);

  --color-primary: oklch(65% 0.20 260);
  --color-primary-content: oklch(15% 0.02 260);
  --color-secondary: oklch(72% 0.18 200);
  --color-secondary-content: oklch(15% 0.02 200);
  --color-accent: oklch(70% 0.18 160);
  --color-accent-content: oklch(15% 0.02 160);
  --color-neutral: oklch(35% 0.03 260);
  --color-neutral-content: oklch(92% 0.01 260);

  --color-info: oklch(72% 0.16 220);
  --color-info-content: oklch(15% 0.01 220);
  --color-success: oklch(70% 0.20 140);
  --color-success-content: oklch(15% 0.01 140);
  --color-warning: oklch(82% 0.20 80);
  --color-warning-content: oklch(20% 0.05 80);
  --color-error: oklch(68% 0.22 30);
  --color-error-content: oklch(15% 0.01 30);

  --radius-selector: 1rem;
  --radius-field: 0.25rem;
  --radius-box: 0.5rem;
  --size-selector: 0.25rem;
  --size-field: 0.25rem;
  --border: 1px;
  --depth: 0;
  --noise: 0;
}
```

---

## Design Pattern Presets

Ready-to-use shape configurations for common design styles. Copy the shape variables into your theme.

### Modern Minimal

Clean lines, subtle rounding, flat with no visual noise.

```css
--radius-selector: 0.5rem;
--radius-field: 0.25rem;
--radius-box: 0.75rem;
--size-selector: 0.25rem;
--size-field: 0.25rem;
--border: 1px;
--depth: 0;
--noise: 0;
```

**Pairs well with:** `corporate`, `lofi`, `nord` base themes. Low-chroma primary colors.

### Rounded Friendly

Soft, approachable, slightly elevated feel.

```css
--radius-selector: 2rem;
--radius-field: 1rem;
--radius-box: 1rem;
--size-selector: 0.25rem;
--size-field: 0.25rem;
--border: 1px;
--depth: 1;
--noise: 0;
```

**Pairs well with:** `cupcake`, `pastel`, `lemonade`. High-lightness, moderate-chroma primaries.

### Corporate Sharp

Precise, professional, buttoned-up.

```css
--radius-selector: 0.125rem;
--radius-field: 0.125rem;
--radius-box: 0.25rem;
--size-selector: 0.25rem;
--size-field: 0.25rem;
--border: 1px;
--depth: 0;
--noise: 0;
```

**Pairs well with:** `corporate`, `business`, `winter`. Blue-gray hue range (230–260).

### Retro / Vintage

No rounding, thick borders, textured surfaces.

```css
--radius-selector: 0rem;
--radius-field: 0rem;
--radius-box: 0rem;
--size-selector: 0.25rem;
--size-field: 0.25rem;
--border: 2px;
--depth: 0;
--noise: 1;
```

**Pairs well with:** `retro`, `wireframe`, `cmyk`. Warm hues (30–80), reduced chroma.

### Playful Bold

Large rounding, prominent borders, elevated with shadows.

```css
--radius-selector: 2rem;
--radius-field: 1rem;
--radius-box: 1.5rem;
--size-selector: 0.3125rem;
--size-field: 0.3125rem;
--border: 2px;
--depth: 1;
--noise: 0;
```

**Pairs well with:** `acid`, `cyberpunk`, `bumblebee`. High-chroma, high-saturation primaries.

---

## Complete Light + Dark Theme Pair Example

A real-world example of creating matched light and dark themes for a SaaS product:

```css
@import "tailwindcss";
@plugin "daisyui" {
  themes: false;
}

/* ─── Light Theme ─── */
@plugin "daisyui/theme" {
  name: "saas-light";
  default: true;
  color-scheme: light;

  --color-base-100: oklch(99% 0.005 240);
  --color-base-200: oklch(96% 0.01 240);
  --color-base-300: oklch(92% 0.015 240);
  --color-base-content: oklch(22% 0.04 240);

  --color-primary: oklch(52% 0.24 255);
  --color-primary-content: oklch(98% 0.01 255);
  --color-secondary: oklch(58% 0.18 195);
  --color-secondary-content: oklch(98% 0.01 195);
  --color-accent: oklch(68% 0.22 155);
  --color-accent-content: oklch(98% 0.01 155);
  --color-neutral: oklch(32% 0.04 255);
  --color-neutral-content: oklch(96% 0.01 255);

  --color-info: oklch(62% 0.18 240);
  --color-info-content: oklch(98% 0.01 240);
  --color-success: oklch(62% 0.20 148);
  --color-success-content: oklch(98% 0.01 148);
  --color-warning: oklch(78% 0.18 75);
  --color-warning-content: oklch(22% 0.04 75);
  --color-error: oklch(58% 0.24 28);
  --color-error-content: oklch(98% 0.01 28);

  --radius-selector: 0.5rem;
  --radius-field: 0.25rem;
  --radius-box: 0.75rem;
  --size-selector: 0.25rem;
  --size-field: 0.25rem;
  --border: 1px;
  --depth: 1;
  --noise: 0;
}

/* ─── Dark Theme ─── */
@plugin "daisyui/theme" {
  name: "saas-dark";
  default: false;
  prefersdark: true;
  color-scheme: dark;

  --color-base-100: oklch(16% 0.015 255);
  --color-base-200: oklch(20% 0.02 255);
  --color-base-300: oklch(26% 0.025 255);
  --color-base-content: oklch(92% 0.01 255);

  --color-primary: oklch(62% 0.20 255);
  --color-primary-content: oklch(14% 0.02 255);
  --color-secondary: oklch(66% 0.15 195);
  --color-secondary-content: oklch(14% 0.02 195);
  --color-accent: oklch(72% 0.18 155);
  --color-accent-content: oklch(14% 0.02 155);
  --color-neutral: oklch(28% 0.03 255);
  --color-neutral-content: oklch(94% 0.01 255);

  --color-info: oklch(68% 0.15 240);
  --color-info-content: oklch(14% 0.01 240);
  --color-success: oklch(68% 0.18 148);
  --color-success-content: oklch(14% 0.01 148);
  --color-warning: oklch(80% 0.16 75);
  --color-warning-content: oklch(22% 0.04 75);
  --color-error: oklch(65% 0.20 28);
  --color-error-content: oklch(14% 0.01 28);

  --radius-selector: 0.5rem;
  --radius-field: 0.25rem;
  --radius-box: 0.75rem;
  --size-selector: 0.25rem;
  --size-field: 0.25rem;
  --border: 1px;
  --depth: 0;
  --noise: 0;
}
```

### Switching Between Them

```html
<html data-theme="saas-light">

<!-- JavaScript theme toggle -->
<script>
  document.documentElement.setAttribute('data-theme',
    document.documentElement.getAttribute('data-theme') === 'saas-light'
      ? 'saas-dark' : 'saas-light'
  );
</script>
```

---

## Validation Checklist

Before finalizing any custom theme, verify:

| # | Check | How to Verify |
|---|-------|---------------|
| 1 | All 20 color variables defined | Count `--color-*` entries (must be 20) |
| 2 | All 8 shape/effect variables defined | Count `--radius-*`, `--size-*`, `--border`, `--depth`, `--noise` |
| 3 | `--depth` is exactly `0` or `1` | No decimals, no other values |
| 4 | `--noise` is exactly `0` or `1` | No decimals, no other values |
| 5 | `--border` is a CSS length | Must include unit: `1px`, `2px` |
| 6 | Content colors have sufficient contrast | ≥ 40% lightness difference from parent |
| 7 | Warning content is **dark** (not light) | Warning bg is light (~80%), so content must be dark (~20%) |
| 8 | `name` is a valid CSS identifier | No spaces, no special characters |
| 9 | `color-scheme` matches theme type | `light` for light themes, `dark` for dark themes |
| 10 | Theme renders correctly | Test with buttons, cards, alerts, forms, and status colors |

---

## Fetching Theme Snippets

```json
// Tool: daisyui-blueprint-daisyUI-Snippets

// Get everything about themes
{ "themes": { "builtin-themes": true, "colors": true, "custom-theme": true } }

// Just custom theme template
{ "themes": { "custom-theme": true } }

// Just the color system reference
{ "themes": { "colors": true } }
```


## Steering experiences — learned from real agent usage

### The `dark:` trap with semantic colors

**Problem:** Agent adds `dark:bg-base-300` or `dark:text-primary-content` to elements. daisyUI themes already define what `base-300` and `primary-content` resolve to in dark mode — using `dark:` creates conflicts and makes theme switching unreliable.

**Rule:** NEVER use `dark:` prefix with daisyUI semantic color classes.

```html
<!-- ❌ WRONG — dark: on semantic colors -->
<div class="bg-base-100 dark:bg-base-300">
<span class="text-primary dark:text-primary-content">
<button class="btn btn-primary dark:btn-secondary">

<!-- ✅ CORRECT — semantic colors auto-adapt via theme -->
<div class="bg-base-100">
<span class="text-primary">
<button class="btn btn-primary">

<!-- ✅ OK — dark: on NON-semantic utilities (shadows, borders, custom stuff) -->
<div class="shadow-md dark:shadow-lg">
<div class="border border-gray-200 dark:border-gray-700">
<div class="ring-1 ring-black/5 dark:ring-white/10">
```

### Content color pairing

**Problem:** Agent sets `bg-primary` on a surface but leaves text as `text-base-content`, making text invisible or low-contrast.

**Fix:** Every semantic background has a matching content color:

| Background | Text color | Example |
|---|---|---|
| `bg-primary` | `text-primary-content` | Primary buttons, highlighted cards |
| `bg-secondary` | `text-secondary-content` | Secondary surfaces |
| `bg-accent` | `text-accent-content` | Accent highlights |
| `bg-neutral` | `text-neutral-content` | Dark surfaces |
| `bg-base-100` | `text-base-content` | Default page background |
| `bg-base-200` | `text-base-content` | Slightly darker sections |
| `bg-base-300` | `text-base-content` | Sidebar, card backgrounds |
| `bg-info` | `text-info-content` | Info alerts |
| `bg-success` | `text-success-content` | Success messages |
| `bg-warning` | `text-warning-content` | Warning alerts |
| `bg-error` | `text-error-content` | Error states |

### Theme-first workflow

**Problem:** Agent builds the entire UI with hardcoded Tailwind colors (`bg-blue-500`, `text-gray-800`), then tries to convert to daisyUI semantic colors afterward — requiring a complete rewrite.

**Fix:** If the page needs brand colors:
1. Define the theme FIRST (`@plugin "daisyui/theme" { ... }`)
2. Then build all UI using semantic color classes from the start
3. Colors resolve correctly immediately — no rewrite needed

### OKLCH format for custom themes

daisyUI v5 uses OKLCH color format internally. When defining custom themes:

```css
@plugin "daisyui/theme" {
  name: "brand";
  default: true;

  /* OKLCH format: lightness chroma hue */
  --color-primary: oklch(65% 0.24 265);      /* vibrant blue */
  --color-primary-content: oklch(98% 0.01 265); /* near-white on primary */
  --color-secondary: oklch(55% 0.18 150);     /* teal */
  --color-accent: oklch(75% 0.20 50);         /* warm orange */

  /* Base colors */
  --color-base-100: oklch(98% 0.005 265);     /* page background */
  --color-base-200: oklch(95% 0.008 265);     /* slightly darker */
  --color-base-300: oklch(90% 0.012 265);     /* cards, sidebars */
  --color-base-content: oklch(25% 0.02 265);  /* main text */
}
```

**Tip:** Use an OKLCH color picker (oklch.com) to find values. The format is more perceptually uniform than HSL — equal lightness values look equally bright across different hues.
