# Eliminate Blocking Async Waterfalls in Pre-Render Middleware

> **Context:** Middleware & Auth | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Any asynchronous operation executed before `next()` directly increases server response latency and degrades Time to First Byte (TTFB) for every visitor. Executing multiple serial database queries, remote microservice calls, or third-party feature flag lookups creates a blocking waterfall that slows down the entire application. Parallelizing requests or deferring data fetching via lazy properties on `context.locals` maintains ultra-fast server response times.

## 2. How It Differs From Classic React / Next.js

In React Server Components or Next.js, data fetching is usually pushed down into individual component leaves. In Astro, developers frequently attempt to fetch all user profile data, permissions, and organization metadata upfront in middleware, creating a monolithic bottleneck before HTML generation even begins.

## 3. Common Mistakes & Anti-Patterns

Awaiting multiple independent asynchronous promises sequentially before delegating to `next()`.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  // SLOW: 4 sequential network requests add ~350ms to TTFB on every page request!
  const session = await getSession(context.cookies)
  const user = await fetchUserProfile(session.userId)
  const permissions = await fetchUserPermissions(user.id)
  const featureFlags = await fetchFeatureFlags(user.orgId)

  context.locals.user = { ...user, permissions, featureFlags }
  return next()
})
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  const sessionToken = context.cookies.get('session')?.value
  if (!sessionToken) return next()

  // Fast path: Only verify essential session token upfront
  const session = await verifySessionToken(sessionToken)
  if (!session) return next()

  context.locals.session = session

  // Provide lazy getters or parallelized loaders so pages only fetch what they render
  context.locals.getUserProfile = () => fetchUserProfile(session.userId)
  context.locals.getPermissions = () => fetchUserPermissions(session.userId)

  return next()
})
```

## 4. Verification & Audit

Measure TTFB on SSR routes with and without authentication:

```bash
curl -o /dev/null -s -w 'TTFB: %{time_starttransfer}s\n' http://localhost:4321/dashboard
# Target TTFB should remain under 50ms on local server
```
