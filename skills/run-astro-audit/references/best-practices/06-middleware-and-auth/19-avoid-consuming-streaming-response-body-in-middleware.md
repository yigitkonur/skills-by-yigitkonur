# Avoid Consuming Streaming Response Bodies in Post-Execution Middleware

> **Context:** Middleware & Auth | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro renders on-demand pages using chunked HTML streaming via WHATWG `ReadableStream` to achieve instantaneous Time to First Byte (TTFB). When middleware awaits `next()`, `response.body` is an active, single-consumption byte stream. Calling `await response.text()` or `await response.json()` in middleware permanently locks and exhausts the stream, forcing the server to buffer the entire page in RAM before flushing. This destroys streaming performance, creates high memory pressure, and causes unrecoverable `TypeError: Body has already been consumed` runtime crashes.

## 2. How It Differs From Classic React / Next.js

Traditional Node.js/Express middleware often intercepts buffered strings before calling `res.send()`. In Astro, the response conforms strictly to Web Standards. HTML modification in middleware must operate via streaming pipelines (`TransformStream` or `HTMLRewriter`), not string buffering.

## 3. Common Mistakes & Anti-Patterns

Reading `await response.text()` in post-execution middleware to inject tracking scripts or inspect HTML content, killing streaming and throwing stream consumption errors.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  const response = await next()

  // FATAL: Consuming response.text() destroys chunk streaming and buffers entire HTML!
  if (response.headers.get('content-type')?.includes('text/html')) {
    const html = await response.text() // Exhausts stream!
    const modified = html.replace('</body>', "<script src='/track.js'></script></body>")
    return new Response(modified, response)
  }

  return response
})
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  const response = await next()

  // Best Practice 1: Mutate headers directly on the active streaming response
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('X-Frame-Options', 'DENY')

  // Best Practice 2: If HTML modification is strictly required, use TransformStream or HTMLRewriter
  // rather than buffering the body with response.text()
  return response
})
```

## 4. Verification & Audit

Measure Time to First Byte (TTFB) on a large streaming page using curl:

```bash
curl -w "TTFB: %{time_starttransfer}s | Total: %{time_total}s\n" -o /dev/null -s http://localhost:4321/
# TTFB must occur almost instantaneously (<50ms) rather than waiting for the entire body to buffer
```
