# Never Consume `Request.body` Before or After Rewriting in Middleware

> **Context:** Middleware & Auth | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Under the Web standard Streams API, a `Request` body is a `ReadableStream` that can only be locked and consumed once. When middleware rewrites a request via `next(new Request(...))` or `context.rewrite()`, Astro constructs a new request wrapping the underlying stream. If middleware or a downstream handler (such as an Astro Action or POST endpoint) attempts to read `.formData()`, `.json()`, or `.text()` after the body has already been consumed, the runtime throws an unrecoverable `TypeError: Body has already been consumed`.

## 2. How It Differs From Classic React / Next.js

Express uses body-parser middleware that caches parsed objects onto `req.body`. Astro adheres strictly to standard WHATWG `Request` and `Response` streams without automatic buffering.

## 3. Common Mistakes & Anti-Patterns

Reading request payloads in middleware for logging or signature inspection, then passing the request to Astro Actions or POST endpoints that need the body.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  if (context.request.method === 'POST') {
    // FATAL: Consuming body here permanently locks and exhausts the stream!
    const bodyText = await context.request.text()
    console.log('Payload:', bodyText)

    // Downstream Astro Action will throw: Body has already been consumed!
    return next(new Request('/api/v2/handler'))
  }
  return next()
})
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  // If request payload inspection is required, clone the request first
  if (context.request.method === 'POST' && shouldLog(context)) {
    const clone = context.request.clone()
    const bodyText = await clone.text()
    console.log('Inspected payload without consuming original:', bodyText)
  }

  // For POST routes using Astro Actions, handle rewrites in templates (Astro.rewrite)
  // rather than rewriting mutated requests inside middleware
  return next()
})
```

## 4. Verification & Audit

Verify form actions and POST endpoints succeed with middleware active:

```bash
curl -X POST http://localhost:4321/_actions/submitForm \
  -H "Content-Type: application/json" \
  -d '{"name":"test"}'
# Response must succeed (HTTP 200), not throw "Body has already been consumed"
```
