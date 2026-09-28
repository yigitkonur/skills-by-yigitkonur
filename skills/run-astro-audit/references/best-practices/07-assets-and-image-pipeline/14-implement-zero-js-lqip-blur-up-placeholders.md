# Implement Zero-JS Low-Quality Image Placeholders (LQIP)

> **Context:** Assets & Image Pipeline | **Impact:** Medium | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Large content imagery can leave blank empty blocks before bytes finish streaming over slow networks. Low-Quality Image Placeholders (LQIP) provide an instant blurred thumbnail preview while the high-resolution image downloads. Implementing this with zero client JavaScript preserves CPU cycles on mobile devices and eliminates hydration overhead.

## 2. How It Differs From Classic React / Next.js

Next.js provides `placeholder="blur"` using statically imported image data URLs or blurDataURL props. In Astro, developers achieve superior performance using CSS-only transitions (`filter: blur(12px)`) with inline base64 WebP strings or CSS background colors, triggering the un-blur via native `onload="this.dataset.loaded='true'"` without shipping React hydration code.

## 3. Common Mistakes & Anti-Patterns

Importing heavyweight JavaScript libraries (like `react-lazy-load-image-component` or heavy canvas blur scripts) inside hydrated client islands just to create a cross-fade effect, negating Astro's zero-JS speed advantage.

### ❌ Bad Practice / Anti-Pattern

Hydrating a React island solely for image placeholder cross-fades:

```astro
---
// ❌ Anti-Pattern: Hydrating a 45KB React bundle solely for image fading
import ReactBlurImage from '../components/ReactBlurImage.jsx';
---
<ReactBlurImage client:visible src="/heavy-hero.jpg" placeholder="/placeholder.jpg" />
```

### ✅ Best Practice / Idiomatic

Use CSS-only Gaussian blur-up with native DOM events and zero framework runtime:

```astro
---
import { Image } from 'astro:assets';
import heroVisual from '../assets/hero-visual.jpg';
// Low-res inline base64 WebP preview (generated at build time or via script)
const lqipBase64 = "data:image/webp;base64,UklGRmYAAABXRUJQVlA4IFoAAAAwAQCdASoFAAMAPxF8s1CvqaSjAA==";
---
<div
  class="lqip-container overflow-hidden relative bg-cover"
  style={`background-image: url('${lqipBase64}');`}
>
  <Image
    src={heroVisual}
    alt="Platform Overview"
    class="lqip-image transition-opacity duration-500 opacity-0 blur-sm"
    onload="this.classList.remove('opacity-0', 'blur-sm')"
  />
</div>

<style>
  .lqip-container {
    filter: blur(0px); /* Hardware-accelerated container */
  }
</style>
```

## 4. Verification & Audit

Throttle network to Slow 3G in Chrome DevTools: verify the blur preview appears instantly and transitions smoothly upon image load without executing any client framework JavaScript.
