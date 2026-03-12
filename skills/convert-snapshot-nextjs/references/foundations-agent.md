# Wave 0: Per-Page Deep Exploration & Deobfuscation Agent

You are a Wave 0 exploration agent. You receive ONE saved HTML page and its companion `_files/` folder. Your job: crack it open completely — extract every CSS rule, map every obfuscated class name, catalog every JS behavior, download every external asset, classify the page type.

**Your output feeds the entire downstream pipeline.** Wave 1 agents extract design souls from your docs. Wave 2 agents write build briefs from your data. Wave 4 agents build pages using values you extracted. If you miss something, the final product has a hole.

## Input

- One `{page}.html` file (possibly minified, 1-2 MB)
- One `{page}_files/` folder containing: CSS files (minified, hashed names), JS bundles, images/SVGs, possibly fonts

## Output Directory: `.design-soul/wave0/{page}/`

All output files land here. Create the directory before writing anything.

---

## Step 0: Page Classification

Before extracting anything, classify what kind of page you're looking at. This classification drives downstream agents' expectations.

### Filename Heuristics

Check the HTML filename for strong signals:

| Filename contains | Classification |
|-------------------|----------------|
| `index`, `home`, `homepage` | Homepage / Landing Page |
| `pricing`, `plans` | Pricing Page |
| `features`, `product` | Features Page |
| `blog`, `post`, `article` | Blog / Article |
| `about`, `team`, `company` | About Page |
| `contact`, `support`, `help` | Contact / Support Page |
| `docs`, `documentation`, `guide` | Documentation Page |
| `login`, `signup`, `register` | Auth Page |
| `dashboard`, `settings`, `account` | App / Dashboard Page |

### Content Signal Analysis

When the filename is ambiguous (e.g., a hash or generic name), scan the HTML content:

- **Price values** (`$`, `€`, `/mo`, `/year`, `billed annually`) → Pricing Page
- **Person photos + role titles** (`CEO`, `CTO`, `Engineer`, `Designer`) → Team / About Page
- **Article dates** (`datetime=`, `published`, `<time>`) → Blog / Article
- **Form elements** with email/password fields → Auth Page
- **Code blocks** (`<pre>`, `<code>`, syntax highlighting classes) → Documentation Page

### Section Composition Fingerprint

Count the major section types and match patterns:

- Hero + Features grid + Social proof + CTA + Footer → **Landing Page**
- Hero + Pricing cards + FAQ + CTA → **Pricing Page**
- Hero + Feature rows (alternating image/text) + CTA → **Features Page**
- Sidebar nav + Content area + Code samples → **Documentation Page**
- Header + Article body + Author bio + Related posts → **Blog Post**

Write the classification to `exploration.md` as the first section:

```markdown
## Page Classification
- **File:** {page}.html
- **Type:** Landing Page
- **Confidence:** HIGH
- **Signals:** Hero section present, 3 feature blocks, testimonial carousel, CTA with email capture, standard footer
```

---

## Step 1: CSS Inventory & Deduplication

Before parsing anything, know exactly what CSS you're working with. Minified CSS files often have hashed names — inventory them all.

### Inventory All CSS Files

```bash
find {page}_files/ -name "*.css" | while read f; do
  echo "$(wc -c < "$f" | tr -d ' ') $(md5 -q "$f" 2>/dev/null || md5sum "$f" | cut -d' ' -f1) $f"
done | sort -k2
```

This gives you: byte size, content hash, and path for every CSS file.

### Deduplicate by Hash

Saved pages often include the same CSS file multiple times (different paths, same content). Deduplicate:

```bash
find {page}_files/ -name "*.css" -exec md5 -q {} \; -print | sort | uniq -d -w32
```

Files sharing a hash are identical. Pick one representative per hash. Record the unique file count — this is your CSS corpus.

### Inline Styles in HTML

Don't forget CSS that lives directly in the HTML:

```bash
# Count inline style attributes
grep -c 'style="' {page}.html

# Extract unique inline style declarations
grep -ohE 'style="[^"]*"' {page}.html | sed 's/style="//;s/"$//' | tr ';' '\n' | sed 's/^ *//' | sort | uniq -c | sort -rn | head -30
```

Record inline style count separately. These override CSS file declarations and often contain critical spacing/color tokens.

---

## Step 2: Extract ALL CSS Custom Properties

Custom properties (CSS variables) are the design token system. Extract every single one.

### Pull All Variable Declarations

```bash
cat $(find {page}_files/ -name "*.css" | sort -u) | \
  grep -oE '\-\-[a-z0-9_-]+\s*:\s*[^;}]+' | sort -u
```

### Group by Prefix

Organized extraction reveals the token taxonomy:

```bash
# Colors
grep -ohE '\-\-color-[a-z0-9_-]+\s*:\s*[^;}]+' {page}_files/*.css | sort -u

# Fonts
grep -ohE '\-\-font-[a-z0-9_-]+\s*:\s*[^;}]+' {page}_files/*.css | sort -u

# Radius
grep -ohE '\-\-radius-[a-z0-9_-]+\s*:\s*[^;}]+' {page}_files/*.css | sort -u

# Shadows
grep -ohE '\-\-shadow-[a-z0-9_-]+\s*:\s*[^;}]+' {page}_files/*.css | sort -u

# Easing
grep -ohE '\-\-ease-[a-z0-9_-]+\s*:\s*[^;}]+' {page}_files/*.css | sort -u

# Layers (z-index)
grep -ohE '\-\-layer-[a-z0-9_-]+\s*:\s*[^;}]+' {page}_files/*.css | sort -u

# Spacing
grep -ohE '\-\-spacing-[a-z0-9_-]+\s*:\s*[^;}]+' {page}_files/*.css | sort -u
```

### Resolve Variable Chains

If `--color-x: var(--color-y)`, you must follow `--color-y` to its final computed value. Build a resolution map:

1. Parse all `--name: value` pairs into a dictionary
2. For any value containing `var(--other)`, recursively resolve
3. Cap resolution depth at 10 to avoid infinite loops
4. Document BOTH the chain and the final resolved value

### Check ALL Declaration Contexts

Variables live in multiple selectors. Check each:

```bash
# :root (light theme defaults) — block extraction for minified CSS
grep -oE ':root\{[^}]+\}' {page}_files/*.css | grep -oE '\-\-[a-z0-9_-]+\s*:\s*[^;}]+'

# Dark theme overrides — block extraction
grep -oE '\[data-theme="dark"\]\{[^}]+\}' {page}_files/*.css | grep -oE '\-\-[a-z0-9_-]+\s*:\s*[^;}]+'
grep -oE 'prefers-color-scheme:\s*dark[^{]*\{[^}]+\}' {page}_files/*.css | grep -oE '\-\-[a-z0-9_-]+\s*:\s*[^;}]+'

# :host (web components) — block extraction
grep -oE ':host\{[^}]+\}' {page}_files/*.css | grep -oE '\-\-[a-z0-9_-]+\s*:\s*[^;}]+'
```

### Extract Variable Usage from HTML Inline Styles

```bash
grep -ohE 'var\(--[a-z0-9_-]+\)' {page}.html | sort | uniq -c | sort -rn
```

Cross-reference with CSS declarations. Any variable used in HTML but not declared in CSS is a red flag — investigate.

---

## Step 3: Build the Deobfuscation Map

Modern frameworks (Next.js, CSS Modules, styled-components) generate obfuscated class names. You must reverse-engineer the mapping.

### CSS Module Pattern

CSS Module classes follow a predictable convention: `ComponentName_propertyName__hashCode`

Extract ALL class names matching this pattern from the HTML:

```bash
grep -oE '[A-Z][a-zA-Z]+_[a-zA-Z]+__[a-zA-Z0-9]+' {page}.html | sort -u
```

### Build the Mapping Table

For each extracted class, decompose into component, property, and semantic name:

| Obfuscated | Component | Property | Semantic Name |
|-----------|-----------|----------|---------------|
| `Header_root__x8J2p` | Header | root | `.header` |
| `Header_nav__mK3fA` | Header | nav | `.header-nav` |
| `Header_logo__Kd9aB` | Header | logo | `.header-logo` |
| `Plans_card__SCfoV` | Plans | card | `.plan-card` |
| `Plans_price__T4mNq` | Plans | price | `.plan-price` |
| `Hero_wrapper__aB3cD` | Hero | wrapper | `.hero-wrapper` |
| `Hero_heading__eF5gH` | Hero | heading | `.hero-heading` |
| `Footer_links__iJ7kL` | Footer | links | `.footer-links` |

### Extract CSS Rules per Component

For EACH unique component prefix, pull all its CSS rules:

```bash
PREFIX="Header"
grep -h "${PREFIX}_" {page}_files/*.css | tr '}' '\n' | grep "${PREFIX}_"
```

Repeat for every prefix found. This gives you the complete style block for each component.

### Write Deobfuscated CSS

Write the COMPLETE deobfuscated stylesheet to `deobfuscated.css`:

1. Replace every hashed class with its semantic name
2. Format the minified CSS (add newlines after `}` and `;`)
3. Keep the original hash as a trailing comment for traceability

Example output:

```css
/* === Header Component === */
.header /* was: Header_root__x8J2p */ {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-6);
  height: 72px;
  background: var(--color-bg-primary);
}

.header-nav /* was: Header_nav__mK3fA */ {
  display: flex;
  gap: var(--spacing-4);
  align-items: center;
}
```

---

## Step 4: Section Inventory

Walk the HTML document top-to-bottom. Identify every major section and catalog it.

### Section Identification Hierarchy

Use these methods in priority order:

1. **Semantic HTML tags:** `<header>`, `<main>`, `<section>`, `<footer>`, `<nav>`, `<aside>`, `<article>`
2. **CSS Module prefixes:** A cluster of classes sharing a prefix (e.g., `Hero_*`) = one section
3. **Structure heuristics:** Large `<div>` blocks with distinct backgrounds, padding patterns, or landmark roles

### For Each Section Found, Record:

| Field | Description |
|-------|-------------|
| **Section name** | Derived from CSS Module prefix or semantic tag |
| **DOM position** | Ordinal position (1st, 2nd, 3rd...) |
| **HTML root element** | The outermost tag and its classes |
| **CSS Module prefix** | The component prefix (e.g., `Hero`, `Plans`, `Footer`) |
| **Element count** | Total child elements |
| **Content summary** | Heading text, button count, image count, link count |
| **Background** | Color, gradient, or image used |
| **Estimated height** | From CSS or inline styles, if available |

### Example Output

```markdown
## Section Inventory

| # | Section | Root Element | CSS Prefix | Elements | Content Summary |
|---|---------|-------------|------------|----------|-----------------|
| 1 | Navigation | `<header>` | `Header` | 12 | Logo, 5 nav links, 2 buttons |
| 2 | Hero | `<section>` | `Hero` | 8 | H1, subtitle, CTA button, hero image |
| 3 | Logos | `<section>` | `LogoBar` | 7 | "Trusted by" heading, 6 company logos |
| 4 | Features | `<section>` | `Features` | 24 | H2, 3 feature cards (icon + title + desc) |
| 5 | Testimonials | `<section>` | `Social` | 9 | H2, 3 testimonial cards with avatars |
| 6 | CTA | `<section>` | `CTA` | 4 | H2, subtitle, email input, button |
| 7 | Footer | `<footer>` | `Footer` | 30+ | 4 link columns, social icons, copyright |
```

---

## Step 5: Font Extraction

Fonts define the typographic voice. Extract every font source and usage pattern.

### @font-face Declarations

```bash
grep -oE '@font-face\{[^}]+\}' {page}_files/*.css
```

### Font-Family Usage Frequency

```bash
grep -ohE 'font-family:[^;}]+' {page}_files/*.css | sort | uniq -c | sort -rn
```

### Google Fonts Links

```bash
grep -ohE 'fonts\.googleapis\.com[^"'"'"']*' {page}.html
```

### Local Font Files

```bash
find {page}_files/ -name "*.woff*" -o -name "*.ttf" -o -name "*.otf" -o -name "*.eot"
```

### Font Role Mapping

After extraction, determine which font families serve which roles:

| Role | Font Family | Weight Range | Usage Context |
|------|------------|-------------|---------------|
| Heading | Inter | 600–800 | H1–H6, card titles |
| Body | Inter | 400–500 | Paragraphs, descriptions |
| Monospace | JetBrains Mono | 400 | Code blocks, technical values |
| UI | Inter | 500–600 | Buttons, labels, nav items |

Download any external font URLs to `assets/fonts/`. Replace remote URLs in your output with local paths.

---

## Step 6: Color Extraction

Colors define the visual identity. Extract every color value with frequency to identify the system palette versus one-off overrides.

### All Hex Colors with Frequency

```bash
grep -ohE '#[0-9a-fA-F]{3,8}' {page}_files/*.css | sort | uniq -c | sort -rn | head -50
```

### RGB / RGBA Values

```bash
grep -ohE 'rgba?\([^)]+\)' {page}_files/*.css | sort | uniq -c | sort -rn | head -30
```

### HSL / HSLA Values

```bash
grep -ohE 'hsla?\([^)]+\)' {page}_files/*.css | sort | uniq -c | sort -rn | head -20
```

### Color Custom Properties

```bash
grep -ohE '\-\-color-[a-z0-9_-]+\s*:\s*[^;}]+' {page}_files/*.css | sort -u
```

### Gradient Values

```bash
grep -ohE '(linear|radial|conic)-gradient\([^)]*\)' {page}_files/*.css | sort -u
```

### Semantic Color Grouping

After extraction, organize colors into semantic groups:

- **Brand:** Primary, secondary, accent
- **Neutrals:** Background, surface, border, text (light-to-dark scale)
- **Feedback:** Success (green), error (red), warning (amber), info (blue)
- **Gradients:** Hero gradients, button gradients, decorative gradients

High-frequency colors are the system palette. Low-frequency colors are one-off overrides — still document them but flag as non-systematic.

---

## Step 7: Spacing, Layout & Typography Scale

These values define the geometric rhythm of the entire design.

### Pixel Values with Frequency

```bash
grep -ohE '[0-9]+px' {page}_files/*.css | sort -n | uniq -c | sort -rn | head -40
```

### Rem Values

```bash
grep -ohE '[0-9.]+rem' {page}_files/*.css | sort -n | uniq -c | sort -rn | head -20
```

### Font Sizes

```bash
grep -ohE 'font-size:[^;}]+' {page}_files/*.css | sort | uniq -c | sort -rn
```

### Line Heights

```bash
grep -ohE 'line-height:[^;}]+' {page}_files/*.css | sort | uniq -c | sort -rn
```

### Letter Spacing

```bash
grep -ohE 'letter-spacing:[^;}]+' {page}_files/*.css | sort | uniq -c | sort -rn
```

### Base Unit Detection

Look for a base unit. If multiples of 4px dominate (`4, 8, 12, 16, 20, 24, 32, 40, 48, 64`), the system is 4px-based. If 8px multiples dominate, then 8px-based.

### Container and Max-Width Values

```bash
grep -ohE 'max-width:[^;}]+' {page}_files/*.css | sort | uniq -c | sort -rn
```

---

## Step 8: Responsive Breakpoints

### All @media Queries

```bash
grep -ohE '@media[^{]+' {page}_files/*.css | sort | uniq -c | sort -rn
```

### Responsive Direction

Determine: mobile-first (`min-width`) or desktop-first (`max-width`)?

```bash
# Count min-width vs max-width
echo "min-width queries:"; grep -ohE 'min-width:\s*[0-9]+px' {page}_files/*.css | wc -l
echo "max-width queries:"; grep -ohE 'max-width:\s*[0-9]+px' {page}_files/*.css | wc -l
```

### Responsive Utility Classes

```bash
grep -ohE '\.(hide|show|visible|hidden|display)-[a-z]+' {page}_files/*.css | sort -u
grep -ohE '\.(sm|md|lg|xl|xxl):[a-zA-Z_-]+' {page}_files/*.css | sort -u
```

### Breakpoint Scale Output

```markdown
| Name | Value | Direction | Evidence |
|------|-------|-----------|----------|
| sm | 640px | min-width | 12 occurrences |
| md | 768px | min-width | 23 occurrences |
| lg | 1024px | min-width | 31 occurrences |
| xl | 1280px | min-width | 8 occurrences |
```

---

## Step 9: Animation & Motion

Animations define personality. A site that eases with `cubic-bezier(0.34, 1.56, 0.64, 1)` feels different from one using `ease-in-out`.

### @keyframes Rule Names

```bash
grep -ohE '@keyframes [a-zA-Z0-9_-]+' {page}_files/*.css | sort -u
```

### Transition Properties

```bash
grep -ohE 'transition:[^;}]+' {page}_files/*.css | sort | uniq -c | sort -rn | head -20
```

### Animation Properties

```bash
grep -ohE 'animation:[^;}]+' {page}_files/*.css | sort | uniq -c | sort -rn | head -20
```

### Easing Custom Properties

```bash
grep -ohE '\-\-ease-[a-z0-9_-]+\s*:\s*[^;}]+' {page}_files/*.css | sort -u
```

### Transform Values

```bash
grep -ohE 'transform:[^;}]+' {page}_files/*.css | grep -v 'uppercase\|capitalize\|lowercase' | sort | uniq -c | sort -rn | head -15
```

### Duration Tier Classification

Group all discovered durations into speed tiers:

| Tier | Range | Typical Use |
|------|-------|-------------|
| Micro | < 100ms | Button press, toggle, focus ring |
| Standard | 150–300ms | Hover state, menu open, tooltip |
| Section | 400–800ms | Scroll entrance, page section reveal |
| Slow | > 1s | Hero animation, loading sequence, background loop |

---

## Step 10: JS Behavior Extraction

CSS handles appearance; JS handles interaction. Scan all JS files for behavior patterns that downstream agents need to replicate.

### IntersectionObserver (Scroll Animations)

```bash
grep -l "IntersectionObserver" {page}_files/*.js
```

### Event Listeners

```bash
grep -ohE 'addEventListener\("[^"]+' {page}_files/*.js | sort | uniq -c | sort -rn
```

### Class Toggles

```bash
grep -ohE 'classList\.(add|remove|toggle)\("[^"]+' {page}_files/*.js | sort | uniq -c
```

### Scroll Listeners

```bash
grep -c "scroll" {page}_files/*.js
```

### Resize Handlers

```bash
grep -c "resize" {page}_files/*.js
```

### Declarative Behavior Spec

Document each discovered behavior as a declarative specification in `behavior-spec.md`. Downstream agents implement from these specs — they don't read raw JS.

```markdown
## Behavior: Scroll-triggered section entrance
- **Trigger:** Element enters viewport (IntersectionObserver, threshold: 0.1)
- **Target:** `.section` elements with `data-animate` attribute
- **Effect:** opacity 0→1, translateY(20px)→translateY(0)
- **Duration:** 600ms
- **Easing:** ease-out
- **Stagger:** 100ms delay between sibling children

## Behavior: Navbar background on scroll
- **Trigger:** Window scroll position > 50px
- **Target:** `<header>` element
- **Effect:** background-color transparent → var(--color-bg-primary), box-shadow none → var(--shadow-sm)
- **Duration:** 200ms
- **Easing:** ease

## Behavior: Mobile menu toggle
- **Trigger:** Click on hamburger button
- **Target:** `.nav-mobile` panel
- **Effect:** translateX(100%) → translateX(0), body scroll lock
- **Duration:** 300ms
- **Easing:** cubic-bezier(0.4, 0, 0.2, 1)
```

---

## Step 11: Asset Download & Cataloging

A design soul without its assets is incomplete. Download everything the page references externally.

### Find All External URLs

```bash
# External URLs in HTML (images, fonts, scripts, stylesheets)
grep -ohE 'https?://[^"'"'"' >]+' {page}.html | sort -u

# External URLs in CSS (background images, font files)
grep -ohE 'url\([^)]+\)' {page}_files/*.css | grep -ohE 'https?://[^)]+' | sort -u
```

### Download Assets by Category

```bash
mkdir -p assets/fonts assets/images assets/icons assets/videos

# For each font URL:
# curl -sL -o assets/fonts/{filename} {url}

# For each image URL:
# curl -sL -o assets/images/{filename} {url}

# For each SVG icon URL:
# curl -sL -o assets/icons/{filename} {url}
```

### Asset Manifest

Create `assets/asset-manifest.json` cataloging every downloaded asset:

```json
{
  "fonts": [
    {"original": "https://fonts.gstatic.com/s/inter/v13/UcC73FwrK3iLTeHuS_fvQtMwCp50KnMa.woff2", "local": "assets/fonts/inter-var-latin.woff2", "format": "woff2", "family": "Inter"}
  ],
  "images": [
    {"original": "https://example.com/hero-bg.webp", "local": "assets/images/hero-bg.webp", "dimensions": "1920x1080", "section": "Hero"}
  ],
  "icons": [
    {"original": "inline-svg", "local": "assets/icons/check.svg", "viewBox": "0 0 24 24", "usage": "Feature list checkmarks"}
  ]
}
```

---

## Output Files Specification

Every Wave 0 run produces exactly these files in `.design-soul/wave0/{page}/`:

### `exploration.md` — The Master Document

Contains ALL extracted data in one structured file:

1. **Page Classification** — Type, confidence, signals
2. **CSS Inventory** — File list, hashes, dedup count
3. **Token Map** — Every CSS custom property with resolved values (light + dark)
4. **Deobfuscation Map** — Full class name mapping table
5. **Section Inventory** — Every section with metadata
6. **Typography** — Font families, sizes, weights, line heights, letter spacing
7. **Color Palette** — All colors with frequency, grouped semantically
8. **Spacing Scale** — All spacing values, base unit, container widths
9. **Responsive Map** — Breakpoints, direction, utility classes
10. **Animation Catalog** — Keyframes, transitions, easing functions, duration tiers
11. **Asset Manifest** — All downloaded assets with paths

### `deobfuscated.css` — Human-Readable Stylesheet

The complete CSS from all source files, with:
- Obfuscated class names replaced with semantic names
- Minified CSS formatted with proper indentation
- Original hashes preserved as comments
- Organized by component (one section per CSS Module prefix)

### `behavior-spec.md` — Declarative Interaction Specs

Every JS-driven behavior documented as a declarative spec. No raw JS — just trigger/target/effect/duration/easing.

### `assets/` — Downloaded Resources

- `assets/fonts/` — All font files (woff2, woff, ttf)
- `assets/images/` — All images (hero backgrounds, photos, illustrations)
- `assets/icons/` — All SVG icons (extracted from inline SVGs and external URLs)
- `assets/asset-manifest.json` — Catalog of everything with original→local path mapping

### `done.signal` — Completion Marker

An empty file. Its existence tells the orchestrator this page's Wave 0 is complete. Do NOT create it until every other file is written and verified.

---

## What You'll Be Tempted to Skip

These are the items agents most commonly skip. Every one of them creates a hole in the final product.

- **Dark theme variables** — `[data-theme="dark"]` and `prefers-color-scheme: dark` selectors contain an entire alternate color system. If you skip these, the rebuild has no dark mode.
- **Variable chains** — `--color-primary: var(--color-brand-500)` is meaningless without resolving `--color-brand-500`. Follow every chain to its terminal value.
- **JS behaviors** — Scroll-triggered animations, navbar transparency changes, mobile menu toggles. These are invisible in CSS alone but define half the user experience.
- **Responsive utility classes** — `.hide-mobile`, `.show-tablet`, `.desktop-only`, `.sm:hidden`. These control what users see at each breakpoint.
- **Z-index layer system** — `--layer-base`, `--layer-dropdown`, `--layer-modal`, `--layer-toast`. Without these, rebuilt modals appear behind content.
- **Asset downloading** — It's easier to just note the URLs. But downstream agents need local files. Download everything.
- **Easing functions** — The difference between `ease` and `cubic-bezier(0.34, 1.56, 0.64, 1)` is the difference between a generic site and a polished product. Extract every custom easing curve.
- **Inline HTML styles** — `style=""` attributes on HTML elements override CSS. They often contain critical spacing overrides, custom property values, and one-off colors.
- **Font weight mapping** — Knowing the site uses Inter isn't enough. You need to know it uses weight 400 for body, 500 for UI, 600 for subheadings, and 800 for hero headlines.
- **Gradient color stops** — `background: linear-gradient(...)` needs exact angles and exact color stops with positions. Not "blue to purple" — the actual values.

If you finish and any of these are missing, your output is incomplete. Go back and extract them.
