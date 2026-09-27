# Sequence Chained Middleware With Strict Fail-Fast Order

> **Context:** Middleware & Auth | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro provides `sequence()` to chain modular middleware functions in a deterministic pipeline. Middleware executes in FIFO order before `next()` is called, and in LIFO (reverse) order after `await next()`. When an upstream middleware returns a `Response` directly (e.g. an authentication redirect or rate-limit rejection), execution **short-circuits immediately**, preventing downstream middleware from executing unnecessary database queries or heavy computations.

## 2. How It Differs From Classic React / Next.js

Next.js supports a single `middleware.ts` file without native function chaining utilities; developers must build custom runner wrappers or compose functions manually. Astro's `sequence()` provides a first-class onion-model pipeline native to the runtime.

## 3. Common Mistakes & Anti-Patterns

Placing expensive business logic or session lookup before rapid security guards or static asset filters. Another mistake is assuming downstream middleware still runs when an upstream guard issues a redirect.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { sequence } from 'astro:middleware'

// Session DB lookup runs before rate limiting and asset filtering!
export const onRequest = sequence(heavySessionLoader, rateLimiter, staticAssetFilter)
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { sequence, defineMiddleware } from 'astro:middleware'

const assetBypass = defineMiddleware((ctx, next) => {
  if (ctx.url.pathname.startsWith('/_astro/')) return next()
  return next()
})

const rateLimiter = defineMiddleware(async (ctx, next) => {
  if (isRateLimited(ctx)) return new Response('Too Many Requests', { status: 429 })
  return next()
})

const authGuard = defineMiddleware(async (ctx, next) => {
  // Executes only if rate limiting passed
  return next()
})

export const onRequest = sequence(assetBypass, rateLimiter, authGuard)
```

## 4. Verification & Audit

Verify execution order and short-circuiting in terminal logs:

```bash
# Send rapid requests exceeding rate limit threshold
curl -i http://localhost:4321/api/protected
# Response must be HTTP 429 and downstream auth logs must not appear
```
