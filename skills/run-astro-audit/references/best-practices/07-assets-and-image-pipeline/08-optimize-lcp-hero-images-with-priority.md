# Prioritize Above-the-Fold LCP Hero Images

> **Context:** Assets & Image Pipeline | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro's `<Image />` component defaults to `loading="lazy"` and `decoding="async"`. This is optimal for below-the-fold content, but catastrophically damages Largest Contentful Paint (LCP) when applied to the primary above-the-fold hero image. Lazy-loaded hero images defer network fetching until the main thread completes layout passes, delaying LCP by up to 2 seconds.

## 2. How It Differs From Classic React / Next.js

Next.js provides a `priority` boolean on `next/image` to disable lazy loading and add `<link rel="preload">`. Astro 5.10 introduced the first-class `priority` prop (or explicit `loading="eager"` and `fetchpriority="high"` in Astro 4), which automatically configures `loading="eager"`, `decoding="sync"`, and `fetchpriority="high"`.

## 3. Common Mistakes & Anti-Patterns

Leaving the primary homepage or article header hero image on default lazy loading, causing a harsh LCP penalty in Google Search and Core Web Vitals audits.

### ❌ Bad Practice / Anti-Pattern

Defaulting to lazy loading for the largest visual element in the initial viewport:

```astro
---
// ❌ Anti-Pattern: Defaults to loading="lazy"; delays LCP paint
import { Image } from 'astro:assets';
import heroVisual from '../assets/hero-visual.png';
---
<section class="hero-section">
  <h1>Engineered for Edge Scale</h1>
  <Image src={heroVisual} alt="Platform Architecture Overview" />
</section>
```

### ✅ Best Practice / Idiomatic

Add `priority` (or `loading="eager" fetchpriority="high"`) to signal the browser to start downloading immediately:

```astro
---
import { Image } from 'astro:assets';
import heroVisual from '../assets/hero-visual.png';
---
<section class="hero-section">
  <h1>Engineered for Edge Scale</h1>
  <!-- ✅ Injects loading="eager", decoding="sync", fetchpriority="high" -->
  <Image
    src={heroVisual}
    priority
    alt="Platform Architecture Overview"
    quality="max"
  />
</section>
```

## 4. Verification & Audit

Inspect the rendered hero `<img>` tag in Chrome DevTools:

```bash
curl -s http://localhost:4321/ | grep -E 'loading="eager"[^>]+fetchpriority="high"|fetchpriority="high"[^>]+loading="eager"'
```
