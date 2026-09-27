# Wrap `await next()` in Resilient Error Boundaries for Robust Fallbacks

> **Context:** Middleware & Auth | **Impact:** Medium | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

When downstream Astro pages or API endpoints encounter unexpected exceptions during server rendering, the error bubbles up through the `await next()` call. If middleware does not handle or log this exception, the request crashes ungracefully. Furthermore, if middleware itself crashes, `Astro.locals` becomes unavailable to custom 500 error pages. Wrapping downstream execution preserves diagnostic context and ensures clean 500 fallbacks.

## 2. How It Differs From Classic React / Next.js

React error boundaries (`ErrorBoundary`) catch rendering errors inside client or server components, but cannot intercept server endpoint crashes or middleware pipeline errors. Astro middleware acts as the outermost HTTP wrapper around the entire rendering engine.

## 3. Common Mistakes & Anti-Patterns

Letting unhandled exceptions crash the worker or Node process without structured logging or omitting the return of a valid `Response` in catch blocks.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  // UNPROTECTED: If a page component throws an unhandled error,
  // this middleware halts and returns undefined, triggering MiddlewareNoDataOrNextCalled
  try {
    return await next()
  } catch (err) {
    console.error('Crash:', err)
    // Missing return! Throws second internal Astro error
  }
})
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  try {
    return await next()
  } catch (error) {
    // 1. Emit structured telemetry / error report
    console.error('[Middleware Error Boundary]', {
      url: context.url.pathname,
      error: error instanceof Error ? error.message : String(error),
      requestId: context.locals.requestId,
    })

    // 2. Return a valid HTTP 500 Response to complete the HTTP exchange cleanly
    return new Response(
      JSON.stringify({ error: 'Internal Server Error', requestId: context.locals.requestId }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      },
    )
  }
})
```

## 4. Verification & Audit

Simulate an endpoint crash and verify error boundary capture:

```bash
curl -i http://localhost:4321/api/broken-route
# Must return HTTP 500 with valid JSON response and structured server log
```
