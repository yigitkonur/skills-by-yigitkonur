# Mutate `context.locals` Properties; Never Overwrite the Object

> **Context:** Middleware & Auth | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

`context.locals` is a shared container managed by the Astro runtime and third-party integrations (e.g., i18n adapters, hosting runtime contexts like Cloudflare Workers `env`, and authentication libraries). Astro explicitly prohibits reassigning `context.locals` to a primitive (throwing `LocalsNotAnObject`). Furthermore, reassigning `context.locals = { ... }` wipes out properties pre-populated by upstream integrations and adapter runtimes.

## 2. How It Differs From Classic React / Next.js

In Express, middleware often writes to `res.locals = {}` to reset state. In Astro, `context.locals` is instantiated once per route lifecycle. Overriding the reference destroys adapter bindings (such as `context.locals.runtime.env` on Cloudflare or OpenNext).

## 3. Common Mistakes & Anti-Patterns

Assigning a fresh object literal or setting `context.locals` to `null` or a non-object to clear state between requests.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware((context, next) => {
  // FATAL: Overwriting context.locals destroys adapter runtime and integration data!
  context.locals = {
    user: { id: '42', name: 'Alice' },
  }

  // Even worse: setting to primitive throws LocalsNotAnObject error
  // context.locals = null;

  return next()
})
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware((context, next) => {
  // Mutate individual properties directly
  context.locals.user = { id: '42', name: 'Alice' }

  // Or merge safely without blowing away existing integration keys
  Object.assign(context.locals, {
    tenantId: 'org_enterprise',
    featureFlags: { betaUI: true },
  })

  return next()
})
```

## 4. Verification & Audit

Verify that runtime context and integration locals persist:

```bash
# In Cloudflare or Node SSR, check that context.locals.runtime remains accessible
curl -i http://localhost:4321/api/check-locals
# Ensure status is 200 and integration keys are intact
```
