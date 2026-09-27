# Default to Zero-JS Static Compilation Over Client Runtime Bloat

> **Context:** Architecture & Philosophy | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro compiles `.astro` components into pure HTML and CSS during build or request time. Client-side JavaScript is not shipped unless a component explicitly declares a client directive or script tag. Shipping zero JavaScript by default eliminates browser main-thread parsing overhead, minimizes Time to Interactive (TTI), and drastically boosts Core Web Vitals (INP, LCP).

## 2. How It Differs From Classic React / Next.js

In Next.js (Pages and App Router), even static pages hydrate with the React runtime (`react`, `react-dom`, and router bundles totaling 70KB–100KB+ minified/gzipped). In contrast, Astro strips frontmatter script fences and templating logic entirely, outputting clean HTML with 0 KB of client runtime.

## 3. Common Mistakes & Anti-Patterns

Developers coming from React often wrap static marketing elements (headers, cards, footers) in React components and hydrate them using `client:load`, unintentionally shipping the entire framework runtime to display static markup.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/blog/[slug].astro
// Unnecessary hydration of static content in an e-commerce article
import ProductBanner from '../../components/react/ProductBanner.jsx';
const { slug } = Astro.params;
---
<main>
  <!-- Forces React runtime (45KB+) to load immediately for a purely static banner -->
  <ProductBanner client:load title="Summer Sale" discount="30%" />
</main>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/ProductBanner.astro
// Pure Astro component compiled to static HTML (0 KB JS shipped)
interface Props {
  title: string;
  discount: string;
}
const { title, discount } = Astro.props;
---
<aside class="promo-banner">
  <h3>{title}</h3>
  <p>Save up to {discount} today!</p>
</aside>
```

```astro
---
// src/pages/blog/[slug].astro
import ProductBanner from '../../components/ProductBanner.astro';
---
<main>
  <ProductBanner title="Summer Sale" discount="30%" />
</main>
```

## 4. Verification & Audit

Run a production build and inspect the generated assets:

```bash
npx astro build
# Verify that no JavaScript chunks are emitted for static routes:
find dist/ -name "*.js" -size +0c
# In Chrome DevTools Network panel, filter by 'JS' and confirm 0 scripts transfer on page load.
```
