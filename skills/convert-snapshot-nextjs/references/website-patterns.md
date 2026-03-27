# Website Section Patterns — Identification from Captured or Saved Pages

This reference helps you identify section types from CSS Module class prefixes, semantic HTML tags, heading structure, and content patterns. Use it for both saved snapshots and browser-captured live routes.

**Section Identification Hierarchy (use in this order):**
1. Semantic HTML tags (`<header>`, `<section>`, `<footer>`, `<nav>`)
2. CSS Module class prefix (the part before `_` in `Header_root__x8J2p`)
3. Heading outline and route context
4. Screenshot confirmation for below-the-fold sections
5. Structure heuristics (layout patterns, content signals)

**CSS Module naming convention:** `ComponentName_propertyName__hashCode`
- The **ComponentName** (before the first `_`) often tells you which section or component you're looking at
- The **propertyName** (between `_` and `__`) tells you which element within that component
- The **hashCode** (after `__`) is a build-time unique identifier — ignore it

**Tailwind example rule:** Tailwind classes in this document illustrate structure and implementation shape only. Replace their concrete values with token-backed classes and extracted numbers from Waves 1–3 before you write production code.

---

## Master Prefix Identification Table

| CSS Module Prefix | Section Type | HTML Signal | Content Signal |
|-------------------|-------------|-------------|----------------|
| `Header_`, `Nav_`, `Navigation_`, `TopBar_` | Navigation | `<header>`, `<nav>` | Logo, nav links, CTA button |
| `Hero_`, `Banner_`, `Masthead_`, `Jumbotron_` | Hero | First `<section>` in `<main>` | Large H1, subtitle, 1-2 CTAs |
| `Feature_`, `Features_`, `Benefit_`, `Capabilities_` | Features | Grid/flex of cards | Icons + headings + descriptions |
| `Pricing_`, `Plans_`, `Plan_`, `Tiers_` | Pricing | Cards with prices | Dollar amounts, plan names, CTAs per card |
| `Comparison_`, `Compare_`, `Matrix_`, `FeatureTable_` | Comparison | `<table>` or grid | Checkmarks, plan columns |
| `Testimonial_`, `Quote_`, `Review_`, `Social_` | Testimonials | Blockquotes or cards | Quote text, avatar, name, role |
| `Logo_`, `Customer_`, `CustomerMarquee_`, `Brand_`, `Clients_` | Logo Cloud | Image row/grid | Small company logos, marquee animation |
| `CTA_`, `CallToAction_`, `Prefooter_`, `GetStarted_` | CTA | Contrasting section | Prominent heading + 1-2 buttons |
| `FAQ_`, `Accordion_`, `Questions_` | FAQ | Question/answer pairs | Expand/collapse, question text |
| `Team_`, `People_`, `About_`, `Leadership_` | Team | Person grid | Photos, names, roles |
| `Blog_`, `Post_`, `Article_`, `News_` | Blog/Content | Article structure | Dates, authors, reading time |
| `Footer_`, `SiteFooter_` | Footer | `<footer>` | Link columns, copyright, social icons |
| `Stats_`, `Metrics_`, `Numbers_` | Stats | Number grid | Large numbers + labels |
| `Dashboard_`, `AppShell_`, `Shell_`, `Workspace_` | App Shell / Dashboard | persistent sidebar + top bar + content pane | navigation chrome, filters, data cards, dense content |
| `Sidebar_`, `SideNav_`, `Rail_` | Sidebar Navigation | `<aside>` or fixed left column | stacked nav items, workspace switcher, collapsed labels |
| `Metric_`, `Kpi_`, `StatCard_` | KPI / Metric Cards | repeated compact cards | large value + label + delta/trend |
| `Table_`, `DataTable_`, `GridTable_` | Data Table | `<table>` or row grid | column headers, dense rows, sorting/filter affordances |
| `Filter_`, `Toolbar_`, `SegmentedControl_` | Filter / Toolbar | control bar above content | pills, selects, search, date filters |
| `Timeline_`, `History_`, `Roadmap_` | Timeline | Sequential items | Dates, milestone descriptions |
| `Changelog_`, `Updates_`, `Release_` | Changelog | Versioned entries | Version numbers, descriptions |
| `Integrations_`, `Partners_`, `AppStore_` | Integrations | Logo/card grid | App icons, "Connect" buttons |

**Disambiguation rules when prefixes are ambiguous:**
- Outermost prefix wins (a `Header_` wrapping `Button_` means this is the Header section, not the Button section)
- Semantic HTML tags validate: `<footer>` + `Footer_` = definitely footer
- Utility prefixes are NOT sections: `Flex_`, `Grid_`, `Layout_`, `Spacer_`, `Container_`, `Wrapper_`, `Bleed_`

**App-UI escape hatch:** If a snapshot is clearly an authenticated product surface rather than a marketing page, classify the outer shell as **App Shell / Dashboard** first, then classify repeated regions as **Sidebar Navigation**, **KPI / Metric Cards**, **Data Table**, **Filter / Toolbar**, or another grounded app-ui pattern. Do not force these into hero/features/CTA buckets.

**How to extract the prefix map from any page:**
```bash
# Extract all CSS Module prefixes from an HTML file
grep -oE '[A-Z][a-zA-Z]+_[a-zA-Z]+__[a-zA-Z0-9]+' page.html | sed 's/_[a-zA-Z]*__[a-zA-Z0-9]*$//' | sort -u

# Count elements per prefix (to see section sizes)
for prefix in $(grep -oE '[A-Z][a-zA-Z]+_' page.html | sort -u); do
  echo "$(grep -c "$prefix" page.html) $prefix"
done | sort -rn
```

---

## 1. Navigation

The topmost persistent element on every page — logo, links, and primary CTA. Usually fixed or sticky, often changes appearance on scroll.

**CSS Module Identification:**
- Prefixes: `Header_`, `Nav_`, `Navigation_`, `TopBar_`
- HTML signals: `<header>`, `<nav>`, or first child of `<body>` before `<main>`
- CSS signals: `position: fixed` or `sticky`, `z-index` > 100, `backdrop-filter: blur()`
- Content signals: Logo image/SVG, horizontal link list, CTA button at far right

### Sub-patterns

- **Fixed/Sticky Nav**: Stays pinned to viewport top on scroll. Look for `position: fixed/sticky`, high `z-index`, and scroll-triggered background transitions (transparent → solid with shadow). State captured via `data-scrolled="true"` or `data-transparent-header="false"`.
- **Transparent → Solid Nav**: Starts transparent over hero section, gains background color + shadow after scroll threshold. Text color often inverts (white → dark). May swap logo variants (light → dark).
- **Hamburger Menu (Mobile)**: Three-line icon replaces horizontal links below a breakpoint. Panel types: slide-in from right, full-screen overlay, or dropdown push. Look for `@media` queries toggling `display: none` on the desktop nav and `display: block` on the mobile menu.
- **Mega Menu**: Wide dropdown with multi-column link groups, possibly containing images, icons, or featured content. Triggered by hover or click. CSS: `position: absolute`, large `width` or `left: 0; right: 0`, grid layout inside.

**Key CSS properties to extract:**
1. `position` + `top` + `z-index` (sticky/fixed behavior)
2. Background color in both default and scrolled states
3. `backdrop-filter` value (blur amount for glass effect)
4. Nav height (default and scrolled — often shrinks)
5. Transition properties for scroll-state change

### Reconstruction Strategy

**Component structure:** Client component — always needs scroll state detection and mobile toggle. Sticky wrapper → flex container → logo + nav links + CTA button. Export as `<NavBar>` with a `transparent` prop for hero overlay mode.

**Tailwind approach:**
- `sticky top-0 z-50` for fixed positioning
- `backdrop-blur-md bg-white/80 dark:bg-gray-950/80` for glass effect
- `transition-all duration-200` for scroll state changes
- `h-16 data-[scrolled=true]:h-14` for height shrink on scroll
- `border-b border-transparent data-[scrolled=true]:border-border` for scroll separator

**Responsive:** Mobile-first — hamburger menu visible by default via `md:hidden`. Desktop nav links hidden by default, shown with `hidden md:flex md:items-center md:gap-6`. Mobile menu is a separate `<div>` toggled by state, not a CSS-only solution.

**Animation:** CSS-only via `data-scrolled` attribute toggling Tailwind classes. Scroll detection via `useEffect` + `window.scrollY > threshold`. No animation library needed. Mobile menu transition: `transition-transform duration-300` with `translate-x-full` → `translate-x-0`.

**Common pitfalls:**
- Forgetting the transparent → solid transition on hero pages (requires tracking scroll position and passing it as a data attribute)
- Z-index wars with modals/overlays — use the z-index scale from `tokens.ts` (`z-nav: 50`, `z-modal: 100`)
- Mobile menu accessibility — needs `aria-expanded`, focus trap, `Escape` key to close
- Logo swap (light → dark variant) when nav transitions from transparent to solid — use two `<Image>` tags with conditional opacity, not src swap

---

## 2. Hero

The first major visual section — makes the first impression. Contains the primary headline, value proposition, and main call-to-action. Almost always the first child of `<main>`.

**CSS Module Identification:**
- Prefixes: `Hero_`, `Banner_`, `Masthead_`, `Jumbotron_`, `Landing_`
- HTML signals: First `<section>` or large `<div>` inside `<main>`
- CSS signals: Large font-size (40px+), full-width background, generous padding (80px+)
- Content signals: Single H1, subtitle text, 1-2 CTA buttons, possibly background video/image

### Sub-patterns

- **Split Hero**: Image/video on one side, text on the other. CSS: `grid-template-columns: 1fr 1fr` or `display: flex` with two equal children. Mobile: stacks vertically. Image side may have device frames, shadows, or slight 3D perspective transforms.
- **Centered Hero**: All text centered, full-width background (color, gradient, or image). Stack order: optional eyebrow label → H1 → subtitle → CTA button(s). CSS: `text-align: center`, `max-width` on text container. Most common hero variant.
- **Video Background Hero**: `<video>` element or CSS `background-image` with video poster. CSS: `position: relative; overflow: hidden` on wrapper, `position: absolute; object-fit: cover` on video. Semi-transparent overlay ensures text readability.
- **Animated Hero**: Elements animate on load or in response to scroll/mouse. Look for `@keyframes` definitions, `animation` properties, `IntersectionObserver` triggers, or canvas/WebGL elements. Saved snapshots capture a single frame — elements may appear with `opacity: 0` or `transform` offsets.

**Key CSS properties to extract:**
1. H1 `font-size` / `font-weight` / `line-height` / `letter-spacing`
2. Section `padding-top` / `padding-bottom` (vertical rhythm)
3. Background treatment (color, gradient, image, video overlay)
4. CTA button styles (primary + secondary variants)
5. `max-width` on text container (controls line length)

### Reconstruction Strategy

**Component structure:** Server component by default — hero is static content on most pages. Wrap in a `<section>` with `id="hero"`. Split hero uses a two-column grid: `<div>` for text + `<div>` for image/media. Centered hero uses a single column with `text-align: center`. Make it a client component only if it has a countdown timer, typed text animation, or video play controls.

**Tailwind approach:**
- `min-h-[80vh] flex items-center` or `py-24 lg:py-32` for vertical space
- `max-w-3xl mx-auto text-center` for centered hero text constraint
- `text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl` for responsive H1
- `text-lg text-muted-foreground max-w-2xl` for subtitle
- `grid grid-cols-1 lg:grid-cols-2 gap-12 items-center` for split layout

**Responsive:** Mobile-first — single column stack default. Split hero image drops below text on mobile. H1 scales up: `text-4xl → sm:text-5xl → lg:text-6xl`. CTA buttons stack vertically on mobile via `flex flex-col sm:flex-row gap-3`.

**Animation:** Staggered fade-in on mount — use CSS `@keyframes fadeInUp` with `animation-delay` per element (heading 0ms, subtitle 100ms, CTAs 200ms). No JS animation library needed for simple entrance. For typed text or video heroes, use a client component boundary around just the animated element.

**Common pitfalls:**
- Background images without `next/image` `priority` flag — causes LCP regression. Hero images must always use `priority` prop
- Text unreadable over images — always extract and apply the overlay (semi-transparent gradient or solid color with opacity)
- Cumulative Layout Shift — set explicit `min-h` on hero to reserve vertical space before fonts/images load
- Split hero image not sized correctly — use `relative aspect-[4/3]` container with `next/image fill` and `object-cover`

---

## 3. Features

Showcases product capabilities, benefits, or key selling points. Typically a grid or alternating rows of icon/image + heading + description units.

**CSS Module Identification:**
- Prefixes: `Feature_`, `Features_`, `Benefit_`, `Capabilities_`, `Solution_`
- HTML signals: Repeated card-like `<div>` siblings inside a grid/flex container
- CSS signals: `display: grid` with `grid-template-columns: repeat(3, 1fr)` or `display: flex; flex-wrap: wrap`
- Content signals: Icon/illustration + heading + short description, repeated 3-6 times

### Sub-patterns

- **Feature Grid (3-4 columns)**: Uniform card grid. Each card has icon + title + description. Responsive: 3→2→1 or 4→2→1. CSS: `display: grid`, uniform `gap`. Cards may have background, border, or shadow on hover.
- **Bento Grid**: Asymmetric grid where some cells span 2 columns or rows (Apple-style). Mixed content types per cell. CSS: explicit `grid-column: span 2` or `grid-row: span 2` rules. Each cell may have distinct background treatment.
- **Alternating Image+Text Rows**: Row 1: image left, text right. Row 2: reversed. Classic feature walkthrough layout. CSS: grid with `:nth-child(even)` reversing column order, or flex with `flex-direction: row-reverse`.
- **Feature Tabs / Switcher**: Tab bar or pill toggle switches between content panels. Shows multiple features without vertical scrolling. Look for `[data-state="active"]` on tabs and corresponding panel visibility toggles.

**Key CSS properties to extract:**
1. Grid template (`grid-template-columns`, `gap`)
2. Card styles (padding, background, border-radius, shadow, hover state)
3. Icon size and color treatment
4. Responsive breakpoints and column count changes
5. Section heading + subheading typography

### Reconstruction Strategy

**Component structure:** Server component — feature grids are static content. Section wrapper → section heading + subheading → grid container → feature cards. For feature tabs/switcher, wrap only the tab controller in a client component; keep individual tab panel content as server-rendered children.

**Tailwind approach:**
- `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8` for standard 3-column grid
- `rounded-xl border bg-card p-6 shadow-sm hover:shadow-md transition-shadow` for cards
- `text-primary` on icons, `size-10` for icon containers
- Bento grid: `grid-cols-2 lg:grid-cols-3` with specific children using `col-span-2` or `row-span-2`

**Responsive:** Grid collapses: `3→2→1` or `4→2→1`. Use `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`. Alternating image+text rows reverse via `lg:grid-cols-2` with even items using `lg:[&>*:first-child]:order-2` or a manual `flex-row-reverse`.

**Animation:** Scroll-triggered fade-in per card with staggered delay. Use `IntersectionObserver` hook + CSS classes: `opacity-0 translate-y-4` → `opacity-100 translate-y-0 transition-all duration-500`. Stagger via inline `style={{ transitionDelay: index * 100 + 'ms' }}`.

**Common pitfalls:**
- Inconsistent icon sizing — extract exact dimensions from source and enforce uniform `width`/`height` on all icons
- Cards with unequal content length breaking grid alignment — use `grid` (not flex) and cards stretch naturally
- Bento grid cells not spanning correctly on mobile — reset all spans to `col-span-1` at small breakpoints
- Feature tabs losing SEO content — render all tab panels in HTML, hide inactive with CSS (not conditional rendering)

---

## 4. Social Proof — Testimonials

Customer quotes that build trust. Presented as blockquotes, cards, or carousel slides with attribution (name, role, company, avatar).

**CSS Module Identification:**
- Prefixes: `Testimonial_`, `Quote_`, `Review_`, `Social_`, `CaseStudy_`
- HTML signals: `<blockquote>` elements, avatar `<img>` tags, star rating elements
- CSS signals: Quote mark pseudo-elements (`::before { content: '"' }`), card-based layout
- Content signals: Quote text in italics or with quotation marks, person name + title, company name, avatar photo

### Sub-patterns

- **Testimonial Carousel**: One testimonial visible at a time, navigated by dots or arrows. CSS: `overflow: hidden` container with `translateX` on inner track. Look for navigation dots, auto-advance interval, and transition timing.
- **Testimonial Grid / Masonry**: Multiple testimonials displayed simultaneously in a grid. Varying card heights create a masonry effect. CSS: `columns` property for CSS-only masonry, or grid with `grid-auto-rows: min-content`.
- **Single Featured Quote**: One large, prominent testimonial — often with a larger avatar, company logo, and emphasized styling. Used for high-profile customer quotes.
- **Video Testimonials**: Thumbnail grid with play buttons. Click opens video in lightbox or inline player. Look for `<video>` or YouTube/Vimeo embed wrappers.

**Key CSS properties to extract:**
1. Card/quote styling (background, border, border-radius, padding, shadow)
2. Quote typography (font-style, font-size, line-height)
3. Avatar dimensions and shape (`border-radius: 50%` for circle)
4. Attribution text hierarchy (name bold, role lighter)
5. Carousel transition properties (duration, easing, auto-advance)

### Reconstruction Strategy

**Component structure:** Client component for carousels (needs active index state + navigation). Server component for static grids. Carousel: outer container with `overflow-hidden` → inner track with `translateX` → individual slide cards. Grid: standard card grid like features.

**Tailwind approach:**
- Card: `rounded-xl border bg-card p-6` with `relative` for decorative quote mark
- Quote mark: `before:content-['"'] before:absolute before:top-4 before:left-4 before:text-6xl before:text-muted-foreground/20 before:font-serif`
- Avatar: `size-12 rounded-full object-cover`
- Attribution: `font-semibold text-sm` for name, `text-muted-foreground text-sm` for role

**Responsive:** Carousel stays single-item across breakpoints — adjust card padding. Grid: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`. Masonry: use `columns-1 md:columns-2 lg:columns-3 gap-6` with `break-inside-avoid` on cards.

**Animation:** Carousel transitions via `transition-transform duration-500 ease-in-out` on the track element. Change `translateX` by slide width per active index. Auto-advance via `useEffect` + `setInterval` — clear on unmount and pause on hover. No animation library needed.

**Common pitfalls:**
- Carousel not accessible — add `aria-roledescription="carousel"`, `aria-label` on slides, keyboard arrow navigation
- Auto-advance not pausing on hover/focus — users can't read the quote before it slides away
- Masonry layout with CSS `columns` causes cards to split across columns — add `break-inside-avoid` to every card
- Quote marks rendering as text content instead of decorative — use `::before` pseudo-element so screen readers skip them

---

## 5. Social Proof — Logo Cloud

A row or grid of customer/partner logos demonstrating market validation. Usually grayscale with optional hover colorize effect.

**CSS Module Identification:**
- Prefixes: `Logo_`, `Customer_`, `CustomerMarquee_`, `Brand_`, `Clients_`, `TrustedBy_`
- HTML signals: Row of `<img>` or `<svg>` elements, all similarly sized, inside a flex/grid container
- CSS signals: `filter: grayscale(1)`, `opacity: 0.5-0.7`, uniform `max-height` on images
- Content signals: Company logos (small, uniform height), "Trusted by" or "Used by" heading

### Sub-patterns

- **Static Logo Row**: Single row of logos, centered or space-between. Wraps on mobile. CSS: `display: flex; align-items: center; justify-content: center; gap: ...; flex-wrap: wrap`. Logos share a `max-height` (24-40px typically).
- **Marquee / Auto-Scroll**: Infinite horizontal scroll animation. CSS: `@keyframes marquee { from { transform: translateX(0) } to { transform: translateX(-50%) } }` with duplicated logo set. `animation: marquee Ns linear infinite`.
- **Multi-Row Logo Grid**: 2-3 rows of logos for sites with many customers. CSS: standard grid layout. May include "and N more" text.

**Key CSS properties to extract:**
1. Logo `max-height` or `height` (controls uniform sizing)
2. `filter: grayscale()` + `opacity` values (and hover restore)
3. Container `gap` between logos
4. Marquee `animation` (duration, direction) if present
5. Section heading text and typography ("Trusted by 1,000+ companies")

### Reconstruction Strategy

**Component structure:** Client component if marquee animation is present (needs CSS animation + duplication logic). Server component for static logo rows. Marquee: outer `overflow-hidden` div → inner flex container with logos duplicated 2× → CSS `@keyframes` drives infinite scroll.

**Tailwind approach:**
- Static row: `flex flex-wrap items-center justify-center gap-x-8 gap-y-6`
- Logo images: `h-8 w-auto grayscale opacity-60 hover:grayscale-0 hover:opacity-100 transition-all duration-300`
- Marquee wrapper: `flex gap-8 animate-marquee` (define `marquee` keyframe in `tailwind.config.ts`)
- Section heading: `text-center text-sm font-medium text-muted-foreground uppercase tracking-wider`

**Responsive:** Static row wraps naturally with `flex-wrap`. Marquee works at all sizes — adjust `gap` and logo `h-6 sm:h-8` for smaller screens. Consider showing fewer logos on mobile by hiding extras with `hidden sm:block` on overflow items in static rows.

**Animation:** Pure CSS — define in `tailwind.config.ts` under `extend.keyframes`: `marquee: { '0%': { transform: 'translateX(0)' }, '100%': { transform: 'translateX(-50%)' } }` and `extend.animation`: `marquee: 'marquee 30s linear infinite'`. Duplicate the logo set in JSX so content is seamless.

**Common pitfalls:**
- Marquee gap visible at seam point — you must duplicate the full logo set (render logos twice in the track) so the second set fills the gap as the first scrolls out
- Logo heights inconsistent — enforce uniform `h-8` and let `w-auto` handle varying aspect ratios. Never set both width and height
- Grayscale filter not working on SVGs — SVGs with inline `fill` colors ignore CSS `grayscale()`. Convert SVG fills to `currentColor` and control color via parent `text-gray-400 hover:text-original`
- `prefers-reduced-motion` not respected — add `motion-reduce:animate-none` to the marquee container

---

## 6. Social Proof — Stats

Large numeric values with labels that quantify credibility. Often animated with count-up effect on scroll into view.

**CSS Module Identification:**
- Prefixes: `Stats_`, `Metrics_`, `Numbers_`, `Counter_`, `Impact_`
- HTML signals: Large numbers in headings or spans, accompanied by descriptive labels
- CSS signals: Very large `font-size` (48px-80px) on numbers, `font-weight: 700-900`, `font-variant-numeric: tabular-nums`
- Content signals: Formatted numbers ("10M+", "99.9%", "150+"), unit labels ("users", "uptime", "countries")

### Sub-patterns

- **Inline Stats Row**: 3-4 stats side by side in a single row. CSS: `display: flex` or `display: grid` with equal columns. Each stat: large number above, smaller label below. Often separated by vertical dividers.
- **Stats with Icons**: Each stat paired with an icon or illustration. Icon sits above or beside the number. Adds visual interest to pure numeric data.
- **Animated Counter**: Numbers count up from 0 to target value when scrolled into view. Implementation: JavaScript with `IntersectionObserver` trigger. In saved snapshots, you'll see the final value since JS has already executed.

**Key CSS properties to extract:**
1. Number `font-size` / `font-weight` / `color` (the hero element of this section)
2. Label typography (size, color, text-transform)
3. Container layout (flex/grid, gap, alignment)
4. Divider styles between stat items (border, pseudo-element)
5. Section background (often contrasting to stand out)

### Reconstruction Strategy

**Component structure:** Client component — count-up animation requires `IntersectionObserver` and state. Each stat item: number `<span>` + label `<span>` inside a flex column. Wrap all stats in a grid. Create a `useCountUp(target, duration)` hook that returns the current animated value.

**Tailwind approach:**
- Container: `grid grid-cols-2 lg:grid-cols-4 gap-8` or `flex flex-wrap justify-center gap-12`
- Base card: `rounded-2xl border bg-card p-8`
- Highlighted card: `border-primary ring-2 ring-primary/20 shadow-lg relative` with badge `absolute -top-4 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-xs font-semibold px-3 py-1 rounded-full`
- Price: `text-5xl font-bold` for amount, `text-base text-muted-foreground` for period
- Feature list: `space-y-3` with check icon `text-primary size-4 shrink-0` + `text-sm`

**Responsive:**
- Desktop: `grid-cols-4` → `grid-cols-3` → `grid-cols-2` → `grid-cols-1`
- Tablet: `grid-cols-3` → `grid-cols-2` → `grid-cols-1`
- Mobile: `grid-cols-2` → `grid-cols-1`

**Animation:** `useEffect` + `IntersectionObserver` to detect when stats enter viewport. On intersection, animate from 0 to target value over ~2 seconds using `requestAnimationFrame`. Format numbers with locale-aware `Intl.NumberFormat` for commas/decimals. Fire the animation only once — track that with a ref flag.

**Common pitfalls:**
- Count-up animation causing layout shift — numbers change width as digits increase. Fix with `tabular-nums` font feature and `min-w-[ch-count]` or fixed-width container
- Number formatting differences (US: "1,000" vs EU: "1.000") — use `Intl.NumberFormat` with the site's locale from `tokens.ts`
- Stats not triggering animation on fast scroll — set `IntersectionObserver` threshold to `0.3` not `1.0`
- Suffix/prefix handling ("+", "%", "M") — separate from the animated number so formatting doesn't interfere with the count-up

---

## 7. Pricing

Displays available plans with prices, features, and per-plan CTAs. Almost always includes a billing toggle (monthly/annual) and a visually highlighted "recommended" plan.

**CSS Module Identification:**
- Prefixes: `Pricing_`, `Plans_`, `Plan_`, `PricingCard_`, `PlanToggle_`, `Tiers_`
- HTML signals: Dollar/euro signs in text, `/month` or `/year` suffixes, toggle/switch elements
- CSS signals: Card with `transform: scale(1.05)` or distinct `border`/`box-shadow` (highlighted plan)
- Content signals: Plan names ("Starter", "Pro", "Enterprise"), price values, feature checklists, CTA button per card

### Sub-patterns

- **Standard Pricing Cards**: 2-4 plan cards side by side. Popular/recommended plan visually emphasized (larger scale, colored border, "Most Popular" badge). Monthly/annual toggle switches displayed prices. Each card: plan name → price → feature list → CTA button.
- **Pricing Table**: Full feature-comparison matrix. Features as rows, plans as columns. Cells contain checkmarks, crosses, or specific values. Sticky header with plan names. Mobile: often collapses into individual cards or horizontal scroll.
- **Enterprise / Custom CTA**: Separate "Contact Sales" card or section. Distinct from standard plans — may have darker background, custom illustration, or a list of enterprise-specific features with a contact form link.

**Key CSS properties to extract:**
1. Card dimensions, padding, border-radius, background
2. Highlighted plan treatment (border color, scale, badge position/style)
3. Price typography (currency symbol size vs. amount size vs. period size)
4. Toggle/switch component styles (track, thumb, active state)
5. Feature list check/cross icon styles and spacing

### Reconstruction Strategy

**Component structure:** Client component — billing toggle (monthly/annual) requires state that updates displayed prices. Top-level: section heading + toggle + card grid. Toggle is a `<button>` or pair of buttons with `aria-pressed`. Cards receive `billingPeriod` as prop. Each card: plan name → price block → feature list → CTA button. Highlighted card gets a wrapper `<div>` with badge.

**Tailwind approach:**
- Card grid: `grid grid-cols-1 md:grid-cols-3 gap-8 items-start`
- Base card: `rounded-2xl border bg-card p-8`
- Highlighted card: `border-primary ring-2 ring-primary/20 shadow-lg relative` with badge `absolute -top-4 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-xs font-semibold px-3 py-1 rounded-full`
- Price: `text-5xl font-bold` for amount, `text-base text-muted-foreground` for period
- Feature list: `space-y-3` with check icon `text-primary size-4 shrink-0` + `text-sm`

**Responsive:**
- Desktop: `grid-cols-3` → `grid-cols-2` → `grid-cols-1`
- Tablet: `grid-cols-2` → `grid-cols-1`
- Mobile: `grid-cols-1`

**Animation:**
- Toggle state change can crossfade prices: wrap price in a container with `transition-opacity duration-200`.
- On toggle, briefly set `opacity-0`, update price, then `opacity-100`.
- No library needed — `useState` + `useEffect` with a short timeout.

**Common pitfalls:**
- Price display not updating when toggle changes — ensure price data structure maps both monthly and annual prices per plan, not just one
- "Most Popular" badge clipped by overflow — parent card needs `overflow-visible` or badge must be inside the card's padding area
- Feature list check/cross alignment — use `flex items-start gap-2` not `items-center` (multi-line features misalign with center)
- Annual price "Save X%" badge calculation — compute from actual monthly vs annual values in data, never hardcode

---

## 8. Comparison Tables

Side-by-side feature comparison between plans, products, or your product vs. competitors. Structured as a data grid with rows of features and columns of options.

**CSS Module Identification:**
- Prefixes: `Comparison_`, `Compare_`, `Matrix_`, `FeatureTable_`, `Versus_`
- HTML signals: `<table>` element, or grid of aligned cells, checkmark/cross icons
- CSS signals: `border-collapse`, alternating row backgrounds, sticky `<thead>`
- Content signals: Feature names in left column, checkmarks (✓/✗) or values in plan columns

### Sub-patterns

- **HTML Table**: Standard `<table>` with `<thead>` for plan names and `<tbody>` for feature rows. CSS: sticky header, row hover, alternating `background-color`. Most semantically correct approach.
- **CSS Grid Table**: Grid-based layout simulating a table. CSS: `display: grid; grid-template-columns: 2fr repeat(N, 1fr)` where N = number of plans. Allows more flexible cell styling than `<table>`.
- **Collapsible Feature Groups**: Features organized into categories (e.g., "Security", "Support") that expand/collapse. Reduces visual overwhelm for long feature lists. Look for category headers with expand/collapse behavior.

**Key CSS properties to extract:**
1. Column widths (feature label column vs. value columns)
2. Header styling (sticky position, background, typography)
3. Cell content format (checkmark icon, text value, tooltip)
4. Row styling (padding, border-bottom, alternate background)
5. Highlighted column treatment (background tint, top border accent)

### Reconstruction Strategy

**Component structure:** Server component for static tables. Client component only if collapsible feature groups or horizontal scroll controls are needed. Use semantic `<table>` with `<thead>` and `<tbody>` when possible — better accessibility than CSS grid tables. For collapsible groups, wrap each group's `<tbody>` in a client component that manages open/closed state.

**Tailwind approach:**
- Table wrapper: `overflow-x-auto -mx-4 px-4` (horizontal scroll on mobile without page bleed)
- Table: `w-full text-sm`
- Header: `sticky top-0 bg-background/95 backdrop-blur-sm` with `text-left font-semibold text-sm p-4`
- Rows: `border-b` with `even:bg-muted/50` for alternating backgrounds
- Checkmark cell: `text-center text-primary` with inline SVG check icon
- Highlighted column: `bg-primary/5` on header + all cells in that column

**Responsive:**
- Tables are inherently difficult on mobile. Two strategies: (1) horizontal scroll with `overflow-x-auto` and `min-w-[640px]` on the table, (2) collapse into individual cards per plan. Choose (1) for 3 columns or fewer, (2) for 4+.
- Sticky header needs `z-10` when combined with horizontal scroll.

**Animation:**
- Collapsible groups use `grid-rows` animation pattern: container with `grid grid-rows-[0fr]` → `grid-rows-[1fr]` on open, inner content with `overflow-hidden`.
- Smoother than `max-height` because it doesn't need a hardcoded max.
- Rotate chevron icon with `transition-transform duration-200`.

**Common pitfalls:**
- Sticky header not working inside `overflow-x-auto` — this is a known CSS limitation. Solution: make the header sticky via JavaScript `position: fixed` mirroring, or accept non-sticky header on mobile
- Checkmark/cross icons inconsistent sizes — standardize on `size-4` for all cell icons
- Column highlighting breaking on hover row — use `relative z-0` on rows and `z-[-1]` on column background pseudo-elements
- Feature group collapse animation jerky — `max-height` approach requires guessing a max value. Use the `grid-rows-[0fr]` technique instead

---

## 9. CTA (Call-to-Action)

A conversion-focused section, typically near the bottom of the page (pre-footer). Designed to stand out with contrasting colors, large text, and prominent button(s).

**CSS Module Identification:**
- Prefixes: `CTA_`, `CallToAction_`, `Prefooter_`, `GetStarted_`, `SignUp_`
- HTML signals: `<form>` with email input, prominent `<button>`, isolated section with minimal elements
- CSS signals: Contrasting background (often brand color or dark), large padding, `text-align: center`
- Content signals: Action-oriented heading ("Get started today", "Try free for 14 days"), single or dual buttons

### Sub-patterns

- **Full-Width CTA Band**: Contrasting background color or gradient. Large heading + optional subtitle + 1-2 CTA buttons. Centered text, generous padding (80px+). Purely conversion-focused — no distracting content.
- **Newsletter / Email Signup**: Email input field + submit button, arranged inline (desktop) or stacked (mobile). May include privacy text or success state. CSS: `display: flex` on input+button group, custom input styling.
- **Card CTA**: CTA content inside a card with distinct background, border-radius, and shadow. Floats visually above the page background. Often contains a small illustration or icon alongside text.
- **Floating / Sticky CTA**: Fixed-position button or mini-bar that follows user on scroll. Appears after a scroll threshold (hero passes out of view). CSS: `position: fixed; bottom: 0`, entrance animation via `transform: translateY`.

**Key CSS properties to extract:**
1. Section background (color, gradient — must contrast with rest of page)
2. Heading typography (size, weight, color against the CTA background)
3. Button styles (primary + optional secondary variant)
4. Section padding (usually much larger than other sections)
5. Input field styles if email signup (border, radius, placeholder color)

### Reconstruction Strategy

**Component structure:** Server component for pure button CTAs. Client component only if it contains an email signup form (needs form state, validation, submission). Section wrapper with contrasting background → centered container → heading + subtitle + action area (buttons or form).

**Tailwind approach:**
- Section: `bg-primary text-primary-foreground py-24` or `bg-gradient-to-r from-primary to-primary/80 py-24`
- Container: `max-w-2xl mx-auto text-center px-4`
- Heading: `text-3xl font-bold sm:text-4xl`
- Button on dark bg: `bg-white text-primary hover:bg-white/90 font-semibold px-8 py-3 rounded-lg`
- Email form: `flex flex-col sm:flex-row gap-3 max-w-md mx-auto` with input `flex-1 rounded-lg bg-white/10 border-white/20 text-white placeholder:text-white/60 px-4 py-3`

**Responsive:**
- Buttons stack vertically on mobile: `flex flex-col sm:flex-row gap-3`.
- Email input + submit button stack the same way.
- Section padding reduces slightly on mobile: `py-16 sm:py-24`.
- Heading scales down: `text-2xl sm:text-3xl lg:text-4xl`.

**Animation:**
- Minimal — this section should feel stable and confident, not flashy.
- Optional: subtle fade-in on scroll.
- If card CTA variant, a gentle `hover:-translate-y-1 transition-transform` on the card wrapper.
- Floating/sticky CTA enters from bottom with `translate-y-full → translate-y-0` triggered by scroll position.

**Common pitfalls:**
- Button contrast insufficient on gradient backgrounds — test both ends of the gradient for WCAG AA compliance
- Email form submission without client-side validation — at minimum validate email format before sending
- Floating CTA covering footer content — dismiss it when footer is in viewport, or add sufficient `padding-bottom` to `<body>`
- CTA section gradient not matching brand colors from `tokens.ts` — always pull colors from the extracted token values, never eyeball hex codes

---

## 10. FAQ

Frequently asked questions displayed as expandable question/answer pairs. Reduces support load and addresses objections near the conversion point.

**CSS Module Identification:**
- Prefixes: `FAQ_`, `Accordion_`, `Questions_`, `Help_`
- HTML signals: `<details>` / `<summary>` elements, or custom divs with expand/collapse behavior
- CSS signals: `max-height` transitions, `overflow: hidden`, rotating chevron/plus icon via `transform: rotate`
- Content signals: Question text (often bold) followed by answer text, expand/collapse indicator icon

### Sub-patterns

- **Native Details/Summary**: Uses HTML `<details>` and `<summary>` elements. Browser-native expand/collapse. CSS customizes the marker/icon via `summary::marker` or `summary::-webkit-details-marker`. Accessible by default.
- **Custom Accordion**: Custom `<div>` implementation with JavaScript toggle. CSS: `max-height: 0; overflow: hidden; transition: max-height 0.3s` for collapse animation. State tracked via `data-state="open"` or `aria-expanded="true"`.
- **Two-Column FAQ**: Questions split into two columns at desktop widths. CSS: `columns: 2` or `display: grid; grid-template-columns: 1fr 1fr`. Collapses to single column on mobile.

**Key CSS properties to extract:**
1. Question text styling (font-weight, font-size, padding, cursor: pointer)
2. Answer text styling (font-size, line-height, color — often lighter than question)
3. Expand/collapse icon (type: chevron/plus/arrow, rotation degrees, transition)
4. Item separator (border-bottom style, color, width)
5. Open/closed state transitions (max-height, opacity, timing)

### Reconstruction Strategy

**Component structure:** Client component — always needs expand/collapse state. Create a `<FAQItem>` client component that manages its own open/closed state. Parent section (server) renders heading + maps data to `<FAQItem>` children. Each item: `<button>` trigger (question + icon) → collapsible `<div>` (answer). Use `aria-expanded` on the button and `role="region"` on the answer.

**Tailwind approach:**
- Item wrapper: `border-b border-border`
- Question button: `flex w-full items-center justify-between py-4 text-left font-medium hover:text-primary transition-colors`
- Chevron icon: `size-5 shrink-0 text-muted-foreground transition-transform duration-200 data-[state=open]:rotate-180`
- Answer container: `grid grid-rows-[0fr] transition-[grid-template-rows] duration-300 data-[state=open]:grid-rows-[1fr]`
- Answer inner: `overflow-hidden` → answer text with `pb-4 text-muted-foreground leading-relaxed`

**Responsive:**
- FAQ layout works well at all sizes by default.
- Two-column FAQ uses `lg:columns-2 lg:gap-x-8`.
- Max-width on the FAQ container: `max-w-3xl mx-auto` keeps lines readable.

**Animation:**
- Use the CSS Grid rows technique for smooth expand/collapse: parent toggles between `grid-rows-[0fr]` and `grid-rows-[1fr]`, child has `overflow-hidden`.
- This is smoother than `max-height` because it doesn't require a hardcoded max value.
- Chevron rotation via `transition-transform duration-200 rotate-180`.
- No animation library needed.

**Common pitfalls:**
- Using `max-height: 999px` for open state — causes visible delay on short answers because the transition covers the full `999px` range. Use the `grid-rows` technique instead
- Missing keyboard accessibility — the question must be a `<button>`, not a `<div>` with `onClick`. It must respond to Enter and Space keys
- Multiple items open simultaneously when only one should be — decide upfront: independent (each item has its own state) or exclusive (accordion with single shared state)
- Answer content flashing on page load — ensure the initial state is closed in both JS state and CSS to avoid hydration mismatch

---

## 11. Content Sections (Blog, Team, Timeline, About)

Umbrella category for information-dense sections that don't fit the conversion-focused patterns above. Prioritize readability and content hierarchy.

**CSS Module Identification:**
- Prefixes: `Blog_`, `Post_`, `Article_`, `News_` (blog); `Team_`, `People_`, `Leadership_` (team); `Timeline_`, `History_`, `Roadmap_` (timeline); `About_`, `Story_`, `Mission_` (about)
- HTML signals: `<article>` elements, person photo grids, ordered/sequential items, rich text blocks
- CSS signals: `max-width: 65ch-75ch` (prose), `columns` property, ordered list styling
- Content signals: Dates, author names, reading time, person photos with bios, milestone descriptions

### Sub-patterns — Blog

- **Blog Card Grid**: Card grid with featured image + title + excerpt + meta (date, author, category). CSS: grid of 3→2→1 columns. Card hover lifts (translateY + shadow increase). Image aspect ratio constrained via `aspect-ratio` or `padding-top` trick.
- **Blog Post Detail**: Full article page. Heading + meta + hero image → long-form prose body. CSS: `max-width: 65ch-75ch` on prose container for optimal readability. Typography system for h2-h4, blockquotes, code blocks, images, lists.

### Sub-patterns — Team

- **Team Grid**: Photo + name + role + optional social links per member. Grid: 4→3→2→1 responsive. Photo often circular (`border-radius: 50%`) or rounded rectangle. Hover may reveal social icons or colorize grayscale photo.

### Sub-patterns — Timeline

- **Vertical Timeline**: Sequential items connected by a vertical line. Each item: date/label + content block, alternating left/right on desktop. CSS: `::before` pseudo-element for the connecting line, circular markers at each node.
- **Horizontal Timeline**: Fewer items (3-5 steps/milestones) arranged horizontally. Connected by horizontal line. CSS: `display: flex`, line via `::after` pseudo-element. Mobile: often converts to vertical.

### Sub-patterns — About

- **Mission / Values Section**: Large statement text + supporting content. CSS: large `font-size` for mission statement, grid for value cards. Often paired with full-bleed background image or illustration.

**Key CSS properties to extract:**
1. Prose `max-width` and `line-height` (readability fundamentals)
2. Card/grid layout and responsive behavior
3. Photo sizing, shape, and hover treatment
4. Timeline connector line styles (color, width, position)
5. Content typography hierarchy (h2, h3, body, meta text)

### Reconstruction Strategy

**Component structure:** Server component — content sections are almost always static. Blog card grid: section → grid → `<BlogCard>` components. Team grid: section → grid → `<TeamMember>` components. Timeline: section → ordered list with `<TimelineItem>` components. Make client only if filtering/search is needed (blog category filter).

**Tailwind approach:**
- Blog card grid: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8`
- Blog card: `group rounded-xl overflow-hidden border bg-card` with image `aspect-[16/9] object-cover group-hover:scale-105 transition-transform duration-300`
- Team grid: `grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-8`
- Team photo: `aspect-square rounded-full object-cover` or `rounded-xl` for rectangle
- Timeline line: `absolute left-4 top-0 bottom-0 w-px bg-border` with nodes `absolute left-2.5 size-3 rounded-full bg-primary border-2 border-background`
- Prose: `mx-auto max-w-[75ch] leading-relaxed` or an equivalent token-backed class set built from extracted typography values. Do not use `@tailwindcss/typography`; this skill forbids extra Tailwind plugins.

**Responsive:**
- Blog grid: `1→2→3` columns.
- Team grid: `2→3→4` columns.
- Timeline: single column on mobile (items stacked with left line), alternating left/right on `lg:` breakpoint.
- Prose sections are naturally responsive — constrain `max-width` and padding handles the rest.

**Animation:**
- Blog cards: `group-hover:scale-105` on image with `transition-transform duration-300` and `overflow-hidden` on card.
- Team photos: `grayscale hover:grayscale-0 transition-all duration-300` for the desaturate-on-hover effect.
- Timeline items: staggered scroll-triggered fade-in, alternating from left/right.

**Common pitfalls:**
- Blog card images with inconsistent aspect ratios — force `aspect-[16/9]` with `object-cover` on all thumbnail images
- Team member photo not loading — always provide a fallback avatar (initials or placeholder SVG) via `onError` handler or CSS background
- Timeline line not connecting properly — use `absolute` positioning on the line element relative to the timeline container, not individual items
- Prose content wider than viewport on mobile — ensure `overflow-x-hidden` on the prose container and `max-w-full` on any embedded code blocks or images

---

## 12. Footer

The final section of every page — contains navigation links, legal information, social icons, and brand elements. Almost always has a dark or contrasting background.

**CSS Module Identification:**
- Prefixes: `Footer_`, `SiteFooter_`, `Bottom_`
- HTML signals: `<footer>` semantic tag, `<nav>` elements inside footer, copyright text (`©`)
- CSS signals: Dark `background-color`, multi-column grid, smaller `font-size` (12-14px)
- Content signals: Link columns with category headings, social media icons, legal links (Privacy, Terms), copyright year, possibly newsletter signup

### Sub-patterns

- **Multi-Column Footer**: 3-5 columns of categorized links under headings (Product, Company, Resources, Legal). Top row: logo + tagline. Bottom bar: copyright + legal links + social icons. CSS: `display: grid; grid-template-columns: 2fr repeat(N, 1fr)` giving the brand column more space.
- **Minimal Footer**: Single row or two rows. Logo, a few essential links, social icons, copyright. CSS: `display: flex; justify-content: space-between; align-items: center`. Clean, compact.
- **Rich Footer**: Expansive footer with additional content: newsletter signup form, contact information, office addresses, app download badges, or embedded map. Multiple distinct sub-sections within `<footer>`.

**Key CSS properties to extract:**
1. Background color and any top border/gradient
2. Grid template for link columns (column count, widths, gap)
3. Link typography (color, hover color, font-size — usually smaller than body)
4. Column heading styles (font-weight, text-transform, letter-spacing)
5. Bottom bar separator (border-top) and layout

### Reconstruction Strategy

**Component structure:** Server component — footers are entirely static. Three-layer structure: top area (logo + tagline or newsletter), middle area (link columns grid), bottom bar (copyright + legal links + social icons). Each link column can be a simple mapped array. Social icons are inline SVG components.

**Tailwind approach:**
- Footer: `bg-gray-950 text-gray-400` (or extracted dark color from `tokens.ts`)
- Container: `max-w-7xl mx-auto px-4 py-12`
- Link columns grid: `grid grid-cols-2 md:grid-cols-4 gap-8` with brand column `col-span-2 md:col-span-1`
- Column heading: `text-sm font-semibold text-white uppercase tracking-wider mb-4`
- Links: `text-sm text-gray-400 hover:text-white transition-colors` with `space-y-3` for vertical spacing
- Bottom bar: `border-t border-gray-800 mt-12 pt-8 flex flex-col sm:flex-row justify-between items-center gap-4`
- Social icons: `size-5 text-gray-400 hover:text-white transition-colors`

**Responsive:**
- Link columns collapse: `grid-cols-2` on mobile → `md:grid-cols-4` or more on desktop.
- Brand column spans full width on mobile.
- Bottom bar stacks vertically on mobile: `flex-col` → `sm:flex-row`.
- Social icons stay as a horizontal row at all sizes.

**Animation:**
- None needed — footers should be stable and utilitarian.
- Only interactive element: link hover color transitions via `transition-colors duration-150`.
- No scroll animations, no fade-ins.

**Common pitfalls:**
- Copyright year hardcoded — use `{new Date().getFullYear()}` in JSX
- Footer link columns uneven height — this is fine; don't try to equalize. Use `items-start` on the grid
- Social icons using `<img>` tags for SVGs — use inline SVG components for color control via `currentColor`
- Footer newsletter form (if present) same as CTA form — reuse the same form component, don't rebuild

---

## 13. Next.js Implementation Patterns

Decision guidance for building extracted patterns in Next.js App Router.

### Server vs Client Component Decision Tree

| Pattern | Default | Make Client When |
|---------|---------|-----------------|
| Navigation | Client | Always — needs scroll state, mobile toggle |
| Hero | Server | Has countdown timer, typed text animation, or video controls |
| Features | Server | Has tabs/switcher interaction |
| Testimonials | Client | Has carousel navigation |
| Logo Cloud | Client | Has marquee animation |
| Stats | Client | Has count-up animation |
| Pricing | Client | Has billing toggle (monthly/annual) |
| Comparison | Client | Has collapsible rows or horizontal scroll |
| CTA | Server | Has email form |
| FAQ | Client | Always — needs expand/collapse state |
| Content (Blog) | Server | Has filtering or search |
| Footer | Server | Rarely needs interactivity |

### Image Optimization Per Pattern

| Pattern | Strategy |
|---------|----------|
| Hero background | `next/image` with `fill` + `priority` + `sizes="100vw"` |
| Feature icons | Inline SVG components (not next/image) |
| Testimonial avatars | `next/image` with fixed width/height, `sizes="48px"` |
| Logo cloud | `next/image` with `height={32}` + auto width |
| Team photos | `next/image` with `sizes="(max-width: 768px) 50vw, 25vw"` |
| Blog thumbnails | `next/image` with `sizes="(max-width: 768px) 100vw, 33vw"` |

### Font Loading Strategy

1. Download all fonts to `public/fonts/`
2. Define `@font-face` in `styles/globals.css` with `font-display: swap`
3. Create `next/font/local` instances in `lib/fonts.ts` for Next.js optimization
4. Apply via `className` on `<body>` or specific elements
5. NEVER use Google Fonts CDN or any external font URL

### Animation Approach Per Pattern

| Animation Type | Implementation | Example Pattern |
|----------------|---------------|-----------------|
| Scroll-triggered fade/slide | `useScrollAnimation` hook + CSS classes | Hero elements, feature cards |
| Infinite scroll/marquee | CSS `@keyframes` + `animation` (no JS) | Logo cloud |
| State toggle | `useState` + conditional classes | FAQ accordion, mobile menu |
| Hover effects | Tailwind `hover:` utilities (no JS) | Cards, buttons, links |
| Count-up numbers | `useEffect` + `IntersectionObserver` | Stats section |
| Carousel | `useState` for active index + CSS transform | Testimonials |

### Self-Hosting Checklist

Before marking any page complete:
- [ ] All `<img>` src attributes point to `/assets/images/...`
- [ ] All `@font-face` src attributes point to `/fonts/...`
- [ ] All SVG icons are inline components or in `/assets/icons/...`
- [ ] No `<link>` tags reference external stylesheets
- [ ] No `<script>` tags reference external scripts
- [ ] `next build` produces zero external URL warnings

---

## Capture- and Snapshot-Specific Patterns

These patterns matter when the source comes from either a saved snapshot or a live browser capture. Some are snapshot-specific, some are runtime-specific, and many appear in both.

Unless stated otherwise, `_files/` examples in this section mean the primary snapshot mode. In adjacent-asset mode, substitute the page's discovered CSS corpus and asset root.

### Mangled Image References
Images saved with CDN query strings baked into filenames:
```
f=auto,dpr=2,q=80,w=1200,h=630...
hero-image_files/image%3Fwidth%3D1200%26quality%3D80.webp
```
- These are real images — the naming is just how the browser saved them
- Check file size and extension to identify format
- Use context (parent CSS class, alt text, dimensions) to determine image purpose, not filename

### Shared CSS Files Across Pages
Same CSS file (same hash) appearing in multiple route captures or `_files/` folders:
- Deduplicate before frequency counting
- Shared CSS often contains the design system (`:root` variables, typography, color tokens)
- Search across all route artifacts before deciding a rule is page-specific

### Data Attributes for State
`data-highlighted="true"`, `data-state="open"`, `data-transparent-header="false"`:
- These indicate component variants or runtime states at the time the page was captured
- Look for matching CSS selectors such as `[data-highlighted="true"]`
- Document both states when the opposing state is recoverable from CSS or behavior evidence

### Runtime-Metadata Hints
In live-capture mode, inspect runtime artifacts for section clues:
- `__NEXT_DATA__`
- `self.__next_f`
- build IDs
- discovered chunk or manifest URLs
- route-level script/style lists

These do not replace DOM/CSS extraction, but they often reveal route scope and asset provenance.

### Scroll-Revealed Sections
Some routes look complete in the first viewport but reveal major sections only after scrolling:
- use full-page screenshots or scroll slices to verify section completeness
- do not assume the visible top viewport is the whole page
- if a section appears in screenshots but is weak in HTML, mark it for closer evidence review instead of omitting it

### Responsive Utility Classes
Compiled from CSS: `.hide-mobile`, `.hide-tablet`, `.show-tablet`, `.hide-laptop`:
- these are responsive visibility toggles
- look for `@media` queries targeting these classes in CSS files
- some elements in HTML may be invisible at certain viewports — document which

### Inline CSS Variables
`style="--height: 80px; --text-color: var(--color-text-tertiary);"`:
- these override design tokens at the element level
- resolve the referenced variables by searching the captured stylesheets
- document these overrides in the section's variable usage map

### SVG Files as Separate Assets
Icons and illustrations saved as separate files or discovered from runtime asset URLs:
- check `viewBox`, `fill`, and `stroke` for styling patterns
- icon sizing is often set by CSS on the container, not the SVG itself
- extract fill colors, stroke widths, and viewBox dimensions as design tokens when relevant

---

## Unknown Section Decision Flow

When you encounter a section you can't immediately classify, follow this flow:

**Step 1: Check semantic HTML tags**
- Has `<header>` → Navigation
- Has `<footer>` → Footer
- Has `<nav>` → Navigation (or footer nav if inside `<footer>`)
- Has `<main>` → Content wrapper, look at children
- Has `<aside>` → Sidebar or supplementary content
- None of the above → Continue to Step 2

**Step 2: Check CSS Module prefixes**
- Extract prefix: take text before first `_` in class names like `PrefixName_element__hash`
- Look up prefix in the Master Prefix Identification Table above
- Found → Use that section type
- Not found → Use the prefix name directly (e.g., `Workflow_` → "Workflow Section")
- No CSS Module classes → Continue to Step 3

**Step 3: Identify by content signals**
- Images in a uniform row → Logo cloud or partner logos
- Dollar/euro values with plan names → Pricing section
- Question text + expandable answers → FAQ
- Person photos + names + roles → Team section
- Large numbers + labels → Stats section
- Sequential items with dates → Timeline
- Large heading + 1-2 CTA buttons:
  - If first major section on page → Hero
  - If near the bottom / before footer → CTA section
- Grid of icon + heading + description cards → Features section
- Quote text + person attribution → Testimonial

**Step 4: Still unidentified?**
- Name it descriptively based on visible content (e.g., "Product Workflow Section", "Integration Showcase")
- Add a `NEEDS-REVIEW` tag in your documentation
- Check CSS files for additional context — the class names in CSS may be more descriptive than the HTML
