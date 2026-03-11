# daisyUI 5 — Custom Themes & Color System

> **Purpose**: Complete reference for creating custom themes, understanding the oklch color system, all CSS variables, and working with daisyUI's 35 built-in themes.

---

## Theme Architecture

daisyUI 5 themes are pure CSS — no JavaScript config needed. Each theme defines CSS custom properties that all components read automatically.

### How Themes Work

1. Define theme via `@plugin "daisyui/theme" { ... }` in your CSS
2. Apply theme via `data-theme="name"` on any HTML element
3. All daisyUI components automatically use theme colors
4. Themes can be nested — inner `data-theme` overrides outer

---

## Custom Theme Template

```css
@import "tailwindcss";
@plugin "daisyui";

@plugin "daisyui/theme" {
  name: "mytheme";
  default: true;           /* Apply by default */
  prefersdark: false;       /* Not a dark theme */
  color-scheme: light;      /* Browser color-scheme */

  /* ── Base colors (page background & text) ── */
  --color-base-100: oklch(98% 0.02 240);         /* Primary background */
  --color-base-200: oklch(95% 0.03 240);         /* Slightly darker bg */
  --color-base-300: oklch(92% 0.04 240);         /* Borders, dividers */
  --color-base-content: oklch(20% 0.05 240);     /* Default text color */

  /* ── Brand colors ── */
  --color-primary: oklch(55% 0.3 240);           /* Primary buttons, links */
  --color-primary-content: oklch(98% 0.01 240);  /* Text on primary */
  --color-secondary: oklch(70% 0.25 200);        /* Secondary actions */
  --color-secondary-content: oklch(98% 0.01 200);
  --color-accent: oklch(65% 0.25 160);           /* Accent highlights */
  --color-accent-content: oklch(98% 0.01 160);

  /* ── Neutral ── */
  --color-neutral: oklch(50% 0.05 240);          /* Neutral UI surfaces */
  --color-neutral-content: oklch(98% 0.01 240);  /* Text on neutral */

  /* ── State colors ── */
  --color-info: oklch(70% 0.2 220);              /* Informational */
  --color-info-content: oklch(98% 0.01 220);
  --color-success: oklch(65% 0.25 140);          /* Success */
  --color-success-content: oklch(98% 0.01 140);
  --color-warning: oklch(80% 0.25 80);           /* Warning */
  --color-warning-content: oklch(20% 0.05 80);   /* Dark text on warning */
  --color-error: oklch(65% 0.3 30);              /* Error/danger */
  --color-error-content: oklch(98% 0.01 30);

  /* ── Shape & Depth ── */
  --radius-selector: 1rem;    /* Tabs, toggles, checkboxes */
  --radius-field: 0.25rem;    /* Inputs, selects, textareas */
  --radius-box: 0.5rem;       /* Cards, modals, alerts */

  --size-selector: 0.25rem;   /* Toggle/checkbox visual size */
  --size-field: 0.25rem;      /* Input element height */

  --border: 1px;              /* Default border width */
  --depth: 1;                 /* 0 = flat, 1 = shadows/depth */
  --noise: 0;                 /* 0 = smooth, 1 = textured */
}
```

---

## All CSS Variables Reference

### Color Variables (20)

| Variable | Purpose | Example |
|----------|---------|---------|
| `--color-base-100` | Page background | `oklch(98% 0.02 240)` |
| `--color-base-200` | Card/section background | `oklch(95% 0.03 240)` |
| `--color-base-300` | Borders, dividers, hover states | `oklch(92% 0.04 240)` |
| `--color-base-content` | Default text on base backgrounds | `oklch(20% 0.05 240)` |
| `--color-primary` | Primary brand actions | `oklch(55% 0.3 240)` |
| `--color-primary-content` | Text on primary surfaces | `oklch(98% 0.01 240)` |
| `--color-secondary` | Secondary brand actions | `oklch(70% 0.25 200)` |
| `--color-secondary-content` | Text on secondary | `oklch(98% 0.01 200)` |
| `--color-accent` | Accent highlights | `oklch(65% 0.25 160)` |
| `--color-accent-content` | Text on accent | `oklch(98% 0.01 160)` |
| `--color-neutral` | Neutral surfaces | `oklch(50% 0.05 240)` |
| `--color-neutral-content` | Text on neutral | `oklch(98% 0.01 240)` |
| `--color-info` | Info alerts, badges | `oklch(70% 0.2 220)` |
| `--color-info-content` | Text on info | `oklch(98% 0.01 220)` |
| `--color-success` | Success states | `oklch(65% 0.25 140)` |
| `--color-success-content` | Text on success | `oklch(98% 0.01 140)` |
| `--color-warning` | Warning states | `oklch(80% 0.25 80)` |
| `--color-warning-content` | Text on warning | `oklch(20% 0.05 80)` |
| `--color-error` | Error/danger states | `oklch(65% 0.3 30)` |
| `--color-error-content` | Text on error | `oklch(98% 0.01 30)` |

### Shape Variables (8)

| Variable | Type | Purpose | Range |
|----------|------|---------|-------|
| `--radius-selector` | radius | Tabs, toggles, radio, checkbox | `0` – `2rem` |
| `--radius-field` | radius | Inputs, selects, textareas | `0` – `2rem` |
| `--radius-box` | radius | Cards, modals, alerts, dropdowns | `0` – `2rem` |
| `--size-selector` | size | Toggle/checkbox element size | `0.2rem` – `0.4rem` |
| `--size-field` | size | Input/button height baseline | `0.2rem` – `0.4rem` |
| `--border` | border | Default border width | `0` – `3px` |
| `--depth` | effect | Shadow depth (0=flat, 1=default) | `0` or `1` |
| `--noise` | effect | Background noise texture | `0` or `1` |

---

## oklch Color Format

daisyUI 5 uses oklch — perceptually uniform color space with wider gamut than HSL.

### Format

```
oklch(lightness chroma hue)
```

| Parameter | Range | Description |
|-----------|-------|-------------|
| Lightness | `0%` (black) – `100%` (white) | Perceived brightness |
| Chroma | `0` (gray) – `0.4` (vivid) | Color saturation |
| Hue | `0` – `360` | Color angle on color wheel |

### Hue Reference

| Hue | Color |
|-----|-------|
| 0–30 | Red |
| 30–80 | Orange → Yellow |
| 80–140 | Yellow → Green |
| 140–200 | Green → Cyan |
| 200–260 | Blue |
| 260–320 | Purple → Magenta |
| 320–360 | Pink → Red |

### Content Color Contrast Rules

- Light backgrounds → dark content: lightness ≤ 30%
- Dark backgrounds → light content: lightness ≥ 90%
- Warning is an exception: use dark content on yellow/orange

---

## 35 Built-in Themes

### Light Themes (18)

| Theme | Style |
|-------|-------|
| `light` | Default light theme |
| `cupcake` | Pastel pink/purple |
| `bumblebee` | Yellow/amber |
| `emerald` | Green professional |
| `corporate` | Blue business |
| `retro` | Warm retro palette |
| `valentine` | Pink romantic |
| `garden` | Nature greens |
| `lofi` | Monochrome minimal |
| `pastel` | Soft pastels |
| `fantasy` | Purple fantasy |
| `wireframe` | Sketch/wireframe style |
| `cmyk` | Vivid print colors |
| `autumn` | Warm fall colors |
| `acid` | Vivid neon |
| `lemonade` | Fresh citrus |
| `silk` | Elegant neutral |
| `caramellatte` | Warm brown café |

### Dark Themes (17)

| Theme | Style |
|-------|-------|
| `dark` | Default dark theme |
| `synthwave` | Purple/pink retro |
| `cyberpunk` | Neon yellow/pink |
| `halloween` | Orange/purple spooky |
| `forest` | Dark green |
| `aqua` | Teal aquatic |
| `black` | Pure black background |
| `luxury` | Gold on dark |
| `dracula` | Dark purple |
| `business` | Dark professional |
| `night` | Deep blue dark |
| `coffee` | Dark brown |
| `winter` | Cool blue-gray |
| `dim` | Muted dark |
| `nord` | Nord color palette |
| `sunset` | Warm orange dark |
| `abyss` | Deep blue-black |

---

## Theme Usage Patterns

### Set Default Theme

```html
<html data-theme="light">
```

### Scope Themes to Sections

```html
<html data-theme="dark">
  <body>
    <div data-theme="light">
      <!-- This section uses light theme -->
    </div>
  </body>
</html>
```

### Theme Switching with Controller

```html
<!-- Dropdown theme selector -->
<select data-choose-theme class="select">
  <option value="light">Light</option>
  <option value="dark">Dark</option>
  <option value="cupcake">Cupcake</option>
</select>
```

### Toggle Dark Mode

```html
<label class="swap swap-rotate">
  <input type="checkbox" class="theme-controller" value="dark" />
  <svg class="swap-on size-6 fill-current"><!-- sun icon --></svg>
  <svg class="swap-off size-6 fill-current"><!-- moon icon --></svg>
</label>
```

### Map Tailwind `dark:` to a daisyUI Theme

```css
@custom-variant dark (&:where([data-theme=night], [data-theme=night] *));
```

Now `dark:bg-base-300` applies when `data-theme="night"` is active.

### Auto-detect System Preference

```css
@plugin "daisyui" {
  themes: light --default, dark --prefersdark;
}
```

This uses `prefers-color-scheme: dark` media query automatically.

---

## Design System Presets

### Sharp / Technical

```css
--radius-selector: 0;
--radius-field: 0;
--radius-box: 0;
--depth: 0;
--noise: 0;
--border: 2px;
```

### Rounded / Friendly

```css
--radius-selector: 2rem;
--radius-field: 0.5rem;
--radius-box: 1rem;
--depth: 1;
--noise: 0;
--border: 1px;
```

### Flat / Material

```css
--radius-selector: 0.5rem;
--radius-field: 0.25rem;
--radius-box: 0.25rem;
--depth: 0;
--noise: 0;
--border: 0;
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using HSL colors (`hsl(210, 50%, 50%)`) | Use oklch: `oklch(55% 0.2 240)` |
| Forgetting `-content` colors | Always pair: `--color-primary` needs `--color-primary-content` |
| Setting `--depth: 2` | Only `0` (flat) or `1` (shadows) are valid |
| Missing `color-scheme` | Set `color-scheme: light` or `dark` for browser defaults |
| Using `dark:` prefix on semantic colors | Not needed — `bg-primary` auto-adapts to theme |
| Hard-coding `bg-white` / `bg-black` | Use `bg-base-100` / `bg-neutral` |
| Putting theme config in `tailwind.config.js` | v5 uses `@plugin "daisyui/theme" { ... }` in CSS |
| Low contrast `-content` colors | Ensure WCAG AA: ≥4.5:1 contrast ratio |

---

## CDN Theme Usage

```html
<!-- Load specific theme -->
<link href="https://cdn.jsdelivr.net/npm/daisyui@5/themes/dark.css" rel="stylesheet" />

<!-- Or inline for custom CDN theme -->
<style>
  :root:has(input.theme-controller[value=mytheme]:checked),
  [data-theme="mytheme"] {
    color-scheme: light;
    --color-base-100: oklch(98% 0.02 240);
    --color-primary: oklch(55% 0.3 240);
    /* ... remaining variables ... */
  }
</style>
```
