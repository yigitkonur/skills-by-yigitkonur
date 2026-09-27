# Keep Server Island Props Lightweight and Under URL Limit

> **Context:** Islands & Hydration | **Impact:** High | **Target:** Astro 5

## 1. Why We Do This

Astro Server Islands encrypt their component props into a query string parameter on a `GET` request. Standard browser and CDN infrastructure cache HTTP `GET` responses using standard `Cache-Control` headers. However, if the encrypted query parameter exceeds 2048 bytes (the browser URL length limit), Astro is forced to fall back to a `POST` request with props in the body. HTTP `POST` requests are **never cached** by browsers or CDN edge caches, destroying caching benefits.

## 2. How It Differs From Classic React / Next.js

In Next.js React Server Components (RSC), server data streams over a persistent HTTP payload stream. In Astro, Server Islands are discrete RESTful endpoints requested individually by the browser client, making URL length and HTTP verb semantics critical for caching.

## 3. Common Mistakes & Anti-Patterns

Passing an entire database entity (e.g. a 50-field `user` or `product` object with nested reviews) as props to a server island component.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/products/[id].astro - Passing bloated objects through server island props
import ProductReviews from '../components/ProductReviews.astro';
const fullProduct = await getFullProduct(Astro.params.id); // 50+ fields, descriptions, specs
---
<!-- Exceeds 2048 bytes! Forces uncacheable POST request fallback -->
<ProductReviews server:defer product={fullProduct}>
  <div slot="fallback">Loading reviews...</div>
</ProductReviews>
```

### ✅ Best Practice / Idiomatic

Pass only scalar identifiers (IDs, slugs, timestamps) and fetch details inside the island:

```astro
---
// src/pages/products/[id].astro - Passing only minimal scalar ID
import ProductReviews from '../components/ProductReviews.astro';
const productId = Astro.params.id;
---
<!-- Small query string preserves GET request; enables edge/browser Cache-Control -->
<ProductReviews server:defer productId={productId}>
  <div slot="fallback">Loading reviews...</div>
</ProductReviews>
```

In `ProductReviews.astro`:

```astro
---
const { productId } = Astro.props;
const reviews = await fetchReviews(productId);
Astro.response.headers.set('Cache-Control', 'public, max-age=300, stale-while-revalidate=600');
---
<ul class="reviews">...</ul>
```

## 4. Verification & Audit

Inspect network requests in Chrome DevTools when loading the page:
Verify that the request to `/_server-islands/[ComponentName]` is an HTTP `GET` request with status 200, and NOT an HTTP `POST` request.
