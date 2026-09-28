# Store Transformable Images in src/assets/ Not public/

> **Context:** Assets & Image Pipeline | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro's build engine transforms, compresses, converts, and generates content-hashed filenames exclusively for image files imported from `src/`. Files placed in the `public/` directory are copied directly into the build output verbatim with zero processing. Storing content images in `public/` ships oversized PNGs and JPEGs, prevents modern format generation (AVIF/WebP), and forfeits immutable CDN cache headers (`Cache-Control: public, max-age=31536000, immutable`).

## 2. How It Differs From Classic React / Next.js

In Next.js, referencing `/public/hero.png` as `src="/hero.png"` inside `next/image` still invokes runtime image optimization via the `/_next/image` serverless endpoint. In Astro, passing a string URL to `/public` tells the compiler to bypass the Sharp build pipeline completely. To trigger Astro's static optimization, images must be colocated in `src/assets/` and imported as ESM modules.

## 3. Common Mistakes & Anti-Patterns

Placing product photos, blog covers, or hero imagery in `public/images/` and referencing them via relative string URLs.

### ❌ Bad Practice / Anti-Pattern

Images in `public/` bypass format conversion and dimension extraction:

```astro
---
// src/pages/blog/[slug].astro
// ❌ Anti-Pattern: public/ images are copied verbatim; no WebP conversion or cache hashing
---
<article class="post">
  <img
    src="/images/blog/serverless-architecture.png"
    alt="Serverless Architecture Diagram"
  />
</article>
```

### ✅ Best Practice / Idiomatic

Colocate images in `src/assets/` and import them directly to trigger automated Sharp processing:

```astro
---
// src/pages/blog/[slug].astro
import { Image } from 'astro:assets';
import archDiagram from '../../assets/blog/serverless-architecture.png';
---
<article class="post">
  <!-- ✅ Generates optimized WebP, extracts dimensions, outputs hashed asset in _astro/ -->
  <Image
    src={archDiagram}
    alt="Serverless Architecture Diagram"
    quality="high"
  />
</article>
```

## 4. Verification & Audit

Verify that your built HTML references `/_astro/` hashed WebP assets rather than raw `/images/` paths:

```bash
pnpm build && grep -rn 'src="/images/' dist/ && echo "Warning: Raw public images detected" || echo "Pass: All images use optimized _astro pipeline"
```
