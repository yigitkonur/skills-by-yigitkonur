# Tune CSS Bundle Control and Stylesheet Inlining Thresholds

> **Context:** Performance & Prefetch | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

By default, Astro inlines CSS chunks smaller than 4kB directly into `<head>` as `<style>` tags to avoid extra network roundtrips, while linking larger chunks as external `<link rel="stylesheet">` files. On large multi-page websites where users visit dozens of pages, inlining repeated CSS inflates every HTML document and prevents browser cache reuse. Tuning `build.inlineStylesheets` aligns bundling with your site's access pattern.

## 2. How It Differs From Classic React / Next.js

Next.js automatically extracts and links CSS per route without built-in options to control CSS inlining thresholds. Astro exposes granular build controls (`build.inlineStylesheets: 'never' | 'auto' | 'always'` and `vite.build.assetsInlineLimit`), allowing architects to optimize between zero-roundtrip landing pages and high-cacheability multi-page apps.

## 3. Common Mistakes & Anti-Patterns

Leaving the default 4kB inlining threshold on large content sites, causing shared layout CSS to be re-downloaded inside every HTML document.

### ❌ Bad Practice / Anti-Pattern

```javascript
// astro.config.mjs
// Unconfigured default: Inlines all small CSS chunks into every HTML file
import { defineConfig } from 'astro/config'

export default defineConfig({
  // No build configuration: Shared layout fragments inflate 1,000+ HTML files
})
```

### ✅ Best Practice / Idiomatic

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config'

export default defineConfig({
  build: {
    // 'never' forces external stylesheets, maximizing browser HTTP caching
    // across multi-page navigation sessions
    inlineStylesheets: 'never',
  },
  vite: {
    build: {
      // Prevent small font/SVG assets from inflating CSS with base64 data URIs
      assetsInlineLimit: 1024, // 1KB threshold
    },
  },
})
```

## 4. Verification & Audit

Build the project and inspect emitted HTML files in `dist/`:

```bash
pnpm astro build && grep -rn '<style>' dist/ | wc -l
```

Confirm that with `inlineStylesheets: 'never'`, `dist/` pages reference `.css` files via `<link rel="stylesheet">` with `Cache-Control: public, max-age=31536000, immutable`.
