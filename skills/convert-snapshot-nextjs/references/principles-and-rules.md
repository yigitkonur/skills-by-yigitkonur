# Principles & Rules

Core philosophy, grounding constraints, section identification methodology, and CSS Module decoding patterns that govern every wave of the pipeline.

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

The **prefix before the first underscore** IS the section identifier — more reliable than HTML nesting, more precise than semantic tags.

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

This produces a clean list of component names present on that page. Cross-reference with `references/website-patterns.md` for section-type mapping.

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

## Zero Dependencies Rule

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
