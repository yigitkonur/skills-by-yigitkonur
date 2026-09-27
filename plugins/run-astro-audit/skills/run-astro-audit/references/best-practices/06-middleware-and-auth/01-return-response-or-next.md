# Always Return a Response or `next()` From Every Middleware Branch

> **Context:** Middleware & Auth | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro middleware functions (`onRequest`) must always resolve to a `Response` object. If a middleware branch terminates without explicitly returning `next()` or a custom `Response`, Astro immediately halts the execution pipeline and raises runtime error `MiddlewareNoDataOrNextCalled`. Returning a proper `Response` guarantees that request pipelines either advance to page rendering or exit cleanly with an intended HTTP status code.

## 2. How It Differs From Classic React / Next.js

In Express or Connect middleware, calling `next()` without returning its result is standard practice (`next();`), and returning nothing simply delegates down the stack. In Next.js middleware, omitting a return defaults to `NextResponse.next()`. In Astro, however, `next()` returns a `Promise<Response>` which **must be returned or awaited and returned** by the handler.

## 3. Common Mistakes & Anti-Patterns

Developers frequently forget to return in conditional execution branches (such as logging, metric emissions, or unauthenticated route checks), causing unhandled paths to return `undefined`.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware((context, next) => {
  if (context.url.pathname.startsWith('/api/public')) {
    // Missing return! Resolves to undefined, throwing MiddlewareNoDataOrNextCalled
    next()
  } else {
    return next()
  }
})
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  if (context.url.pathname.startsWith('/api/public')) {
    return next()
  }

  // Ensure every branch returns a valid Response object
  return next()
})
```

## 4. Verification & Audit

Run dev mode or dynamic SSR requests across all branch paths:

```bash
# Verify no unhandled execution paths trigger MiddlewareNoDataOrNextCalled
curl -I http://localhost:4321/api/public/ping
# Response must be HTTP 200/OK, not an Astro 500 MiddlewareNoDataOrNextCalled error
```
