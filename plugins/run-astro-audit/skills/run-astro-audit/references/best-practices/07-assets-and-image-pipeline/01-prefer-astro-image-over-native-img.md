# Use astro:assets Image Component to Eradicate CLS

> **Context:** Assets & Image Pipeline | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Raw HTML `<img>` tags without explicit dimensions cause Cumulative Layout Shift (CLS) as content reflows when bytes arrive. The `<Image />` component from `astro:assets` automatically infers intrinsic dimensions from imported assets, sets explicit `width` and `height` attributes to reserve the exact layout box, generates modern `.webp` by default, and sets `decoding="async"` and `loading="lazy"` automatically.

## 2. How It Differs From Classic React / Next.js

Next.js `next/image` wraps images in nested `<span>` elements or requires CSS wrappers with `position: relative` and `fill`. Astro's `<Image />` outputs a clean, semantic HTML `<img>` tag directly into the static document with zero wrapper elements and zero client-side JavaScript.

## 3. Common Mistakes & Anti-Patterns

Accessing the `.src` string of an ESM-imported image on a standard `<img>` tag without dimensions, which throws away Astro's automatic format conversion and layout shift protection.

### ❌ Bad Practice / Anti-Pattern

Using the imported image object's `.src` directly on a standard HTML `<img>` tag:

```astro
---
// src/components/AuthorBio.astro
import authorAvatar from '../assets/team/alex-rivera.png';
---
<!-- ❌ Anti-Pattern: Unprocessed original PNG, missing dimensions, triggers CLS -->
<div class="author-card">
  <img src={authorAvatar.src} alt="Alex Rivera" />
</div>
```

### ✅ Best Practice / Idiomatic

Pass the imported metadata object directly to `<Image />` with a mandatory `alt` description:

```astro
---
// src/components/AuthorBio.astro
import { Image } from 'astro:assets';
import authorAvatar from '../assets/team/alex-rivera.png';
---
<!-- ✅ Inferred dimensions, converted to WebP, decoding="async", loading="lazy" -->
<div class="author-card">
  <Image
    src={authorAvatar}
    alt="Alex Rivera, Principal Architect"
    width={80}
    height={80}
  />
</div>
```

## 4. Verification & Audit

Run a Lighthouse Core Web Vitals audit to confirm CLS is strictly 0.00:

```bash
npx lighthouse http://localhost:4321/blog/my-post --only-audits=cumulative-layout-shift --output=json | grep -o '"score": [0-9.]*'
```
