# Custom Theme Generation Workflow

> Create daisyUI 5 custom themes from brand colors, images, or design specifications.

---

## Quick Reference

| Source | Process |
|--------|---------|
| Brand colors / hex values | Direct mapping to semantic color variables |
| Image / screenshot | Extract dominant colors → map to semantics |
| Existing website | Extract colors from CSS → map to semantics |
| Design system / Figma | Pull color tokens → map to semantics |

---

## Method 1: From Brand Colors

### Step 1: Identify the Brand's Color Palette

Gather these colors:
- **Primary brand color** (main CTA, logo color)
- **Secondary brand color** (supporting actions)
- **Accent color** (highlights, links)
- **Dark/neutral color** (headings, dark backgrounds)
- **Background tones** (page bg, card bg, border bg)

### Step 2: Map to daisyUI Semantic Colors

| Brand Role | daisyUI Variable | Purpose |
|-----------|------------------|---------|
| Main brand color | `--color-primary` | Buttons, links, active states |
| Supporting color | `--color-secondary` | Secondary buttons, less prominent actions |
| Highlight / pop color | `--color-accent` | Eye-catching elements, badges |
| Dark text / bg | `--color-neutral` | Dark backgrounds, emphasis areas |
| Page background (lightest) | `--color-base-100` | Main page background |
| Card / section background | `--color-base-200` | Elevated surface |
| Border / divider tone | `--color-base-300` | Subtle backgrounds, borders |
| Main text color | `--color-base-content` | Body text on base backgrounds |

### Step 3: Generate Content Colors

For each semantic color, generate a contrasting "content" color for text/icons on that background:

| If Background Is... | Content Color Should Be |
|---------------------|------------------------|
| Dark (lightness < 0.5) | White or very light (`#ffffff`, `oklch(1 0 0)`) |
| Light (lightness > 0.5) | Black or very dark (`#000000`, `oklch(0 0 0)`) |
| Medium | Test both — pick the one with higher contrast ratio |

**Target:** WCAG AA contrast ratio (4.5:1 for normal text, 3:1 for large text).

### Step 4: Choose Status Colors

| Status | Typical Color | daisyUI Variable |
|--------|--------------|------------------|
| Informational | Blue | `--color-info` |
| Success | Green | `--color-success` |
| Warning | Amber / Orange | `--color-warning` |
| Error / Danger | Red | `--color-error` |

These can stay as defaults unless the brand has specific status colors.

### Step 5: Set Radius, Size, and Effects

| Variable | Purpose | Typical Values |
|----------|---------|----------------|
| `--radius-selector` | Radio buttons, checkboxes, toggles | `0.25rem` – `1rem` |
| `--radius-field` | Inputs, selects, textareas | `0.25rem` – `0.75rem` |
| `--radius-box` | Cards, modals, drawers, alerts | `0.5rem` – `1.5rem` |
| `--size-selector` | Height of checkbox, toggle elements | `0.25rem` – `0.375rem` |
| `--size-field` | Height of input/select padding | `0.25rem` – `0.375rem` |
| `--border` | Default border width | `1px` |
| `--depth` | Enables shadow/elevation | `0` (flat) or `1` (elevated) |
| `--noise` | Adds texture noise overlay | `0` (clean) or `1` (textured) |

---

## Method 2: From an Image

### Step 1: Analyze the Image

Extract the dominant colors from the image. Look for:
1. **Most prominent color** → primary candidate
2. **Second most prominent** → secondary candidate
3. **Accent/pop color** → accent candidate
4. **Background/neutral tones** → base colors
5. **Dark tones** → neutral

### Step 2: Refine for UI Use

Raw image colors may not work well for UI. Adjust:
- **Saturate slightly** for primary/secondary/accent (UI needs vibrant CTAs)
- **Desaturate** for base colors (backgrounds should be subtle)
- **Darken or lighten** neutral for sufficient contrast

### Step 3: Generate the Theme

Follow steps 3-5 from Method 1 above.

---

## Method 3: From an Existing Website

### Step 1: Extract Colors

Use browser DevTools or the MCP scraping tools to extract:
- Primary button background
- Link color
- Header/navbar background
- Page background
- Card/section backgrounds
- Text color
- Status/alert colors

### Step 2: Map and Generate

Follow the mapping process from Method 1.

---

## Complete Theme Template

```css
@plugin "daisyui/theme" {
  --name: "my-custom-theme";
  --default: true;                     /* Set as default theme (optional) */

  /* ─── Base Colors (backgrounds & text) ─── */
  --color-base-100: oklch(0.98 0.01 240);     /* Lightest background (page) */
  --color-base-200: oklch(0.94 0.01 240);     /* Card / section background */
  --color-base-300: oklch(0.88 0.02 240);     /* Borders, dividers, subtle bg */
  --color-base-content: oklch(0.25 0.02 240); /* Text on base backgrounds */

  /* ─── Primary ─── */
  --color-primary: oklch(0.55 0.22 260);         /* Main brand / CTA color */
  --color-primary-content: oklch(0.98 0.01 260); /* Text/icon on primary bg */

  /* ─── Secondary ─── */
  --color-secondary: oklch(0.65 0.15 320);         /* Supporting actions */
  --color-secondary-content: oklch(0.98 0.01 320); /* Text on secondary bg */

  /* ─── Accent ─── */
  --color-accent: oklch(0.72 0.18 180);         /* Highlights, badges */
  --color-accent-content: oklch(0.15 0.02 180); /* Text on accent bg */

  /* ─── Neutral ─── */
  --color-neutral: oklch(0.28 0.03 260);         /* Dark backgrounds */
  --color-neutral-content: oklch(0.95 0.01 260); /* Text on neutral bg */

  /* ─── Status Colors ─── */
  --color-info: oklch(0.65 0.15 240);            /* Informational */
  --color-info-content: oklch(0.98 0.01 240);    /* Text on info bg */
  --color-success: oklch(0.65 0.18 150);         /* Success states */
  --color-success-content: oklch(0.98 0.01 150); /* Text on success bg */
  --color-warning: oklch(0.80 0.15 80);          /* Warnings */
  --color-warning-content: oklch(0.20 0.05 80);  /* Text on warning bg */
  --color-error: oklch(0.60 0.20 25);            /* Errors */
  --color-error-content: oklch(0.98 0.01 25);    /* Text on error bg */

  /* ─── Border Radius ─── */
  --radius-selector: 0.5rem;   /* Checkboxes, toggles, radios */
  --radius-field: 0.5rem;      /* Inputs, selects */
  --radius-box: 1rem;          /* Cards, modals, drawers */

  /* ─── Sizes ─── */
  --size-selector: 0.25rem;    /* Selector element sizing */
  --size-field: 0.25rem;       /* Field element sizing */

  /* ─── Effects ─── */
  --border: 1px;               /* Default border width */
  --depth: 1;                  /* 0 = flat, 1 = shadows/elevation */
  --noise: 0;                  /* 0 = clean, 1 = noise texture overlay */
}
```

---

## All Required CSS Variables

Every custom theme should define all 20 color variables plus the 8 shape/effect variables below.

### Color Variables (20 required)

| Variable | Description |
|----------|-------------|
| `--color-base-100` | Lightest background (page level) |
| `--color-base-200` | Card / elevated surface background |
| `--color-base-300` | Subtle background, borders, dividers |
| `--color-base-content` | Default text color on base backgrounds |
| `--color-primary` | Primary brand / action color |
| `--color-primary-content` | Text/icons on primary background |
| `--color-secondary` | Secondary action color |
| `--color-secondary-content` | Text/icons on secondary background |
| `--color-accent` | Accent / highlight color |
| `--color-accent-content` | Text/icons on accent background |
| `--color-neutral` | Dark neutral color |
| `--color-neutral-content` | Text/icons on neutral background |
| `--color-info` | Informational status color |
| `--color-info-content` | Text on info background |
| `--color-success` | Success status color |
| `--color-success-content` | Text on success background |
| `--color-warning` | Warning status color |
| `--color-warning-content` | Text on warning background |
| `--color-error` | Error status color |
| `--color-error-content` | Text on error background |

### Shape & Size Variables (5 required)

| Variable | Description | Typical Range |
|----------|-------------|---------------|
| `--radius-selector` | Border radius for selectors | `0.25rem` – `1rem` |
| `--radius-field` | Border radius for form fields | `0.25rem` – `0.75rem` |
| `--radius-box` | Border radius for boxes/cards | `0.25rem` – `1.5rem` |
| `--size-selector` | Size scale for selectors | `0.1875rem` – `0.375rem` |
| `--size-field` | Size scale for fields | `0.1875rem` – `0.375rem` |

### Effect Variables (3 required)

| Variable | Description | Values |
|----------|-------------|--------|
| `--border` | Default border width | `1px`, `2px` |
| `--depth` | Shadow/elevation toggle | `0` (flat) or `1` (elevated) |
| `--noise` | Noise texture overlay | `0` (off) or `1` (on) |

---

## Color Format: OKLCH

daisyUI 5 prefers OKLCH color format:

```
oklch(lightness chroma hue)
```

| Component | Range | Description |
|-----------|-------|-------------|
| Lightness | 0 – 1 | 0 = black, 1 = white |
| Chroma | 0 – 0.4 | 0 = gray, higher = more saturated |
| Hue | 0 – 360 | Color wheel degree |

### Hex to OKLCH Quick Reference

| Hex | OKLCH (approximate) | Color |
|-----|---------------------|-------|
| `#3b82f6` | `oklch(0.62 0.19 260)` | Blue |
| `#ef4444` | `oklch(0.58 0.22 25)` | Red |
| `#22c55e` | `oklch(0.72 0.19 150)` | Green |
| `#f59e0b` | `oklch(0.77 0.17 75)` | Amber |
| `#8b5cf6` | `oklch(0.55 0.22 290)` | Purple |
| `#ec4899` | `oklch(0.60 0.22 345)` | Pink |
| `#06b6d4` | `oklch(0.68 0.13 210)` | Cyan |
| `#ffffff` | `oklch(1 0 0)` | White |
| `#000000` | `oklch(0 0 0)` | Black |
| `#f3f4f6` | `oklch(0.96 0.01 260)` | Light gray |
| `#1f2937` | `oklch(0.27 0.02 260)` | Dark gray |

> **Tip:** You can also use hex values directly: `--color-primary: #3b82f6;`

---

## Built-in Themes (35 Available)

Use built-in themes before creating custom ones:

### Light Themes
| Theme | Vibe |
|-------|------|
| `light` | Default light theme |
| `cupcake` | Soft pastels, friendly |
| `bumblebee` | Yellow/amber warm tones |
| `emerald` | Green nature-inspired |
| `corporate` | Professional blue/gray |
| `garden` | Natural greens and earth tones |
| `lofi` | Minimal, low-contrast |
| `pastel` | Soft pastel colors |
| `fantasy` | Playful purple tones |
| `wireframe` | Minimal wireframe look |
| `cmyk` | Print-inspired colors |
| `autumn` | Warm fall colors |
| `acid` | Vibrant neon-like |
| `lemonade` | Fresh citrus tones |
| `winter` | Cool blue winter tones |
| `nord` | Nordic color palette |
| `caramellatte` | Warm caramel/coffee light |
| `silk` | Soft elegant tones |

### Dark Themes
| Theme | Vibe |
|-------|------|
| `dark` | Default dark theme |
| `synthwave` | 80s retro neon |
| `retro` | Vintage warm tones |
| `cyberpunk` | Neon/futuristic |
| `valentine` | Pink romantic tones |
| `halloween` | Spooky orange/purple |
| `forest` | Deep forest greens |
| `aqua` | Teal/aqua underwater |
| `black` | Pure black minimal |
| `luxury` | Gold and dark luxury |
| `dracula` | Popular dark color scheme |
| `business` | Professional dark |
| `night` | Deep blue night sky |
| `coffee` | Rich coffee/brown dark |
| `dim` | Muted dark tones |
| `sunset` | Warm sunset oranges |
| `abyss` | Deep dark blue |

### Enabling Built-in Themes

In your `tailwind.config` or CSS:

```css
/* Enable specific themes */
@plugin "daisyui" {
  themes: light --default, dark --prefersdark, cupcake, corporate;
}

/* Or enable all themes */
@plugin "daisyui" {
  themes: all;
}
```

### Using Themes in HTML

```html
<!-- Set theme on the html element -->
<html data-theme="cupcake">

<!-- Or override for a specific section -->
<div data-theme="dark">
  <!-- This section uses dark theme -->
</div>
```

---

## Theme Design Patterns

### Minimal / Clean
```css
--radius-selector: 0.25rem;
--radius-field: 0.375rem;
--radius-box: 0.5rem;
--border: 1px;
--depth: 0;     /* Flat, no shadows */
--noise: 0;
```

### Modern / Rounded
```css
--radius-selector: 0.5rem;
--radius-field: 0.5rem;
--radius-box: 1rem;
--border: 1px;
--depth: 1;     /* Shadows enabled */
--noise: 0;
```

### Bold / Sharp
```css
--radius-selector: 0;
--radius-field: 0;
--radius-box: 0;
--border: 2px;
--depth: 0;
--noise: 0;
```

### Textured / Organic
```css
--radius-selector: 1rem;
--radius-field: 0.75rem;
--radius-box: 1.5rem;
--border: 1px;
--depth: 1;
--noise: 1;     /* Noise texture on */
```

---

## Dark Theme Creation Tips

When creating a dark variant:

1. **Flip base colors:** `base-100` is darkest, `base-300` is lightest
2. **Reduce chroma:** Highly saturated colors feel too bright on dark backgrounds — reduce by 10-20%
3. **Increase lightness of status colors:** Info/success/warning/error need to be brighter to stand out
4. **Content colors become light:** `base-content` should be near-white

```css
@plugin "daisyui/theme" {
  --name: "my-dark-theme";
  --color-base-100: oklch(0.18 0.02 260);     /* Dark background */
  --color-base-200: oklch(0.22 0.02 260);     /* Slightly lighter */
  --color-base-300: oklch(0.28 0.02 260);     /* Lightest dark bg */
  --color-base-content: oklch(0.90 0.01 260); /* Light text */
  --color-primary: oklch(0.65 0.20 260);      /* Brighter for dark bg */
  --color-primary-content: oklch(0.15 0.02 260);
  /* ... rest of theme */
}
```

---

## Validation Rules

| Rule | Detail |
|------|--------|
| All variables required | Every variable listed above must be defined |
| Color format | OKLCH preferred; hex also accepted |
| `--depth` | Must be exactly `0` or `1` |
| `--noise` | Must be exactly `0` or `1` |
| `--border` | CSS length value (e.g., `1px`, `2px`) |
| `--radius-*` | CSS length values (e.g., `0.5rem`, `8px`) |
| `--size-*` | CSS length values |
| Content colors | Must have sufficient contrast against their parent color |
| `--name` | Required, must be a valid CSS identifier |
