---
name: convert-snapshot-nextjs
description: Use skill if you are converting saved HTML snapshots into buildable Next.js pages with self-hosted assets and extracted styles.
---

# Snapshot to Next.js

**Convert saved HTML pages into pixel-perfect Next.js projects**

**Mission:** Take saved HTML snapshots — produced by browser "Save As", wget, HTTrack, SingleFile, or any offline capture tool — and convert them into a fully buildable Next.js App Router project with zero third-party dependencies.

The pipeline can also produce intermediate design documentation (Waves 0–2 only) when a full build isn't needed yet.

This is not a summarizer. This is not a screenshot describer. This is a forensic CSS parser that reads every minified rule, decodes every CSS Module class name, resolves every custom property chain, catalogs every `@keyframes` block, and maps every `@media` breakpoint — then builds a production-ready Next.js project from it.

Every design value traces to real CSS/JS from the source snapshot. No approximations. No invented tokens. No "close enough." The downstream builder implements your values **literally** — an unverified guess is worse than an honest gap.

---

## Input Specification

This skill is designed for **saved HTML snapshots** — the kind produced by browser "Save As", wget, HTTrack, SingleFile, or any offline snapshot tool.

### Expected Directory Structure

```
source-pages/
├── {site}-homepage.html              # Full HTML (minified, often 1-2MB)
├── {site}-homepage_files/            # Companion assets folder
│   ├── 06cc9eb5faccd3be.css          # Minified CSS (hashed filenames, 12+ files)
│   ├── 8422-c4149e3ed1566f84.js      # JS bundles (minified)
│   ├── f79251b06e9e...352x352.png    # Images / SVGs / favicons
│   └── Inter-roman.var.woff2         # Font files
├── {site}-pricing.html
├── {site}-pricing_files/
├── {site}-features.html
├── {site}-features_files/
└── ...
```

### Auto-Detection Logic

On first scan of the input directory, detect the input type:

```bash
# Step 1: Find all HTML files
find . -maxdepth 2 -name "*.html" -o -name "*.htm" | sort

# Step 2: Classify each
for f in *.html; do
  base="${f%.html}"
  if [ -d "${base}_files" ]; then
    echo "SNAPSHOT: $f → ${base}_files/ ($(ls ${base}_files/*.css 2>/dev/null | wc -l) CSS files)"
  else
    echo "SINGLEFILE: $f ($(grep -c '<style' "$f" 2>/dev/null) <style> blocks)"
  fi
done
[ -f "package.json" ] && echo "SOURCE REPO: package.json found"
```

### Auto-Detection Table

| Signal | Input Type | Behavior |
|--------|-----------|----------|
| `.html` files + `_files/` directories | Saved snapshot | **Primary mode** — grep minified CSS, decode CSS Module names, extract from companion folders |
| `.html` with `<style>` blocks only, no `_files/` | SingleFile export | **Inline CSS mode** — extract from `<style>` tags within the HTML |
| `package.json` + `src/` directory | Source repository | **Fallback mode** — read component files directly, parse `tailwind.config.*`, follow imports |

### Key Characteristics of Saved Snapshots

- CSS is **MINIFIED** — single-line blobs, 100–400KB each, 12+ files per page
- Filenames are **hashed** (`06cc9eb5faccd3be.css`) — no semantic meaning in filenames
- Class names follow the **CSS Module pattern**: `ComponentName_propertyName__hashCode`
- **CSS custom properties** (`--color-*`, `--font-*`, `--ease-*`) form the design system backbone
- HTML preserves **semantic tags**: `<header>`, `<main>`, `<section>`, `<footer>`, `<nav>`
- Inline `style=""` attributes frequently reference CSS variables via `var(--token-name)`
- Each HTML file represents **one page type** (homepage, pricing, features, about, etc.)
- **Same CSS file** often appears in multiple `_files/` folders — deduplication is mandatory
- JS bundles contain **behavior logic**: scroll animations, intersection observers, dynamic class toggling

---

## Output Specification

The pipeline produces TWO output trees. Extraction-only mode (Waves 0–2) produces the first. Full reconstruction (Waves 0–4) produces both.

### Tree 1: Design Documentation (`.design-soul/`)

```
.design-soul/                                    ← Intermediate extraction docs
├── wave0/                                       ← Per-page deep exploration
│   ├── homepage/
│   │   ├── exploration.md                       # Section inventory + CSS token map + behavior map
│   │   ├── deobfuscated.css                     # Full CSS with semantic class names
│   │   ├── behavior-spec.md                     # JS behaviors as declarative specs
│   │   ├── assets/                              # Downloaded fonts, images, icons, videos
│   │   │   ├── fonts/
│   │   │   ├── images/
│   │   │   └── icons/
│   │   └── done.signal                          # Empty file = this agent completed
│   ├── pricing/
│   │   ├── exploration.md
│   │   ├── deobfuscated.css
│   │   ├── behavior-spec.md
│   │   ├── assets/
│   │   └── done.signal
│   └── {additional-pages}/
├── wave1/                                       ← Design soul per page-type group
│   ├── landing/
│   │   ├── design-soul.md                       # Unified visual DNA for this group
│   │   ├── token-values.json                    # Machine-readable tokens (all traced)
│   │   ├── component-inventory.md               # Every repeating UI element
│   │   ├── responsive-map.md                    # Breakpoint behavior per component
│   │   ├── cross-site-patterns.md               # Patterns shared across pages in group
│   │   └── done.signal
│   └── {additional-groups}/
├── wave2/                                       ← Build briefs per page
│   ├── homepage/
│   │   ├── agent-brief.md                       # Self-contained build instructions
│   │   └── done.signal
│   ├── pricing/
│   │   ├── agent-brief.md
│   │   └── done.signal
│   └── {additional-pages}/
└── wave3/                                       ← Design system foundation docs
    ├── foundation-brief.md                      # How Wave 4 agents use the design system
    ├── traceability-matrix.md                   # Token → Wave 2 brief → Wave 0 source
    └── foundation-ready.signal                  # ONLY written after quality gate passes
```

### Tree 2: Buildable Next.js Project (`nextjs-project/`)

```
nextjs-project/                                  ← Buildable project (Waves 3–4 only)
├── app/                                         # App Router page routes
│   ├── layout.tsx                               # Root layout with fonts + global styles
│   ├── page.tsx                                 # Homepage
│   ├── pricing/page.tsx                         # Pricing page
│   └── {additional-routes}/page.tsx
├── components/
│   ├── shared/                                  # Shared components (header, footer, CTA)
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   └── ...
│   └── pages/                                   # Page-specific components
│       ├── homepage/
│       │   ├── Hero.tsx
│       │   ├── FeatureGrid.tsx
│       │   └── ...
│       └── pricing/
│           ├── PlanCards.tsx
│           ├── ComparisonTable.tsx
│           └── ...
├── lib/
│   ├── tokens.ts                                # Typed design tokens from REAL CSS
│   └── animations.ts                            # Animation utilities from extracted @keyframes
├── styles/
│   └── globals.css                              # @font-face declarations + CSS custom properties
├── public/
│   └── assets/                                  # Self-hosted fonts, images, icons
│       ├── fonts/
│       ├── images/
│       └── icons/
├── tailwind.config.ts                           # Extended with REAL extracted values
├── postcss.config.js                            # Standard PostCSS with Tailwind + autoprefixer
├── package.json                                 # ONLY: next, react, react-dom, typescript, tailwindcss
├── tsconfig.json                                # strict: true
└── next.config.js                               # Minimal Next.js config
```

---

## Philosophy: Seven Principles

### 1. Parse, Don't Guess

CSS is minified but **COMPLETE**. Every value the browser renders exists somewhere in those `.css` files. Use `grep -oE` with regex patterns to extract values programmatically. Never infer from visual appearance. Never assume based on "what looks like 16px." If a value cannot be found in CSS/HTML, mark it `UNVERIFIED` — do not invent it.

### 2. CSS Module Names Are Your Map

The CSS Module naming convention is the most reliable section identifier in saved snapshots:

```
Header_root__x8J2p          → Component: Header,         Element: root
Plans_card__SCfoV            → Component: Plans,          Element: card
CTA_sectionPrefooter__kW_wF → Component: CTA,            Element: sectionPrefooter
CustomerMarquee_logos__abc   → Component: CustomerMarquee, Element: logos
```

The **prefix before the first underscore** IS the section identifier — more reliable than HTML nesting, more precise than semantic tags. This is your primary map.

### 3. Every Page Is a Page Type

Each `.html` file represents exactly one page type. `linear-homepage.html` → page type "homepage". `stripe-pricing.html` → page type "pricing". Document and extract each independently. Cross-page analysis happens in Wave 1 after individual extraction.

### 4. CSS Variables Are the Design System

Custom properties (`--color-brand-bg`, `--font-weight-medium`, `--ease-out-quad`) declared in `:root` or `[data-theme]` selectors ARE the foundation tokens. They are the skeleton that every section references. Extract them FIRST — the entire downstream pipeline depends on resolved token values.

### 5. Shared Sections, Documented Once

Header and Footer appear on every page. Navigation may be identical or vary slightly per page (transparent vs. solid header). Document the base version once, note page-specific variations as overrides. Never duplicate full documentation across pages.

### 6. Build What You Extract

Every documented value becomes runnable code. If it's in the design soul docs, it goes in the Next.js project. No "aspirational" documentation. No tokens that don't map to real CSS. The documentation IS the specification for the build — they must be 1:1.

### 7. Zero External Dependencies

The final Next.js project uses ONLY these packages: `next`, `react`, `react-dom`, `typescript`, `tailwindcss`, `@types/react`, `@types/node`, `postcss`, `autoprefixer`. No CDN fonts — self-host them. No icon libraries — inline SVGs. No animation libraries — CSS transitions and @keyframes only. No component libraries — build from scratch using extracted specs. All assets self-hosted in `public/`.

---

## The Grounding Rule (Non-Negotiable)

Every value documented in any wave must trace to exactly one of these sources:

1. **A CSS rule** in a `_files/*.css` file — cite the filename and selector
2. **A CSS custom property declaration** in `:root` or `[data-theme]` — cite the filename and selector
3. **An inline `style=""` attribute** in the HTML — cite the element and attribute
4. **A `<style>` block** in the HTML — cite the block context
5. **A `@keyframes` or `@media` rule** in CSS — cite the filename and rule name

If you cannot find a source for a value:
- Mark it as `UNVERIFIED — not found in snapshot CSS/HTML`
- Do NOT invent "close enough" values
- Do NOT round to convenient numbers (e.g., "roughly 16px" → NO)
- Do NOT assume a value matches a common design framework default

The downstream builder implements your values **literally**. An unverified guess produces a wrong pixel. An honest gap produces a searchable TODO.

---

## Section Identification Hierarchy

When identifying sections within a page, follow this priority order:

1. **Semantic HTML tags** — `<header>`, `<main>`, `<section>`, `<footer>`, `<nav>` are first-class section markers. These are the most reliable structural boundaries.

2. **CSS Module class prefixes** — `Header_`, `Hero_`, `Plans_`, `CTA_`, `Footer_` — each unique prefix corresponds to a distinct visual section. The prefix IS the component name.

3. **Structure heuristics** (fallback only) — When neither semantic tags nor CSS Module prefixes are available, fall back to large container elements with distinct visual boundaries (background color changes, significant padding shifts, full-width dividers).

Extract the prefix map from any page:

```bash
grep -oE '[A-Z][a-zA-Z]+_[a-zA-Z]+__[a-zA-Z0-9]+' page.html | sed 's/_[a-zA-Z]*__[a-zA-Z0-9]*$//' | sort -u
```

This produces a clean list of component names present on that page. Cross-reference with the `references/website-patterns.md` catalog for section-type mapping.

---

## CSS Module Decoding

### Pattern

```
ComponentName_propertyName__hashCode
```

### Decoding Table

| Raw Class | Component | Element | Hash (ignore) |
|-----------|-----------|---------|---------------|
| `Header_root__x8J2p` | Header | root | x8J2p |
| `Header_nav__abc12` | Header | nav | abc12 |
| `Hero_headline__Kz9mQ` | Hero | headline | Kz9mQ |
| `Plans_card__SCfoV` | Plans | card | SCfoV |
| `Plans_price__3xR7t` | Plans | price | 3xR7t |
| `CTA_sectionPrefooter__kW_wF` | CTA | sectionPrefooter | kW_wF |
| `Footer_links__m2nP4` | Footer | links | m2nP4 |
| `CustomerMarquee_logos__Yp8sK` | CustomerMarquee | logos | Yp8sK |

### Utility Prefixes (NOT Sections)

Some CSS Module prefixes are **utility classes**, not section identifiers:

| Prefix | Type | Meaning |
|--------|------|---------|
| `Flex_` | Utility | Flexbox layout helper |
| `Grid_` | Utility | CSS Grid layout helper |
| `Container_` | Utility | Width constraint wrapper |
| `Spacer_` | Utility | Spacing utility |
| `Text_` | Utility | Typography utility |
| `Icon_` | Utility | Icon sizing/alignment utility |

These appear INSIDE sections but do not define section boundaries. Filter them out when building the section inventory.

---

## Wave 0 — Per-Page Deep Exploration & Deobfuscation

**Trigger:** Orchestrator scans `source-pages/` and finds `.html` files with `_files/` companion directories
**Agents:** 1 per page (ALL run in parallel)
**Input:** One `{page}.html` + its `{page}_files/` folder
**Output:** `.design-soul/wave0/{page}/`

### Pre-Flight: Input Scan

Before spawning agents, the orchestrator must:

```bash
# 1. Inventory all pages
find source-pages/ -maxdepth 1 -name "*.html" | sort

# 2. Verify companion folders exist
for f in source-pages/*.html; do
  base="${f%.html}"
  if [ -d "${base}_files" ]; then
    css_count=$(ls "${base}_files"/*.css 2>/dev/null | wc -l)
    js_count=$(ls "${base}_files"/*.js 2>/dev/null | wc -l)
    echo "READY: $(basename $f) → ${css_count} CSS, ${js_count} JS"
  else
    echo "WARNING: $(basename $f) has no _files/ companion"
  fi
done

# 3. Deduplicate CSS across all _files/ folders
find source-pages/ -name "*.css" -path "*_files*" -exec md5 -r {} \; | sort | uniq -d -w 32
```

### Agent Spawning

For EACH `.html` file found, spawn one Wave 0 agent with:
- Path to the `.html` file
- Path to its `_files/` folder
- Shared CSS dedup map (so agents don't re-process identical files)
- Instruction: "Read `references/foundations-agent.md` and execute Wave 0 extraction for this page"

### What Each Agent Produces

1. **`exploration.md`** — Complete section inventory with:
   - Ordered list of every section found (top → bottom)
   - CSS Module prefix map with element counts per prefix
   - CSS token map: every custom property used, its declaration, its resolved value
   - Responsive behavior map: what changes at each `@media` breakpoint
   - Animation catalog: every `@keyframes`, `transition`, and `transform` with trigger context
   - Font inventory: every `font-family` + `@font-face` source
   - Color inventory: every unique color value (hex, rgb, hsl, custom property)

2. **`deobfuscated.css`** — ALL CSS from `_files/*.css` files:
   - Concatenated into a single file
   - Deduplicated (identical rules removed)
   - Obfuscated class names mapped to semantic names via comment annotations
   - Example: `.Plans_card__SCfoV { ... }` → annotated as `/* Section: Plans, Element: card */`

3. **`behavior-spec.md`** — JS behaviors documented as declarative specifications:
   - Each behavior: trigger → target element → effect → timing → easing
   - Scroll-triggered animations (IntersectionObserver patterns)
   - Hover/focus/active state changes driven by JS class toggling
   - Dynamic content loading (lazy images, deferred sections)
   - Navigation behavior (mobile menu toggle, dropdown logic)
   - NO raw JS code — only declarative specs a builder can implement

4. **`assets/`** — All referenced external assets:
   - `assets/fonts/` — All font files (.woff2, .woff, .ttf) from `@font-face` declarations
   - `assets/images/` — All images referenced in HTML or CSS (backgrounds, heroes, logos)
   - `assets/icons/` — SVG icons extracted from inline SVGs or external references
   - Asset manifest listing source URL → local path for each file

5. **`done.signal`** — Empty file written ONLY after all other outputs are complete

### Completion Gate

Wave 0 is complete when ALL `wave0/{page}/done.signal` files exist. The orchestrator must verify:

```bash
# Count expected vs actual signals
expected=$(find source-pages/ -maxdepth 1 -name "*.html" | wc -l)
actual=$(find .design-soul/wave0/ -name "done.signal" | wc -l)
[ "$expected" -eq "$actual" ] && echo "WAVE 0 COMPLETE" || echo "WAVE 0 INCOMPLETE: $actual/$expected"
```

**Do NOT proceed to Wave 1 until this gate passes.**

---

## Wave 1 — Design Soul Extraction (Page-Type Grouping)

**Trigger:** ALL Wave 0 `done.signal` files exist
**Agents:** 1 per page-type group (ALL run in parallel)
**Input:** All `wave0/` docs for pages in each type group
**Output:** `.design-soul/wave1/{group}/`

### Page-Type Grouping

Before spawning Wave 1 agents, classify every page into a type group:

| Page Indicators | Group Name | Typical Pages |
|----------------|-----------|---------------|
| Hero + feature sections + CTA | `landing` | Homepage, product pages |
| Plan cards + comparison tables | `pricing` | Pricing, plans |
| Feature detail grids + demos | `features` | Features, integrations |
| Blog post layout + article body | `content` | Blog, docs, changelog |
| Team bios + company info | `about` | About, careers, team |
| All sections in one HTML file | `single` | Single-page sites |

Grouping criteria (in priority order):
1. **Shared navigation structure** — same nav items = same group
2. **Section composition overlap** — >60% shared CSS Module prefixes = same group
3. **Visual treatment similarity** — same background pattern, typography scale, spacing rhythm

If only one page exists → group name is `single`.

### Agent Spawning

For EACH page-type group, spawn one Wave 1 agent with:
- List of `wave0/{page}/` directories belonging to this group
- All `exploration.md` files from those directories
- All `deobfuscated.css` files from those directories
- Instruction: "Read `references/sections-agent.md` and extract the unified design soul for this page-type group"

### What Each Agent Produces

1. **`design-soul.md`** — Unified visual DNA for this page-type group:
   - Typography system: font families, weight scale, size scale, line heights, letter spacing
   - Color system: named palette, semantic color roles, dark mode mapping (if present)
   - Spacing system: padding scale, margin patterns, gap values, section rhythm
   - Component anatomy: how each UI element is composed (container → children → leaf)
   - Layout patterns: grid systems, flex patterns, max-width constraints, alignment
   - Responsive architecture: breakpoint strategy, layout shifts, typography scaling
   - Motion language: easing curves, duration scale, trigger patterns, stagger timing

2. **`token-values.json`** — Machine-readable token values:
   ```json
   {
     "colors": { "--color-bg-primary": "#0a0a0a", "source": "homepage_files/06cc9eb.css :root" },
     "typography": { "--font-display": "'Inter', sans-serif", "source": "homepage_files/a3b2c1.css :root" },
     "spacing": { "--section-padding-y": "120px", "source": "homepage_files/06cc9eb.css .Hero_root" },
     "breakpoints": { "tablet": "768px", "desktop": "1024px", "wide": "1280px" }
   }
   ```
   Every value MUST include its source file and selector.

3. **`component-inventory.md`** — Every repeating UI element:
   - Component name (from CSS Module prefix)
   - Anatomy breakdown (root → child elements)
   - Visual variants (if any: primary/secondary, light/dark)
   - Interactive states (hover, focus, active, disabled)
   - Responsive behavior (layout changes per breakpoint)
   - Shared vs. page-specific classification

4. **`responsive-map.md`** — Breakpoint behavior per component:
   - Every `@media` query found in the CSS, sorted by breakpoint
   - What changes at each breakpoint: layout, font sizes, spacing, visibility
   - Mobile-first vs. desktop-first detection
   - Components that hide/show at specific breakpoints

5. **`cross-site-patterns.md`** — Patterns shared across pages in this group:
   - Section ordering conventions (Hero always first, CTA always before Footer)
   - Visual rhythm (alternating light/dark sections, padding consistency)
   - Content density patterns (text-heavy vs. visual-heavy sections)
   - CTA placement strategy (frequency, visual weight, spacing from content)

6. **`done.signal`** — Empty file, written ONLY after all outputs complete

### Landing Page Reality Check

Wave 1 agents processing landing pages and marketing sites must understand these anatomical patterns and document them explicitly:

- **Hero composition** — Headline hierarchy (display → heading → subtext), CTA placement relative to copy, visual weight distribution (text vs. media), background treatment (gradient, image, video, animated)
- **Social proof strategy** — Logo bar position (immediately after hero or deeper), testimonial format (cards, quotes, video), stats/metrics placement, trust signals
- **Feature presentation** — Grid layout vs. alternating left/right, icon usage (inline SVG, custom illustrations), description density, interactive demos
- **Pricing hierarchy** — Card emphasis (which plan is "recommended"), comparison table structure, toggle (monthly/annual), feature differentiation strategy
- **CTA rhythm** — Primary vs. secondary CTA styling, spacing between CTA sections, urgency signals, CTA copy patterns
- **Conversion architecture** — How sections flow toward action: awareness → interest → trust → decision → action

### Completion Gate

Wave 1 is complete when ALL `wave1/{group}/done.signal` files exist.

---

## Wave 2 — Page Build Brief Manufacturing

**Trigger:** ALL Wave 1 `done.signal` files exist
**Agents:** 1 per page (batch: up to 3 same-type pages per agent)
**Input:** `wave1/{group}/` soul docs + `wave0/{page}/` raw data
**Output:** `.design-soul/wave2/{page}/`

### Agent Spawning

For EACH page (or batch of up to 3 same-type pages):
- The relevant `wave1/{group}/design-soul.md` and `token-values.json`
- The page's `wave0/{page}/exploration.md` and `deobfuscated.css`
- The page's `wave0/{page}/behavior-spec.md`
- Instruction: "Read `references/section-template.md` and create a complete, self-contained build brief for this page"

### What Each Agent Produces

1. **`agent-brief.md`** — Self-contained build instructions that follow the Wave 2 template. This document must be **complete enough that a Wave 4 agent can build the page from this brief ALONE**, without accessing Wave 0 or Wave 1 outputs.

2. **`done.signal`** — Written only after the brief passes completeness checks

### Brief Completeness Rule

Every `agent-brief.md` MUST include ALL of the following sections:

| Section | Contents | Why Required |
|---------|----------|-------------|
| Page Identity | Route path, page title, meta description, page type | Builder needs routing and SEO |
| Section Blueprint | Every section top→bottom with full visual spec | Builder needs the complete page structure |
| Component Manifest | Every component tagged SHARED or PAGE-SPECIFIC | Builder knows what to import vs. create |
| Token Reference | All design tokens used on this page with values | Builder doesn't need to look up tokens |
| Asset Reference Table | `wave0/` path → `public/` destination for every asset | Builder knows where every image/font goes |
| Interaction Spec | Every animation/transition: trigger → effect → timing → easing | Builder implements exact motion |
| Responsive Spec | Layout at every breakpoint for every section | Builder handles all screen sizes |
| State Variants | Hover, focus, active, disabled for every interactive element | Builder implements all states |
| Acceptance Criteria | Specific visual assertions that must pass | Builder can self-verify |

### Brief Self-Containment Test

Ask: "If I gave this brief to a developer who has NEVER seen the original website and has NO access to Wave 0 or Wave 1 outputs — could they build a pixel-perfect page?" If not, the brief is incomplete.

### Completion Gate

Wave 2 is complete when ALL `wave2/{page}/done.signal` files exist.

---

## Wave 3 — Design System Foundation & Next.js Scaffold

**Trigger:** ALL Wave 2 `done.signal` files exist
**Agents:** 1 orchestrator agent (may spawn specialist sub-agents for complex tasks)
**Input:** ALL `wave2/` briefs + ALL `wave1/` soul docs
**Output:** `nextjs-project/` scaffold + `.design-soul/wave3/`

### What the Orchestrator Produces

**1. `nextjs-project/` — Complete project scaffold:**

| File/Directory | Contents | Source |
|---------------|----------|--------|
| `package.json` | Dependencies: ONLY next, react, react-dom, typescript, tailwindcss, @types/react, @types/node, postcss, autoprefixer | Wave 3 constraint |
| `tsconfig.json` | `strict: true`, path aliases for `@/components`, `@/lib` | Standard Next.js |
| `tailwind.config.ts` | Extended theme with REAL breakpoints, colors, fonts, spacing from Wave 1 tokens | `wave1/*/token-values.json` |
| `postcss.config.js` | Standard PostCSS: tailwindcss + autoprefixer | Standard |
| `styles/globals.css` | `@font-face` declarations for all self-hosted fonts + CSS custom properties from `:root` | `wave0/*/assets/fonts/` + `wave1/*/token-values.json` |
| `lib/tokens.ts` | Typed TypeScript constants for all design tokens | `wave1/*/token-values.json` |
| `lib/animations.ts` | Animation utility functions from extracted `@keyframes` and transition patterns | `wave0/*/behavior-spec.md` |
| `components/shared/` | Shared component shells (Header, Footer, etc.) with props interfaces | `wave2/*/agent-brief.md` component manifests |
| `app/layout.tsx` | Root layout importing fonts, globals.css, shared header/footer | All wave outputs |
| `app/*/page.tsx` | Route stubs for every page with placeholder content | `wave2/` page list |

**2. `.design-soul/wave3/` — Foundation documentation:**

- **`foundation-brief.md`** — Instructions for Wave 4 agents on how to use the design system:
  - How to import and use `tokens.ts`
  - How to use `animations.ts` utilities
  - How to extend shared components
  - Tailwind class conventions (when to use Tailwind vs. tokens.ts)
  - Responsive approach (mobile-first, breakpoint naming)
  - Asset path conventions (`/assets/fonts/`, `/assets/images/`)

- **`traceability-matrix.md`** — Complete trace from tokens to source:
  ```
  Token Name              → Wave 2 Brief Reference      → Wave 0 Source File
  --color-bg-primary      → homepage/agent-brief.md:L42  → homepage_files/06cc9eb.css :root
  --font-display          → homepage/agent-brief.md:L18  → homepage_files/a3b2c1.css :root
  section-padding-desktop → pricing/agent-brief.md:L67   → pricing_files/8f2a1b.css .Plans_root
  ```

- **`foundation-ready.signal`** — Written ONLY after the quality gate passes

### Foundation Quality Gate

Before writing `foundation-ready.signal`, verify ALL of these conditions:

| Check | Verification Method | Pass Criteria |
|-------|-------------------|---------------|
| Token coverage | Diff `tokens.ts` exports vs. all `wave2/*/agent-brief.md` token references | 100% of referenced tokens exist in `tokens.ts` |
| Shared components | List SHARED-tagged components across all Wave 2 briefs | Every SHARED component has a file in `components/shared/` |
| Breakpoints | Compare `tailwind.config.ts` breakpoints vs. Wave 1 `responsive-map.md` | All source breakpoints represented |
| Font loading | Verify `@font-face` in `globals.css` references files in `public/assets/fonts/` | All fonts self-hosted and loadable |
| Animations | Check `animations.ts` covers all Wave 2 interaction specs | All shared animation patterns defined |
| Zero deps | Read `package.json` dependencies | NO UI libraries, NO animation libraries, NO icon libraries, NO font CDN packages |
| TypeScript | `tsc --noEmit` passes | Zero errors |
| Route stubs | Count `app/*/page.tsx` files vs. Wave 2 page count | Every page has a route |

Read `references/system-template.md` for the complete quality gate specification and scaffold structure.

### Completion Gate

Wave 3 is complete when `.design-soul/wave3/foundation-ready.signal` exists.

---

## Wave 4 — Full Page Build (Pixel-Perfect Reconstruction)

**Trigger:** `.design-soul/wave3/foundation-ready.signal` exists
**Agents:** 1 per page (or per batch of up to 3 same-type pages)
**Input:** `wave2/{page}/agent-brief.md` + `wave3/foundation-brief.md`
**Output:** `app/{route}/page.tsx` + `components/pages/{page}/`

### Agent Spawning

For EACH page (or batch of up to 3 same-type pages), spawn one Wave 4 agent with:
- The page's `wave2/{page}/agent-brief.md` (complete build spec)
- The `wave3/foundation-brief.md` (how to use the design system)
- Path to `nextjs-project/` (the existing scaffold)
- Instruction: "Read the agent-brief and foundation-brief. Build this page using ONLY the Wave 3 design system. Zero external dependencies. Every visual value must match the brief exactly."

### What Each Agent Produces

1. **`app/{route}/page.tsx`** — The page component:
   - Server component by default (add `'use client'` only where interaction requires it)
   - Imports shared components from `@/components/shared/`
   - Imports page-specific components from `@/components/pages/{page}/`
   - Uses tokens from `@/lib/tokens` for any programmatic style values
   - Follows the section stacking order from the agent-brief exactly

2. **`components/pages/{page}/`** — Page-specific components:
   - One component file per section (e.g., `Hero.tsx`, `FeatureGrid.tsx`, `PlanCards.tsx`)
   - TypeScript interfaces for all props
   - Tailwind classes using the extended theme from `tailwind.config.ts`
   - CSS custom properties via inline styles where Tailwind doesn't cover the value
   - Responsive classes matching the agent-brief breakpoint spec

3. **`public/assets/{page}/`** — Page-specific assets:
   - Images copied from `wave0/{page}/assets/images/`
   - Icons copied from `wave0/{page}/assets/icons/`
   - Asset paths matching the agent-brief's asset reference table

### Acceptance Criteria (Per Page)

Every Wave 4 agent must verify these criteria before signaling completion:

| Criterion | Verification |
|-----------|-------------|
| Visual match — desktop (≥1280px) | Layout, typography, colors, spacing match agent-brief at wide viewport |
| Visual match — tablet (768–1279px) | Responsive layout shifts match agent-brief tablet spec |
| Visual match — mobile (≤767px) | Mobile layout, stacking, font scaling match agent-brief mobile spec |
| Interactive states | All hover/focus/active/disabled states match original behavior spec |
| Animations | All scroll-triggered, load, and hover animations fire with correct timing/easing |
| Typography | All fonts render with correct family, weight, size, line-height, letter-spacing |
| Images | All images self-hosted in `public/assets/` and displaying correctly |
| No external requests | Zero network requests to CDNs, Google Fonts, external APIs |
| TypeScript strict | `tsc --noEmit` passes with zero errors |
| Build succeeds | `next build` completes without errors |

---

## Global Fleet Rules

These rules apply across ALL waves and ALL agents:

### Wave Sequencing (STRICT)

```
Wave 0 (all agents) → Gate → Wave 1 (all agents) → Gate → Wave 2 (all agents) → Gate → Wave 3 → Gate → Wave 4 (all agents)
```

No Wave N+1 agent may start until ALL Wave N `done.signal` files exist. This is non-negotiable — each wave depends on the complete output of the previous wave.

### Parallelism Within Waves

Within a single wave, ALL agents run in parallel:
- Wave 0: All page agents simultaneously
- Wave 1: All page-type group agents simultaneously
- Wave 2: All page brief agents simultaneously
- Wave 3: Single orchestrator (may spawn parallel sub-agents internally)
- Wave 4: All page build agents simultaneously

### Signal File Convention

```
.design-soul/wave{N}/{identifier}/done.signal     # Per-agent completion (Waves 0, 1, 2)
.design-soul/wave3/foundation-ready.signal          # Wave 3 completion (single signal)
```

Signal files are EMPTY files. Their existence is the ONLY indicator of completion. An agent must write its signal file LAST, after all other outputs are verified.

### The Grounding Rule (Repeated — It's That Important)

Every value in every document in every wave must trace to real CSS, real HTML, or real JS from the source snapshot. No approximations. No "standard" values. No framework defaults assumed. If you can't find it, mark it `UNVERIFIED`.

### Zero Dependencies Rule

The `nextjs-project/package.json` may contain ONLY:
- `next`
- `react`
- `react-dom`
- `typescript`
- `tailwindcss`
- `@types/react`
- `@types/node`
- `postcss`
- `autoprefixer`

NO exceptions. No `framer-motion`. No `shadcn/ui`. No `@mui/*`. No `@chakra-ui/*`. No `lucide-react`. No `@fontsource/*`. No `gsap`. No `lottie`. Everything is built from scratch using the extracted design specs.

### Consistency Rule

The same token name must mean the same value everywhere:
- `tokens.ts` value = `tailwind.config.ts` extension = `globals.css` custom property = `wave2/*/agent-brief.md` reference
- If a discrepancy is found, trace back to Wave 0 source and use the authoritative value

---

## Request Interpretation Table

How the orchestrator decides which waves to execute based on user intent:

| User Says | Waves Executed | Primary Output |
|-----------|---------------|----------------|
| "Extract the design" | 0 → 1 → 2 | `.design-soul/` documentation only |
| "Document this site" | 0 → 1 → 2 | `.design-soul/` documentation only |
| "Capture the design DNA" | 0 → 1 → 2 | `.design-soul/` documentation only |
| "Rebuild this site" | 0 → 1 → 2 → 3 → 4 | `.design-soul/` + `nextjs-project/` |
| "Recreate this page" | 0 → 1 → 2 → 3 → 4 | `.design-soul/` + `nextjs-project/` |
| "Clone this design" | 0 → 1 → 2 → 3 → 4 | `.design-soul/` + `nextjs-project/` |
| "Reconstruct from snapshot" | 0 → 1 → 2 → 3 → 4 | `.design-soul/` + `nextjs-project/` |
| "Pixel-perfect copy" | 0 → 1 → 2 → 3 → 4 | `.design-soul/` + `nextjs-project/` |
| "Just the tokens" | 0 → 1 | `wave0/` + `wave1/` only |
| "Just the design system" | 0 → 1 | `wave0/` + `wave1/` only |
| "Extract and scaffold" | 0 → 1 → 2 → 3 | `.design-soul/` + `nextjs-project/` scaffold (no page builds) |

### Ambiguity Resolution

If the user's intent is unclear:
1. Default to **Waves 0–2** (extraction only) — it's safe and non-destructive
2. Ask: "I've extracted the design documentation. Would you also like me to rebuild it as a Next.js project? (That would run Waves 3–4)"
3. Never assume reconstruction unless the user explicitly says "build", "rebuild", "recreate", "html to nextjs", "page to react", "convert this design", or "make a nextjs version"

---

## Anti-Patterns

### Extraction Anti-Patterns (Waves 0–2)

#### 1. Trying to "Read" Minified CSS Visually
Thousands of CSS rules on one line, 100KB+ per file. Use `grep -oE` with targeted regex patterns. Never scroll through minified CSS hoping to spot values.

#### 2. Ignoring CSS Custom Properties
`--color-*`, `--font-*`, `--radius-*`, `--ease-*` ARE the design system. They reveal intent — the named tokens composing every section. Skipping them means documenting symptoms, not the system.

#### 3. Treating Each CSS File Independently
12+ CSS files are one system split by the build tool. A selector in one file may reference a variable declared in another. Always grep across ALL `_files/*.css` files simultaneously.

#### 4. Missing the CSS Module Naming Pattern
Not decoding `Plans_card__SCfoV` as "Plans component, card element" means guessing section boundaries from `<div>` nesting. The prefix IS the section identifier — use it.

#### 5. Documenting Only Inline Styles
Inline `style=""` attributes are the tip of the iceberg. The vast majority of styles live in external CSS files matched by class names. Always grep CSS files for the section's prefix before documenting.

#### 6. Assuming Section Boundaries from `<div>` Tags
Nested `<div>` elements don't reliably mark sections. Use semantic HTML tags + CSS Module prefix transitions as your boundary detection mechanism.

#### 7. Skipping Shared Sections
Header and Footer appear on every page but must be documented ONCE, not duplicated. Page-specific variations (transparent vs. solid header on different pages) are critical builder details that must be noted.

#### 8. Not Deduplicating CSS Files
The same hashed CSS file appears in multiple `_files/` folders. Without deduplication, token counts inflate 2×, color palettes appear doubled, and analysis misleads.

### Build Anti-Patterns (Waves 3–4)

#### 9. Using Tailwind Defaults Instead of Extracted Values
Tailwind ships with a default color palette, spacing scale, and breakpoint set. The final project must use ONLY the values extracted from the source snapshot, configured via `tailwind.config.ts` theme extensions. Never use `bg-blue-500` when the source uses `--color-brand: #2563eb`.

#### 10. Adding Component Libraries "For Convenience"
No `shadcn/ui`. No Material UI. No Chakra UI. No Radix primitives. Every component is built from scratch using the extracted design specs. The spec IS the component library.

#### 11. Using Google Fonts CDN Instead of Self-Hosting
All font files must be downloaded during Wave 0, stored in `public/assets/fonts/`, and loaded via `@font-face` in `globals.css`. Zero CDN requests. Zero external font loading.

#### 12. Guessing Mobile Layout Instead of Extracting from @media
The source CSS contains explicit `@media` queries defining exactly what happens at each breakpoint. Extract and implement those exact rules. Never guess "it probably stacks on mobile."

#### 13. Skipping Animation Extraction
"Users won't notice" is not acceptable. Scroll animations, hover transitions, page-load stagger effects, and micro-interactions are part of the visual DNA. Every `@keyframes`, every `transition`, every `IntersectionObserver` pattern gets documented in Wave 0 and implemented in Wave 4.

---

## Reference Files

These files contain detailed agent prompts, templates, and quality gates. Each wave references specific files.

| File | Wave(s) | Purpose |
|------|---------|---------|
| `references/foundations-agent.md` | Wave 0 | Per-page exploration agent prompt — methodology for CSS parsing, token extraction, deobfuscation |
| `references/sections-agent.md` | Wave 1 | Design soul extraction agent prompt — methodology for unifying visual DNA across pages |
| `references/section-template.md` | Wave 2 | Build brief template — the exact format for self-contained page build instructions |
| `references/system-template.md` | Wave 3 | Design system scaffold template — project structure, quality gate spec, foundation format |
| `references/website-patterns.md` | All Waves | Pattern identification catalog — CSS Module prefix → section type mapping, common website anatomy |
| `references/quality-checklist.md` | All Waves | Quality gates — extraction completeness checks, build verification criteria, signal file prerequisites |

### How to Use Reference Files

- **Wave 0 agents** MUST read `references/foundations-agent.md` before starting extraction
- **Wave 1 agents** MUST read `references/sections-agent.md` before starting soul extraction
- **Wave 2 agents** MUST read `references/section-template.md` before writing build briefs
- **Wave 3 orchestrator** MUST read `references/system-template.md` before scaffolding
- **All agents** SHOULD consult `references/website-patterns.md` for section-type identification
- **All agents** SHOULD consult `references/quality-checklist.md` before writing their `done.signal`

Agents that skip their reference file will produce incomplete or incorrectly formatted output, breaking downstream waves.
