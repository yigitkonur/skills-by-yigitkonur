# Implement Distributed Rate Limiting; Avoid Unbounded In-Memory Maps

> **Context:** Middleware & Auth | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Middleware is the first line of defense against volumetric denial-of-service and credential-stuffing attacks. However, storing request counters in standard JavaScript in-memory `Map` objects fails in distributed edge/serverless environments (where memory is not shared across regional isolates) and introduces unbounded memory leaks in persistent Node.js servers without proper TTL garbage collection.

## 2. How It Differs From Classic React / Next.js

Express servers often use simple in-process `express-rate-limit` instances. Astro applications deployed to distributed edge runtimes (Cloudflare Workers, Fastly, Vercel Edge) execute across multiple isolated global instances, necessitating stateless or remote KV-backed token bucket stores.

## 3. Common Mistakes & Anti-Patterns

Using global mutable in-memory Maps that leak memory indefinitely and fail to synchronize across multi-core or serverless worker instances.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

// MEMORY LEAK & DISTRIBUTED BLIND SPOT:
// Unbounded Map leaks memory on Node.js and fails across multi-worker edge nodes!
const requestCounts = new Map<string, number>()

export const onRequest = defineMiddleware((context, next) => {
  const ip = context.request.headers.get('cf-connecting-ip') || 'unknown'
  const count = (requestCounts.get(ip) || 0) + 1
  requestCounts.set(ip, count)

  if (count > 100) {
    return new Response('Too Many Requests', { status: 429 })
  }
  return next()
})
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  // Only rate-limit sensitive mutation endpoints
  if (!context.url.pathname.startsWith('/api/auth/')) {
    return next()
  }

  const clientIp = context.request.headers.get('cf-connecting-ip') ?? '127.0.0.1'

  // Use distributed atomic store (e.g., Upstash Redis, Cloudflare Rate Limiting API)
  const isAllowed = await checkRateLimit(clientIp, { limit: 10, windowSec: 60 })
  if (!isAllowed) {
    return new Response(JSON.stringify({ error: 'Rate limit exceeded' }), {
      status: 429,
      headers: {
        'Content-Type': 'application/json',
        'Retry-After': '60',
      },
    })
  }

  return next()
})
```

## 4. Verification & Audit

Verify HTTP 429 and Retry-After header with benchmark tool or curl:

```bash
for i in {1..12}; do curl -i -X POST http://localhost:4321/api/auth/login; done
# 11th and 12th requests must return HTTP 429 with Retry-After: 60
```
