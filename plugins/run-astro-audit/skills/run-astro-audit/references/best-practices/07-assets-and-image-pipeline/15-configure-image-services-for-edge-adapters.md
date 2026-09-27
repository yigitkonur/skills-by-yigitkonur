# Configure Passthrough or Edge Image Services on Serverless Runtimes

> **Context:** Assets & Image Pipeline | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro's default image service uses `sharp`, which relies on native C/C++ libvips binaries compiled for Node.js. Serverless edge runtimes like Cloudflare Workers or Deno Deploy lack native Node C++ binary support. Invoking dynamic image transformation endpoints at runtime on these edge platforms causes unhandled worker exceptions unless an edge-compatible service or passthrough service is explicitly configured.

## 2. How It Differs From Classic React / Next.js

Next.js routes all image transformations through Vercel's proprietary image infrastructure or edge middleware. In Astro, you have full ownership of the image engine: you can keep Sharp for static builds (SSG) while opting into `passthroughImageService()` or a cloud image service (Cloudflare Images, Unpic, ImageKit) for on-demand serverless routes.

## 3. Common Mistakes & Anti-Patterns

Deploying an SSR Astro application to Cloudflare Workers with default Sharp configuration and dynamic image parameters, triggering edge worker runtime crashes on image requests.

### ❌ Bad Practice / Anti-Pattern

Invoking default Sharp image transformation in an edge worker SSR environment:

```javascript
// astro.config.mjs
// ❌ Anti-Pattern: Sharp native binary cannot run in standard Cloudflare Workers runtime
import { defineConfig } from 'astro/config'
import cloudflare from '@astrojs/cloudflare'

export default defineConfig({
  adapter: cloudflare(),
  output: 'server',
  // Missing image.service configuration causes runtime crash on on-demand image routes
})
```

### ✅ Best Practice / Idiomatic

Configure `passthroughImageService()` to bypass native binary execution while retaining `<Image />` dimensions and CLS prevention, or use an edge-native provider:

```javascript
// astro.config.mjs
import { defineConfig, passthroughImageService } from 'astro/config'
import cloudflare from '@astrojs/cloudflare'

export default defineConfig({
  adapter: cloudflare(),
  output: 'server',
  image: {
    // ✅ Safe for Cloudflare Workers: serves images without runtime Sharp dependency
    service: passthroughImageService(),
  },
})
```

## 4. Verification & Audit

Run a local edge preview build to verify no missing native binding errors occur during SSR image route execution:

```bash
pnpm astro build && echo "Pass: Image service compiled cleanly for target runtime"
```
