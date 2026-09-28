# Guard Dynamic Operations Against Build-Time Execution via `context.isPrerendered`

> **Context:** Middleware & Auth | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

In Astro projects with static or hybrid rendering (`output: 'static'` or `prerender = true`), middleware executes **at build time** for each prerendered page. During static compilation, runtime request headers (like `cookie`, `authorization`, or client Geo-IP) are unavailable or represent simulated build contexts. Checking `context.isPrerendered` allows middleware to safely skip dynamic authentication guards and session lookups during build.

## 2. How It Differs From Classic React / Next.js

In Next.js, `middleware.ts` runs strictly at edge request time and never executes during static page compilation (`next build`). In Astro, middleware participates in both the static SSG build phase and dynamic SSR requests.

## 3. Common Mistakes & Anti-Patterns

Attempting to issue dynamic redirects or throwing errors when cookies are missing during `astro build`.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  // CRASHES BUILD: During static generation, cookies are undefined.
  // This aborts astro build on prerendered marketing or landing pages!
  const session = context.cookies.get('session')?.value
  if (!session) {
    return context.redirect('/login') // Throws during static generation
  }

  return next()
})
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  // 1. Immediately pass through prerendered static pages at build time
  if (context.isPrerendered) {
    return next()
  }

  // 2. Execute dynamic cookie parsing and auth guards strictly on on-demand SSR routes
  const sessionToken = context.cookies.get('session')?.value
  if (!sessionToken && context.url.pathname.startsWith('/app')) {
    return context.redirect('/login', 302)
  }

  if (sessionToken) {
    context.locals.user = await validateSession(sessionToken)
  }

  return next()
})
```

## 4. Verification & Audit

Run production build to verify static pages compile without middleware failures:

```bash
npx astro build
# Static routes must compile cleanly without throwing unhandled redirect errors
```
