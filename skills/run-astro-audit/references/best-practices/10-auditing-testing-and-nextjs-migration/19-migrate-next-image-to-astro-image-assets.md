# Migrate next/image to Native Astro Image and Picture Components

> **Context:** Auditing & Next.js Migration | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Next.js applications rely on `next/image` to perform on-demand server-side image resizing, formatting, and optimization. This architecture requires a Node.js or edge server runtime (`/_next/image?url=...`), adding cold-start latency and bandwidth costs. Astro's native `astro:assets` (`<Image />` and `<Picture />`) processes local and remote images ahead-of-time at build time into modern formats (AVIF, WebP), generating responsive `srcset` attributes and preventing Cumulative Layout Shift (CLS) without an image-resizing server.

## 2. How It Differs From Classic React / Next.js

In Next.js, `next/image` requires the `priority` prop to avoid lazy loading the LCP image. In Astro, `<Image />` supports `loading="eager"` (for LCP hero imagery) and defaults to `loading="lazy"` with automatic width, height, and format inferencing derived directly from local image imports.

## 3. Common Mistakes & Anti-Patterns

Using standard unoptimized HTML `<img src="/images/hero.png" />` tags without dimensions, or porting `next/image` into React islands purely to render images, which forces the client to download the React runtime for a static picture.

### ❌ Bad Practice / Anti-Pattern

```tsx
// Next.js: next/image requires server-side runtime optimizer
import Image from 'next/image'
import heroImg from '../public/hero.jpg'

export default function Hero() {
  return <Image src={heroImg} alt="Hero banner" priority placeholder="blur" />
}
```

### ✅ Best Practice / Idiomatic

```astro
---
// Astro: Native build-time asset optimization (Zero runtime JS)
import { Image, Picture } from 'astro:assets';
import heroImg from '../assets/hero.jpg';
---
<!-- Generates optimized AVIF/WebP formats with intrinsic dimensions at build time -->
<Picture
  src={heroImg}
  formats={['avif', 'webp']}
  widths={[640, 1024, 1600]}
  alt="Hero banner"
  loading="eager"
  fetchpriority="high"
/>
```

## 4. Verification & Audit

Verify that the generated HTML references pre-optimized WebP/AVIF files in `dist/_astro/`:

```bash
# Check that dist output contains modern optimized picture formats
grep -E '<source\b[^>]*\btype="image/avif"' dist/index.html && echo "PASS: Build-time AVIF picture verified"
```
