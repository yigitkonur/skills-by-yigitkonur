# Quality Checklist — Extraction + Build

Two-part quality gate system. Part A verifies extraction completeness (Waves 0–2).
Part B verifies build fidelity (Waves 3–4).
Run Part A after Wave 2 completes. Run Part B after Wave 4 completes.

> **N/A is acceptable only when the source genuinely lacks the feature.**
> Add a note explaining why — e.g., "N/A — site has no dark mode selectors in any CSS file."

---

# ═══════════════════════════════════════════════════════════════
# PART A: EXTRACTION QUALITY (Waves 0–2)
# ═══════════════════════════════════════════════════════════════

Run this entire part after Wave 2 completes. Every item must pass
before any Wave 3 work begins.

---

## A1. Wave 0 Completeness — File Discovery & Asset Capture

Every source file must be found, catalogued, and processed.
Missing a single CSS file can cascade into missing tokens for the entire build.

### File Discovery
- [ ] All `.html` / `.htm` files discovered and listed in the inventory
- [ ] Each page's snapshot asset context documented and mapped to its parent HTML file (`_files/`, adjacent local assets, or inline-only mode)
- [ ] All CSS files inventoried with file sizes and content-hash deduplication
- [ ] All inline `<style>` blocks extracted from each HTML file
- [ ] Input format detected and documented (browser snapshot / SingleFile / wget mirror / source export)

### Page Classification
- [ ] Page types classified for each HTML file (homepage, pricing, about, blog, docs, etc.)
- [ ] Classification rationale documented (URL pattern, `<title>`, content analysis)
- [ ] Pages with ambiguous types flagged and resolved

### CSS Module Processing
- [ ] CSS Module prefix map extracted per page (e.g., `Hero_`, `Pricing_`, `Nav_`)
- [ ] Every prefix mapped to a section type with confidence level
- [ ] Utility prefixes identified and excluded (`Flex_`, `Grid_`, `Layout_`, `utils_`)
- [ ] Shared prefixes (appearing on 2+ pages) flagged for global treatment

### Variable & Class Extraction
- [ ] ALL CSS custom properties extracted from `:root` and theme selectors
- [ ] Variable→value map built (including full chain resolution: `--a: var(--b)` → final value)
- [ ] Variable chains resolve completely — no dangling `var()` references remain
- [ ] Class deobfuscation map created (hash class → semantic human-readable name)
- [ ] `deobfuscated.css` generated per page with readable class names

### Behavior & Asset Capture
- [ ] JS behaviors documented in `behavior-spec.md` (scroll triggers, toggles, carousels, etc.)
- [ ] All external assets downloaded to `assets/` directory
- [ ] `asset-manifest.json` created with original URL → local path mapping
- [ ] Font files downloaded (woff2, woff, ttf) and stored in `assets/fonts/`
- [ ] Image files downloaded and stored in `assets/images/`
- [ ] SVG icons extracted and stored individually in `assets/icons/`

### Signal
- [ ] `done.signal` written for each page after all above pass

---

## A2. Wave 0 Data Quality — Extracted Values

Raw data must be complete and accurate. Every value that exists in the source
CSS must appear in the extraction. No rounding. No approximation. No invention.

### Font Extraction
- [ ] All `@font-face` declarations captured with font file references
- [ ] All `font-family` values captured with usage frequency counts
- [ ] All `font-weight` values captured with usage frequency counts
- [ ] All `font-size` values captured with usage frequency counts
- [ ] All `line-height` values captured with usage frequency counts
- [ ] All `letter-spacing` values captured with usage frequency counts
- [ ] Font stacks preserved completely (not just the first family name)

### Color Extraction
- [ ] All CSS custom property color values extracted
- [ ] All raw color values extracted (hex, rgb, rgba, hsl, hsla, oklch, color-mix)
- [ ] Color frequency counts built (how many times each value appears)
- [ ] Opacity variants captured alongside their base colors
- [ ] Gradient color stops captured with exact positions (e.g., `#1a1a2e 0%, #16213e 50%`)

### Spacing Extraction
- [ ] All px values frequency-counted across all CSS files
- [ ] All rem values frequency-counted across all CSS files
- [ ] All em values frequency-counted across all CSS files
- [ ] Gap, padding, and margin values catalogued separately
- [ ] Spacing scale pattern identified (e.g., 4px base, 8/12/16/24/32/48/64/96)

### Breakpoint Extraction
- [ ] All `@media` queries captured with exact expressions
- [ ] Direction documented for each (min-width vs max-width vs range)
- [ ] Breakpoint values deduplicated and ordered
- [ ] Container queries captured (if present) or documented as absent

### Animation Extraction
- [ ] All `@keyframes` rules captured with full keyframe definitions
- [ ] All `transition` shorthand values decomposed (property, duration, easing, delay)
- [ ] All `animation` shorthand values decomposed
- [ ] All easing functions captured (cubic-bezier values, named easings)
- [ ] All duration values captured with frequency counts
- [ ] `prefers-reduced-motion` rules captured (or documented as absent)

### Other Systems
- [ ] Z-index layer system documented with all values and their selectors
- [ ] `border-radius` values catalogued with frequency
- [ ] `box-shadow` values catalogued with exact parameters
- [ ] `backdrop-filter` / `filter` values captured
- [ ] Dark theme selectors captured (`.dark`, `[data-theme="dark"]`, `prefers-color-scheme`)
- [ ] Dark theme documented as absent if no selectors found

### HTML-Embedded Values
- [ ] Inline `style=""` attribute CSS variable usage captured from HTML
- [ ] `data-*` attribute values documented for interactive elements
- [ ] Section inventory with DOM order per page (top-to-bottom as rendered)

---

## A3. Wave 1 Design Soul — Unified System

Wave 1 synthesizes Wave 0 raw data into a coherent design system.
Every value must trace back to Wave 0 — nothing is invented at this stage.

### Page-Type Grouping
- [ ] Page-type grouping documented with rationale for each group
- [ ] Grouping accounts for shared layout patterns (e.g., marketing pages vs docs)
- [ ] Each page assigned to exactly one group

### Typography System
- [ ] Typography system unified across each group with exact values
- [ ] Type scale documented (all sizes with their semantic names)
- [ ] Heading hierarchy documented (h1–h6 with size/weight/line-height per level)
- [ ] Body text styles documented (paragraph, small, caption, label)
- [ ] Font pairing strategy documented (which families for headings vs body)

### Color System
- [ ] Color system unified across all groups
- [ ] All CSS variables mapped to final resolved values
- [ ] All raw color values that aren't variables catalogued
- [ ] Semantic color names assigned (primary, secondary, accent, surface, text, muted, etc.)
- [ ] Color contrast ratios documented for text/background pairs
- [ ] Dark mode color mappings documented (or absence confirmed)

### Spacing System
- [ ] Spacing system documented with base unit identified (e.g., 4px or 0.25rem)
- [ ] Spacing scale documented (list of all used values as multiples of base)
- [ ] Section padding rhythm documented (hero=128px, features=96px, CTA=64px, etc.)
- [ ] Component internal spacing patterns documented

### Component Inventory
- [ ] Component inventory complete with anatomy for each component
- [ ] Each component documented with: variants, states, props
- [ ] Components tagged as SHARED (appears on 2+ pages) vs PAGE-SPECIFIC
- [ ] Shared components listed with every page they appear on
- [ ] Component hierarchy documented (e.g., Card contains CardHeader, CardBody, CardFooter)

### Layout Patterns
- [ ] Layout patterns documented per page type
- [ ] Grid systems identified (column counts, gap values, max-widths)
- [ ] Flex patterns identified (direction, alignment, wrapping)
- [ ] Content width constraints documented (max-width values per context)
- [ ] Section stacking order documented per page

### Responsive Architecture
- [ ] Responsive architecture documented per component per breakpoint
- [ ] Column collapse patterns documented (e.g., 4→2→1 at specific breakpoints)
- [ ] Element visibility changes documented (hidden/shown per breakpoint)
- [ ] Font size scaling per breakpoint documented
- [ ] Spacing scaling per breakpoint documented

### Motion Language
- [ ] Motion language unified across all pages
- [ ] Easing functions catalogued with semantic names (ease-in-out-custom, bounce, etc.)
- [ ] Duration scale documented (fast=150ms, normal=300ms, slow=500ms, etc.)
- [ ] `@keyframes` animations catalogued with their trigger conditions
- [ ] Entrance animation patterns documented (fade-up, slide-in, scale, etc.)
- [ ] Scroll-triggered animation thresholds documented

### Landing Page Architecture (if applicable)
- [ ] Landing page conversion architecture documented
- [ ] CTA placement strategy documented
- [ ] Visual hierarchy flow documented (attention path)
- [ ] Social proof placement documented
- [ ] Urgency/scarcity patterns documented (if present)

### Machine-Readable Output
- [ ] `token-values.json` generated and machine-readable
- [ ] `token-values.json` contains ALL colors, fonts, spacing, breakpoints, motion values
- [ ] JSON structure is flat or consistently nested (not mixed)
- [ ] Values in JSON match values in markdown docs exactly (byte-for-byte)

### Cross-Validation
- [ ] Every value in Wave 1 docs traces to Wave 0 deobfuscated CSS
- [ ] No value is rounded, approximated, or "improved"
- [ ] No value is invented (e.g., hover states that don't exist in source CSS)
- [ ] `done.signal` written for each group after validation passes

---

## A4. Wave 2 Build Briefs — Implementation-Ready Specs

Build briefs are the contract between extraction and implementation.
A Wave 4 builder agent must be able to build each page from its brief ALONE,
with zero access to the original HTML/CSS source files.

### Brief Coverage
- [ ] One brief per page (or per 3-page batch for very similar pages)
- [ ] Every page in the source has a corresponding brief
- [ ] No page is left without build instructions

### Page Identity
- [ ] Route path documented (e.g., `/`, `/pricing`, `/about`)
- [ ] Page title documented (from `<title>` tag)
- [ ] Meta description documented (from `<meta name="description">`)
- [ ] Page type documented (homepage, pricing, about, blog, docs, etc.)
- [ ] OG/social meta tags documented (if present)

### Per-Section Visual Specification
For EVERY section in EVERY brief:

- [ ] Section name and DOM position documented
- [ ] Layout with exact CSS properties AND Tailwind class mapping
- [ ] Typography with exact CSS properties AND Tailwind class mapping
- [ ] Colors with CSS variable resolution chain AND Tailwind class mapping
- [ ] Spacing (padding, margin, gap) with exact values AND Tailwind class mapping
- [ ] States and variants documented (hover, focus, active, disabled, selected)
- [ ] Responsive behavior per breakpoint with exact property changes
- [ ] Animations documented with trigger, effect, duration, easing, delay
- [ ] CSS recreation block provided (copy-paste ready, all breakpoints included)
- [ ] Background treatment documented (solid color, gradient, image, pattern)
- [ ] Border and shadow treatments documented

### Component & Asset References
- [ ] Component manifest included with SHARED / PAGE-SPECIFIC tags
- [ ] Each component reference includes: name, variant, props needed
- [ ] Asset reference table provided (Wave 0 path → `public/` path)
- [ ] Every image referenced includes dimensions and alt text
- [ ] Every icon referenced includes the SVG filename

### Interaction Specification
- [ ] Every animation documented as a declarative spec (not "add some animation")
- [ ] Scroll-triggered animations specify: threshold, direction, replay behavior
- [ ] Hover effects specify: property, from-value, to-value, duration, easing
- [ ] Click/toggle interactions specify: trigger, state change, animation
- [ ] Form interactions specify: validation, error states, success states (if applicable)

### Acceptance Criteria
- [ ] Acceptance criteria section present in every brief
- [ ] Criteria are objective and testable (not subjective like "looks good")
- [ ] Desktop, tablet, and mobile criteria listed separately
- [ ] Performance criteria listed (no external requests, build succeeds, etc.)

### The Builder Test
- [ ] A Wave 4 agent can build this page from the brief ALONE
- [ ] Brief contains every value needed — no "refer to source" instructions
- [ ] Brief contains no ambiguous language ("roughly", "about", "similar to")
- [ ] Every numeric value is exact (not "around 16px" but "16px" or "1rem")

### Signal
- [ ] `done.signal` written for each page brief after all above pass

---

## A5. Cross-Reference Integrity — Nothing Orphaned, Nothing Missing

Every value in every document must be traceable. If a section doc references
a color, that color must exist in Wave 1. If a brief uses a component,
that component must exist in the Wave 1 inventory.

- [ ] Every CSS variable referenced in section docs exists in Wave 1 `token-values.json`
- [ ] Every color value in section docs matches the Wave 1 palette documentation
- [ ] Every font family in section docs matches the Wave 1 typography documentation
- [ ] Every font size in section docs matches the Wave 1 type scale
- [ ] Every breakpoint value in briefs matches the Wave 1 responsive documentation
- [ ] Every easing function in briefs matches the Wave 1 motion documentation
- [ ] Every component referenced in briefs exists in the Wave 1 component inventory
- [ ] Every asset referenced in briefs exists in Wave 0 `asset-manifest.json`
- [ ] No orphan document references (`→ see filename.md` all point to real files)
- [ ] No UNVERIFIED values left unexplained — each is either resolved or marked with reason
- [ ] `cross-page-patterns.md` references correct page folders
- [ ] Shared components documented once in global docs (not duplicated per page)

---

## A6. The Grounding Test — Proof of Extraction Honesty

This test catches hallucinated, rounded, or invented values.
Perform it on a random sample of at least 10 values across different documents.

### Sample Selection
Pick 10 values randomly from across the extraction:
- 2 color values from different section docs
- 2 font-size values from different section docs
- 2 spacing values from different section docs
- 1 animation duration or easing value
- 1 breakpoint value
- 1 border-radius or shadow value
- 1 z-index value

### Verification
For each sampled value:

- [ ] Can trace it to a specific CSS file + specific selector in Wave 0 output
- [ ] Can trace each color to a CSS variable declaration or raw value in the stylesheet
- [ ] Value is exact — no rounding (not "approximately 16px" but "16px")
- [ ] Value is exact — no unit conversion errors (rem↔px conversion is correct)
- [ ] No invented hover states (`:hover` rule must exist in source CSS)
- [ ] No invented animations (`@keyframes` or `transition` must exist in source CSS)
- [ ] No invented responsive behaviors (`@media` rule must exist in source CSS)
- [ ] CSS recreation block matches what the original CSS actually declares
- [ ] Font sizes are exact (not "close to" but the literal value from the source)
- [ ] Gradient stops are exact (not "similar colors" but exact hex/rgb values and positions)

### Result
- [ ] All 10 values pass → Grounding test PASSES
- [ ] Any value fails → Fix the source, re-run, document what was wrong

---

# ═══════════════════════════════════════════════════════════════
# PART B: BUILD QUALITY (Waves 3–4)
# ═══════════════════════════════════════════════════════════════

Run this entire part after Wave 4 completes. Every item must pass
before the build is considered shippable.

---

## B1. Wave 3 Foundation — Token Coverage

The token system is the single source of truth for the entire build.
Every design value flows through tokens. If a value isn't in tokens, it doesn't exist.

- [ ] `tokens.ts` covers 100% of values from ALL Wave 2 briefs
- [ ] Every color from Wave 1 `token-values.json` present in tokens
- [ ] Every semantic color name (primary, secondary, accent, surface, text, muted) mapped
- [ ] Every opacity variant present
- [ ] Every gradient definition present
- [ ] Every font family in tokens AND `@font-face` declarations AND `tailwind.config`
- [ ] Every font size in tokens AND `tailwind.config.theme.fontSize`
- [ ] Every font weight in tokens AND `tailwind.config.theme.fontWeight`
- [ ] Every spacing value in tokens AND `tailwind.config.theme.spacing`
- [ ] Every breakpoint in tokens AND `tailwind.config.theme.screens`
- [ ] Every easing function in tokens AND `tailwind.config.theme.transitionTimingFunction`
- [ ] Every animation duration in tokens AND `tailwind.config.theme.transitionDuration`
- [ ] Every border-radius value in tokens AND `tailwind.config.theme.borderRadius`
- [ ] Every box-shadow value in tokens AND `tailwind.config.theme.boxShadow`
- [ ] Every z-index value in tokens AND `tailwind.config.theme.zIndex`
- [ ] Token values match Wave 1 `token-values.json` exactly (byte-for-byte comparison)

---

## B2. Wave 3 Foundation — Component Coverage

Shared components are the building blocks. Every component specified in
Wave 2 briefs must exist, accept the right props, and use only token values.

- [ ] Every SHARED-tagged component from Wave 2 manifests exists in `components/shared/`
- [ ] Every PAGE-SPECIFIC component from Wave 2 manifests exists in its page folder
- [ ] Components accept the props specified in Wave 2 briefs
- [ ] Components use ONLY `tokens.ts` values — no hardcoded colors, sizes, or fonts
- [ ] Components handle ALL variants specified in Wave 1 component inventory
- [ ] Header component handles transparent vs solid variant (if both exist in source)
- [ ] Header component handles mobile menu toggle
- [ ] Footer component matches extracted layout exactly
- [ ] Footer column count and stacking behavior match source responsive rules
- [ ] Button component handles all size and color variants from source
- [ ] Card component handles all layout variants from source (if applicable)
- [ ] Form components handle all states: default, hover, focus, error, disabled (if applicable)
- [ ] Component file naming follows project convention (PascalCase, `.tsx` extension)

---

## B3. Wave 3 Foundation — Build Integrity

The project must build cleanly from a fresh install.
Zero errors. Zero warnings. No workarounds.

### Package & Dependencies
- [ ] `npm install` succeeds with zero errors
- [ ] `package.json` contains ONLY these dependencies:
  - `next`
  - `react`
  - `react-dom`
  - `typescript`
  - `tailwindcss`
  - `@types/react`
  - `@types/react-dom`
  - `@types/node`
  - `postcss`
  - `autoprefixer`
- [ ] No other npm packages installed (no framer-motion, no lodash, no axios, etc.)
- [ ] `package-lock.json` is committed and consistent

### TypeScript & Build
- [ ] `npx tsc --noEmit` — zero TypeScript errors
- [ ] `npm run build` — zero build errors (route stubs are acceptable)
- [ ] `npm run build` — zero build warnings
- [ ] No `// @ts-ignore` or `// @ts-expect-error` comments in codebase
- [ ] No `any` types used — all types are properly defined with interfaces

### Tailwind Configuration
- [ ] `tailwind.config.ts` uses extracted values from tokens, NOT Tailwind defaults
- [ ] Default Tailwind color palette is NOT included (only extracted colors)
- [ ] Default Tailwind font families are NOT included (only extracted fonts)
- [ ] `content` array correctly targets all `.tsx` files

### Global Styles
- [ ] `globals.css` has `@font-face` declarations with local font file paths
- [ ] `globals.css` has CSS custom properties matching Wave 1 `token-values.json`
- [ ] `globals.css` includes `@tailwind base`, `@tailwind components`, `@tailwind utilities`
- [ ] CSS custom property names match Wave 1 naming exactly

---

## B4. Wave 3 Foundation — Zero External Dependencies

The built site must work completely offline. No external requests.
Every resource is self-hosted. This is non-negotiable.

### Source Code Scan
- [ ] `grep -r "http://" --include="*.ts" --include="*.tsx" --include="*.css" nextjs-project/` returns ZERO results
- [ ] `grep -r "https://" --include="*.ts" --include="*.tsx" --include="*.css" nextjs-project/` returns ZERO results
  - Exception: `next.config` legitimate URLs (e.g., image domains) — document each
- [ ] No Google Fonts CDN links anywhere in the project
- [ ] No CDN script tags anywhere in the project
- [ ] No remote image URLs in any component or page

### Asset Self-Hosting
- [ ] All font files present in `public/assets/fonts/` (or equivalent local path)
- [ ] All font files referenced locally in `@font-face` declarations
- [ ] All images present in `public/assets/images/` (or equivalent local path)
- [ ] All SVG icons present in `public/assets/icons/` (or inline in components)
- [ ] All assets referenced via relative paths (starting with `/assets/` or `./`)

---

## B5. Wave 3 Foundation — Traceability

Every token in the build must trace back to the extraction.
This is how we prove the build matches the source — not our imagination.

- [ ] `traceability-matrix.md` exists in the project root
- [ ] Every token in `tokens.ts` maps to a Wave 2 brief section
- [ ] Every token in `tokens.ts` maps to a Wave 0 source CSS file + selector
- [ ] No token exists without a source citation
- [ ] Matrix format is consistent and machine-parseable
- [ ] `foundation-ready.signal` written ONLY after ALL B1–B5 checks pass
- [ ] Foundation review completed before any Wave 4 page building begins

---

## B6. Wave 4 Per-Page — Visual Fidelity

For EACH page built, verify at three viewport widths.
Open the source HTML and the built page side by side.

### Desktop (≥1280px)
- [ ] Every section matches source visual layout (position, alignment, stacking)
- [ ] All text renders with correct font family
- [ ] All text renders with correct font size
- [ ] All text renders with correct font weight
- [ ] All text renders with correct line-height
- [ ] All text renders with correct letter-spacing
- [ ] All text renders with correct color
- [ ] All background colors match exactly (not "close enough")
- [ ] All background gradients match exactly (stops, positions, direction)
- [ ] All spacing matches exactly (padding, margin, gap — compare with DevTools)
- [ ] All images display at correct size and position
- [ ] All images have correct aspect ratio (not stretched or squished)
- [ ] All border-radius values match exactly
- [ ] All box-shadow values match exactly
- [ ] All border styles match exactly (width, color, style)
- [ ] Content max-width constraints match source
- [ ] Section vertical spacing rhythm matches source

### Tablet (768px–1279px)
- [ ] Layout changes match source `@media` rules at each breakpoint
- [ ] Column collapse is correct (e.g., 3→2 at 1024px, 2→1 at 768px)
- [ ] Font size adjustments match source per breakpoint
- [ ] Spacing adjustments match source per breakpoint
- [ ] Images resize correctly maintaining aspect ratio
- [ ] Elements that hide on tablet are hidden
- [ ] Elements that appear on tablet are shown
- [ ] Navigation changes to mobile variant at correct breakpoint

### Mobile (≤767px)
- [ ] Full responsive layout matches source
- [ ] Touch targets are adequate (minimum 44×44px interactive areas)
- [ ] Mobile menu functions correctly (open, close, navigation)
- [ ] No horizontal overflow causing horizontal scroll
- [ ] Font sizes are comfortable for mobile reading (min 14px body text)
- [ ] Images don't overflow their containers
- [ ] Cards stack vertically with appropriate spacing
- [ ] Footer columns stack correctly
- [ ] CTA buttons are full-width or appropriately sized for mobile

---

## B7. Wave 4 Per-Page — Interactions & Animations

Every interaction in the build must match the source CSS behavior exactly.
No invented animations. No "enhanced" hover effects. Match the source.

### Hover & Focus States
- [ ] All hover states match source CSS `:hover` selectors exactly
- [ ] Hover transitions match source `transition` properties (property, duration, easing)
- [ ] All focus states visible and match source `:focus-visible` selectors
- [ ] Focus ring color and style match source
- [ ] Active states match source `:active` selectors (if present)
- [ ] Disabled states match source `:disabled` or `[disabled]` selectors (if present)

### Scroll-Triggered Animations
- [ ] Scroll-triggered animations fire at correct viewport threshold
- [ ] Animation direction is correct (fade-up, slide-in-left, etc.)
- [ ] Animation durations match extracted values exactly (not "about 300ms" but "300ms")
- [ ] Animation easing functions match extracted values exactly (the full `cubic-bezier()`)
- [ ] Stagger delays between elements match source (if applicable)
- [ ] Animations play once or replay correctly based on source behavior

### Accessibility
- [ ] `prefers-reduced-motion: reduce` disables all non-essential animations
- [ ] Reduced motion fallback shows final state without animation
- [ ] Keyboard navigation works for all interactive elements

### Interactive Components
- [ ] Mobile menu open/close animation works correctly
- [ ] Accordion/FAQ expand/collapse works with correct animation (if applicable)
- [ ] Carousel/slider works with correct transition (if applicable)
- [ ] Plan toggle (monthly/annual) switches values and visual state (if applicable)
- [ ] Tab switching works with correct animation (if applicable)
- [ ] Modal/dialog open/close works with correct animation (if applicable)
- [ ] Tooltip positioning and show/hide works correctly (if applicable)

---

## B8. Wave 4 Per-Page — Technical Quality

The built page must be technically clean. No errors, no warnings,
no compromises.

### Build & Type Safety
- [ ] TypeScript strict mode — zero errors across entire project
- [ ] `next build` succeeds with zero errors
- [ ] `next build` succeeds with zero warnings
- [ ] No `console.log`, `console.warn`, or `console.error` left in production code
- [ ] No `TODO` or `FIXME` comments left in production code

### Runtime Quality
- [ ] No console errors when page loads in browser
- [ ] No console warnings when page loads in browser
- [ ] No external network requests visible in DevTools Network tab
- [ ] Page renders correctly without JavaScript (SSR/SSG content visible)
- [ ] No layout shift on page load (CLS should be near zero)

### Asset Integrity
- [ ] All fonts self-hosted and rendering with correct font-family
- [ ] All images self-hosted and displaying at correct dimensions
- [ ] All SVG icons rendering correctly (no missing icons, no broken paths)
- [ ] No 404 errors for any asset in the Network tab

### Semantic HTML
- [ ] Semantic HTML structure preserved: `<header>`, `<main>`, `<footer>`
- [ ] Sections use `<section>` with appropriate `aria-label` or heading
- [ ] Navigation uses `<nav>` element
- [ ] Lists use `<ul>`/`<ol>` (not divs styled as lists)
- [ ] Correct heading hierarchy (h1 → h2 → h3, no skipping levels)
- [ ] Correct `<meta>` tags in `<head>` (title, description, viewport, charset)
- [ ] Images have meaningful `alt` attributes
- [ ] Links have descriptive text (no "click here")

---

## B9. The Three Ultimate Tests

These are the final gates. If any one fails, the page is NOT done.
No exceptions. No "close enough."

### Test 1: Visual Test

Open the source `page.html` file and the built Next.js page side by side.
Compare at three viewport widths:

| Viewport | Width  | What to Compare                                    |
|----------|--------|----------------------------------------------------|
| Desktop  | 1280px | Full layout, all sections, all typography, colors  |
| Tablet   | 768px  | Responsive layout, column collapse, font scaling   |
| Mobile   | 375px  | Full mobile layout, stacking, mobile menu, CTAs    |

**Pass criteria:** The two pages are visually indistinguishable at each width.
Not "similar." Not "close." Indistinguishable.

- [ ] Desktop visual comparison passes
- [ ] Tablet visual comparison passes
- [ ] Mobile visual comparison passes

### Test 2: Network Test

Open the built page in a browser. Open DevTools → Network tab.
Hard-refresh the page (Cmd+Shift+R / Ctrl+Shift+R).
Wait for page to fully load. Filter to external requests.

**Pass criteria:** ZERO external network requests after initial page load.
All fonts, images, icons, and styles are served locally.

- [ ] Zero external font requests
- [ ] Zero external image requests
- [ ] Zero external script requests
- [ ] Zero external stylesheet requests

### Test 3: Build Test

Run in the project directory:
```bash
rm -rf .next node_modules
npm install
npm run build
```

**Pass criteria:** The entire sequence completes with ZERO errors and ZERO warnings.
Clean install, clean build.

- [ ] `npm install` — zero errors
- [ ] `npm run build` — zero errors
- [ ] `npm run build` — zero warnings

### Verdict

- [ ] ALL three ultimate tests pass → Page is DONE
- [ ] ANY test fails → Page is NOT done. Fix and re-test.

---

## B10. Common Failure Modes — Known Traps

Check specifically for each of these. They are the most frequent causes
of build rejection. Finding them early saves entire rework cycles.

### Token & Value Errors
- [ ] NOT using Tailwind default colors instead of extracted token values
- [ ] NOT using Tailwind default font sizes instead of extracted values
- [ ] NOT using Tailwind default spacing instead of extracted values
- [ ] NOT hardcoding color hex values in components (must use token references)
- [ ] NOT hardcoding pixel values in components (must use token/Tailwind classes)
- [ ] Animation timing is exact, not "close enough" (300ms ≠ 250ms)

### Responsive Errors
- [ ] NOT missing mobile breakpoint (tested desktop-only is the #1 failure)
- [ ] NOT missing tablet breakpoint (the forgotten middle child)
- [ ] NOT using wrong breakpoint values (extracted values, not Tailwind defaults)
- [ ] Column collapse is correct at each breakpoint (not just "it stacks")

### Asset Errors
- [ ] NOT loading fonts from Google Fonts CDN (must be self-hosted)
- [ ] NOT loading images from external URLs (must be in `public/`)
- [ ] Font files actually exist at the paths referenced in `@font-face`
- [ ] Image files actually exist at the paths referenced in components

### Interaction Errors
- [ ] NOT missing hover states (every `:hover` in source CSS is implemented)
- [ ] NOT missing focus states (accessibility requirement)
- [ ] Scroll animation threshold is correct (not firing too early or too late)
- [ ] Image aspect ratios are correct (extracted exact dimensions, not guessed)

### Dependency Errors
- [ ] NOT added an extra npm package "for convenience" (only allowed packages)
- [ ] NOT using `framer-motion` when CSS transitions/animations suffice
- [ ] NOT using `axios` when `fetch` works
- [ ] NOT using any icon library (icons are extracted SVGs)

### TypeScript Errors
- [ ] NOT using `any` type anywhere (proper interfaces defined)
- [ ] NOT using `// @ts-ignore` anywhere (fix the type error properly)
- [ ] NOT using `as` type assertions excessively (design types correctly)
- [ ] Props interfaces defined for every component

---

# ═══════════════════════════════════════════════════════════════
# COMPLETION CRITERIA
# ═══════════════════════════════════════════════════════════════

## Part A Completion (after Wave 2)

All of A1–A6 must pass before Wave 3 begins:

1. Every checkbox is checked or marked N/A with written justification
2. The grounding test (A6) passes for all 10 sampled values
3. Cross-reference integrity (A5) has zero broken references
4. Every `done.signal` file exists

**Sign-off:** `[Agent] [Date] [Part A Status: PASS / FAIL with notes]`

## Part B Completion (after Wave 4)

All of B1–B10 must pass before the build is shippable:

1. Every checkbox is checked or marked N/A with written justification
2. All three ultimate tests (B9) pass for every page
3. Zero common failure modes (B10) are present
4. `foundation-ready.signal` exists
5. `traceability-matrix.md` is complete

**Sign-off:** `[Agent] [Date] [Part B Status: PASS / FAIL with notes]`

---

> **Remember:** N/A requires a note. "Close enough" is not enough.
> Every value is either exact or it's wrong.
