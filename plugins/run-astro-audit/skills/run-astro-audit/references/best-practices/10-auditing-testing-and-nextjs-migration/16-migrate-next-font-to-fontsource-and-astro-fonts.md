# Migrate next/font to Self-Hosted @fontsource or Astro Config Font Providers

> **Context:** Auditing & Next.js Migration | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

`next/font` provides automatic font self-hosting and zero layout shift in Next.js applications. Migrating to Astro requires preserving these performance benefits without loading fonts from Google CDN at runtime. Using `@fontsource/*` packages or Astro's Font API self-hosts all font subsets locally, embeds optimized `@font-face` rules at build time, eliminates third-party privacy tracking (GDPR compliance), and prevents layout shifts (CLS).

## 2. How It Differs From Classic React / Next.js

In Next.js, font instances are initialized in JavaScript files (`const inter = Inter({ subsets: ['latin'] })`) and injected into JSX elements via generated CSS class strings (`<body className={inter.className}>`). In Astro, fonts are defined globally in `astro.config.mjs` or imported into layout frontmatter as pure static CSS (`import '@fontsource/inter/400.css'`).

## 3. Common Mistakes & Anti-Patterns

Reverting to external Google Fonts `<link rel="stylesheet" href="https://fonts.googleapis.com/...">` tags in `<head>`, which re-introduces render-blocking external network requests and third-party DNS lookups.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/layouts/Layout.astro - External Google Fonts (Blocks render, fails GDPR)
---
<head>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
</head>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/layouts/Layout.astro - Self-hosted via @fontsource (Zero-runtime, local assets)
import '@fontsource/inter/400.css';
import '@fontsource/inter/700.css';
---
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>My Site</title>
  </head>
  <body class="font-sans">
    <slot />
  </body>
</html>

<style is:global>
  body {
    font-family: 'Inter', system-ui, sans-serif;
  }
</style>
```

## 4. Verification & Audit

Verify that fonts are bundled locally into `dist/_astro/` and that no external requests to `fonts.googleapis.com` occur:

```bash
# Verify no external font links exist in built HTML
grep -i "fonts.googleapis.com" dist/index.html && \
  echo "FAIL: External Google Fonts found" || \
  echo "PASS: 100% self-hosted local typography"
```
