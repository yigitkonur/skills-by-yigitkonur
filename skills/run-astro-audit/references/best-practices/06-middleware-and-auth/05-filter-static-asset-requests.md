# Filter Out Static Assets Before Executing Heavy Middleware Logic

> **Context:** Middleware & Auth | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

In SSR and edge worker environments (such as Cloudflare Workers or Node server adapters), all incoming HTTP requests hit the middleware pipeline. Executing database session queries, JWT validations, or external API calls for static assets (`/_astro/*`, images, fonts, `favicon.ico`, or `robots.txt`) introduces massive latency, inflates edge compute costs, and exhausts database connection pools.

## 2. How It Differs From Classic React / Next.js

In Next.js, `middleware.ts` uses an exported `config.matcher` with regex patterns to exclude static files at the engine level. Astro does not use a `matcher` export; route filtering must be evaluated programmatically inside the middleware logic using `context.url.pathname`.

## 3. Common Mistakes & Anti-Patterns

Performing asynchronous authentication or database checks on every request without inspecting the URL pathname.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  // Heavy DB session lookup runs for /_astro/style.css and /favicon.ico!
  const token = context.cookies.get('session')?.value
  context.locals.user = await db.verifySession(token)

  return next()
})
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

const STATIC_PREFIXES = ['/_astro/', '/assets/', '/fonts/', '/favicon.ico', '/robots.txt']

export const onRequest = defineMiddleware(async (context, next) => {
  const { pathname } = context.url

  // Immediately bypass middleware for static bundles and public files
  if (STATIC_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
    return next()
  }

  // Also skip prerendered pages if dynamic session checks are not required
  if (context.isPrerendered) {
    return next()
  }

  const token = context.cookies.get('session')?.value
  if (token) {
    context.locals.user = await db.verifySession(token)
  }

  return next()
})
```

## 4. Verification & Audit

Audit network requests to ensure static assets return without session headers or DB delay:

```bash
curl -I http://localhost:4321/_astro/client.bundle.js
# Static response should be served immediately with minimal latency (<5ms)
```
