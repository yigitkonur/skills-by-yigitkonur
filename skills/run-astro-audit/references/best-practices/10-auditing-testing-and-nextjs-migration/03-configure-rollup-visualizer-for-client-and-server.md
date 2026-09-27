# Configure Rollup Visualizer with emitFile to Separate Client and Server Bundles

> **Context:** Auditing & Next.js Migration | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Analyzing bundle sizes in Astro requires understanding Vite's dual build passes. When Astro builds an on-demand (SSR) or hybrid project, it triggers a client build for hydrated islands and a server build for SSR endpoints and components. Configuring `rollup-plugin-visualizer` with `emitFile: true` ensures that Rollup emits isolated `stats.html` visualizer reports into the appropriate output targets (`dist/client/stats.html` and `dist/server/stats.html`), preventing client island bundle bloat from being masked by server-only libraries.

## 2. How It Differs From Classic React / Next.js

Next.js uses `@next/bundle-analyzer` with Webpack/Turbopack, creating client, server, and edge HTML reports. In Next.js, large chunks often spill from server components into client components via module graph leaks. In Astro, client bundles only contain island code and client scripts; configuring the Rollup visualizer inside `vite.plugins` visualizes exactly which external npm packages are pulled into hydrated client islands.

## 3. Common Mistakes & Anti-Patterns

Omitting `emitFile: true` causes the visualizer to attempt writing directly to disk before output directories exist or overwrite files between client and server passes. Another mistake is assuming that `stats.html` represents a single page's load: Astro's visualizer reflects site-wide island dependencies, not a single monolithic SPA bundle.

### ❌ Bad Practice / Anti-Pattern

```js
// astro.config.mjs - INCORRECT: Missing emitFile; conflicts across passes
import { defineConfig } from 'astro/config'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  vite: {
    plugins: [
      // Fails to adapt to Astro's client/server dual-build output directories
      visualizer({ filename: 'bundle-stats.html' }),
    ],
  },
})
```

### ✅ Best Practice / Idiomatic

```js
// astro.config.mjs - CORRECT: Uses emitFile to target dist/client and dist/server
// @ts-check
import { defineConfig } from 'astro/config'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  vite: {
    plugins: [
      visualizer({
        emitFile: true,
        filename: 'stats.html',
        template: 'treemap',
        gzipSize: true,
        brotliSize: true,
      }),
    ],
  },
})
```

## 4. Verification & Audit

Run the build and inspect the generated visualizer report:

```bash
pnpm build
# For static SSG:
test -f dist/stats.html && echo "PASS: Static bundle visualizer generated at dist/stats.html"
# For on-demand SSR:
test -f dist/client/stats.html && echo "PASS: Client bundle visualizer generated at dist/client/stats.html"
```
