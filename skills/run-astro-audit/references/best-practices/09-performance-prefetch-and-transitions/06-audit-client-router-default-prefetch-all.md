# Override ClientRouter Default prefetchAll Configuration

> **Context:** Performance & Prefetch | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Adding Astro's `<ClientRouter />` (Astro 5) or `<ViewTransitions />` (Astro 4) automatically enables client-side routing and silently flips the prefetch engine to `{ prefetchAll: true }`. On archive pages, tag clouds, or footer navigation with dozens of links, this default causes every hovered or visible link to prefetch, flooding the client thread and edge CDN cache.

## 2. How It Differs From Classic React / Next.js

In Next.js App Router, link prefetching is built into `<Link>` with heuristic viewport queues. In Astro, `<ClientRouter />` activates SPA navigation over an MPA architecture. Because `<ClientRouter />` sets `prefetchAll: true` behind the scenes, developers must explicitly override it in `astro.config.mjs` to keep prefetching strictly opt-in.

## 3. Common Mistakes & Anti-Patterns

Importing `<ClientRouter />` without configuring `prefetch.prefetchAll: false` in `astro.config.mjs`.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/layouts/BaseLayout.astro
import { ClientRouter } from 'astro:transitions';
---
<html>
  <head>
    <!-- Silently forces prefetchAll: true across all 200+ links on the page -->
    <ClientRouter />
  </head>
  <body>
    <slot />
  </body>
</html>
```

### ✅ Best Practice / Idiomatic

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config'

export default defineConfig({
  // Explicitly override the ClientRouter prefetch default
  prefetch: {
    prefetchAll: false, // Prevent uncontrolled prefetching of all links
    defaultStrategy: 'hover', // Controlled intent strategy
  },
})
```

```astro
---
// src/layouts/BaseLayout.astro
import { ClientRouter } from 'astro:transitions';
---
<html>
  <head>
    <ClientRouter />
  </head>
  <body>
    <!-- Now only links with explicit data-astro-prefetch will prefetch -->
    <a href="/featured" data-astro-prefetch>Featured Story</a>
    <a href="/terms">Terms of Service</a>
  </body>
</html>
```

## 4. Verification & Audit

Check `astro.config.mjs` to confirm `prefetchAll` is explicitly set to `false`:

```bash
grep -n "prefetchAll:\s*false" astro.config.mjs
```

Open a long index page, hover rapidly across 20 unannotated links, and confirm in DevTools Network tab that zero prefetch requests are dispatched.
