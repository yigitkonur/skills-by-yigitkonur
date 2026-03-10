# Image/Picture to daisyUI Theme Prompt

> Built-in prompt for the **daisyui-blueprint** MCP server.
> Extracts a color palette from any image and generates a complete daisyUI custom theme.

---

## Trigger

User uploads an image (photo, brand asset, mood board) and asks:

- *"Create a daisyUI theme from this image"*
- *"Generate a color palette based on this picture"*
- *"Make a custom theme that matches this brand image"*

---

## System Prompt

```
You are a color extraction and theme generation specialist. Given an image,
you will extract the dominant color palette and map it to daisyUI 5 semantic
color roles. Output a complete `@plugin "daisyui/theme"` CSS block using
OKLCH color format with proper contrast ratios for content colors.
```

---

## Agent Workflow

### Step 1 — Extract Colors from the Image

Analyze the image and identify:

| Color Category | What to Look For |
|---------------|-----------------|
| **Dominant color** | The most prominent color covering the largest area |
| **Secondary dominant** | The second most prominent color |
| **Accent / pop color** | A vibrant, eye-catching color used sparingly |
| **Dark tones** | Deep/dark colors in the image |
| **Light tones** | Light/pale colors or whites |
| **Warm vs cool bias** | Overall temperature of the palette |

Extract 5–8 distinct colors as hex values, then convert to OKLCH.

### Step 2 — Map to daisyUI Semantic Color Roles

| Extracted Color | Maps To | Rationale |
|----------------|---------|-----------|
| **Dominant color** | `primary` | The main brand/interaction color |
| **Secondary dominant** | `secondary` | Supporting color for secondary actions |
| **Accent / pop color** | `accent` | Highlights, active states, decorative elements |
| **Darkest tone** | `neutral` | Text, borders, dark UI elements |
| **Lightest tone** | `base-100` | Page background |
| **Slightly darker light** | `base-200` | Card backgrounds, subtle sections |
| **Medium light** | `base-300` | Borders, dividers, disabled states |
| **Derived from dominant** | `primary-content` | Text on primary background (ensure contrast) |
| **Derived from secondary** | `secondary-content` | Text on secondary background |
| **Derived from accent** | `accent-content` | Text on accent background |
| **Derived from neutral** | `neutral-content` | Text on neutral background |
| **Derived from base** | `base-content` | Main body text color |

### Step 3 — Generate Status Colors

If the image doesn't contain obvious info/success/warning/error colors, generate complementary ones:

| Status Color | Generation Strategy |
|-------------|-------------------|
| `info` | Derive a blue tone from the palette, or pick a cool complementary |
| `success` | Derive a green tone, or shift the dominant hue toward green |
| `warning` | Derive an amber/yellow tone, or shift toward warm yellow |
| `error` | Derive a red tone, or use the complementary of the dominant |

Each status color needs a matching `-content` color for text contrast.

### Step 4 — Set Theme Variables

Beyond colors, the theme needs structural variables:

| Variable | Purpose | Value Range |
|----------|---------|-------------|
| `--radius-selector` | Border radius for small selectors (checkboxes, radios) | `0rem` – `2rem` |
| `--radius-field` | Border radius for inputs, selects | `0rem` – `1rem` |
| `--radius-box` | Border radius for cards, modals | `0rem` – `2rem` |
| `--size-selector` | Size of checkboxes, radios, toggles | `0.25rem` – `0.5rem` |
| `--size-field` | Height of input fields, selects | `0.25rem` – `0.5rem` |
| `--border` | Border width for components | `0px` – `2px` |
| `--depth` | Shadow depth (0 = flat, 1 = normal, 2 = elevated) | `0` – `2` |
| `--noise` | Background noise texture (0 = clean, 1 = subtle texture) | `0` – `1` |

Choose values based on the image mood:

| Image Mood | radius | border | depth | noise |
|-----------|--------|--------|-------|-------|
| **Modern / clean** | `1rem` | `1px` | `1` | `0` |
| **Soft / organic** | `2rem` | `0px` | `1` | `0` |
| **Sharp / corporate** | `0.25rem` | `1px` | `1` | `0` |
| **Flat / minimal** | `0.5rem` | `0px` | `0` | `0` |
| **Retro / textured** | `0rem` | `2px` | `0` | `1` |
| **Playful / bubbly** | `2rem` | `0px` | `2` | `0` |

### Step 5 — Output the Theme Block

Generate the complete CSS theme definition:

```css
@plugin "daisyui/theme" {
  name: "my-custom-theme";
  default: true;

  /* Primary */
  --color-primary: oklch(0.65 0.20 250);
  --color-primary-content: oklch(0.98 0.01 250);

  /* Secondary */
  --color-secondary: oklch(0.55 0.15 180);
  --color-secondary-content: oklch(0.98 0.01 180);

  /* Accent */
  --color-accent: oklch(0.75 0.18 50);
  --color-accent-content: oklch(0.20 0.02 50);

  /* Neutral */
  --color-neutral: oklch(0.25 0.02 250);
  --color-neutral-content: oklch(0.90 0.01 250);

  /* Base */
  --color-base-100: oklch(0.98 0.005 250);
  --color-base-200: oklch(0.93 0.005 250);
  --color-base-300: oklch(0.88 0.01 250);
  --color-base-content: oklch(0.25 0.02 250);

  /* Status colors */
  --color-info: oklch(0.65 0.15 230);
  --color-info-content: oklch(0.98 0.01 230);

  --color-success: oklch(0.65 0.18 145);
  --color-success-content: oklch(0.98 0.01 145);

  --color-warning: oklch(0.75 0.18 75);
  --color-warning-content: oklch(0.20 0.02 75);

  --color-error: oklch(0.60 0.20 25);
  --color-error-content: oklch(0.98 0.01 25);

  /* Structure */
  --radius-selector: 1rem;
  --radius-field: 0.5rem;
  --radius-box: 1rem;
  --size-selector: 0.25rem;
  --size-field: 0.25rem;
  --border: 1px;
  --depth: 1;
  --noise: 0;
}
```

---

## OKLCH Color Format

daisyUI 5 uses the **OKLCH** color space. Each color has three components:

```
oklch(L C H)
│     │ │ └── Hue: 0–360 (color wheel angle)
│     │ └──── Chroma: 0–0.4 (saturation intensity)
│     └────── Lightness: 0–1 (0 = black, 1 = white)
```

### Quick Reference — Hue Angles

| Hue Range | Color |
|-----------|-------|
| 0–30 | Red / Rose |
| 30–60 | Orange |
| 60–100 | Yellow / Gold |
| 100–150 | Green |
| 150–200 | Teal / Cyan |
| 200–260 | Blue |
| 260–310 | Purple / Violet |
| 310–360 | Pink / Magenta |

### Converting from Hex to OKLCH

If you extract hex values from the image, convert them:

| Hex | OKLCH (approximate) |
|-----|---------------------|
| `#3b82f6` (blue-500) | `oklch(0.62 0.21 260)` |
| `#ef4444` (red-500) | `oklch(0.58 0.22 25)` |
| `#22c55e` (green-500) | `oklch(0.72 0.19 145)` |
| `#f59e0b` (amber-500) | `oklch(0.75 0.18 75)` |
| `#8b5cf6` (violet-500) | `oklch(0.55 0.22 290)` |
| `#ffffff` (white) | `oklch(1.00 0 0)` |
| `#000000` (black) | `oklch(0.00 0 0)` |
| `#1f2937` (gray-800) | `oklch(0.25 0.02 250)` |

---

## Ensuring Proper Contrast

### Content Color Rules

For every background color, its `-content` color must have sufficient contrast:

| Background Lightness | Content Color Lightness | Guideline |
|---------------------|------------------------|-----------|
| **L > 0.65** (light bg) | **L < 0.30** (dark text) | WCAG AA: 4.5:1 contrast |
| **L < 0.50** (dark bg) | **L > 0.85** (light text) | WCAG AA: 4.5:1 contrast |
| **L 0.50–0.65** (mid bg) | Test both light/dark | Pick whichever gives better contrast |

### Quick Formula

```
If background L > 0.6 → content L = 0.15 to 0.25 (dark text)
If background L < 0.5 → content L = 0.90 to 0.98 (light text)
Content hue = same as background hue (keeps harmony)
Content chroma = 0.01 to 0.03 (near-neutral for readability)
```

---

## Complete Example: Sunset Photo → Warm Theme

### Input
A sunset photograph with warm oranges, deep purples, soft pinks, and dark navy.

### Color Extraction

| Extracted Color | Hex | OKLCH | Role |
|----------------|-----|-------|------|
| Warm orange | `#f97316` | `oklch(0.72 0.20 50)` | Primary |
| Deep purple | `#7c3aed` | `oklch(0.50 0.25 290)` | Secondary |
| Soft pink | `#f9a8d4` | `oklch(0.80 0.10 340)` | Accent |
| Dark navy | `#1e1b4b` | `oklch(0.20 0.08 280)` | Neutral |
| Pale cream | `#fef3c7` | `oklch(0.96 0.04 85)` | Base-100 |
| Light warm | `#fde68a` | `oklch(0.92 0.08 85)` | Base-200 |
| Medium warm | `#fcd34d` | `oklch(0.87 0.12 85)` | Base-300 |

### Generated Theme

```css
@plugin "daisyui/theme" {
  name: "sunset";
  default: true;

  /* Primary — warm orange from the sun */
  --color-primary: oklch(0.72 0.20 50);
  --color-primary-content: oklch(0.15 0.02 50);

  /* Secondary — deep purple from the sky */
  --color-secondary: oklch(0.50 0.25 290);
  --color-secondary-content: oklch(0.95 0.01 290);

  /* Accent — soft pink from the clouds */
  --color-accent: oklch(0.80 0.10 340);
  --color-accent-content: oklch(0.20 0.02 340);

  /* Neutral — dark navy from deep sky */
  --color-neutral: oklch(0.20 0.08 280);
  --color-neutral-content: oklch(0.92 0.01 280);

  /* Base — pale cream from horizon light */
  --color-base-100: oklch(0.96 0.04 85);
  --color-base-200: oklch(0.92 0.06 85);
  --color-base-300: oklch(0.87 0.08 85);
  --color-base-content: oklch(0.20 0.03 50);

  /* Status — derived from the warm palette */
  --color-info: oklch(0.62 0.18 240);
  --color-info-content: oklch(0.95 0.01 240);

  --color-success: oklch(0.68 0.17 155);
  --color-success-content: oklch(0.15 0.02 155);

  --color-warning: oklch(0.78 0.16 70);
  --color-warning-content: oklch(0.18 0.02 70);

  --color-error: oklch(0.58 0.22 20);
  --color-error-content: oklch(0.95 0.01 20);

  /* Structure — warm and slightly soft */
  --radius-selector: 1.5rem;
  --radius-field: 0.75rem;
  --radius-box: 1.25rem;
  --size-selector: 0.25rem;
  --size-field: 0.25rem;
  --border: 1px;
  --depth: 1;
  --noise: 0;
}
```

### Usage

```html
<html data-theme="sunset">
  <!-- All daisyUI components now use the sunset palette -->
  <body class="bg-base-100 text-base-content min-h-screen">
    <div class="navbar bg-primary text-primary-content">
      <a class="btn btn-ghost text-xl">Sunset App</a>
    </div>
    <div class="p-6">
      <div class="card bg-base-200 shadow-xl">
        <div class="card-body">
          <h2 class="card-title">Warm Welcome</h2>
          <p>This card uses the sunset theme colors.</p>
          <div class="card-actions">
            <button class="btn btn-primary">Primary</button>
            <button class="btn btn-secondary">Secondary</button>
            <button class="btn btn-accent">Accent</button>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>
```

---

## More Examples

### Forest Photo → Nature Theme

| Color | OKLCH | Role |
|-------|-------|------|
| Forest green | `oklch(0.50 0.15 150)` | Primary |
| Bark brown | `oklch(0.42 0.08 60)` | Secondary |
| Moss yellow-green | `oklch(0.70 0.14 120)` | Accent |
| Dark soil | `oklch(0.22 0.03 80)` | Neutral |
| Pale leaf | `oklch(0.95 0.02 120)` | Base-100 |

### Ocean Photo → Cool Theme

| Color | OKLCH | Role |
|-------|-------|------|
| Deep blue | `oklch(0.52 0.18 240)` | Primary |
| Seafoam teal | `oklch(0.62 0.12 190)` | Secondary |
| Coral accent | `oklch(0.70 0.16 30)` | Accent |
| Dark navy | `oklch(0.18 0.06 250)` | Neutral |
| Sandy white | `oklch(0.97 0.02 80)` | Base-100 |

### Brand Logo → Corporate Theme

When working with a brand logo:

1. **Primary** = Main brand color
2. **Secondary** = Secondary brand color (or a complementary)
3. **Accent** = Highlight brand color (or derive from primary)
4. **Neutral/Base** = Choose professional grays that complement the brand

---

## Dark Theme Variant

To generate a dark variant from the same image:

1. **Swap lightness values** for base colors:
   - `base-100` → L ≈ `0.18` (dark background)
   - `base-200` → L ≈ `0.22`
   - `base-300` → L ≈ `0.28`
   - `base-content` → L ≈ `0.90` (light text)

2. **Keep the same hues** for primary, secondary, accent

3. **Adjust chroma slightly** (colors pop more on dark backgrounds, so reduce chroma by ~10%)

4. **Flip content colors** to ensure contrast

```css
@plugin "daisyui/theme" {
  name: "sunset-dark";
  prefersdark: true;

  --color-primary: oklch(0.72 0.18 50);
  --color-primary-content: oklch(0.15 0.02 50);

  --color-base-100: oklch(0.18 0.03 280);
  --color-base-200: oklch(0.22 0.04 280);
  --color-base-300: oklch(0.28 0.04 280);
  --color-base-content: oklch(0.90 0.02 50);

  /* ... other colors same as light with flipped content ... */
}
```

---

## Tips for Best Results

| Tip | Why |
|-----|-----|
| **Use high-quality images** | More accurate color extraction |
| **Avoid overly busy images** | Too many colors = unclear palette |
| **Landscapes work great** | Natural color hierarchies (sky=primary, earth=neutral) |
| **Brand assets are ideal** | Colors are already intentional |
| **Test with all daisyUI components** | Some components use unexpected color roles |
| **Always check contrast** | Beautiful themes can fail accessibility if content colors are wrong |
| **Generate both light and dark** | Users expect dark mode support |
