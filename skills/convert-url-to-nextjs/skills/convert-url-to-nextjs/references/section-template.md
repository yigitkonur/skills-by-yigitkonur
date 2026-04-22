# Wave 2: Page Build Brief Template

> **Purpose:** This is the template each Wave 2 agent fills out — one per page. A Wave 4 agent must be able to build this page from this brief ALONE, with no access to the original HTML.

> **Input:** `wave0/{page}/exploration.md` + `wave0/{page}/deobfuscated.css` + `wave1/{group}/design-soul.md` + `wave1/{group}/token-values.json`
> **Output:** `wave2/{page}/agent-brief.md` + `wave2/{page}/done.signal`

┌─────────────────────────────────────────────────────────────────┐
│  THE GROUNDING RULE: Every value in this brief MUST trace to a  │
│  real CSS property extracted from the source page. No guessing. │
│  No "looks about right." No Tailwind defaults.                  │
└─────────────────────────────────────────────────────────────────┘

---

## Page Identity

| Field | Value |
|-------|-------|
| **Page Name** | {e.g., Homepage} |
| **Source File** | {e.g., linear-homepage.html} |
| **Page Type** | {landing / pricing / features / blog / docs / about / dashboard / auth / legal / custom} |
| **Route** | {e.g., `/` or `/pricing`} |
| **Meta Title** | {extracted from `<title>` tag} |
| **Meta Description** | {extracted from `<meta name="description">`} |
| **Total Sections** | {integer count} |
| **Wave 0 Source** | `wave0/{page}/exploration.md` |
| **Wave 1 Source** | `wave1/{group}/design-soul.md` |
| **Page Type Group** | {group name from Wave 1} |

---

## Quick Reference — CSS Extraction Commands

Run these against the page's CSS corpus, not just `_files/`.

- Primary mode: run inside `{page}_files/` and use the commands as written.
- Adjacent-asset mode: run from the snapshot directory and replace `*.css` with the local CSS files referenced by the HTML.
- Inline-only mode: extract the page's `<style>` blocks to a temporary CSS file first, or run the commands against Wave 0 `deobfuscated.css`.

### Custom Properties (Design Tokens)
```bash
# All CSS custom properties
grep -ohE -e '--[a-zA-Z0-9-]+' *.css | sort | uniq -c | sort -rn

# Custom property definitions with values
grep -ohE -e '--[a-zA-Z0-9-]+:\s*[^;}]+' *.css | sort -u

# Color variables specifically
grep -ohE -e '--color-[a-zA-Z0-9-]+:\s*[^;}]+' *.css | sort -u

# Font variables
grep -ohE -e '--font-[a-zA-Z0-9-]+:\s*[^;}]+' *.css | sort -u

# Spacing/size variables
grep -ohE -e '--spacing-[a-zA-Z0-9-]+:\s*[^;}]+' *.css | sort -u
```

### Typography
```bash
# All font-family declarations
grep -ohE 'font-family:\s*[^;}]+' *.css | sort | uniq -c | sort -rn

# All font-size values
grep -ohE 'font-size:\s*[^;}]+' *.css | sort | uniq -c | sort -rn

# All font-weight values
grep -ohE 'font-weight:\s*[^;}]+' *.css | sort | uniq -c | sort -rn

# All line-height values
grep -ohE 'line-height:\s*[^;}]+' *.css | sort | uniq -c | sort -rn

# All letter-spacing values
grep -ohE 'letter-spacing:\s*[^;}]+' *.css | sort | uniq -c | sort -rn
```

### Colors
```bash
# All hex colors
grep -ohE '#[0-9a-fA-F]{3,8}' *.css | sort | uniq -c | sort -rn

# All rgb/rgba colors
grep -ohE 'rgba?\([^)]+\)' *.css | sort | uniq -c | sort -rn

# All hsl/hsla colors
grep -ohE 'hsla?\([^)]+\)' *.css | sort | uniq -c | sort -rn

# All gradient definitions
grep -ohE '(linear|radial|conic)-gradient\([^)]*\)' *.css | sort -u
```

### Spacing
```bash
# All padding values
grep -ohE 'padding[^:]*:\s*[^;}]+' *.css | sort | uniq -c | sort -rn

# All margin values
grep -ohE 'margin[^:]*:\s*[^;}]+' *.css | sort | uniq -c | sort -rn

# All gap values
grep -ohE 'gap:\s*[^;}]+' *.css | sort | uniq -c | sort -rn
```

### Layout
```bash
# All grid definitions
grep -ohE 'grid-template-columns:\s*[^;}]+' *.css | sort -u

# All flex directions
grep -ohE 'flex-direction:\s*[^;}]+' *.css | sort | uniq -c | sort -rn

# All max-width values
grep -ohE 'max-width:\s*[^;}]+' *.css | sort | uniq -c | sort -rn
```

### Responsive
```bash
# All @media breakpoints
grep -ohE '@media[^{]+' *.css | grep -ohE '(min|max)-width:\s*[0-9]+px' | sort -t: -k2 -n | uniq

# Media query blocks (shows what changes)
grep -B0 -A5 '@media' *.css | head -100
```

### Animation
```bash
# All transition properties
grep -ohE 'transition:\s*[^;}]+' *.css | sort | uniq -c | sort -rn

# All animation properties
grep -ohE 'animation:\s*[^;}]+' *.css | sort -u

# All @keyframes definitions
grep -ohE '@keyframes\s+[a-zA-Z0-9_-]+' *.css | sort -u

# All transform values
grep -ohE 'transform:\s*[^;}]+' *.css | grep -v 'uppercase\|capitalize\|lowercase' | sort | uniq -c | sort -rn

# All easing functions
grep -ohE '(ease|ease-in|ease-out|ease-in-out|cubic-bezier\([^)]+\))' *.css | sort | uniq -c | sort -rn
```

### Other
```bash
# All border-radius values
grep -ohE 'border-radius:\s*[^;}]+' *.css | sort | uniq -c | sort -rn

# All box-shadow values
grep -ohE 'box-shadow:\s*[^;}]+' *.css | sort | uniq -c | sort -rn

# All z-index values
grep -ohE 'z-index:\s*[^;}]+' *.css | sort -t: -k2 -n | uniq

# All opacity values
grep -ohE 'opacity:\s*[^;}]+' *.css | sort | uniq -c | sort -rn

# CSS Module prefix map
grep -ohE '[A-Z][a-zA-Z]+_[a-zA-Z]+__[a-zA-Z0-9]+' ../page.html | sed 's/_[a-zA-Z]*__[a-zA-Z0-9]*$//' | sort -u
```

---

## Section Map

List all sections in top-to-bottom DOM order before documenting each one.

| # | Section Name | CSS Module Prefix | Type (from `website-patterns.md`) | Component Tag | Approx Height |
|---|-------------|-------------------|-----------------------------------|---------------|---------------|
| 1 | Navigation | `Header_` | Navigation | SHARED | 64px |
| 2 | Hero | `Hero_` | Hero — Split | PAGE-SPECIFIC | 680px |
| 3 | Logo Cloud | `Customers_` | Logo Cloud — Marquee | SHARED | 120px |
| ... | ... | ... | ... | ... | ... |
| N | Footer | `Footer_` | Footer — Multi-Column | SHARED | 320px |

---

## Per-Section Blueprint

Repeat this complete template for EVERY section on the page. Do not skip sections. Do not abbreviate.

---

### Section {N}: {Section Name}

#### Section Identity

| Field | Value |
|-------|-------|
| **CSS Module Prefix** | {e.g., `Hero_`} |
| **HTML Root Tag** | {e.g., `<section>`} |
| **Section Type** | {from `references/website-patterns.md`} |
| **Sub-pattern** | {e.g., "Split Hero" or "Centered Hero"} |
| **Component Tag** | `SHARED` / `PAGE-SPECIFIC` |
| **Server/Client** | Server Component / Client Component (with reason) |
| **Estimated TSX Lines** | {rough estimate for Wave 4 planning} |

#### Section Anatomy — Desktop (≥1280px)

```
┌─────────────────────────────────────────────────────────────┐
│  Section: Hero                              padding-top: 120px
│  ┌──────────────────────┐  ┌──────────────────────────────┐ │
│  │   Text Column        │  │   Image Column               │ │
│  │   max-width: 540px   │  │                              │ │
│  │                      │  │   ┌────────────────────────┐ │ │
│  │   [Eyebrow]          │  │   │                        │ │ │
│  │   mb: 16px           │  │   │   Product Screenshot   │ │ │
│  │                      │  │   │   aspect-ratio: 16/10  │ │ │
│  │   [H1 Heading]       │  │   │                        │ │ │
│  │   mb: 24px           │  │   └────────────────────────┘ │ │
│  │                      │  │                              │ │
│  │   [Subtitle]         │  └──────────────────────────────┘ │
│  │   mb: 40px           │                                   │
│  │                      │  gap: 64px                        │
│  │   [CTA Primary]      │                                   │
│  │   gap: 12px          │  grid-template-columns: 1fr 1fr   │
│  │   [CTA Secondary]    │                                   │
│  └──────────────────────┘                                   │
│                                             padding-bottom: 120px
└─────────────────────────────────────────────────────────────┘
```

#### Section Anatomy — Mobile (≤767px)

```
┌───────────────────────────┐
│  Section: Hero   pt: 60px │
│                           │
│  [Eyebrow]    mb: 12px   │
│  [H1 Heading] mb: 16px   │
│  [Subtitle]   mb: 32px   │
│  [CTA Primary]  mb: 12px │
│  [CTA Secondary]          │
│                   mt: 40px│
│  [Product Screenshot]     │
│  width: 100%              │
│                           │
│               pb: 60px    │
└───────────────────────────┘
```

#### Element Inventory

Every visible element in this section. Missing one = missing it in the build.

| # | Element | Tag | CSS Classes (deobfuscated) | Role | States | Notes |
|---|---------|-----|---------------------------|------|--------|-------|
| 1 | Section wrapper | `<section>` | `Hero_root__x8J2p` → `.hero-root` | Container | — | Full-width, centered content |
| 2 | Content grid | `<div>` | `Hero_grid__b2C3d` → `.hero-grid` | Layout | — | 2-col grid desktop, stack mobile |
| 3 | Text column | `<div>` | `Hero_textCol__c3D4e` → `.hero-text` | Content group | — | max-width: 540px |
| 4 | Eyebrow label | `<span>` | `Hero_eyebrow__d4E5f` → `.hero-eyebrow` | Category label | — | Uppercase, small, brand color |
| 5 | Main heading | `<h1>` | `Hero_heading__e5F6g` → `.hero-heading` | Primary heading | — | Largest text on page |
| 6 | Subtitle | `<p>` | `Hero_subtitle__f6G7h` → `.hero-subtitle` | Value proposition | — | Secondary color, max-width |
| 7 | CTA primary | `<a>` | `Hero_ctaPrimary__g7H8i` → `.hero-cta-primary` | Primary action | default, hover, focus, active | Brand bg, white text |
| 8 | CTA secondary | `<a>` | `Hero_ctaSecondary__h8I9j` → `.hero-cta-secondary` | Secondary action | default, hover, focus, active | Outlined variant |
| 9 | Image column | `<div>` | `Hero_imageCol__i9J0k` → `.hero-image-col` | Media container | — | Aspect ratio preserved |
| 10 | Product image | `<img>` | `Hero_image__j0K1l` → `.hero-image` | Visual | — | WebP, 1200x750 |

#### Layout & Grid

| Property | Desktop (≥1280px) | Tablet (768-1279px) | Mobile (≤767px) |
|----------|-------------------|---------------------|-----------------|
| **Display** | `grid` | `grid` | `flex` |
| **Grid Columns** | `1fr 1fr` | `1fr 1fr` | n/a (single column) |
| **Flex Direction** | n/a | n/a | `column` |
| **Gap** | `64px` | `48px` | `40px` |
| **Content Max Width** | `1200px` | `100%` | `100%` |
| **Centering** | `margin: 0 auto` | padding only | padding only |
| **Horizontal Padding** | `0` (within max-width) | `40px` | `20px` |
| **Vertical Alignment** | `center` | `center` | `stretch` |

#### Typography

All values MUST come from Wave 0 extraction + Wave 1 design soul. No approximations.

| Element | Font Family | Size (D) | Size (T) | Size (M) | Weight | Line Height | Letter Spacing | Color | Text Transform |
|---------|------------|----------|----------|----------|--------|-------------|----------------|-------|----------------|
| Eyebrow | `var(--font-regular)` | 14px | 14px | 12px | 500 | 1.4 | 0.08em | `var(--color-brand-primary)` | uppercase |
| H1 | `var(--font-display)` | 64px | 48px | 36px | 700 | 1.08 | -0.02em | `var(--color-text-primary)` | none |
| Subtitle | `var(--font-regular)` | 20px | 18px | 16px | 400 | 1.6 | 0 | `var(--color-text-secondary)` | none |
| CTA text | `var(--font-regular)` | 16px | 16px | 14px | 500 | 1.0 | 0 | `#FFFFFF` / `var(--color-text-primary)` | none |

> **(D)** = Desktop ≥1280px, **(T)** = Tablet 768-1279px, **(M)** = Mobile ≤767px

#### Color Usage

| Element | Property | Light Mode | Dark Mode | CSS Variable | Resolved from Source |
|---------|----------|-----------|-----------|-------------|---------------------|
| Section bg | `background-color` | `#FFFFFF` | `#0A0A0F` | `var(--color-bg-primary)` | ✓ wave0 line 47 |
| H1 text | `color` | `#1A1A2E` | `#F0F0F5` | `var(--color-text-primary)` | ✓ wave0 line 52 |
| Subtitle | `color` | `#6B6B80` | `#8B8BA0` | `var(--color-text-secondary)` | ✓ wave0 line 54 |
| Eyebrow | `color` | `#5E6AD2` | `#7B85E0` | `var(--color-brand-primary)` | ✓ wave0 line 61 |
| CTA bg | `background-color` | `#5E6AD2` | `#5E6AD2` | `var(--color-brand-primary)` | ✓ wave0 line 61 |
| CTA hover | `background-color` | `#6C75DB` | `#6C75DB` | `var(--color-brand-hover)` | ✓ wave0 line 63 |
| CTA secondary border | `border-color` | `#D0D0E0` | `#2A2A3E` | `var(--color-border-primary)` | ✓ wave0 line 70 |

#### Background & Atmosphere

| Property | Value | Source |
|----------|-------|--------|
| **Background type** | {solid / gradient / image / video / pattern} | |
| **Background value** | {exact CSS value} | wave0 deobfuscated.css line N |
| **Gradient** | {exact gradient definition if applicable} | |
| **Overlay** | {color + opacity if applicable} | |
| **Decorative elements** | {blur blobs, grain texture, geometric shapes} | |
| **Noise/grain CSS** | {exact CSS if applicable: `background-image: url(data:...)` or filter} | |

Example:
```css
background: linear-gradient(180deg, var(--color-bg-primary) 0%, var(--color-bg-secondary) 100%);
```

If decorative pseudo-elements exist:
```css
.hero::before {
  content: '';
  position: absolute;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(94,106,210,0.15), transparent 70%);
  top: -200px;
  right: -100px;
  filter: blur(80px);
  pointer-events: none;
}
```

#### Spacing & Rhythm

```
Section Spacing Diagram:
┌─────────────────────────────────────────────┐
│              padding-top: 120px             │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Eyebrow                             │   │
│  │     margin-bottom: 16px             │   │
│  │                                     │   │
│  │ H1 Heading                          │   │
│  │     margin-bottom: 24px             │   │
│  │                                     │   │
│  │ Subtitle                            │   │
│  │     margin-bottom: 40px             │   │
│  │                                     │   │
│  │ CTA Group                           │   │
│  │     gap: 12px (between buttons)     │   │
│  │     display: flex; flex-wrap: wrap   │   │
│  └─────────────────────────────────────┘   │
│                                             │
│              padding-bottom: 120px          │
└─────────────────────────────────────────────┘
```

| Spacing | Desktop | Tablet | Mobile | CSS Property |
|---------|---------|--------|--------|-------------|
| Section padding-top | 120px | 80px | 60px | `padding-top` |
| Section padding-bottom | 120px | 80px | 60px | `padding-bottom` |
| Eyebrow → H1 | 16px | 16px | 12px | `margin-bottom` |
| H1 → Subtitle | 24px | 20px | 16px | `margin-bottom` |
| Subtitle → CTA | 40px | 32px | 24px | `margin-bottom` |
| CTA button gap | 12px | 12px | 12px | `gap` |
| Grid column gap | 64px | 48px | 0 | `gap` / `column-gap` |

#### States & Variants

| Element | Trigger | Property | From | To | Duration | Easing |
|---------|---------|----------|------|----|----------|--------|
| CTA Primary | `:hover` | `background-color` | `#5E6AD2` | `#6C75DB` | 150ms | ease |
| CTA Primary | `:hover` | `transform` | `none` | `translateY(-1px)` | 150ms | ease |
| CTA Primary | `:hover` | `box-shadow` | `none` | `0 4px 12px rgba(94,106,210,0.3)` | 150ms | ease |
| CTA Primary | `:focus-visible` | `outline` | `none` | `2px solid #5E6AD2` | 0ms | — |
| CTA Primary | `:focus-visible` | `outline-offset` | `0` | `2px` | 0ms | — |
| CTA Primary | `:active` | `transform` | `translateY(-1px)` | `translateY(0)` | 50ms | ease |
| CTA Secondary | `:hover` | `background-color` | `transparent` | `rgba(94,106,210,0.08)` | 150ms | ease |
| CTA Secondary | `:hover` | `border-color` | `var(--color-border-primary)` | `var(--color-brand-primary)` | 150ms | ease |

#### CSS Variable Usage Map

| Variable | Resolved Value (Light) | Resolved Value (Dark) | Used For in This Section |
|----------|----------------------|----------------------|-------------------------|
| `--color-brand-primary` | `#5E6AD2` | `#7B85E0` | Eyebrow text, CTA bg, link color |
| `--color-text-primary` | `#1A1A2E` | `#F0F0F5` | H1 heading |
| `--color-text-secondary` | `#6B6B80` | `#8B8BA0` | Subtitle, meta text |
| `--color-bg-primary` | `#FFFFFF` | `#0A0A0F` | Section background |
| `--color-border-primary` | `#D0D0E0` | `#2A2A3E` | CTA secondary border |
| `--font-display` | `'Inter Display', sans-serif` | same | H1 heading font-family |
| `--font-regular` | `'Inter', sans-serif` | same | Body text, CTA, eyebrow |

#### Responsive Behavior

| Breakpoint | Property | Change | CSS Source |
|------------|----------|--------|-----------|
| `≤1279px` | Grid columns | `1fr 1fr` → `1fr 1fr` (narrower) | `@media (max-width: 1279px)` |
| `≤1023px` | Grid columns | `1fr 1fr` → `1fr` (stack) | `@media (max-width: 1023px)` |
| `≤1023px` | Image order | below text (`order: 2`) | same media query |
| `≤767px` | H1 font-size | `64px` → `36px` | `@media (max-width: 767px)` |
| `≤767px` | Section padding | `120px` → `60px` | same media query |
| `≤767px` | CTA layout | `flex-direction: column; width: 100%` | same media query |
| `≤767px` | Gap | `64px` → `40px` | same media query |

Breakpoint extraction (run against the page's CSS corpus):
```bash
grep -ohE '@media[^{]+' *.css | grep -ohE '(min|max)-width:\s*[0-9]+px' | sort -t: -k2 -n | uniq
```

#### Scroll & Animation

| # | Element | Trigger | Animation | Duration | Easing | Delay | Implementation |
|---|---------|---------|-----------|----------|--------|-------|----------------|
| 1 | Eyebrow | viewport-enter | fadeInUp: `opacity 0→1`, `translateY 20px→0` | 500ms | `cubic-bezier(0.16, 1, 0.3, 1)` | 0ms | IntersectionObserver |
| 2 | H1 | viewport-enter | fadeInUp | 500ms | same | 100ms | IntersectionObserver |
| 3 | Subtitle | viewport-enter | fadeInUp | 500ms | same | 200ms | IntersectionObserver |
| 4 | CTA group | viewport-enter | fadeInUp | 500ms | same | 300ms | IntersectionObserver |
| 5 | Image | viewport-enter | fadeIn + scale: `opacity 0→1`, `scale 0.95→1` | 700ms | same | 200ms | IntersectionObserver |

> **IntersectionObserver config:** `threshold: 0.2`, `rootMargin: '0px 0px -50px 0px'`, trigger once.

> **Reduced motion:** When `prefers-reduced-motion: reduce`, skip all animations — elements appear immediately at their final state. Use `useScrollAnimation` hook from `lib/animations.ts`.

#### CSS Recreation Block

The EXACT CSS needed to recreate this section. This is the PRIMARY build reference for Wave 4 agents.

```css
/* Section Container */
.hero {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 64px;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  padding: 120px 0;
}

/* Text Column */
.hero-text {
  max-width: 540px;
}

/* Eyebrow */
.hero-eyebrow {
  font-family: var(--font-regular);
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-brand-primary);
  margin-bottom: 16px;
}

/* Heading */
.hero-heading {
  font-family: var(--font-display);
  font-size: 64px;
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: -0.02em;
  color: var(--color-text-primary);
  margin-bottom: 24px;
}

/* Subtitle */
.hero-subtitle {
  font-family: var(--font-regular);
  font-size: 20px;
  font-weight: 400;
  line-height: 1.6;
  color: var(--color-text-secondary);
  margin-bottom: 40px;
  max-width: 480px;
}

/* CTA Group */
.hero-cta-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* CTA Primary */
.hero-cta-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 24px;
  background-color: var(--color-brand-primary);
  color: #FFFFFF;
  font-family: var(--font-regular);
  font-size: 16px;
  font-weight: 500;
  line-height: 1;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 150ms ease;
  text-decoration: none;
}

.hero-cta-primary:hover {
  background-color: var(--color-brand-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(94, 106, 210, 0.3);
}

.hero-cta-primary:active {
  transform: translateY(0);
}

/* CTA Secondary */
.hero-cta-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 24px;
  background-color: transparent;
  color: var(--color-text-primary);
  font-family: var(--font-regular);
  font-size: 16px;
  font-weight: 500;
  line-height: 1;
  border-radius: 8px;
  border: 1px solid var(--color-border-primary);
  cursor: pointer;
  transition: all 150ms ease;
  text-decoration: none;
}

.hero-cta-secondary:hover {
  background-color: rgba(94, 106, 210, 0.08);
  border-color: var(--color-brand-primary);
}

/* Image Column */
.hero-image-col {
  position: relative;
}

.hero-image {
  width: 100%;
  height: auto;
  border-radius: 12px;
}

/* Responsive */
@media (max-width: 1023px) {
  .hero {
    grid-template-columns: 1fr;
    gap: 40px;
    padding: 80px 40px;
  }
  .hero-image-col {
    order: 2;
  }
  .hero-heading {
    font-size: 48px;
  }
}

@media (max-width: 767px) {
  .hero {
    padding: 60px 20px;
  }
  .hero-heading {
    font-size: 36px;
    letter-spacing: -0.01em;
  }
  .hero-subtitle {
    font-size: 16px;
  }
  .hero-cta-group {
    flex-direction: column;
  }
  .hero-cta-primary,
  .hero-cta-secondary {
    width: 100%;
    justify-content: center;
  }
}
```

#### Next.js Implementation Hints

| Aspect | Guidance |
|--------|----------|
| **Component type** | {Server / Client — and why} |
| **Shared components to use** | {from Wave 1 inventory: `Button`, `Container`, etc.} |
| **Image handling** | {`next/image` with `priority` for hero, `sizes` attribute, local path} |
| **Animation approach** | {CSS-only / `useScrollAnimation` hook / `useEffect` + IntersectionObserver} |
| **Key Tailwind classes** | {`grid grid-cols-2 gap-16 items-center max-w-[1200px] mx-auto py-[120px]`} |
| **Font loading** | {Uses `--font-display` → loaded via `next/font/local` in root layout} |
| **Dark mode** | {Tailwind `dark:` variants or CSS `[data-theme="dark"]`} |

---

## Component Manifest

After documenting ALL sections, compile the component manifest.

### Shared Components

Components used across multiple pages or sections. Import from `/components/shared/`.

Start with an empty table. Add rows only for components that already exist in the Wave 1 inventory or for explicitly allowed structural helpers that Wave 3 created on purpose. Delete any example row that is not grounded in the current page group.

| Component | Props Interface | Used In Sections | Wave 1 Source |
|-----------|----------------|-----------------|---------------|
| `Button` | `variant: 'primary' \| 'secondary' \| 'ghost'`, `size: 'sm' \| 'md' \| 'lg'`, `href?: string`, `children: ReactNode` | Hero, CTA, Pricing | wave1/landing/component-inventory.md |
| `Container` | `maxWidth?: string`, `padding?: string`, `children: ReactNode` | All sections | wave1/landing/component-inventory.md |
| `SectionWrapper` | `id: string`, `className?: string`, `animate?: boolean`, `children: ReactNode` | All sections | wave1/landing/component-inventory.md |
| `Badge` | `variant: 'default' \| 'brand'`, `children: ReactNode` | Hero, Features | wave1/landing/component-inventory.md |

### Page-Specific Components

Components unique to this page. Create in `/components/pages/{page}/`.

Again, start empty. Add a row only when the page actually needs that component. Do not copy example component names from this template into the brief unless the source page proves they exist.

| Component | Props Interface | Used In Section | Purpose |
|-----------|----------------|----------------|---------|
| `HeroIllustration` | `className?: string` | Hero | Product screenshot with frame effects |
| `FeatureCard` | `icon: ReactNode`, `title: string`, `description: string` | Features | Individual feature card |
| `PricingCard` | `plan: Plan`, `highlighted?: boolean` | Pricing | Pricing plan card |
| `TestimonialSlider` | `testimonials: Testimonial[]` | Testimonials | Carousel with navigation |

---

## Asset Reference Table

Every image, icon, font, and media file used on this page.

| # | Asset Description | Wave 0 Path | Public Path | Used In Section | Format | Dimensions | Size |
|---|-------------------|-------------|-------------|----------------|--------|------------|------|
| 1 | Hero product screenshot | `wave0/homepage/assets/images/hero-product.webp` | `/assets/images/hero-product.webp` | Hero | WebP | 1200×750 | 142KB |
| 2 | Feature icon: Speed | `wave0/homepage/assets/icons/speed.svg` | `/assets/icons/speed.svg` | Features | SVG | 24×24 | 1.2KB |
| 3 | Customer logo: Acme | `wave0/homepage/assets/images/logo-acme.svg` | `/assets/images/logos/acme.svg` | Logo Cloud | SVG | 120×32 | 2.1KB |
| 4 | Avatar: Jane Doe | `wave0/homepage/assets/images/avatar-jane.webp` | `/assets/images/avatars/jane.webp` | Testimonials | WebP | 96×96 | 8KB |

┌─────────────────────────────────────────────────────────────────┐
│  RULE: Every asset in this table must exist in wave0/{page}/    │
│  assets/. If an asset is missing from Wave 0 output, flag it   │
│  with ⚠️ MISSING and note the original URL for manual download. │
└─────────────────────────────────────────────────────────────────┘

---

## Interaction Specification

Document every user interaction on this page as a declarative spec.

| # | Trigger | Target Element | Effect | Duration | Easing | Implementation Notes |
|---|---------|---------------|--------|----------|--------|---------------------|
| 1 | Page scroll > 80px | Nav bar | Background: transparent → solid with shadow | 200ms | ease | CSS: `[data-scrolled="true"]` toggled by scroll listener |
| 2 | Click hamburger icon | Mobile menu | Slide in from right, overlay appears | 300ms | `cubic-bezier(0.16, 1, 0.3, 1)` | Client component with `useState` |
| 3 | Hover on feature card | Card | translateY(-4px), shadow increase | 200ms | ease | CSS `:hover` only — no JS |
| 4 | Section enters viewport | Section children | Staggered fadeInUp (100ms delay per child) | 500ms | `cubic-bezier(0.16, 1, 0.3, 1)` | `useScrollAnimation` hook |
| 5 | Hover on CTA primary | Button | Background lighten, subtle lift, shadow | 150ms | ease | CSS `:hover` — Tailwind `hover:` utilities |
| 6 | Click billing toggle | Price displays | Monthly ↔ Annual price swap | 200ms | ease | `useState` for billing period |
| 7 | Click FAQ question | Answer panel | Expand with max-height transition | 300ms | ease-out | `useState` per item or `<details>` |

---

## Acceptance Criteria

A Wave 4 agent building this page MUST verify ALL of the following before declaring the page build complete.

### Visual Fidelity — Desktop (≥1280px)

- [ ] Every section present in correct order (matches Section Map above)
- [ ] Section heights approximately match (within 5% tolerance)
- [ ] All typography matches: font-family, font-size, font-weight, line-height, letter-spacing, color
- [ ] All colors match: backgrounds, text, borders, shadows, gradients
- [ ] All spacing matches: padding, margin, gap (exact px values from this brief)
- [ ] All images and icons display correctly from `/public/assets/`
- [ ] Grid/flex layouts match column counts and gap values
- [ ] Border-radius values match on all elements

### Visual Fidelity — Tablet (768-1279px)

- [ ] Responsive layout changes match the breakpoint tables above
- [ ] Typography scales to tablet sizes specified in typography tables
- [ ] No horizontal scrollbar appears
- [ ] Images scale appropriately (no overflow, no distortion)

### Visual Fidelity — Mobile (≤767px)

- [ ] Layouts collapse to single column where specified
- [ ] Typography scales to mobile sizes specified in typography tables
- [ ] Touch targets are minimum 44×44px
- [ ] No horizontal scrollbar appears
- [ ] Mobile-specific UI elements appear (hamburger menu, stacked CTAs)

### Interactions & Animation

- [ ] All hover states from States & Variants tables are implemented
- [ ] All focus-visible states provide clear keyboard navigation indicators
- [ ] All scroll animations fire at correct thresholds with correct timing
- [ ] Transitions use exact durations and easings from this brief
- [ ] `prefers-reduced-motion: reduce` disables all motion
- [ ] Carousel/accordion/toggle interactions work correctly

### Technical Requirements

- [ ] Zero external network requests (fonts, images, scripts — all local)
- [ ] All fonts load from local `@font-face` declarations
- [ ] TypeScript strict mode — zero type errors
- [ ] Only Tailwind utilities + `tokens.ts` values used (no magic numbers)
- [ ] Component imports match the Component Manifest above
- [ ] `next build` succeeds with zero errors
- [ ] All images use `next/image` with appropriate `sizes` and `priority` attributes

### The Self-Containment Test

> **Can a Wave 4 agent build this page from this brief ALONE?**
>
> - Does the brief specify every font-size, color, and spacing value? → YES required
> - Does the brief include CSS Recreation Blocks for every section? → YES required
> - Does the brief list every asset with its exact public path? → YES required
> - Does the brief document every interaction with timing? → YES required
> - Does the brief specify responsive behavior at every breakpoint? → YES required
>
> If any answer is NO, the brief is incomplete. Go back and fill the gap.

---

## Anti-Patterns — Do NOT Do These

1. **Guessing responsive behavior** — Every breakpoint change must trace to a real `@media` query from the CSS. If you can't find the media query, the breakpoint doesn't exist.

2. **Using Tailwind defaults** — Use ONLY values that trace to real extracted CSS. `text-blue-500` is wrong unless the actual color happens to be `#3b82f6`. Use `text-[#5E6AD2]` or better, reference `tokens.ts`: `text-brand-primary`.

3. **Omitting animation details** — "it fades in" is not a spec. Every animation needs: property, from-value, to-value, duration (ms), easing (exact function), trigger, and delay.

4. **Skipping dark mode** — If the source CSS has dark mode variables (`:root[data-theme="dark"]`, `@media (prefers-color-scheme: dark)`), document BOTH modes for every color in every section.

5. **Describing instead of specifying** — ❌ "large heading" → ✅ "64px / Inter Display / 700 / 1.08 / -0.02em / `var(--color-text-primary)`"

6. **Missing the CSS Recreation Block** — This is the MOST IMPORTANT section per section. Without it, Wave 4 agents are guessing and will produce wrong output. Write the complete CSS.

7. **Forgetting asset references** — Every `<img>`, every SVG icon, every background image must appear in the Asset Reference Table with exact paths.

8. **Incomplete element inventory** — Walk the DOM top-to-bottom and count every visible element. Missing an element = missing it in the build. Interactive elements (buttons, links, inputs) are especially critical.

9. **Approximate values** — ❌ "about 120px padding" → ✅ "padding-top: 120px (from `.hero { padding: 120px 0 }` in deobfuscated.css line 234)"

10. **Forgetting z-index context** — Overlapping elements (sticky nav, modals, tooltips, floating CTAs) need explicit z-index values from the extraction. Document the stacking order.

---

## Output Files

When complete, the Wave 2 agent writes:

### `wave2/{page}/agent-brief.md`

This file — the complete build brief for one page, following this template exactly.

### `wave2/{page}/done.signal`

Empty file written only after `agent-brief.md` passes the coverage, grounding, and self-containment checks above. Keep any completion notes in the brief itself; the signal file remains empty so every wave can use simple existence checks consistently.

┌──────────────────────────────────────────────────────────────────┐
│  A Wave 2 brief is ONLY complete when every section has:         │
│  1. ASCII anatomy (desktop + mobile)                             │
│  2. Complete element inventory (every visible element)           │
│  3. Full typography table with responsive columns                │
│  4. Full color table with light/dark + variable resolution       │
│  5. Spacing diagram with exact values                            │
│  6. States & variants table (every interactive element)          │
│  7. CSS Recreation Block (complete, tested CSS)                  │
│  8. Responsive behavior table (every breakpoint)                 │
│  9. Next.js implementation hints                                 │
│  Missing ANY of these = incomplete brief = broken Wave 4 build.  │
└──────────────────────────────────────────────────────────────────┘
