# Serialize Server Data to Client Scripts via HTML Data Attributes Over Inline Scripts

> **Context:** Architecture & Philosophy | **Impact:** Medium | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Passing server-computed values to client-side scripts via `data-*` attributes leverages the browser’s native `HTMLElement.dataset` API. This pattern is naturally protected against Cross-Site Scripting (XSS) via HTML attribute escaping, works smoothly with strict Content Security Policies (CSP) without requiring `'unsafe-inline'`, and keeps client scripts fully deduplicated.

## 2. How It Differs From Classic React / Next.js

In Next.js, props passed to `"use client"` components are transparently serialized into the React Server Component (RSC) flight payload. In pure Astro components without a framework island, there is no virtual DOM prop bus; server data must be passed to client scripts through standard DOM attributes.

## 3. Common Mistakes & Anti-Patterns

Using unescaped template literals inside inline `<script>` tags to inject server variables introduces XSS vulnerabilities and breaks script deduplication across multiple component instances.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/ProductTracker.astro
// Anti-pattern: String interpolation inside an inline script (XSS risk, no deduplication)
const { productId, userEmail } = Astro.props;
---
<div class="tracker">
  <!-- DANGEROUS: XSS vector if userEmail contains quotes or script tags; executes per instance -->
  <script is:inline>
    window.trackProduct("${productId}", "${userEmail}");
  </script>
</div>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/ProductTracker.astro
// Idiomatic: Pass values safely via dataset to a bundled, deduplicated script
interface Props {
  productId: string;
  category: string;
}
const { productId, category } = Astro.props;
---
<product-tracker data-product-id={productId} data-category={category}>
  <button type="button" class="track-btn">Track Product</button>
</product-tracker>

<script>
  class ProductTracker extends HTMLElement {
    connectedCallback() {
      const productId = this.dataset.productId;
      const category = this.dataset.category;
      const btn = this.querySelector('.track-btn');

      btn?.addEventListener('click', () => {
        console.log(`Tracking product ${productId} in category ${category}`);
      });
    }
  }
  customElements.define('product-tracker', ProductTracker);
</script>
```

## 4. Verification & Audit

Verify that scripts are bundled into static external files without inline script tags:

```bash
npx astro build
# Verify HTML contains data attributes and external script links, with zero inline unhashed scripts:
grep -rn "data-product-id=" dist/ | head -n 3
```
