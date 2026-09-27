# Use Page Partials for HTMX and Atomic Micro-Frontend Routing

> **Context:** Routing & Pages | **Impact:** Medium | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Page Partials (`export const partial = true`) allow `.astro` components in `src/pages/` to be served as bare HTML fragments rather than complete documents. They emit no `<!DOCTYPE>`, `<html>`, or `<head>` scaffolding, making them the ideal low-overhead endpoint for HTMX, Alpine.js, or vanilla `fetch()` swaps.

## 2. How It Differs From Classic React / Next.js

In Next.js, API routes return JSON, requiring client components to receive data and render JSX. In Astro, partials render pure server-side HTML directly at a URL, enabling hypermedia-driven architectures (HDA) with zero client-side React hydration overhead.

## 3. Common Mistakes & Anti-Patterns

Using `<style>` or `<script>` tags inside a partial. In partials, Astro strips scoped styles and scripts because there is no `<head>` to inject them into. If a partial requires styling, use global utility classes (Tailwind) or ensure styles are pre-loaded in the host page.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/partials/card.astro
export const partial = true;
---
<div class="user-card">
  <p>User Data</p>
</div>

<!-- ERROR: Scoped styles are stripped in partials! -->
<style>
  .user-card { background: red; }
</style>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/partials/cart-count.astro
// Exporting partial = true creates an HTML-only fragment endpoint
export const partial = true;
export const prerender = false; // Render dynamically on request

const cart = await getCart(Astro.cookies.get("cart_id")?.value);
const count = cart?.items.length ?? 0;
---
<span id="cart-counter" class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-rose-500 text-white">
  {count}
</span>
```

```html
<!-- Consumed seamlessly in any host page via HTMX or standard fetch -->
<button
  hx-get="/partials/cart-count"
  hx-trigger="every 10s"
  hx-target="#cart-counter"
  hx-swap="outerHTML"
>
  Refresh Cart Count
</button>
```

## 4. Verification & Audit

Fetch the partial endpoint via curl and verify it returns raw HTML tags without `<!DOCTYPE>` or `<html>`:

```bash
curl -s http://localhost:4321/partials/cart-count
```

Confirm the output starts directly with the root partial element (e.g. `<span id="cart-counter"...`).
