# Master the Astro Assets and Image Pipeline Architecture

> **Context:** Assets & Image Pipeline | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro's `astro:assets` pipeline transforms visual media into an automated performance asset. By optimizing images at build time via Sharp, emitting modern formats (AVIF and WebP), inferring intrinsic dimensions, and generating content-hashed immutable URLs, Astro eliminates Cumulative Layout Shift (CLS) and slashes Largest Contentful Paint (LCP) latency without runtime client-side JavaScript overhead.

## 2. How It Differs From Classic React / Next.js

- **Zero-JS Output**: While Next.js `next/image` injects client-side runtime scripts, custom spans, and hydration wrappers, Astro outputs clean, native, standards-compliant HTML elements (`<img>`, `<picture>`, `<svg>`).
- **Static vs Edge Processing**: Next.js defaults to on-demand serverless optimization via `/_next/image`. Astro prerenders optimized image variations into static hashed assets in `dist/_astro/` during SSG, eliminating cold-start latency on edge CDNs.
- **Directory Contract**: Next.js serves and optimizes string paths pointing to `/public`. Astro treats `public/` strictly as an unoptimized passthrough; local images must reside in `src/assets/` and be imported via ESM to enter the optimization pipeline.

## 3. Common Mistakes & Anti-Patterns

Developers migrating from Next.js frequently bring old mental models: storing transformable assets in `public/`, using unstyled raw `<img>` tags without dimensions, attempting to use React `next/image` components inside Astro islands, or overlooking remote origin authorization policies.

### ❌ Bad Practice / Anti-Pattern

Relying on unoptimized public directory paths and unmeasured HTML image tags in marketing layouts:

```astro
---
// ❌ Anti-Pattern: Bypasses the asset pipeline, lacks dimensions, ships heavy PNG
---
<header class="hero">
  <img src="/images/hero-banner.png" alt="Summer Launch" />
</header>
```

### ✅ Best Practice / Idiomatic

Importing local image assets via ESM, leveraging `<Image />` for automatic dimension inference and WebP conversion:

```astro
---
import { Image } from 'astro:assets';
import heroBanner from '../assets/images/hero-banner.png';
---
<header class="hero">
  <Image src={heroBanner} alt="Summer Launch" priority quality="high" />
</header>
```

## 4. Verification & Audit

Audit your production build output to confirm all local images are transformed into hashed WebP/AVIF formats in `_astro/`:

```bash
pnpm build && find dist/_astro -type f \( -name "*.webp" -o -name "*.avif" \) | wc -l
```
