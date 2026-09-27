# Avoid Blanket Viewport Prefetching on Large Link Collections

> **Context:** Performance & Prefetch | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Enabling `viewport` prefetching across listing pages with 50+ links triggers concurrent HTTP requests as elements scroll into view. On mobile cellular connections, this saturates network bandwidth, spikes CPU usage, depletes device battery, and floods backend origins with unneeded rendering traffic for pages users may never visit.

## 2. How It Differs From Classic React / Next.js

In Next.js `<Link>`, `prefetch={true}` defaults to viewport observation for static routes, downloading RSC payloads automatically. Next.js developers migrating to Astro often set `defaultStrategy: 'viewport'` or apply `data-astro-prefetch="viewport"` on entire grids, failing to realize Astro renders full HTML documents rather than partial JSON diffs, drastically increasing payload weights.

## 3. Common Mistakes & Anti-Patterns

Applying `data-astro-prefetch="viewport"` across product catalogs, search results, or blog archives.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/ProductCatalog.astro
const { products } = Astro.props; // 100+ items
---
<div class="grid grid-cols-4 gap-6">
  {products.map((product) => (
    <div class="product-card">
      <img src={product.thumbnail} alt={product.title} />
      <h3>{product.title}</h3>
      <!-- Blanket viewport prefetching on 100+ catalog links -->
      <a href={`/products/${product.slug}`} data-astro-prefetch="viewport">
        View Product
      </a>
    </div>
  ))}
</div>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/ProductCatalog.astro
const { products } = Astro.props;
---
<div class="grid grid-cols-4 gap-6">
  {products.map((product) => (
    <div class="product-card">
      <img src={product.thumbnail} alt={product.title} />
      <h3>{product.title}</h3>
      <!-- Use 'hover' or 'tap' so network requests trigger only on intent -->
      <a href={`/products/${product.slug}`} data-astro-prefetch="hover">
        View Product
      </a>
    </div>
  ))}
</div>
```

## 4. Verification & Audit

Run a grep audit across templates to detect unbounded `viewport` prefetch directives:

```bash
grep -rn 'data-astro-prefetch="viewport"' src/pages src/components
```

In Chrome DevTools Network panel, throttle to "Fast 4G", scroll the listing page, and ensure the request waterfall does not initiate background HTML transfers until a card is hovered or tapped.
