# Avoid Misusing is:inline on Component Style Tags

> **Context:** Performance & Prefetch | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

`<style is:inline>` instructs Astro to completely bypass Vite's CSS bundling pipeline. The CSS inside the tag is neither scoped, minified, deduplicated, nor extracted into cached stylesheet chunks. If an Astro component containing `<style is:inline>` is rendered multiple times (such as in a product grid), the entire raw CSS string is duplicated inside every HTML instance, bloating document payload and wasting parsing time.

## 2. How It Differs From Classic React / Next.js

In React, inline styles (`style={{ ... }}`) apply directly as element attributes. In Astro, `<style is:inline>` outputs a literal `<style>` tag into the DOM wherever the component is rendered. Developers expecting automatic Vite optimization will accidentally bypass CSS tree-shaking and caching.

## 3. Common Mistakes & Anti-Patterns

Using `is:inline` on repeated list items or card components.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/ProductCard.astro
const { product } = Astro.props;
---
<div class="product-card">
  <h3>{product.title}</h3>
  <p>${product.price}</p>
</div>

<!-- DUPLICATION: If 50 cards render on page, this CSS block repeats 50 times! -->
<style is:inline>
  .product-card {
    border: 1px solid #e2e8f0;
    padding: 1.5rem;
    border-radius: 8px;
  }
</style>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/ProductCard.astro
const { product } = Astro.props;
---
<div class="product-card">
  <h3>{product.title}</h3>
  <p>${product.price}</p>
</div>

<!-- Standard scoped style: Extracted, deduplicated, and cached once by Vite -->
<style>
  .product-card {
    border: 1px solid #e2e8f0;
    padding: 1.5rem;
    border-radius: 8px;
  }
</style>
```

## 4. Verification & Audit

Audit your codebase for repeated `<style is:inline>` tags in components:

```bash
grep -rn '<style is:inline>' src/components/
```

Inspect built HTML output to verify that stylesheet rules are referenced via single `<link rel="stylesheet">` or a single inlined `<head>` chunk rather than scattered through the `<body>`.
