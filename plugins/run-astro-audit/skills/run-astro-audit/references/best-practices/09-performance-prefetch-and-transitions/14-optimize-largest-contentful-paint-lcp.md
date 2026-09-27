# Optimize Largest Contentful Paint (LCP) with Static Heroes and fetchpriority

> **Context:** Performance & Prefetch | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Largest Contentful Paint (LCP) marks the point when the page's main content has loaded. In modern web apps, poor LCP (>2.5s) is almost always caused by: (1) wrapping the hero element in a client-hydrated framework island, creating a script waterfall before rendering, or (2) lazy-loading the hero image without resource prioritization. Server-rendering the hero and annotating it with `fetchpriority="high"` drives LCP well below 1.2s.

## 2. How It Differs From Classic React / Next.js

In Next.js, `<Image priority />` injects a preload tag into `<head>`. In Astro, components are zero-JS HTML by default. You achieve optimal LCP natively by keeping the hero section as pure `.astro` static markup, preconnecting to asset origins, and applying `loading="eager"` + `fetchpriority="high"`.

## 3. Common Mistakes & Anti-Patterns

Wrapping the above-the-fold hero section in a React island with `client:load`, or applying `loading="lazy"` to the main hero image.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/index.astro
// Anti-pattern: Hero is an island, postponing DOM rendering until JS loads
import HeroIsland from '../components/HeroIsland.tsx';
---
<main>
  <HeroIsland client:load />
</main>
```

```tsx
// src/components/HeroIsland.tsx
export default function HeroIsland() {
  return (
    <div className="hero">
      <h1>Accelerate Your Growth</h1>
      {/* Anti-pattern: lazy loading the LCP candidate image */}
      <img src="/hero.webp" loading="lazy" alt="Hero overview" />
    </div>
  )
}
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/index.astro
// Pure static Astro template: Instant zero-JS HTML rendering
---
<main>
  <section class="hero">
    <h1>Accelerate Your Growth</h1>
    <img
      src="/hero.webp"
      alt="Hero overview"
      width="1200"
      height="600"
      loading="eager"
      decoding="async"
      fetchpriority="high"
    />
  </section>
</main>
```

## 4. Verification & Audit

Run PageSpeed Insights or Lighthouse against the page:

```bash
npx lighthouse http://localhost:4321 --only-categories=performance --view
```

Verify the LCP element is identified as the `<img>` or `<h1>`, and LCP is < 1.2s with zero render-blocking JavaScript dependencies.
