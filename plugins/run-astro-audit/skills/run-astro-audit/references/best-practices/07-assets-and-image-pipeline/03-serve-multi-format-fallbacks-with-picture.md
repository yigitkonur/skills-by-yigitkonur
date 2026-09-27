# Serve Multi-Format AVIF and WebP Fallbacks with Picture

> **Context:** Assets & Image Pipeline | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

AVIF delivers up to 50% smaller payloads than JPEG and 20% smaller than WebP at comparable visual fidelity. However, legacy browsers (or specific webview contexts) lack AVIF decoding support. The `<Picture />` component from `astro:assets` generates an HTML `<picture>` element with prioritized modern format `<source>` tags and a dependable fallback `<img>` tag, delivering optimal compression to supporting browsers without breaking older clients.

## 2. How It Differs From Classic React / Next.js

Next.js configures image formats globally via `next.config.js` (`formats: ['image/avif', 'image/webp']`) and relies on HTTP `Accept` header content negotiation at the edge server. Astro provides component-level granularity via `formats={['avif', 'webp']}`, pre-generating static assets at build time for instant CDN delivery without edge compute costs.

## 3. Common Mistakes & Anti-Patterns

Listing formats in reverse order (e.g. `['webp', 'avif']`). Browsers select the very first `<source>` element they support; putting WebP first causes AVIF-capable browsers to settle for larger WebP payloads. Another trap is passing CSS classes directly to `<Picture />` expecting them on the outer `<picture>` tag instead of using `pictureAttributes`.

### ❌ Bad Practice / Anti-Pattern

Suboptimal format prioritization and styling applied to the inner image instead of the picture container:

```astro
---
// ❌ Anti-Pattern: WebP listed before AVIF; class applied to inner img
import { Picture } from 'astro:assets';
import promoBanner from '../assets/promo-banner.jpg';
---
<Picture
  src={promoBanner}
  formats={['webp', 'avif']}
  alt="Autumn Sale"
  class="banner-wrapper"
/>
```

### ✅ Best Practice / Idiomatic

Order formats from most efficient to least efficient, and style the container using `pictureAttributes`:

```astro
---
// ✅ Prioritizes AVIF first, then WebP, with PNG fallback and styled picture tag
import { Picture } from 'astro:assets';
import promoBanner from '../assets/promo-banner.jpg';
---
<Picture
  src={promoBanner}
  formats={['avif', 'webp']}
  fallbackFormat="jpg"
  alt="Autumn Sale - 40% Off Selected Styles"
  pictureAttributes={{ class: "banner-wrapper aspect-video block overflow-hidden" }}
/>
```

## 4. Verification & Audit

Verify the generated HTML markup in `dist/` contains `<source type="image/avif">` as the first child of `<picture>`:

```bash
pnpm build && grep -A 3 '<picture' dist/index.html | grep 'type="image/avif"'
```
