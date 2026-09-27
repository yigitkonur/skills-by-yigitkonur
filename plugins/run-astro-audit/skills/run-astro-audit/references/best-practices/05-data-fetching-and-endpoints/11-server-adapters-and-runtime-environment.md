# Pair On-Demand Routes with Verified Adapter Runtimes and Output Modes

> **Context:** Data Fetching & Endpoints | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro does not bundle a default monolithic Node.js web server runtime. To execute on-demand SSR data fetching or dynamic API endpoints, Astro must know the target infrastructure runtime (Cloudflare Workers, Node.js standalone, Vercel Serverless, Netlify Functions). This bridge is provided by an official Astro adapter. Declaring `export const prerender = false;` without an adapter in `astro.config.mjs` causes a fatal build failure: _"Cannot use on-demand rendering without an adapter."_

## 2. How It Differs From Classic React / Next.js

Next.js assumes a Vercel-like Node or Edge runtime out of the box. In Astro, the build is runtime-agnostic. In Astro 4, projects with mixed static/dynamic routes required `output: 'hybrid'`. In Astro 5, `output: 'hybrid'` was removed: `output: 'static'` now natively supports `prerender = false` on individual routes, while `output: 'server'` flips the default so all routes are server-rendered unless `prerender = true` is added.

## 3. Common Mistakes & Anti-Patterns

Using `prerender = false` without installing an adapter, or retaining obsolete `output: 'hybrid'` in Astro 5.

### ❌ Bad Practice / Anti-Pattern

```js
// astro.config.mjs
import { defineConfig } from 'astro/config'

// ❌ FAILS: Declares hybrid mode (removed in Astro 5) and has no adapter!
// Running `pnpm astro build` with any `prerender = false` route crashes during build.
export default defineConfig({
  output: 'hybrid', // Deprecated/removed in Astro 5
  // Missing adapter: @astrojs/node, @astrojs/cloudflare, etc.
})
```

### ✅ Best Practice / Idiomatic

```js
// astro.config.mjs
import { defineConfig } from 'astro/config'
import node from '@astrojs/node' // Or @astrojs/cloudflare, @astrojs/vercel

export default defineConfig({
  // In Astro 5, 'static' is the modern hybrid default:
  // Static by default; any route with `prerender = false` runs on the adapter.
  output: 'static',
  adapter: node({
    mode: 'standalone',
  }),
})
```

For high-density dynamic applications where 95%+ of routes are live:

```js
// Highly dynamic app: all routes server-rendered by default
export default defineConfig({
  output: 'server',
  adapter: node({ mode: 'standalone' }),
})
```

## 4. Verification & Audit

Audit your project configuration before deployment:

```bash
# Verify the build succeeds and generates server adapter entrypoints
pnpm astro build
```

Check that the build output directory contains the adapter bundle (e.g. `dist/server/entry.mjs` for Node or `_worker.js` for Cloudflare) and reports 0 adapter mismatch errors.
