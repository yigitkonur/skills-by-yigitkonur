# Reverse-Engineering Sources: Extracting Brand DNA

This reference details the systematic procedure for extracting brand tokens from four common input formats: website source code, design markdown repositories, live URLs, and design token JSON files.

---

## 1. Input Source Type 1: Website Codebase (`website-*/`)

When handed a website repository (Astro, Next.js, Nuxt, or static HTML/CSS), look for CSS configuration files:

### Target Files to Inspect
- `src/styles/config/_variables.css`
- `src/styles/globals.css`
- `src/styles/main.css`
- `tailwind.config.mjs` or `tailwind.config.ts`
- `public/fonts/` or `src/assets/fonts/`

### Extraction Recipe (Shell & Grep)
```bash
# 1. Locate root CSS variables
grep -rn --include="*.css" ":root" src/

# 2. Extract surface and color ramps
grep -E --color=never "\-\-c-|\-\-color-" src/styles/config/_variables.css

# 3. Check for dark mode overrides
grep -A 30 "\[data-theme='dark'\]\|\.dark" src/styles/config/_variables.css

# 4. Check typography font-family definitions
grep -rn "font-family" src/styles/
```

### Decoding Website CSS Naming Conventions
Websites often use custom variable prefixes. Map them to modern token semantics:

| Website Variable Pattern | Design Token Equivalent | shadcn / Archestra Token |
| :--- | :--- | :--- |
| `--c-surface`, `--bg-ground` | Base Ground (Surface 0) | `--background` |
| `--c-surface-raised`, `--bg-card` | Raised Surface (Surface 1) | `--card` |
| `--c-surface-2`, `--c-soft-blue` | Tray / Sidebar (Surface 2) | `--sidebar` |
| `--c-surface-inset`, `--bg-well` | Inset Well | `--muted` |
| `--c-ink`, `--color-heading` | High-contrast Heading Ink | `--foreground` (or display) |
| `--c-text`, `--color-body` | Primary Reading Text | `--foreground` / `--secondary-foreground` |
| `--c-text-muted`, `--color-dim` | Secondary / Caption Text | `--muted-foreground` |
| `--c-red`, `--c-primary`, `--brand`| Brand Action Accent | `--primary` |
| `--c-shadow`, `--border-color` | Hairline Divider | `--border`, `--input` |
| `--radius`, `--rounded-base` | Corner Rounding | `--radius` |

---

## 2. Input Source Type 2: Design Markdown (`DESIGN.md`)

When provided with a design manual (such as `teamzeo/design-md` or `company/design-system`), look for the core architectural sections:

1. **Foundational Principles / Design Laws**:
   - Section 1–2 typically states the core visual philosophy (e.g. "Strict Neutral Borders", "Two Reds Principle", "100% Solid Surfaces").
   - These laws dictate what is **forbidden** (e.g. no frosted glass, no colored input borders).
2. **Color Ramps (§2 or §3)**:
   - Extract the exact Hex / OKLCH / HSL values for Light and Dark modes.
   - Note semantic flips: does ink invert from `#0f1a2a` to `#eef2f7`? Does ground shift from `#ffffff` to `#0e1521`?
3. **Typography Specification (§4)**:
   - Identify the 3-role family split: Heading font, Body font, Code font.
   - Look for font-weight rules (e.g. "Weight 300 must remap to Book for complete Latin Extended glyph coverage").
   - Extract line-height and letter-spacing standards.
4. **Elevation & Radii Tokens (§5)**:
   - Note the base radius (strict 4px vs soft 8px).
   - Extract elevation box shadows.

---

## 3. Input Source Type 3: Live Public URL

When given only a URL (e.g. `https://zeo.org` or `https://client.com`), extract the rendered styles using a headless browser (`agent-browser` or Playwright):

```bash
# 1. Open the page
agent-browser open https://zeo.org

# 2. Extract computed styles from DOM root
agent-browser eval '({
  background: getComputedStyle(document.body).backgroundColor,
  color: getComputedStyle(document.body).color,
  fontFamily: getComputedStyle(document.body).fontFamily,
  headingFont: document.querySelector("h1, h2") ? getComputedStyle(document.querySelector("h1, h2")).fontFamily : null,
  primaryButton: document.querySelector("button, .btn, [class*=\"btn\"]") ? {
    bg: getComputedStyle(document.querySelector("button, .btn")).backgroundColor,
    color: getComputedStyle(document.querySelector("button, .btn")).color,
    radius: getComputedStyle(document.querySelector("button, .btn")).borderRadius,
  } : null
})'

# 3. Extract loaded web font files
agent-browser eval 'Array.from(document.fonts.values()).map(f => ({
  family: f.family,
  weight: f.weight,
  status: f.status
}))'
```

---

## 4. Input Source Type 4: Design Tokens JSON (W3C DTCG Format)

Modern Figma plugins (Tokens Studio, Style Dictionary) export `tokens/` JSON files:
- `tokens/colors.json`
- `tokens/typography.json`
- `tokens/elevation.json`

### Parsing Strategy
```python
import json

with open("tokens/colors.json") as f:
    colors = json.load(f)

# Extract ink ramp
head_ink_light = colors["tokens"]["ink"]["head"]["$value"]
body_ink_light = colors["tokens"]["ink"]["text"]["$value"]

# Extract ground ramp
ground_canvas = colors["tokens"]["ground"]["canvas"]["$value"]
ground_card = colors["tokens"]["ground"]["raised"]["$value"]

print(f"Canvas: {ground_canvas}, Card: {ground_card}, Body: {body_ink_light}")
```

---

## 5. Synthesizing the Unified Brand Mental Model

Regardless of which source was analyzed, distill the findings into a **1-Page Brand DNA Summary**:

```markdown
### Brand DNA Summary: [Brand Name]
1. Atmosphere: [Crisp / Editorial / Minimalist / Dense / Warm]
2. Ground & Canvas:
   - Light: #ffffff (Pure White)
   - Dark: #0e1521 (Deep Marine Navy)
3. Surface Elevation:
   - Cards: #ffffff (Light) / #1c2535 (Dark)
   - Sidebar: #f5f8fc (Light Soft Blue) / #131c2b (Dark)
4. Ink Contrast Ladder:
   - Display: #0f1a2a / #eef2f7
   - Body: #273041 / #c9d2e0
   - Muted: #5a6678 / #8b96a8
5. Interactive Accent:
   - Primary: #cc0a4d (Brand Crimson)
   - Resting Borders: #e8ecf2 (Light) / #232e40 (Dark) — Zero accent hue!
   - Focus Ring: #273041 (Light) / #526585 (Dark) — Slate neutral!
6. Geometry & Grid:
   - Base Radius: 0.25rem (Strict 4px)
   - Base Spacing: 0.25rem (4px grid)
7. Typography Stack:
   - Headings & Buttons: Gilroy (SemiBold 600, Bold 700)
   - Interface & Prose: Akagi Pro (Book 400, SemiBold 600)
   - Code & Ports: JetBrains Mono / DM Mono
```
