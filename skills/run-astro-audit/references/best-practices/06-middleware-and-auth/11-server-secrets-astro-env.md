# Access Server Secrets in Middleware via `astro:env/server`

> **Context:** Middleware & Auth | **Impact:** Critical | **Target:** Astro 5 / Astro 4

## 1. Why We Do This

Astro 5 introduced the type-safe `astro:env` module to separate server secrets from client-exposed variables. Middleware frequently handles private encryption keys, OAuth client secrets, and database credentials. Importing secrets exclusively from `astro:env/server` guarantees that private keys are never accidentally bundled into client-side JavaScript or exposed to browser islands.

## 2. How It Differs From Classic React / Next.js

In Next.js, developers rely on naming conventions (`NEXT_PUBLIC_` vs non-prefixed) and `process.env`. If a developer passes a secret into a component that gets rendered client-side, the secret may leak. Astro 5 enforces compile-time and runtime boundaries: importing from `astro:env/server` inside any client island throws a build error immediately.

## 3. Common Mistakes & Anti-Patterns

Using `import.meta.env` with `PUBLIC_` prefixes for server credentials or placing secret keys into `context.locals` and passing them down to client components.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware((context, next) => {
  // CRITICAL SECURITY RISK: PUBLIC_ prefix exposes secret to browser bundles!
  const secretKey = import.meta.env.PUBLIC_JWT_SECRET

  // LEAK RISK: Passing raw secret key into locals which a client island might read
  context.locals.secretToken = secretKey

  return next()
})
```

### ✅ Best Practice / Idiomatic

```typescript
// astro.config.mjs
import { defineConfig, envField } from 'astro/config'

export default defineConfig({
  env: {
    schema: {
      AUTH_SECRET: envField.string({ context: 'server', access: 'secret' }),
    },
    validateSecrets: true,
  },
})

// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'
import { AUTH_SECRET } from 'astro:env/server'

export const onRequest = defineMiddleware(async (context, next) => {
  // Secret is type-safe, validated at startup, and never bundled to client
  const sessionToken = context.cookies.get('session')?.value
  if (sessionToken) {
    context.locals.user = await verifyToken(sessionToken, AUTH_SECRET)
  }
  return next()
})
```

## 4. Verification & Audit

Verify that secrets fail build when missing or exposed to client:

```bash
# Verify startup secret validation
npx astro build
# Build fails immediately if AUTH_SECRET is missing or imported in client code
```
