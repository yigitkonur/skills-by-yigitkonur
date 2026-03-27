# Principles & Rules

Core philosophy, grounding constraints, section identification methodology, and reconstruction rules that govern every phase of the pipeline.

---

## Philosophy: Eight Principles

### 1. Parse, Don't Guess

Captured CSS, HTML, runtime metadata, and saved artifacts are evidence. Use them programmatically. Never infer exact values from visual appearance alone. If a value cannot be found in grounded artifacts, mark it `UNVERIFIED` — do not invent it.

### 2. Live DOM and Saved HTML Are Both Valid Source Artifacts

A live route captured through a browser and a saved `.html` snapshot are both acceptable starting points. Prefer live browser capture when the site is reachable, because hydration, runtime states, and below-the-fold content may never appear in a static response.

### 3. CSS Module Names Are Still Your Best Section Map

The CSS Module naming convention is often the most reliable section identifier in saved or captured pages:

```
Header_root__x8J2p           -> Component: Header, Element: root
Plans_card__SCfoV           -> Component: Plans, Element: card
CTA_sectionPrefooter__kW_wF -> Component: CTA, Element: section-prefooter
```

The prefix before the first underscore is often the component or section name. Use it together with semantic tags, heading outlines, and screenshot coverage.

### 4. Every Route Belongs to a Page Family

Do not rebuild routes as disconnected one-offs. Inventory routes first, classify them into page families, choose canonical exemplars, then extract the shared shell and reusable section blocks before route fan-out.

### 5. CSS Variables Are the Design System

Custom properties declared in `:root`, theme selectors, or scoped containers are the token backbone. Extract them first. The downstream build depends on resolved token values, not approximations.

### 6. Screenshots Verify; They Do Not Author Tokens

Use screenshots, full-page captures, and scroll slices to find missing sections, verify layout rhythm, and measure fidelity. Do not derive exact spacing, type sizes, or colors from screenshot pixels when CSS/HTML evidence exists.

### 7. Build What You Extract

Every documented value becomes runnable code. If it appears in the design soul docs, it must trace to a real source artifact and land in the Next.js build. No aspirational tokens. No generic replacements.

### 8. Zero External Dependencies

The final Next.js project uses only these base packages: `next`, `react`, `react-dom`, `typescript`, `tailwindcss`, `@types/react`, `@types/react-dom`, `@types/node`, `postcss`, and `autoprefixer`. No CDN fonts. No icon libraries. No animation libraries. No component libraries. Self-host all shipped assets under `public/`.

---

## The Grounding Rule (Non-Negotiable)

Every value documented in any phase must trace to one or more of these sources:

1. **A CSS rule** in the page's discovered CSS corpus — mirrored capture stylesheets, `_files/*.css`, adjacent local `.css`, or extracted inline CSS
2. **A CSS custom property declaration** in `:root`, theme selectors, or scoped containers
3. **An inline `style=""` attribute** in the HTML
4. **A `<style>` block** in the HTML
5. **A `@keyframes` or `@media` rule** in CSS
6. **Browser-captured final DOM attributes or text content** when the route started from a live site
7. **Runtime metadata** such as `__NEXT_DATA__`, `self.__next_f`, script/style manifests, build IDs, or exposed asset URLs

If you cannot find a source for a value:

- Mark it as `UNVERIFIED — not found in grounded artifacts`
- Do not invent `close enough` values
- Do not round to convenient numbers
- Do not assume framework defaults

The downstream builder implements values literally. A bad guess creates a wrong pixel. An honest gap stays fixable.

---

## Section Identification Hierarchy

When identifying sections within a page, follow this priority order:

1. **Semantic HTML tags** — `<header>`, `<main>`, `<section>`, `<footer>`, `<nav>`
2. **CSS Module class prefixes** — `Header_`, `Hero_`, `Pricing_`, `CTA_`, `Footer_`
3. **Heading outline** — title, H1, H2, and H3 captured from the rendered route
4. **Screenshot coverage** — use screenshots and scroll slices to confirm no sections were missed below the fold
5. **Structure heuristics** — only when the stronger signals above are absent

Cross-reference section guesses with `references/website-patterns.md`.

---

## Route-Family Rule

Before building many routes:

- inventory the in-scope URLs
- group them into page families
- choose canonical exemplars
- identify shared shell and family-specific section blocks
- only then fan out to route builds

A plausible but generic landing page is failure. The goal is route-family-faithful reconstruction, not a themed rewrite.

---

## Verification Rule

Every serious reconstruction must include visual comparison evidence:

- desktop, tablet, and mobile screenshots
- full-page or scroll-slice comparison for long pages
- diff artifacts or structured compare summaries
- explicit notes about what still drifts and why

Never claim `pixel-perfect` or `faithful` from build success alone.

---

## CSS Module Decoding

### Pattern

```
ComponentName_propertyName__hashCode
```

### Utility Prefixes (Not Sections)

Some prefixes are utilities, not section identifiers:

| Prefix | Type | Meaning |
|---|---|---|
| `Flex_` | Utility | Flexbox helper |
| `Grid_` | Utility | Grid helper |
| `Container_` | Utility | Width constraint wrapper |
| `Spacer_` | Utility | Spacing utility |
| `Text_` | Utility | Typography utility |
| `Icon_` | Utility | Icon sizing/alignment utility |

Filter these out when building the section inventory.

---

## Zero Dependencies Rule

The `nextjs-project/package.json` may contain only:

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

No exceptions. No `framer-motion`. No `shadcn/ui`. No `@mui/*`. No `@chakra-ui/*`. No `lucide-react`. No `@fontsource/*`. No `gsap`. No `lottie`. Everything is built from scratch using the extracted design specs.
