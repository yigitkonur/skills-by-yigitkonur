# Configure Responsive Image Layouts and Sizes Accurately

> **Context:** Assets & Image Pipeline | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Serving desktop-width images (e.g. 1920px) to mobile devices wastes cellular data and slows First Contentful Paint. Astro 5.10 introduced the `layout` property (`constrained`, `full-width`, `fixed`) on `<Image />` and `<Picture />`, which automatically generates standard `srcset` density/width breakpoints and applies zero-specificity CSS `:where([data-astro-image])` rules.

## 2. How It Differs From Classic React / Next.js

Next.js relies on `fill` paired with a mandatory `sizes` attribute and injects inline styles with `position: absolute`. Astro uses standards-based responsive images: `layout="constrained"` applies `max-width: 100%; height: auto` with zero-specificity `:where()`, meaning utility classes (such as Tailwind) effortlessly override default rules without `!important`.

## 3. Common Mistakes & Anti-Patterns

Using `layout="constrained"` in a 3-column product grid without providing an explicit `sizes` attribute. Astro defaults `sizes` to `(min-width: Xpx) Xpx, 100vw`. In a multi-column desktop grid, the browser falsely assumes the image takes 100vw on mobile and tablet, downloading an asset 3x larger than needed.

### ❌ Bad Practice / Anti-Pattern

Relying on default 100vw sizes within a multi-column CSS grid:

```astro
---
// ❌ Anti-Pattern: Omits sizes in grid; browser downloads full-viewport width image
import { Image } from 'astro:assets';
import productThumb from '../assets/product-shot.jpg';
---
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
  <Image src={productThumb} layout="constrained" alt="Running Shoes" />
</div>
```

### ✅ Best Practice / Idiomatic

Specify an accurate `sizes` media condition matching your responsive CSS grid:

```astro
---
import { Image } from 'astro:assets';
import productThumb from '../assets/product-shot.jpg';
---
<!-- ✅ Browser downloads ~33vw on desktop and 100vw on single-column mobile -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
  <Image
    src={productThumb}
    layout="constrained"
    sizes="(min-width: 768px) 33vw, 100vw"
    alt="Running Shoes - Breathable Mesh"
  />
</div>
```

## 4. Verification & Audit

Simulate a mobile viewport in DevTools Network tab: verify the browser requests the smaller width variant from the `srcset` list rather than the full-resolution asset.
