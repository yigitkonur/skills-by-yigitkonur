# Authorize Remote Image Origins Using image.remotePatterns

> **Context:** Assets & Image Pipeline | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Allowing arbitrary remote image optimization creates dangerous Server-Side Request Forgery (SSRF) and Denial-of-Service vectors. Malicious users can force your build server or SSR worker to fetch internal intranet addresses or repeatedly transform multi-gigabyte decompression bombs. Configuring `image.remotePatterns` restricts image processing strictly to trusted origins and paths.

## 2. How It Differs From Classic React / Next.js

Next.js throws an unhandled server error (500) if an unconfigured remote image URL is passed to `next/image`. In contrast, Astro defaults to fail-safe behavior: unconfigured remote images are not rejected with a fatal error; instead, Astro falls back to rendering an unoptimized raw `<img>` tag and logs a non-blocking warning.

## 3. Common Mistakes & Anti-Patterns

Using broad wildcards in `image.domains` (such as `["*"]`) or permissive pattern matchers that permit unauthorized subdomains or arbitrary HTTP/HTTPS endpoints.

### ❌ Bad Practice / Anti-Pattern

Permissive wildcard configuration exposing server-side image fetching to arbitrary domains:

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config'

// ❌ Anti-Pattern: Unrestricted remote access creates SSRF vulnerabilities
export default defineConfig({
  image: {
    domains: ['*'],
  },
})
```

### ✅ Best Practice / Idiomatic

Lock down remote origins using strict `protocol`, `hostname`, and specific `pathname` prefixes:

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config'

export default defineConfig({
  image: {
    // ✅ Strictly authorizes verified CMS asset buckets
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.ctfassets.net',
        pathname: '/w67f89abc/**',
      },
      {
        protocol: 'https',
        hostname: 'cdn.sanity.io',
        pathname: '/images/production/**',
      },
    ],
  },
})
```

## 4. Verification & Audit

Audit your `astro.config.mjs` to ensure no open wildcards exist and that `remotePatterns` specifies explicit protocols and hostnames:

```bash
grep -n "remotePatterns" astro.config.* && grep -rn 'domains: \["\*"\]' astro.config.* && echo "Fail: Wildcard domain found" || echo "Pass: Secure remote patterns enforced"
```
