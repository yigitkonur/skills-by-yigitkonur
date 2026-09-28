# Leverage Speculation Rules API for Client Prerendering

> **Context:** Performance & Prefetch | **Impact:** High | **Target:** Astro 5

## 1. Why We Do This

Standard prefetching fetches raw HTML documents over the network. With client prerendering (introduced in Astro 5.6+ via `experimental.clientPrerender`), supporting browsers leverage the native Speculation Rules API to fully pre-render targeted pages in an invisible background tab. Navigating to the page is instantaneous (0ms perceived latency).

## 2. How It Differs From Classic React / Next.js

React SPA routers prefetch JSON data bundles and re-render components on the client. Astro leverages web standards directly: rather than custom router caching hacks, Astro injects standard Speculation Rules, allowing the browser engine itself to manage background process isolation, CPU limits, and memory disposal.

## 3. Common Mistakes & Anti-Patterns

Using maximum eagerness (`immediate`) on large batches of speculative links, which triggers browser memory limits and discards speculation candidates.

### ❌ Bad Practice / Anti-Pattern

```html
<!-- Client script attempting to force instant prerender on 30 catalog links -->
<script>
  import { prefetch } from 'astro:prefetch'

  // Over-speculation: Forces immediate prerender on 30 URLs, exhausting memory
  document.querySelectorAll('.catalog-link').forEach((a) => {
    prefetch(a.href, { eagerness: 'immediate' })
  })
</script>
```

### ✅ Best Practice / Idiomatic

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config'

export default defineConfig({
  experimental: {
    // Enable client-side prerendering with Speculation Rules
    clientPrerender: true,
  },
})
```

```astro
---
// src/components/FeaturedLinks.astro
---
<a href="/critical-funnel" class="spec-immediate">Start Free Trial</a>
<a href="/product-demo" class="spec-moderate">Watch Demo</a>

<script>
  import { prefetch } from 'astro:prefetch';

  // Immediate eagerness strictly for high-probability conversion path
  prefetch('/critical-funnel', { eagerness: 'immediate' });

  // Moderate eagerness allows browser FIFO heuristics to manage memory safely
  prefetch('/product-demo', { eagerness: 'moderate' });
</script>
```

## 4. Verification & Audit

In Chrome 121+, open DevTools -> **Application** panel -> **Speculative loads**:

- Inspect the active speculation rules.
- Confirm rules show status `Ready` or `Success` without status `Failure: Memory limit exceeded`.
