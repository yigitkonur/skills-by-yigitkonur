# Distinguish `context.rewrite()` From `next(url)` to Prevent Infinite Loops

> **Context:** Middleware & Auth | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro 4.13 introduced internal request rewriting. However, `context.rewrite()` and `next(path)` have fundamentally different lifecycles:

1. `context.rewrite()` re-triggers the entire rendering phase and **re-executes all middleware from the very beginning**. Without a termination guard, it triggers an infinite loop.
2. `next(path)` updates the request in place and **passes it forward to subsequent middleware** in the chain without restarting the pipeline.

## 2. How It Differs From Classic React / Next.js

In Next.js, `NextResponse.rewrite()` immediately proxies the internal request without restarting the middleware pipeline. In Astro, calling `context.rewrite()` restarts the middleware chain, requiring explicit guards on `context.url.pathname`.

## 3. Common Mistakes & Anti-Patterns

Calling `context.rewrite()` without verifying whether the request has already been rewritten, creating an infinite recursion loop that crashes server threads.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware((context, next) => {
  if (!isLoggedIn(context)) {
    // FATAL INFINITE LOOP: Rewrites to /login, which re-executes onRequest,
    // which sees user is still logged out and rewrites to /login again indefinitely!
    return context.rewrite(new Request('/login'))
  }
  return next()
})
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware((context, next) => {
  const { pathname } = context.url

  // Guard: Never rewrite if we are already on the target route
  if (!isLoggedIn(context) && pathname !== '/login') {
    // Option A: context.rewrite() triggers full re-render with new route
    return context.rewrite(
      new Request('/login', {
        headers: { 'x-original-path': pathname },
      }),
    )

    // Option B: next(url) forwards rewritten request downstream without re-running this middleware
    // return next(new Request("/login"));
  }

  return next()
})
```

## 4. Verification & Audit

Verify that rewritten routes render without infinite loop timeouts:

```bash
curl -i http://localhost:4321/private-area
# Must return HTTP 200 with /login page content in <50ms without recursion error
```
