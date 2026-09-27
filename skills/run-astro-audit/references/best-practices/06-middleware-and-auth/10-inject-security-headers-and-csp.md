# Inject Security Headers and CSP in Post-Execution Middleware

> **Context:** Middleware & Auth | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Enforcing defense-in-depth requires consistent HTTP security headers across every server-rendered page and dynamic endpoint. Applying headers like `Content-Security-Policy`, `X-Content-Type-Options`, and `Strict-Transport-Security` inside Astro middleware ensures that all routes adhere to security baselines without requiring individual configuration on every route or layout.

## 2. How It Differs From Classic React / Next.js

In Next.js, headers can be defined statically in `next.config.js` or dynamically in `middleware.ts`. In Astro, middleware provides the dynamic interception layer to inspect, augment, or set headers on the outgoing `Response` returned by `await next()`.

## 3. Common Mistakes & Anti-Patterns

Instantiating an entirely new `Response` from scratch without preserving status code or existing headers set by downstream endpoints (such as `Set-Cookie` or `Cache-Control`).

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  const response = await next()
  // BAD: Creating fresh Response loses Set-Cookie headers and downstream status codes!
  return new Response(response.body, {
    headers: {
      'Content-Security-Policy': "default-src 'self'",
    },
  })
})
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

const SECURITY_HEADERS: Record<string, string> = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  'Content-Security-Policy':
    "default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline';",
}

export const onRequest = defineMiddleware(async (context, next) => {
  const response = await next()

  // Apply security headers to HTML pages while preserving existing response headers
  const contentType = response.headers.get('Content-Type') || ''
  if (contentType.includes('text/html')) {
    for (const [key, value] of Object.entries(SECURITY_HEADERS)) {
      if (!response.headers.has(key)) {
        response.headers.set(key, value)
      }
    }
  }

  return response
})
```

## 4. Verification & Audit

Audit headers on rendered HTML responses:

```bash
curl -I http://localhost:4321/
# Verify X-Content-Type-Options: nosniff and Content-Security-Policy are present
```
