# Self-Host Web Fonts and Preload Critical Above-the-Fold WOFF2

> **Context:** Assets & Image Pipeline | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Relying on external font CDNs (like Google Fonts) introduces extra DNS queries, TLS handshakes, render-blocking stylesheets, and privacy/GDPR liability. Self-hosting modern WOFF2 fonts allows your origin CDN to serve fonts with immutable HTTP caching. Preloading _only_ the single critical font weight required for above-the-fold body text eradicates Flash of Invisible Text (FOIT) without wasting mobile bandwidth.

## 2. How It Differs From Classic React / Next.js

Next.js handles font self-hosting via `next/font/google` and `next/font/local`. In Astro, you self-host fonts using `@fontsource/*` npm packages, local WOFF2 files in `src/assets/fonts/`, or Astro's native Fonts API (`astro.config.mjs` `fonts` config and `<Font />` in `astro:assets`).

## 3. Common Mistakes & Anti-Patterns

Preloading every font weight and style variant (e.g. 400, 500, 600, 700, italics, and subsets). Preloading too many fonts saturates network pipelines and delays critical CSS and HTML execution. Only preload the primary normal body font weight visible above the fold.

### ❌ Bad Practice / Anti-Pattern

Preloading multiple font files and weights in the `<head>`:

```astro
---
// ❌ Anti-Pattern: Preloading 4+ font files starves critical network resources
---
<head>
  <link rel="preload" href="/fonts/Inter-Regular.woff2" as="font" type="font/woff2" crossorigin />
  <link rel="preload" href="/fonts/Inter-Bold.woff2" as="font" type="font/woff2" crossorigin />
  <link rel="preload" href="/fonts/Inter-Italic.woff2" as="font" type="font/woff2" crossorigin />
</head>
```

### ✅ Best Practice / Idiomatic

Preload strictly the primary 400-weight WOFF2 file using `<link rel="preload">` or Astro's `<Font />` component:

```astro
---
// Using Astro's Fonts API
import { Font } from 'astro:assets';
---
<head>
  <!-- ✅ Preloads strictly the single 400-weight Latin subset for above-the-fold text -->
  <Font
    cssVariable="--font-inter"
    preload={[{ weight: "400", style: "normal", subset: "latin" }]}
  />
</head>
```

## 4. Verification & Audit

Audit your DevTools Network tab on initial cold load: confirm exactly one WOFF2 font request is initiated with Highest priority during early document parsing.
