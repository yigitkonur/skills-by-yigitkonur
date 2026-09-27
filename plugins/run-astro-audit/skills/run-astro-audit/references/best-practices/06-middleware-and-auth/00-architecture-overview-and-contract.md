# Enforce Unified Middleware Architecture and Security Boundary Contract

> **Context:** Middleware & Auth | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro middleware acts as the universal interception layer for all HTTP traffic across SSR, SSG build cycles, and API endpoints. Without an architectural contract, middleware files devolve into monolithic, untyped spaghetti scripts where security checks, route rewrites, header injections, and static asset handling are tangled together. Decomposing middleware into focused, composable handlers via `sequence()` ensures predictable execution order, strict type safety, and zero data leakage.

## 2. How It Differs From Classic React / Next.js

In Next.js App Router, middleware is restricted to a subset of Node APIs and cannot easily share typed in-memory objects directly with page components without header mutation. In Astro, `context.locals` provides a type-safe synchronous bridge between the edge/server middleware layer and server-rendered `.astro` components.

## 3. Common Mistakes & Anti-Patterns

Writing one massive `onRequest` function that mixes asset filtering, rate limiting, authentication, headers, and i18n in a single 200-line block.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  // UNMAINTAINABLE: Tangled concerns, missing sequence, no type safety
  if (context.url.pathname.includes('admin') && !context.cookies.get('token')) {
    return context.redirect('/login')
  }
  context.locals.data = await fetchSomeData()
  const res = await next()
  res.headers.set('X-Security', 'true')
  return res
})
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { sequence } from 'astro:middleware'
import { assetFilter } from './middleware/assets'
import { rateLimiter } from './middleware/rateLimit'
import { authGuard } from './middleware/auth'
import { securityHeaders } from './middleware/security'

// Declarative, modular pipeline with deterministic short-circuiting
export const onRequest = sequence(
  assetFilter, // 1. Skip static assets immediately
  rateLimiter, // 2. Reject abusive traffic
  authGuard, // 3. Guard private routes & inject context.locals
  securityHeaders, // 4. Inject CSP & headers on response
)
```

## 4. Verification & Audit

Run the test suite and verify end-to-end middleware pipeline execution:

```bash
npx astro check && npm run test:middleware
# Validates type contracts, route boundaries, and status code assertions
```
