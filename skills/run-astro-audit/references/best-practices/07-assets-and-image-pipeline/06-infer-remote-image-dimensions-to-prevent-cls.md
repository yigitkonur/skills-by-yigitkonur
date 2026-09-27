# Infer Remote Image Dimensions with inferSize

> **Context:** Assets & Image Pipeline | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Headless CMS APIs, microservices, and external content feeds frequently return image URLs without accompanying width and height metadata. Rendering these images without dimensions causes severe layout shifts (CLS) when the image loads. Setting `inferSize` on `<Image />` or calling `inferRemoteSize(url)` instructs Astro to fetch minimal header bytes over HTTP at build/render time to extract the intrinsic aspect ratio and inject explicit `width` and `height`.

## 2. How It Differs From Classic React / Next.js

Next.js `next/image` strictly forces you to provide explicit `width` and `height` numbers for remote images or apply `fill={true}` inside an explicitly sized container element. Astro provides native dimension probing via `inferSize`, eliminating the need to maintain artificial dimension fields in headless CMS schemas.

## 3. Common Mistakes & Anti-Patterns

Omitting both dimensions and `inferSize` on a remote `<Image />`, which throws Astro's `MissingImageDimension` compiler error. Another critical trap is attempting to use `inferSize` on unauthorized remote domains: as of Astro 5.17+, `inferSize` strictly probes domains allowed in `image.remotePatterns` to protect against SSRF.

### ❌ Bad Practice / Anti-Pattern

Missing dimensions on remote images triggers build failure or layout shift:

```astro
---
// ❌ Anti-Pattern: Throws MissingImageDimension error in Astro build
import { Image } from 'astro:assets';
const avatar = "https://images.ctfassets.net/w67f89abc/user-123.jpg";
---
<div class="user-profile">
  <Image src={avatar} alt="Profile photo" />
</div>
```

### ✅ Best Practice / Idiomatic

Use `inferSize` for dynamic remote imagery, ensuring the origin is whitelisted in `image.remotePatterns`:

```astro
---
import { Image } from 'astro:assets';
// Origin must be configured in astro.config.mjs under remotePatterns
const avatar = "https://images.ctfassets.net/w67f89abc/user-123.jpg";
---
<div class="user-profile">
  <!-- ✅ Probes remote header, calculates aspect ratio, injects width/height -->
  <Image src={avatar} inferSize alt="Profile photo" class="rounded-full" />
</div>
```

## 4. Verification & Audit

Inspect the rendered DOM in your browser: confirm the remote `<img>` includes explicit numerical `width` and `height` attributes:

```bash
curl -s http://localhost:4321/profile | grep -E '<img[^>]+width="[0-9]+"[^>]+height="[0-9]+"'
```
