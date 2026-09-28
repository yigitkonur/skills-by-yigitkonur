# Generate Dynamic and Background Image URLs with getImage

> **Context:** Assets & Image Pipeline | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

CSS background images, dynamic Open Graph `<meta property="og:image">` tags, inline SVG fill patterns, and API routes cannot directly render `<Image />` or `<Picture />` HTML tags. The `getImage()` helper provides server-side programmatic access to Astro's Sharp transformation engine, returning an optimized asset URL (`.src`), dimensions, and attributes without emitting HTML markup.

## 2. How It Differs From Classic React / Next.js

In Next.js, generating an image URL for an external service or CSS background usually involves manually assembling `/_next/image?url=...&w=...&q=...` or deploying a dedicated `@vercel/og` Edge function. In Astro, `getImage()` is a server-only function that executes during build or SSR, emitting real hashed static files or signed endpoints.

## 3. Common Mistakes & Anti-Patterns

Importing and calling `getImage()` inside a client-side React island or browser script tag, which throws a runtime exception because `getImage()` requires Node.js/Vite server APIs. Another frequent blunder is referencing unoptimized raw image paths inside inline `style="background-image: url(...)"`.

### ❌ Bad Practice / Anti-Pattern

Referencing an imported image's uncompressed source directly in a CSS background:

```astro
---
// ❌ Anti-Pattern: Bypasses compression; serves raw 4MB PNG as CSS background
import heroPattern from '../assets/hero-pattern.png';
---
<section style={`background-image: url(${heroPattern.src});`}>
  <div class="content"><slot /></div>
</section>
```

### ✅ Best Practice / Idiomatic

Use `getImage()` in the frontmatter to generate a compressed AVIF/WebP asset, passing the resolved `.src` to the CSS property:

```astro
---
import { getImage } from 'astro:assets';
import heroPattern from '../assets/hero-pattern.png';

// ✅ Programmatically generates optimized AVIF background asset
const optimizedBg = await getImage({
  src: heroPattern,
  format: 'avif',
  quality: 80,
  width: 1920
});
---
<section style={`background-image: url(${optimizedBg.src});`}>
  <div class="content"><slot /></div>
</section>
```

## 4. Verification & Audit

Verify the generated CSS background URL references a transformed file in `_astro/`:

```bash
pnpm build && grep -rn 'background-image: url(/_astro/' dist/ && echo "Pass: Background images optimized"
```
