# Prefer Static Leaf Islands Over Mega-Islands

> **Context:** Islands & Hydration | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Wrapping an entire content section, card, or page in a UI framework component ("Mega-Island") forces Astro to ship the entire subtree's JavaScript and props JSON payload to the client. By pushing the `client:*` directive down to the smallest interactive leaf component (e.g. an "Add to Cart" button or like counter), 90%+ of the HTML remains pure, zero-JS markup, minimizing bundle sizes, parse time, and main-thread execution.

## 2. How It Differs From Classic React / Next.js

In Next.js App Router, placing `'use client'` at the top of a component marks that component and all of its imported children as client-rendered. Developers reflexively make entire card components client components. In Astro, `.astro` components are HTML-only compilers: you compose static HTML in Astro and embed only the interactive button or input as a client island.

## 3. Common Mistakes & Anti-Patterns

Migrating a React e-commerce card by importing the entire `ProductCard.jsx` into Astro with `client:load`, sending static images, titles, descriptions, and badge markup through client hydration.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/shop.astro - Hydrating entire product card as a Mega-Island
import ProductCard from '../components/ProductCard.jsx';
const product = await fetchProduct(Astro.params.id);
---
<!-- Entire card, image, text, and pricing re-hydrated in client JS -->
<ProductCard product={product} client:load />
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/shop.astro - Static Astro card with an isolated interactive leaf island
import AddToCartButton from '../components/AddToCartButton.jsx';
const product = await fetchProduct(Astro.params.id);
---
<article class="product-card">
  <img src={product.image} alt={product.title} loading="lazy" />
  <h2>{product.title}</h2>
  <p class="price">${product.price}</p>
  <!-- Only the interactive action button hydrates on the client -->
  <AddToCartButton client:idle productId={product.id} />
</article>
```

## 4. Verification & Audit

Run an Astro production build and inspect the generated client JavaScript chunks:

```bash
npx astro build && ls -lh dist/_astro/
```

Verify that the emitted client script corresponds only to the leaf component (`AddToCartButton`) and does not bundle product description or layout code.
