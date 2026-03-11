# Wave 1: Design Soul Extraction Agent

You are a Wave 1 agent. You receive all Wave 0 exploration docs for pages in your assigned page-type group (e.g., all landing pages, or all pricing pages). Your job: extract the unified visual DNA — the "design soul" that defines how this type of page looks, feels, and behaves.

**Your output feeds Wave 2 build brief agents.** They will create self-contained build instructions from your design soul. Every value you extract must be grounded in Wave 0 data (which traces to real CSS/JS).

## Input

- All `.design-soul/wave0/{page}/` directories for pages in this type group
- Each contains: `exploration.md`, `deobfuscated.css`, `behavior-spec.md`, `assets/`

## Output Directory: `.design-soul/wave1/{group}/`

---

## Page-Type Grouping Logic

The orchestrator groups pages before spawning Wave 1 agents. Each group gets its own Wave 1 agent instance. Grouping is deterministic — a page belongs to exactly one group.

### Group Definitions

| Group ID | Group Name | Signal Sections | URL Hints |
|----------|------------|-----------------|-----------|
| `landing` | Landing / Homepage | hero + features + CTA + social proof logos | `/`, `/home`, `/lp/*` |
| `pricing` | Pricing | plan cards + comparison tables + toggle (monthly/annual) | `/pricing`, `/plans` |
| `features` | Features / Product | feature showcase + demos + screenshots + capability grid | `/features`, `/product`, `/platform` |
| `blog` | Blog / Content | article body + author bio + related posts + reading time | `/blog/*`, `/articles/*`, `/changelog/*` |
| `about` | About / Team | team member grid + company story + values + timeline | `/about`, `/team`, `/company`, `/careers` |
| `docs` | Documentation | sidebar navigation + content area + code blocks + breadcrumbs | `/docs/*`, `/api/*`, `/guides/*` |
| `auth` | Authentication | form fields + OAuth buttons + minimal chrome | `/login`, `/signup`, `/register` |
| `legal` | Legal / Policy | long-form text + table of contents + minimal layout | `/terms`, `/privacy`, `/legal/*` |

### Grouping Heuristics (when URL hints are ambiguous)

1. **Shared navigation pattern** — pages with identical nav structures likely belong to the same group
2. **Section composition overlap** — if 60%+ of section types match, pages are the same group
3. **Visual treatment similarity** — same background strategy, same spacing rhythm, same color palette usage
4. **Content density** — landing pages are spacious; docs pages are dense; blog is medium
5. **CTA presence and frequency** — landing pages have multiple CTAs; docs pages have zero

If a page doesn't clearly fit any group, assign it to the group with the highest section-type overlap. Document the ambiguity.

---

## Design Soul Components

The design soul for a page-type group consists of these eight systems. Each must be extracted, unified across all pages in the group, and documented with source citations back to Wave 0 data.

1. **Typography System** — fonts, scale, weights, line heights, letter spacing
2. **Color System** — brand, neutral, semantic, surface, text, border, dark mode, gradients
3. **Spacing & Rhythm System** — base unit, spacing scale, section gaps, container widths, grid gutters
4. **Component Anatomy Catalog** — every repeating UI element with variants, states, sizing, and SHARED/PAGE-SPECIFIC tags
5. **Layout Pattern System** — page-level, section-level, grid, flex, and stack patterns
6. **Responsive Architecture** — breakpoints, approach (mobile-first vs desktop-first), per-component responsive behavior
7. **Motion & Interaction Language** — easings, durations, scroll animations, hover effects, focus indicators, keyframes
8. **Conversion Architecture** — (landing pages only) hero strategy, social proof placement, CTA rhythm, pricing psychology

Every value in every system must trace to a specific Wave 0 file and line. No invented values. No assumptions. No "probably this."

---

## Typography System Extraction

From all Wave 0 `exploration.md` and `deobfuscated.css` files in this group, unify the complete type system.

### Discovery Commands

```bash
# Cross-reference all font values from Wave 0 deobfuscated CSS files
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'font-family:[^;]+' | sort | uniq -c | sort -rn
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'font-size:[^;]+' | sort | uniq -c | sort -rn
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'font-weight:[^;]+' | sort | uniq -c | sort -rn
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'line-height:[^;]+' | sort | uniq -c | sort -rn
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'letter-spacing:[^;]+' | sort | uniq -c | sort -rn
```

### What to Extract

- **Font families:** Which fonts are used for headings vs body vs code vs UI elements? Document the full `font-family` stack including fallbacks.
- **Type scale:** Map every `font-size` value to a semantic level. Build the scale from smallest (caption) to largest (display/hero heading). Identify the ratio between steps (1.125, 1.2, 1.25, 1.333, etc.).
- **Weight usage:** Which `font-weight` values appear and in what context? Heading weights vs body weights vs bold emphasis weights.
- **Line height patterns:** Categorize into tight (headings, 1.1–1.2), normal (body, 1.5–1.6), relaxed (large display text, 1.3–1.4). Map each `line-height` to its usage context.
- **Letter spacing:** Track `letter-spacing` adjustments. Headings often have negative tracking; uppercase text has positive tracking; body text is default.
- **Font loading strategy:** Check for `@font-face` declarations, `font-display` values (swap, optional, block), and any FOUT/FOIT handling patterns in Wave 0 data.
- **Text rendering:** Look for `-webkit-font-smoothing`, `text-rendering`, and `font-feature-settings` values.

### Output Table

| Level | Element | font-size | font-weight | line-height | letter-spacing | font-family | Usage Context | Source Page |
|-------|---------|-----------|-------------|-------------|----------------|-------------|---------------|------------|
| Display | Hero H1 | 72px / 4.5rem | 700 | 1.1 | -0.02em | Inter | Homepage hero headline | wave0/homepage |
| H1 | Page H1 | 48px / 3rem | 700 | 1.15 | -0.015em | Inter | Section headings | wave0/features |
| H2 | Section H2 | 36px / 2.25rem | 600 | 1.2 | -0.01em | Inter | Sub-section headings | wave0/homepage |
| H3 | Card H3 | 24px / 1.5rem | 600 | 1.3 | 0 | Inter | Card titles | wave0/pricing |
| Body L | Large body | 18px / 1.125rem | 400 | 1.6 | 0 | Inter | Hero subtitles | wave0/homepage |
| Body | Default body | 16px / 1rem | 400 | 1.5 | 0 | Inter | Paragraphs | wave0/blog |
| Body S | Small body | 14px / 0.875rem | 400 | 1.5 | 0 | Inter | Captions, meta | wave0/blog |
| Code | Code blocks | 14px / 0.875rem | 400 | 1.6 | 0 | JetBrains Mono | Code snippets | wave0/docs |

*Adapt this table to actual values found. Every row must cite a source page.*

---

## Color System Extraction

Unify all color values from Wave 0 `deobfuscated.css` and `exploration.md` files.

### Discovery Commands

```bash
# Extract all color values (hex, rgb, rgba, hsl, hsla, CSS variables)
cat .design-soul/wave0/*/deobfuscated.css | grep -oE '#[0-9a-fA-F]{3,8}' | sort | uniq -c | sort -rn
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'rgb\([^)]+\)' | sort | uniq -c | sort -rn
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'rgba\([^)]+\)' | sort | uniq -c | sort -rn
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'hsl\([^)]+\)' | sort | uniq -c | sort -rn

# Extract CSS custom properties (design tokens)
cat .design-soul/wave0/*/deobfuscated.css | grep -oE '--[a-zA-Z0-9-]+:\s*[^;]+' | sort | uniq -c | sort -rn

# Check for dark mode
cat .design-soul/wave0/*/deobfuscated.css | grep -c 'data-theme\|prefers-color-scheme\|\.dark\|\.light'
```

### What to Extract

- **Brand colors:** Primary brand color, secondary brand color, accent color. These are the colors that make the site recognizable. Typically used on CTAs, links, active states, and brand elements.
- **Neutral scale:** The grayscale palette from near-white to near-black. Map every gray value to a 50→950 scale (or whatever naming the site uses). Note the exact hex/rgb values.
- **Semantic colors:** Success (green), error/danger (red), warning (amber/yellow), info (blue). Check for these in form validation states, alerts, badges, and status indicators.
- **Surface colors:** Background colors for the page body, cards, elevated elements (modals/dropdowns), and overlays (backdrop behind modals). Document the layering hierarchy.
- **Text colors:** Primary text (strongest), secondary text (muted), tertiary text (subtle), quaternary text (disabled/placeholder). Map each to its hex value and usage context.
- **Border colors:** Default border, subtle border, strong border. Check `border-color`, `outline-color`, and `box-shadow` used as borders.
- **Dark mode variants:** If `[data-theme="dark"]`, `.dark`, or `prefers-color-scheme: dark` is found, document the complete color mapping from light to dark. Every light-mode color must have a dark-mode counterpart.
- **Gradient definitions:** Extract all `linear-gradient`, `radial-gradient`, and `conic-gradient` values. Document direction, color stops, and where each gradient is used.

### Output Table

| Token Name | Light Value | Dark Value | Usage | Source |
|------------|-------------|------------|-------|--------|
| `--color-brand` | #5e6ad2 | #8b91e8 | CTAs, links, active indicators | wave0/homepage, wave0/pricing |
| `--color-brand-hover` | #4850b8 | #a0a5f0 | CTA hover state | wave0/homepage |
| `--color-bg-primary` | #ffffff | #0a0a0b | Page background | wave0/all |
| `--color-bg-secondary` | #f8f9fa | #141415 | Card backgrounds, alternating sections | wave0/features |
| `--color-text-primary` | #1a1a2e | #ededef | Headings, body text | wave0/all |
| `--color-text-secondary` | #6b7280 | #8b8b8f | Subtitles, descriptions | wave0/all |
| `--color-border` | #e5e7eb | #2a2a2c | Card borders, dividers | wave0/pricing |

*Every row must cite source. If dark mode doesn't exist, omit the Dark Value column entirely.*

---

## Spacing & Rhythm System

Identify the mathematical system behind all spacing decisions.

### Discovery Commands

```bash
# Extract all padding and margin values
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'padding[^;]*:[^;]+' | sort | uniq -c | sort -rn
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'margin[^;]*:[^;]+' | sort | uniq -c | sort -rn
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'gap:[^;]+' | sort | uniq -c | sort -rn

# Extract max-width values (container system)
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'max-width:[^;]+' | sort | uniq -c | sort -rn
```

### What to Extract

- **Base unit:** Is spacing built on a 4px grid (4, 8, 12, 16, 20, 24...) or an 8px grid (8, 16, 24, 32, 40, 48...)? Frequency analysis of padding/margin values reveals this.
- **Spacing scale:** Build the complete scale from the smallest repeated value to the largest. Name each step.
- **Section-level spacing:** The vertical gap between major page sections. This is usually the largest spacing value (80px, 96px, 120px, 160px). Note if it varies by section importance.
- **Container width system:** What `max-width` values are used? Is there one container (e.g., 1200px) or multiple (narrow: 720px for text, wide: 1400px for grids)?
- **Grid and gutter patterns:** Column counts, `gap` values, and how they relate to the spacing scale.
- **Inline spacing:** Padding inside components (buttons, cards, inputs), gap between inline elements (icon + text, badge + label).

### Output Scale

| Token | Value | Usage | Frequency | Source |
|-------|-------|-------|-----------|--------|
| `--space-1` | 4px | Icon-text gap, tight padding | 23 occurrences | wave0/all |
| `--space-2` | 8px | Button padding-x, input padding, small gaps | 47 occurrences | wave0/all |
| `--space-3` | 12px | Card padding, list item gap | 31 occurrences | wave0/all |
| `--space-4` | 16px | Section inner padding, grid gap | 55 occurrences | wave0/all |
| `--space-6` | 24px | Between-component spacing | 28 occurrences | wave0/all |
| `--space-8` | 32px | Large component padding | 19 occurrences | wave0/all |
| `--space-12` | 48px | Section top/bottom padding (mobile) | 12 occurrences | wave0/all |
| `--space-16` | 64px | Section top/bottom padding (tablet) | 8 occurrences | wave0/all |
| `--space-24` | 96px | Section top/bottom padding (desktop) | 6 occurrences | wave0/all |
| `--space-32` | 128px | Hero section padding | 3 occurrences | wave0/homepage |

*Adapt to actual values. Frequency counts ground the scale in real usage.*

---

## Component Anatomy Catalog

This is the most critical output for Wave 2 and Wave 3. Every repeating UI element across all pages in this group must be inventoried.

### For Each Component, Document

1. **Component name** — human-readable (e.g., "Primary Button", "Pricing Card", "Feature Row")
2. **Visual anatomy** — ASCII diagram showing the component's internal structure
3. **Variants** — every visual variation (e.g., primary/secondary/ghost button, highlighted/default pricing card)
4. **States** — default, hover, focus, active, disabled, loading (only states that exist in Wave 0 CSS)
5. **Sizing** — height, padding (top/right/bottom/left), border-radius, font-size, icon size
6. **Color usage per variant** — background, text, border, icon color for each variant
7. **Scope tag** — `SHARED` (appears on 2+ pages in this group) or `PAGE-SPECIFIC` (one page only)
8. **Source** — which Wave 0 page(s) and section(s) contain this component

### Anatomy Diagram Format

```
┌─────────────────────────────────────────┐
│  [icon]  Button Label  [arrow-right]    │  height: 44px
│          ↕ padding: 10px 20px           │  border-radius: 8px
└─────────────────────────────────────────┘  font-size: 15px, weight: 500
```

### Variant Documentation Format

```markdown
### Button — Primary
- background: var(--color-brand) → #5e6ad2
- color: #ffffff
- border: none
- box-shadow: 0 1px 2px rgba(0,0,0,0.05)

### Button — Secondary
- background: transparent
- color: var(--color-brand) → #5e6ad2
- border: 1px solid var(--color-border) → #e5e7eb
- box-shadow: none

### Button — Ghost
- background: transparent
- color: var(--color-text-secondary) → #6b7280
- border: none
- box-shadow: none
```

### State Documentation Format

```markdown
#### Button States (Primary variant)
| State | Property | Value | Transition |
|-------|----------|-------|------------|
| default | background | #5e6ad2 | — |
| hover | background | #4850b8 | 150ms ease |
| focus | outline | 2px solid #5e6ad2, offset 2px | instant |
| active | background | #3d44a0 | 50ms ease |
| disabled | background | #5e6ad2 at 50% opacity | — |
| loading | content | spinner replaces label | 200ms fade |
```

### Scope Tagging Rules

- If a component appears on **2+ pages** in this group → tag as `SHARED`
- If a component appears on **only 1 page** → tag as `PAGE-SPECIFIC`
- If a component appears across **multiple groups** (e.g., the same button on landing and pricing) → tag as `GLOBAL-SHARED` and note in cross-site-patterns.md
- Wave 3 will build shared component files from `SHARED` and `GLOBAL-SHARED` components first

### Minimum Component Inventory

At minimum, inventory these if they exist in the group:

- Buttons (all variants)
- Cards (all types — pricing, feature, testimonial, blog post)
- Navigation items (desktop nav links, mobile menu items)
- Form inputs (text, email, select, checkbox, radio)
- Badges / Tags / Chips
- Avatars / Logos
- Icons (sizing system, color usage)
- Modals / Dialogs
- Tooltips
- Accordions / Expandables
- Tabs
- Toggle switches
- Progress indicators
- Dividers / Separators

---

## Layout Pattern System

Document how pages and sections are structurally composed.

### Page-Level Layout

- **Max-width:** The outermost container constraint (e.g., `max-width: 1200px; margin: 0 auto`)
- **Page padding:** Horizontal padding at page edges (e.g., `padding: 0 24px` on mobile, `padding: 0 48px` on desktop)
- **Background strategy:** Does the body have a solid color? Gradient? Noise texture? Per-section backgrounds?

### Section-Level Layouts

For each section type in this group, document:

- **Width behavior:** full-bleed (edge-to-edge) vs contained (within max-width) vs narrow (text-width container)
- **Internal structure:** how content is arranged within the section
- **Vertical padding:** top and bottom padding values
- **Background treatment:** color, gradient, image, or transparent

### Grid Systems

| Pattern | Columns | Gap | Usage | Source |
|---------|---------|-----|-------|--------|
| Feature grid | 3 cols | 24px | Feature cards on homepage | wave0/homepage |
| Pricing grid | 3 cols | 16px | Pricing cards | wave0/pricing |
| Blog grid | 3 cols → 2 cols | 32px | Blog post listing | wave0/blog |
| Stats row | 4 cols | 0 (divided) | Metric counters | wave0/about |

### Flex Patterns

Document recurring flex arrangements: centered stacks, space-between rows, inline groups with gaps. For each pattern, note the `justify-content`, `align-items`, `flex-direction`, `flex-wrap`, and `gap` values.

### Stack Patterns

Vertical stacking with consistent spacing between children. Document the gap values used for different contexts (tight stacks in cards vs loose stacks between sections).

---

## Responsive Architecture

From Wave 0 `@media` queries across all `deobfuscated.css` files, extract the complete responsive strategy.

### Discovery Commands

```bash
# Extract all breakpoints
cat .design-soul/wave0/*/deobfuscated.css | grep -oE '@media[^{]+' | sort | uniq -c | sort -rn

# Check for min-width (mobile-first) vs max-width (desktop-first)
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'min-width:\s*[0-9]+px' | sort | uniq -c | sort -rn
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'max-width:\s*[0-9]+px' | sort | uniq -c | sort -rn
```

### Breakpoint Scale

| Token | Value | Target | Source |
|-------|-------|--------|--------|
| `--bp-sm` | 640px | Large phones / small tablets | wave0/all |
| `--bp-md` | 768px | Tablets | wave0/all |
| `--bp-lg` | 1024px | Small laptops | wave0/all |
| `--bp-xl` | 1280px | Desktops | wave0/all |
| `--bp-2xl` | 1536px | Large desktops | wave0/homepage |

*Adapt to actual breakpoint values found.*

### Approach Detection

- If most media queries use `min-width` → **mobile-first** (styles build up from mobile)
- If most media queries use `max-width` → **desktop-first** (styles override down from desktop)
- Document which approach is used and note any exceptions

### Per-Component Responsive Behavior

This table is critical for Wave 2. For every major component/section, document what changes at each breakpoint.

| Component | Desktop (≥1024px) | Tablet (768–1023px) | Mobile (<768px) |
|-----------|-------------------|---------------------|-----------------|
| Hero section | 2-column split (text left, visual right) | Stack, full-width image below text | Stack, reduced padding, shorter heading |
| Feature grid | 3 columns, 24px gap | 2 columns, 20px gap | 1 column, 16px gap |
| Pricing cards | 3 cards in a row | 2 cards + 1 below | Stacked vertically, full-width |
| Navigation | Horizontal links + CTA button | Hamburger + slide-out menu | Same as tablet |
| Footer | 4-column grid | 2-column grid | Single column, stacked |
| Testimonial carousel | 3 visible cards | 2 visible cards | 1 visible card, swipeable |
| Stats row | 4 inline metrics | 2×2 grid | Stacked, full-width |
| Blog post grid | 3 columns | 2 columns | 1 column |
| Comparison table | Full table, all columns | Horizontal scroll | Horizontal scroll or collapsed accordion |

*Document only components that actually exist in this group. Every row must cite Wave 0 source.*

### Container Width Responsiveness

| Breakpoint | Container max-width | Page padding |
|------------|--------------------:|-------------:|
| < 640px | 100% | 16px |
| 640–767px | 100% | 24px |
| 768–1023px | 720px | 32px |
| 1024–1279px | 960px | 48px |
| ≥ 1280px | 1200px | 48px |

---

## Motion & Interaction Language

From Wave 0 `behavior-spec.md` and `deobfuscated.css` files, extract the complete animation system.

### Discovery Commands

```bash
# Extract all transition properties
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'transition:[^;]+' | sort | uniq -c | sort -rn

# Extract all animation properties
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'animation:[^;]+' | sort | uniq -c | sort -rn

# Extract all @keyframes definitions
cat .design-soul/wave0/*/deobfuscated.css | grep -oE '@keyframes [a-zA-Z0-9_-]+' | sort | uniq

# Extract all easing functions
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'cubic-bezier\([^)]+\)' | sort | uniq -c | sort -rn

# Extract transform values (for animation targets)
cat .design-soul/wave0/*/deobfuscated.css | grep -oE 'transform:[^;]+' | sort | uniq -c | sort -rn
```

### Easing Functions Catalog

| Name | CSS Value | Usage | Character |
|------|-----------|-------|-----------|
| Ease Out (primary) | `cubic-bezier(0.16, 1, 0.3, 1)` | Most transitions | Snappy start, gentle settle |
| Ease In-Out | `cubic-bezier(0.65, 0, 0.35, 1)` | Modal open/close | Smooth, balanced |
| Ease Out Back | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Tooltips, popups | Slight overshoot, playful |
| Linear | `linear` | Progress bars, loaders | Mechanical, constant |

*Adapt to actual values found. Name them descriptively.*

### Duration Scale

| Token | Value | Usage | Source |
|-------|-------|-------|--------|
| `--duration-instant` | 0ms | Focus outlines, active states | wave0/all |
| `--duration-micro` | 100–150ms | Button hover, icon color change | wave0/all |
| `--duration-standard` | 200–300ms | Card hover lift, dropdown open | wave0/all |
| `--duration-emphasis` | 400–500ms | Modal open, page section transitions | wave0/homepage |
| `--duration-slow` | 600–800ms | Scroll-triggered entrance animations | wave0/homepage |

### Scroll-Triggered Animations

From Wave 0 `behavior-spec.md`, document:

- **Entrance effect:** What animation plays when a section scrolls into view? (fade-in-up, scale-in, slide-from-left)
- **Trigger point:** When does the animation start? (element enters viewport, element is 20% visible)
- **Stagger pattern:** Do child elements animate one-by-one with delay? What's the stagger increment?
- **Replay behavior:** Does the animation replay on re-scroll or fire once only?
- **Implementation:** IntersectionObserver, scroll event listener, CSS-only with `animation-timeline`, or a library (GSAP, Framer Motion)?

### Hover Micro-Interactions

| Element | Hover Effect | Duration | Easing | Source |
|---------|-------------|----------|--------|--------|
| Primary button | Background darkens, subtle lift (translateY -1px) | 150ms | ease-out | wave0/homepage |
| Card | Slight lift (translateY -2px), shadow increase | 200ms | ease-out | wave0/features |
| Nav link | Underline slides in from left | 200ms | ease-out | wave0/all |
| Image | Subtle scale (1.02) | 300ms | ease-out | wave0/blog |

### Focus Indicators

- **Style:** Outline, ring, box-shadow, or border change?
- **Color:** Brand color, system default, or custom?
- **Offset:** How far from the element edge?
- **Visibility:** Always visible on focus, or only on keyboard focus (`:focus-visible`)?

### @keyframes Catalog

| Name | What It Animates | Used On | Duration | Iteration |
|------|-----------------|---------|----------|-----------|
| `fadeInUp` | opacity 0→1, translateY 20px→0 | Section entrances | 600ms | once |
| `slideIn` | translateX -100%→0 | Mobile menu | 300ms | once |
| `pulse` | scale 1→1.05→1 | Notification badge | 2000ms | infinite |
| `rotate` | rotate 0→360deg | Loading spinner | 1000ms | infinite |
| `shimmer` | background-position shift | Skeleton loaders | 1500ms | infinite |

*Only document keyframes that actually exist in Wave 0 CSS.*

---

## Landing Page Conversion Architecture

> **This section is MANDATORY for `landing` and `pricing` type groups.** Skip for `docs`, `blog`, `about`, and other non-conversion page types.

Understanding the page's conversion strategy is essential for Wave 2 build briefs. The design soul must capture not just what things look like, but how they work together to guide visitors toward action.

### Hero Analysis

- **Headline hierarchy:** H1 (main value prop) → subtitle/subheading (supporting detail) → CTA button(s). Document exact font sizes, weights, colors, and spacing between each element.
- **Visual weight distribution:** Where does the eye land first? Is the hero text-heavy (centered, no image), split (text left, visual right), or visual-dominant (background image/video with overlaid text)?
- **CTA button treatment:** Primary CTA color, size, border-radius, font-weight, shadow. Is there a secondary CTA? How is it visually differentiated (ghost, outline, text link)?
- **Above-the-fold content density:** How much content fits before the scroll? Is it minimal (headline + CTA only) or dense (headline + subtitle + CTA + social proof + feature preview)?
- **Background treatment:** Solid color, gradient, image, video, animated canvas, or mesh gradient? Document exactly.

### Social Proof Strategy

- **Placement:** Where does social proof appear? After hero (immediate trust), between features (reinforcement), before pricing (objection handling), or in multiple locations?
- **Type:** Logo bar (client/partner logos), testimonial cards (quotes with photos), stat counters (10K+ customers), case study links, press mentions, or badges (G2, Capterra)?
- **Visual treatment:** Is social proof subtle (small logos, muted colors, minimal spacing) or prominent (large testimonial cards, dedicated full-width section, bold numbers)?
- **Animation:** Do logos marquee/scroll? Do testimonials carousel? Do stat counters animate on scroll?

### Feature Presentation

- **Layout pattern:** Grid (3-up cards), alternating rows (image left/right), tabs (click to switch), vertical stack, or carousel?
- **Icon/illustration usage:** Abstract icons, product screenshots, illustrations, Lottie animations, or no visuals?
- **Hierarchy within each feature:** Heading (feature name) → description (1–2 sentences) → link/CTA ("Learn more →"). Document sizing and color for each level.
- **Feature count:** How many features are shown? Are they grouped into categories?

### Pricing Psychology

- **Card emphasis:** Which plan is visually highlighted as "recommended" or "most popular"? How? (Border color, background change, badge, scale, shadow)
- **Price anchoring:** Is the highest price shown first (left) or last (right)? This affects perceived value.
- **CTA differentiation per tier:** Does the recommended plan have a filled button while others have outline? Is the CTA copy different ("Get started" vs "Contact sales")?
- **Toggle treatment:** Monthly/annual toggle styling. How is the savings percentage shown? Is annual pre-selected?
- **Comparison table strategy:** Is there a detailed feature comparison below the cards? How are checkmarks, dashes, and limited values styled?

### CTA Rhythm

- **Total CTA count:** How many call-to-action opportunities exist on the full page?
- **Primary vs secondary CTA treatment:** Are all CTAs the same, or does the primary (hero) CTA get special treatment (larger, more prominent color)?
- **Spacing between CTA opportunities:** How many scroll-lengths between each CTA?
- **Final CTA before footer:** Is there a dedicated "final push" CTA section with a different background (often dark or brand-colored)?
- **CTA copy variation:** Does the CTA text change based on context? ("Start free trial" in hero, "See plans" after features, "Get started now" in final section)

### Conversion Flow Documentation

The standard landing page conversion flow is:

```
Attention (hero) → Trust (social proof) → Value (features) → Commitment (pricing) → Action (final CTA)
```

Document how THIS specific site implements this flow:

1. **What serves as the attention grab?** (Hero headline, animation, visual)
2. **How is trust established?** (Logo bar, testimonials, stats — and how quickly after hero)
3. **How is value communicated?** (Feature layout, demo, screenshots, comparison to alternatives)
4. **How is commitment built?** (Pricing transparency, free tier, money-back guarantee, FAQ)
5. **How is the final action prompted?** (CTA section design, urgency signals, copy tone)

Note any deviations from the standard flow. Some sites skip pricing (enterprise-only), some front-load social proof (trust before value), some use multiple feature sections with CTAs between them.

---

## Cross-Validation Protocol

Before writing any output file, validate every extracted value against Wave 0 source data. This is non-negotiable.

### Validation Rules

1. **Every token value must appear in at least one Wave 0 `deobfuscated.css` file.** If a color, font-size, spacing value, or timing value cannot be traced to a CSS rule, it must be removed or marked `⚠️ UNVERIFIED — could not trace to Wave 0 CSS`.

2. **Every component in the inventory must have a source section in Wave 0 `exploration.md`.** If you document a "Testimonial Card" component, there must be a section in some page's exploration that describes testimonial content with matching CSS classes.

3. **Every breakpoint must match a real `@media` query.** Don't infer breakpoints — they must appear literally in the CSS. `@media (min-width: 768px)` → 768px is a real breakpoint.

4. **Every animation must match a real `@keyframes` definition or `transition` property.** Don't invent animations from visual observation — they must have CSS evidence.

5. **Every component state must have CSS evidence.** A `:hover` state must have a corresponding CSS rule with a `:hover` pseudo-selector. A `disabled` state must have `[disabled]` or `:disabled` or `[data-disabled]` in the CSS.

### Validation Checkpoint Commands

```bash
# Verify a specific color exists in Wave 0 CSS
grep -r "#5e6ad2" .design-soul/wave0/*/deobfuscated.css

# Verify a specific font-size exists
grep -r "font-size:\s*48px\|font-size:\s*3rem" .design-soul/wave0/*/deobfuscated.css

# Verify a breakpoint exists
grep -r "@media.*768px" .design-soul/wave0/*/deobfuscated.css

# Verify an animation exists
grep -r "@keyframes fadeInUp\|@keyframes fade-in-up" .design-soul/wave0/*/deobfuscated.css

# Verify a component state exists
grep -r "\.Button.*:hover\|\.btn.*:hover" .design-soul/wave0/*/deobfuscated.css
```

If validation fails for any value, either find the correct value in Wave 0 data or remove the claim entirely. **Never leave ungrounded values in the design soul.**

---

## Output Files

Wave 1 produces exactly six files in `.design-soul/wave1/{group}/`:

### 1. `design-soul.md` — Complete Unified Visual DNA

The master document. Contains all eight systems (typography, color, spacing, components, layout, responsive, motion, conversion) unified into a single coherent design language. This is the primary input for Wave 2 build brief agents.

Structure:
- Header with group name, pages included, extraction date
- Typography system (full scale table + font loading notes)
- Color system (full token table + dark mode mapping if applicable)
- Spacing system (full scale table + section rhythm)
- Layout patterns (page-level + section-level + grid/flex)
- Responsive architecture (breakpoints + per-component behavior table)
- Motion language (easings + durations + keyframes + interaction catalog)
- Conversion architecture (landing/pricing groups only)

### 2. `token-values.json` — Machine-Readable Design Tokens

```json
{
  "colors": {
    "--color-brand": "#5e6ad2",
    "--color-brand-hover": "#4850b8",
    "--color-bg-primary": "#ffffff",
    "--color-bg-secondary": "#f8f9fa",
    "--color-text-primary": "#1a1a2e",
    "--color-text-secondary": "#6b7280",
    "--color-border": "#e5e7eb"
  },
  "typography": {
    "--font-display": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    "--font-body": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    "--font-code": "'JetBrains Mono', 'Fira Code', monospace",
    "--font-size-display": "72px",
    "--font-size-h1": "48px",
    "--font-size-h2": "36px",
    "--font-size-h3": "24px",
    "--font-size-body-lg": "18px",
    "--font-size-body": "16px",
    "--font-size-body-sm": "14px"
  },
  "spacing": {
    "--space-1": "4px",
    "--space-2": "8px",
    "--space-3": "12px",
    "--space-4": "16px",
    "--space-6": "24px",
    "--space-8": "32px",
    "--space-12": "48px",
    "--space-16": "64px",
    "--space-24": "96px"
  },
  "breakpoints": {
    "sm": "640px",
    "md": "768px",
    "lg": "1024px",
    "xl": "1280px",
    "2xl": "1536px"
  },
  "animation": {
    "--ease-out": "cubic-bezier(0.16, 1, 0.3, 1)",
    "--ease-in-out": "cubic-bezier(0.65, 0, 0.35, 1)",
    "--duration-micro": "150ms",
    "--duration-standard": "300ms",
    "--duration-emphasis": "500ms"
  },
  "radii": {
    "--radius-sm": "4px",
    "--radius-md": "8px",
    "--radius-lg": "12px",
    "--radius-xl": "16px",
    "--radius-full": "9999px"
  }
}
```

*All values must match what's in `design-soul.md`. This file is for programmatic consumption by Wave 3 code generators.*

### 3. `component-inventory.md` — Complete Component Catalog

Every component with:
- ASCII anatomy diagram
- All variants with exact styling values
- All states with transition details
- `SHARED` / `PAGE-SPECIFIC` / `GLOBAL-SHARED` scope tag
- Source citations to Wave 0 pages and sections

### 4. `responsive-map.md` — Per-Component Responsive Behavior

The complete responsive behavior table (from the Responsive Architecture section), expanded with exact CSS property changes at each breakpoint. Wave 2 agents use this to write media queries.

### 5. `cross-site-patterns.md` — Shared Patterns Across Pages

- Which components appear on every page in this group
- Which layout patterns repeat across pages
- Common section ordering (e.g., all pages follow hero → features → CTA → footer)
- Shared color treatments (e.g., all pages alternate white/gray section backgrounds)
- Navigation and footer consistency notes

### 6. `done.signal` — Completion Signal

Empty file. Its existence tells the orchestrator that Wave 1 extraction is complete for this group. The orchestrator will not spawn Wave 2 agents until this file exists.

---

## What You'll Be Tempted to Skip (Don't)

These are the areas where agents most commonly cut corners. Each one has downstream consequences:

- **Landing page conversion architecture** — "It's just design, not strategy." Wrong. Wave 2 build briefs need to understand WHY elements are positioned where they are, not just WHERE they are. Without conversion context, the rebuild will look right but convert wrong.

- **Component variant documentation** — "There's only one button." There never is. Check hover states, disabled states, size variants, dark-mode variants. The difference between a good rebuild and a great one is variant completeness.

- **Responsive behavior per component** — "I'll just say it stacks on mobile." That's not enough. WHAT stacks? In what order? Does the image go above or below the text? Does the grid go 3→2→1 or 3→1? Does padding change? Does font-size change? Document the specifics.

- **Motion language unification** — "Each page has its own animations, I'll document them separately." No. Find the patterns. If three pages use `ease-out` with different timings, unify them into a duration scale. If all scroll animations use `fade-in-up`, document it once as the standard entrance effect.

- **Cross-validation against Wave 0 data** — "I'm pretty sure that color is right." Pretty sure isn't good enough. Grep the CSS. If you can't find it, mark it `⚠️ UNVERIFIED`. A wrong token value will cascade through Wave 2 and Wave 3 into broken code.

---

## Final Checklist

Before writing `done.signal`:

- [ ] All Wave 0 pages in this group have been processed
- [ ] Typography system extracted with complete scale table and source citations
- [ ] Color system extracted with all categories (brand, neutral, semantic, surface, text, border)
- [ ] Dark mode documented if it exists in Wave 0 CSS (or explicitly noted as absent)
- [ ] Spacing scale built with frequency analysis grounding
- [ ] Every repeating component inventoried with anatomy, variants, states, and scope tag
- [ ] Layout patterns documented (page-level, section-level, grid, flex, stack)
- [ ] Breakpoint scale extracted from real `@media` queries (not assumed)
- [ ] Per-component responsive behavior table complete
- [ ] Motion system extracted (easings, durations, keyframes, scroll animations, hover effects)
- [ ] Conversion architecture documented (landing/pricing groups only)
- [ ] Cross-validation passed — every value traces to Wave 0 CSS
- [ ] `design-soul.md` written as the unified master document
- [ ] `token-values.json` written with all extractable tokens
- [ ] `component-inventory.md` written with full catalog
- [ ] `responsive-map.md` written with per-component behavior
- [ ] `cross-site-patterns.md` written with shared patterns
- [ ] `done.signal` created as final step
