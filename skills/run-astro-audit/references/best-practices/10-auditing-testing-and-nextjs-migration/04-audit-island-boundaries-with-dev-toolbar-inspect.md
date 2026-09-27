# Inspect Island Component Boundaries and Directives Using Astro Dev Toolbar

> **Context:** Auditing & Next.js Migration | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro islands hydrate client components independently. However, developers often choose overly aggressive directives (`client:load` instead of `client:visible`) or serialize massive props (such as multi-megabyte JSON trees) into the DOM attributes of the island container (`<astro-island>`). The built-in Astro Dev Toolbar "Inspect" app highlights all interactive islands on the page, surfaces their exact hydration directives, and displays the serialized props, preventing unintentional client payload bloat.

## 2. How It Differs From Classic React / Next.js

In React/Next.js DevTools, the entire DOM tree is rendered inside the React fiber tree; identifying where server-client boundaries exist requires inspecting flight payloads or separate RSC devtools. In Astro, the page is native HTML with surgical `<astro-island>` tags; the Dev Toolbar Inspect app immediately delineates the server HTML from hydrated client islands.

## 3. Common Mistakes & Anti-Patterns

Passing an entire database record (with 50 unused fields) into a client island component serializes that whole JSON object into the HTML attribute `props="..."`. Another common mistake is using `client:load` for below-the-fold components, blocking initial render.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// Below-the-fold reviews component given eager hydration & massive props
const fullProduct = await getFullProductDetails(id); // 200KB JSON
---
<!-- Bloats initial bundle with client:load and serializes unused product data -->
<CustomerReviews
  client:load
  product={fullProduct}
/>
```

### ✅ Best Practice / Idiomatic

```astro
---
// Pass only minimal required props and hydrate when visible in viewport
const { id, rating, reviewsCount } = await getProductReviewSummary(id);
---
<!-- Defers hydration until scrolled into view; minimal serialized props -->
<CustomerReviews
  client:visible
  productId={id}
  rating={rating}
  reviewsCount={reviewsCount}
/>
```

## 4. Verification & Audit

Audit island boundaries and serialized props using the Dev Toolbar during development or via DOM inspection:

```bash
# Inspect serialized props size on islands in emitted HTML or live page
curl -s http://localhost:4321/products/sample | \
  grep -o 'props="[^"]*"' | \
  awk '{ print length($0), "bytes of serialized island props" }'
```
