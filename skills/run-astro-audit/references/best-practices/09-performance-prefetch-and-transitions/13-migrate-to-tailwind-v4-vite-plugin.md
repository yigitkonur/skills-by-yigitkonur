# Migrate to Tailwind CSS v4 Native Vite Plugin

> **Context:** Performance & Prefetch | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

The legacy `@astrojs/tailwind` integration has been deprecated. Tailwind CSS v4 features a ground-up rewrite that integrates directly into Vite as `@tailwindcss/vite`. Using the native Vite plugin eliminates PostCSS compilation bottlenecks, dramatically speeds up dev server hot-module reloading (HMR), and ensures dead-code CSS purging without configuration mismatches.

## 2. How It Differs From Classic React / Next.js

In Next.js, Tailwind v4 is enabled via PostCSS or Webpack loaders. In Astro, Vite is the native build engine. By wiring `@tailwindcss/vite` directly inside `astro.config.mjs`'s `vite.plugins` array, styles compile at native Vite speeds with zero extra integration abstraction layers.

## 3. Common Mistakes & Anti-Patterns

Retaining `@astrojs/tailwind` and legacy `tailwind.config.js` or `postcss.config.js` files alongside Tailwind v4 dependencies.

### ❌ Bad Practice / Anti-Pattern

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config'
import tailwind from '@astrojs/tailwind' // DEPRECATED: Do not use with Tailwind 4

export default defineConfig({
  integrations: [tailwind()], // Slow PostCSS pipeline
})
```

```css
/* src/styles/global.css - Legacy directives */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### ✅ Best Practice / Idiomatic

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  vite: {
    plugins: [tailwindcss()], // High-performance native Vite compiler
  },
})
```

```css
/* src/styles/global.css - Clean v4 CSS-first import */
@import 'tailwindcss';
```

## 4. Verification & Audit

Verify `@astrojs/tailwind` is uninstalled and `@tailwindcss/vite` is in devDependencies:

```bash
grep -E '@(astrojs/tailwind|tailwindcss/vite)' package.json
```

Measure dev server startup or page rebuild time to verify sub-second style updates.
