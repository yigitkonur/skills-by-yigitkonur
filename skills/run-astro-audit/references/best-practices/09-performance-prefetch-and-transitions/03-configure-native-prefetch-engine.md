# Configure Native Prefetch Engine in astro.config.mjs

> **Context:** Performance & Prefetch | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro 3.5+ replaced the legacy `@astrojs/prefetch` package with a native, built-in prefetch engine. Configuring `prefetch` centrally in `astro.config.mjs` injects an optimized client runtime (less than 1KB) that handles request scheduling, intent debouncing, and slow-connection fallbacks without third-party dependencies.

## 2. How It Differs From Classic React / Next.js

In Next.js, prefetching behavior is bundled into `next/link` and cannot be globally tuned without custom wrappers. In Astro, `astro.config.mjs` provides a centralized control plane to define whether prefetching is global (`prefetchAll: true`) or opt-in (`prefetchAll: false`), and what default strategy applies when `data-astro-prefetch` is omitted.

## 3. Common Mistakes & Anti-Patterns

Continuing to install `@astrojs/prefetch` in modern Astro projects, or setting `prefetchAll: true` globally on dynamic sites, causing all internal links to prefetch indiscriminately.

### ❌ Bad Practice / Anti-Pattern

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config'
import prefetch from '@astrojs/prefetch' // DEPRECATED: Do not use in Astro 4/5

export default defineConfig({
  integrations: [
    prefetch({
      throttle: 3, // Legacy throttle option ignored by modern core
    }),
  ],
})
```

### ✅ Best Practice / Idiomatic

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config'

export default defineConfig({
  // Native prefetch engine: opt-in per-link, hover default
  prefetch: {
    prefetchAll: false, // Require explicit data-astro-prefetch
    defaultStrategy: 'hover', // Strategy when attribute has no value
  },
})
```

## 4. Verification & Audit

Verify that `@astrojs/prefetch` is completely removed from dependencies:

```bash
grep -n "@astrojs/prefetch" package.json
```

Inspect the emitted `<head>` in `dist/` or dev server to confirm the native prefetch script is present without legacy runtime wrappers:

```bash
curl -s http://localhost:4321 | grep -i 'astro-prefetch'
```
