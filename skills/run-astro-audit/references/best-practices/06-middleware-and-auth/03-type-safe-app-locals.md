# Declare `App.Locals` in `src/env.d.ts` for Type-Safe Context Sharing

> **Context:** Middleware & Auth | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro shares request-scoped state (authenticated user, session tokens, tenant IDs, request timings) across middleware, API endpoints, and `.astro` pages via `context.locals` and `Astro.locals`. Declaring `App.Locals` in `src/env.d.ts` provides complete TypeScript autocompletion, prevents runtime property typos, and eliminates unsafe `(context.locals as any)` type assertions.

## 2. How It Differs From Classic React / Next.js

In Next.js, passing data from middleware to Server Components requires mutating request headers (e.g. `request.headers.set('x-user-id', id)`) or using React `AsyncLocalStorage`. In Astro, `locals` is a first-class in-memory object available synchronously during the server render cycle of that request.

## 3. Common Mistakes & Anti-Patterns

Using type assertions or untyped `any` inside middleware or `.astro` templates, leading to silent bugs when property names drift.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts - without env.d.ts augmentation
export const onRequest = (context, next) => {
  // TypeScript error: Property 'user' does not exist on type 'Locals'
  // Or developer resorts to any-casting:
  ;(context.locals as any).user = { id: '123', role: 'admin' }
  return next()
}
```

### ✅ Best Practice / Idiomatic

```typescript
// src/env.d.ts
interface UserSession {
  id: string
  role: 'admin' | 'editor' | 'viewer'
}

declare namespace App {
  interface Locals {
    user?: UserSession
    requestId: string
  }
}

// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware((context, next) => {
  // Fully typed autocompletion on context.locals
  context.locals.requestId = crypto.randomUUID()
  context.locals.user = { id: '123', role: 'admin' }
  return next()
})
```

## 4. Verification & Audit

Run TypeScript type-checking to verify zero `any` assertions or missing property errors:

```bash
npx astro check
# Should complete with 0 errors and full autocompletion across .astro files
```
