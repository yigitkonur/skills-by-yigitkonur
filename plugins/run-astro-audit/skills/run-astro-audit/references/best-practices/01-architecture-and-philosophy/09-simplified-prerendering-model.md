# Leverage Static-First Default With Granular Prerender Over Blanket Server Output

> **Context:** Architecture & Philosophy | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

In Astro 5, the legacy `hybrid` and `static` modes were unified into the default `static` output model. Astro sites pre-render all pages to static HTML by default. When an adapter (e.g. Cloudflare, Node, Netlify) is installed, individual pages can opt into on-demand server rendering simply with `export const prerender = false`. This guarantees maximum edge caching while preserving dynamic capabilities.

## 2. How It Differs From Classic React / Next.js

Next.js App Router uses route segment configs (`dynamic = 'auto'`, `'force-dynamic'`) that easily de-optimize static routes into dynamic SSR whenever a dynamic function (`cookies()`, `headers()`) is touched anywhere in the tree. Astro’s static-first contract requires explicit route-level declaration to opt into dynamic SSR.

## 3. Common Mistakes & Anti-Patterns

Configuring `output: 'server'` globally in `astro.config.mjs` turns every marketing, blog, and docs page into an SSR route, increasing compute costs, server response latency, and CDN cache miss rates.

### ❌ Bad Practice / Anti-Pattern

```javascript
// astro.config.mjs
// Anti-pattern: Forcing the entire site into on-demand SSR for a few dynamic endpoints
import { defineConfig } from 'astro/config'
import node from '@astrojs/node'

export default defineConfig({
  output: 'server', // Blanket SSR: All static pages now execute on every request!
  adapter: node({ mode: 'standalone' }),
})
```

### ✅ Best Practice / Idiomatic

```javascript
// astro.config.mjs
// Idiomatic (Astro 5): Keep static default, use adapter for on-demand routes
import { defineConfig } from 'astro/config'
import node from '@astrojs/node'

export default defineConfig({
  // output: 'static' is the default; no need to specify
  adapter: node({ mode: 'standalone' }),
})
```

```astro
---
// src/pages/api/live-rates.ts or src/pages/account/profile.astro
// Granular opt-out: Only this specific route renders on-demand on the server
export const prerender = false;

const userSession = Astro.cookies.get('session_id');
if (!userSession) return Astro.redirect('/login');
---
<div>Welcome to your real-time account profile!</div>
```

## 4. Verification & Audit

Verify the build output summary in terminal:

```bash
npx astro build
# Observe the build table:
# [○] (Static)   Pre-rendered pages (e.g. /, /about, /blog/*)
# [λ] (Server)   On-demand SSR routes (e.g. /account/profile)
```
