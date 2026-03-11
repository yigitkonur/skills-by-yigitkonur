# Wave Pipeline — Orchestration Details

The 5-wave pipeline converts saved HTML snapshots into buildable Next.js projects. Each wave has strict entry gates, parallel agent spawning, defined outputs, and completion signals.

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
   - Component name (from CSS Module prefix), anatomy breakdown, visual variants
   - Interactive states (hover, focus, active, disabled)
   - Responsive behavior (layout changes per breakpoint)
   - Shared vs. page-specific classification

4. **`responsive-map.md`** — Breakpoint behavior per component:
   - Every `@media` query found, sorted by breakpoint
   - What changes at each: layout, font sizes, spacing, visibility
   - Mobile-first vs. desktop-first detection

5. **`cross-site-patterns.md`** — Patterns shared across pages in this group:
   - Section ordering conventions, visual rhythm, content density patterns
   - CTA placement strategy, conversion architecture flow

6. **`done.signal`** — Empty file, written ONLY after all outputs complete

### Landing Page Reality Check

Wave 1 agents processing landing pages must document these anatomical patterns explicitly:

- **Hero composition** — Headline hierarchy, CTA placement, background treatment
- **Social proof strategy** — Logo bar position, testimonial format, trust signals
- **Feature presentation** — Grid layout vs. alternating, icon usage, description density
- **Pricing hierarchy** — Card emphasis, comparison table, toggle patterns
- **CTA rhythm** — Primary vs. secondary styling, spacing, urgency signals
- **Conversion architecture** — Awareness → interest → trust → decision → action flow

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

1. **`agent-brief.md`** — Self-contained build instructions following the Wave 2 template. Must be **complete enough that a Wave 4 agent can build the page from this brief ALONE**, without accessing Wave 0 or Wave 1 outputs.

2. **`done.signal`** — Written only after the brief passes completeness checks

### Brief Completeness Rule

Every `agent-brief.md` MUST include ALL of these sections:

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
**Agents:** 1 orchestrator agent (may spawn specialist sub-agents)
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

- **`foundation-brief.md`** — Instructions for Wave 4 agents: how to use `tokens.ts`, `animations.ts`, extend shared components, Tailwind conventions, responsive approach, asset paths
- **`traceability-matrix.md`** — Complete trace from tokens to source:
  ```
  Token Name              → Wave 2 Brief Reference      → Wave 0 Source File
  --color-bg-primary      → homepage/agent-brief.md:L42  → homepage_files/06cc9eb.css :root
  --font-display          → homepage/agent-brief.md:L18  → homepage_files/a3b2c1.css :root
  ```
- **`foundation-ready.signal`** — Written ONLY after the quality gate passes

### Foundation Quality Gate

Before writing `foundation-ready.signal`, verify ALL conditions:

| Check | Verification Method | Pass Criteria |
|-------|-------------------|---------------|
| Token coverage | Diff `tokens.ts` exports vs. all `wave2/*/agent-brief.md` token references | 100% of referenced tokens exist |
| Shared components | List SHARED-tagged components across all Wave 2 briefs | Every SHARED component has a file |
| Breakpoints | Compare `tailwind.config.ts` vs. Wave 1 `responsive-map.md` | All source breakpoints represented |
| Font loading | Verify `@font-face` references files in `public/assets/fonts/` | All fonts self-hosted |
| Animations | Check `animations.ts` covers all Wave 2 interaction specs | All shared patterns defined |
| Zero deps | Read `package.json` dependencies | NO UI/animation/icon/font libraries |
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

For EACH page, spawn one Wave 4 agent with:
- The page's `wave2/{page}/agent-brief.md` (complete build spec)
- The `wave3/foundation-brief.md` (how to use the design system)
- Path to `nextjs-project/` (the existing scaffold)
- Instruction: "Read the agent-brief and foundation-brief. Build this page using ONLY the Wave 3 design system. Zero external dependencies. Every visual value must match the brief exactly."

### What Each Agent Produces

1. **`app/{route}/page.tsx`** — Server component by default (`'use client'` only where interaction requires). Imports shared components from `@/components/shared/`, page-specific from `@/components/pages/{page}/`. Uses tokens from `@/lib/tokens`.

2. **`components/pages/{page}/`** — One component file per section (e.g., `Hero.tsx`, `FeatureGrid.tsx`). TypeScript interfaces for all props. Tailwind classes using the extended theme. CSS custom properties via inline styles where Tailwind doesn't cover.

3. **`public/assets/{page}/`** — Page-specific images and icons copied from `wave0/{page}/assets/`.

### Acceptance Criteria (Per Page)

| Criterion | Verification |
|-----------|-------------|
| Visual match — desktop (≥1280px) | Layout, typography, colors, spacing match agent-brief |
| Visual match — tablet (768–1279px) | Responsive layout shifts match tablet spec |
| Visual match — mobile (≤767px) | Mobile layout, stacking, font scaling match mobile spec |
| Interactive states | All hover/focus/active/disabled states match behavior spec |
| Animations | All scroll-triggered, load, and hover animations fire correctly |
| Typography | All fonts render with correct family, weight, size, line-height |
| Images | All images self-hosted in `public/assets/` and displaying |
| No external requests | Zero network requests to CDNs, Google Fonts, external APIs |
| TypeScript strict | `tsc --noEmit` passes with zero errors |
| Build succeeds | `next build` completes without errors |

---

## Global Fleet Rules

These rules apply across ALL waves and ALL agents.

### Wave Sequencing (STRICT)

```
Wave 0 (all agents) → Gate → Wave 1 (all agents) → Gate → Wave 2 (all agents) → Gate → Wave 3 → Gate → Wave 4 (all agents)
```

No Wave N+1 agent may start until ALL Wave N `done.signal` files exist. Non-negotiable.

### Parallelism Within Waves

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

### The Consistency Rule

The same token name must mean the same value everywhere:
- `tokens.ts` value = `tailwind.config.ts` extension = `globals.css` custom property = `wave2/*/agent-brief.md` reference
- If a discrepancy is found, trace back to Wave 0 source and use the authoritative value
