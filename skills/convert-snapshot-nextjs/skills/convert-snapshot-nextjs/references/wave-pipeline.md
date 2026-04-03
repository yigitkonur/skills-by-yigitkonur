# Wave Pipeline — Orchestration Details

The pipeline converts live websites or saved HTML snapshots into buildable Next.js projects. It has one optional pre-wave for live capture plus five strict downstream waves. Each phase has entry gates, defined artifacts, and completion signals.

---

## Capture Wave — Live Route Inventory & Grounded Browser Capture

**Trigger:** The source starts as a live URL or a partially recovered production site
**Agents:** 1 inventory agent + 1 capture agent per canonical route family or in-scope route batch
**Input:** Root URL or explicit route list
**Output:** `.design-soul/capture/`

Read `references/capture-workflow.md` before starting this wave.

### Pre-Flight: Scope and Inventory

Before spawning capture agents, the orchestrator must:

1. record the requested root URL and any allowlist/denylist routes
2. discover candidate routes from header/footer links, sitemap, in-page internal links, and explicit user scope
3. normalize and dedupe routes
4. classify routes into page families
5. choose at least one canonical exemplar per family

Typical families include:

- `home`
- `marketing-landing`
- `pricing`
- `contact`
- `customers-index`
- `blog`
- `docs`
- `about`
- `auth`
- `dashboard`
- `legal`

### Required Capture Artifacts Per Route

Every captured route must preserve:

1. **Final hydrated DOM**
   - `dom.html`
   - title + H1/H2/H3 outline
   - visible section order

2. **Visual evidence**
   - desktop, tablet, and mobile screenshots
   - full-page screenshots when supported
   - scroll-slice screenshots for long pages so below-the-fold sections are not missed

3. **Runtime metadata**
   - stylesheet and script URLs
   - image and font URLs
   - exposed build IDs, route manifests, chunk references
   - `__NEXT_DATA__`, `self.__next_f`, or equivalent framework runtime data when present

4. **Mirrored assets**
   - local copies of CSS, JS, fonts, images, and chunks needed for Wave 0
   - route-level asset manifests tying original URLs to local files

5. **Route classification**
   - URL, pathname, inclusion status, page family, canonical exemplar status, notes

### Capture Wave Outputs

1. **`route-manifest.json`** — one row per discovered route:
   ```json
   {
     "url": "https://example.com/pricing",
     "pathname": "/pricing",
     "included": true,
     "pageFamily": "pricing",
     "canonical": true,
     "notes": ["pricing page", "nav linked", "in scope"]
   }
   ```

2. **`page-types.md`** — page-family grouping with rationale and canonical exemplar choice.

3. **`capture/{route}/...`** — route-level artifacts:
   - `dom.html`
   - `headings.json`
   - `runtime-metadata.json`
   - `assets.json`
   - `mirror/`
   - `screenshots/*.png`
   - `done.signal`

4. **`capture-summary.md`** — gaps, blocked routes, session-specific caveats, and evidence quality.

### Capture Wave Completion Gate

The Capture Wave is complete when:

- every in-scope route in `route-manifest.json` has a route directory
- every canonical page family has at least one exemplar route
- desktop/tablet/mobile screenshots exist for each canonical route
- scroll slices exist for long pages
- mirrored asset roots exist for routes that need Wave 0 extraction
- `.design-soul/capture/done.signal` exists

**Do not proceed to Wave 0 until this gate passes.**

---

## Wave 0 — Per-Page Deep Exploration & Deobfuscation

**Trigger:** Capture Wave completed, or saved snapshots already exist
**Agents:** 1 per page/route (parallel within the phase)
**Input:** One captured route directory or one saved `{page}.html` plus its grounded asset context
**Output:** `.design-soul/wave0/{page}/`

### Wave 0 Entry Requirements

The orchestrator must give each Wave 0 agent one grounded input set:

- **Live-capture path:** `.design-soul/capture/{route}/dom.html`, screenshots, runtime metadata, and `mirror/`
- **Snapshot path:** `{page}.html` plus its `{page}_files/` folder
- **Adjacent-asset snapshot path:** `{page}.html` plus the local CSS/assets referenced by that HTML
- **SingleFile path:** `{page}.html` with inline styles, plus a note about reduced confidence

If a live-capture route lacks `mirror/`, stop and finish the Capture Wave first. If a snapshot route has no `_files/`, no local CSS references, and no inline `<style>` blocks, stop and get a richer snapshot before Wave 0.

### What Each Agent Produces

1. **`exploration.md`**
   - page classification and confidence
   - capture mode (live capture vs saved snapshot)
   - section inventory in render order
   - CSS token map and resolved custom properties
   - responsive map from real media queries
   - animation catalog and runtime behavior notes
   - font inventory, color inventory, spacing inventory
   - screenshot coverage and any missing evidence notes

2. **`deobfuscated.css`**
   - concatenated and deduplicated CSS
   - readable class names where possible
   - source comments for traceability

3. **`behavior-spec.md`**
   - declarative behavior specs only
   - trigger -> target -> effect -> timing -> easing
   - scroll behavior, menu toggles, hover/focus states, visibility changes

4. **`assets/`**
   - copied or downloaded fonts, images, icons, plus asset manifest

5. **`done.signal`**

### Wave 0 Completion Gate

Wave 0 is complete when every in-scope page/route has a `wave0/{page}/done.signal`.

---

## Wave 1 — Design Soul Extraction by Page Family

**Trigger:** All Wave 0 `done.signal` files exist
**Agents:** 1 per page family (parallel within the phase)
**Input:** All `wave0/` outputs for one family
**Output:** `.design-soul/wave1/{group}/`

### Grouping Rules

Families are deterministic. A page belongs to exactly one group.

Typical groups:

| Group | Signal |
|---|---|
| `home` | homepage shell + hero + trust + conversion sections |
| `marketing-landing` | product, platform, or solution landing pages with shared shell and block library |
| `pricing` | pricing cards, comparison, FAQ, conversion CTAs |
| `contact` | form-led contact or demo-request pages |
| `customers-index` | customer story or testimonial listing pages |
| `blog` | article-led content pages |
| `docs` | docs or API reference pages |
| `about` | company and team pages |
| `auth` | login or signup pages |
| `dashboard` | app shells, settings, or dense data pages |
| `legal` | privacy, terms, or policy pages |

### Grouping Criteria

Use these signals in priority order:

1. shared navigation structure
2. section composition overlap
3. visual treatment similarity
4. conversion rhythm or app-shell intent
5. route purpose and content density

If only one page exists, still assign the closest honest semantic group instead of inventing a bespoke one-off family.

### Agent Spawning

For each page family, spawn one Wave 1 agent with:

- the list of `wave0/{page}/` directories in the family
- all `exploration.md` files from those directories
- all `deobfuscated.css` files from those directories
- instruction to read `references/sections-agent.md`

### What Each Agent Produces

1. **`design-soul.md`**
   - unified typography, color, spacing, layout, responsive, and motion systems
   - shared shell analysis
   - canonical section blocks and known overrides
   - route-family-specific conversion or shell architecture when applicable

2. **`token-values.json`**
   - machine-readable tokens with source citations

3. **`component-inventory.md`**
   - repeating components with `GLOBAL-SHARED`, `SHARED`, or `PAGE-SPECIFIC` tags

4. **`responsive-map.md`**
   - per-component changes by breakpoint

5. **`cross-site-patterns.md`**
   - shared ordering, shell patterns, reusable section families, canonical exemplar notes

6. **`done.signal`**

### Wave 1 Completion Gate

Wave 1 is complete when every page family has a `wave1/{group}/done.signal`.

---

## Wave 2 — Page Build Brief Manufacturing

**Trigger:** All Wave 1 `done.signal` files exist
**Agents:** 1 per page, or 1 per small batch of highly similar same-family pages
**Input:** `wave1/{group}/` soul docs + `wave0/{page}/` raw data
**Output:** `.design-soul/wave2/{page}/`

### What Each Agent Produces

1. **`agent-brief.md`** — self-contained build instructions that a Wave 4 agent can use alone
2. **`done.signal`**

### Wave 2 Brief Requirements

Every brief must include:

- route identity and metadata
- section blueprint in render order
- component manifest with reuse rules
- token references with exact values
- asset table with local destinations
- interaction specs with exact triggers/timings
- responsive rules for desktop, tablet, and mobile
- acceptance criteria tied to visual QA

### Wave 2 Completion Gate

Wave 2 is complete when every in-scope page has a `wave2/{page}/done.signal`.

---

## Wave 3 — Design System Foundation & Next.js Scaffold

**Trigger:** All Wave 2 `done.signal` files exist
**Agents:** 1 orchestrator agent, with optional internal specialists
**Input:** All Wave 1 soul docs + all Wave 2 briefs
**Output:** `nextjs-project/` + `.design-soul/wave3/`

### What the Orchestrator Produces

1. **`nextjs-project/` scaffold**
   - `package.json` with only allowed dependencies
   - strict TypeScript config
   - Tailwind config extended with extracted values, not defaults
   - `globals.css`, `tokens.ts`, and shared primitives wired to extracted values
   - route stubs or route implementations for every in-scope page

2. **`.design-soul/wave3/` docs**
   - `foundation-brief.md`
   - `traceability-matrix.md`
   - `foundation-ready.signal`

### Recommended Scaffold Map

| File/Directory | Contents | Source |
|---|---|---|
| `package.json` | Only the allowed Next/React/Tailwind/TypeScript/PostCSS dependencies | Wave 3 constraint |
| `tsconfig.json` | `strict: true`, path aliases for `@/components` and `@/lib` | Standard Next.js scaffold |
| `tailwind.config.ts` | Extended theme with real breakpoints, colors, fonts, and spacing from Wave 1 tokens | `wave1/*/token-values.json` |
| `postcss.config.js` | Standard PostCSS with Tailwind and autoprefixer | Standard scaffold |
| `styles/globals.css` | `@font-face` declarations and CSS custom properties from extracted tokens | `wave0/*/assets/` + `wave1/*/token-values.json` |
| `lib/tokens.ts` | Typed TypeScript constants for all design tokens | `wave1/*/token-values.json` |
| `lib/animations.ts` | Animation utility helpers from extracted `@keyframes` and transition patterns | `wave0/*/behavior-spec.md` |
| `components/shared/` | Shared shell components with props interfaces | `wave2/*/agent-brief.md` |
| `app/layout.tsx` | Root layout importing fonts, globals, and shared shell | All wave outputs |
| `app/*/page.tsx` | Route stubs or real implementations for every in-scope page | `wave2/` page list |

### Wave 3 Quality Gate

Before writing `foundation-ready.signal`, verify:

- token coverage is complete
- shared components exist for all `GLOBAL-SHARED` and required `SHARED` items
- fonts/assets are self-hosted
- breakpoints match extracted values
- strict TypeScript passes
- production build passes
- no forbidden dependencies are introduced

---

## Wave 4 — Full Page Build & Visual QA Loop

**Trigger:** `.design-soul/wave3/foundation-ready.signal` exists
**Agents:** 1 per page, or 1 per small same-family batch
**Input:** `wave2/{page}/agent-brief.md` + `wave3/foundation-brief.md`
**Output:** Next.js route code plus visual comparison artifacts

### What Each Agent Produces

1. **Route code**
   - `app/{route}/page.tsx`
   - `components/pages/{page}/...`
   - copied assets under `public/assets/{page}/`

2. **Visual QA artifacts** under `.design-soul/visual/{page}/`
   - source screenshots
   - build screenshots
   - diff images
   - `summary.json` with similarity metrics and notes

### Wave 4 Acceptance Criteria

Each page must pass:

- desktop compare
- tablet compare
- mobile compare
- full-page or scroll-slice compare for long pages
- interactive states grounded in the brief
- zero external requests for shipped assets
- `tsc --noEmit`
- `npm run build`

### Similarity Rule

Use objective compare artifacts instead of subjective `looks close` language. If the user gives a threshold, hit it. If they do not, use route-by-route comparison artifacts and document the measured gap before claiming fidelity.

---

## Global Fleet Rules

### Strict Phase Order

```text
Capture Wave (if needed)
-> Gate
-> Wave 0 (all agents)
-> Gate
-> Wave 1 (all agents)
-> Gate
-> Wave 2 (all agents)
-> Gate
-> Wave 3
-> Gate
-> Wave 4 (all agents + visual QA loop)
```

No later phase starts before the prior phase gate passes.

### Parallelism Within Phases

- Capture Wave: route inventory first, then per-route or per-family captures in parallel
- Wave 0: all page agents in parallel
- Wave 1: all page-family agents in parallel
- Wave 2: all page brief agents in parallel
- Wave 3: single orchestrator
- Wave 4: all page build agents in parallel where write scopes do not overlap

### Session Hygiene for Live Capture

- Prefer isolated browser sessions per route or per family to avoid cross-route contamination
- Capture source screenshots before comparing against rebuilds
- Preserve the original raw artifacts before normalizing or formatting anything

### Signal File Convention

```text
.design-soul/capture/{route}/done.signal
.design-soul/capture/done.signal
.design-soul/wave{0,1,2}/{identifier}/done.signal
.design-soul/wave3/foundation-ready.signal
```

Signals are written only after the corresponding validation passes.
