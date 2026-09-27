# Safely Forward and Persist Cookies During Middleware Redirects

> **Context:** Middleware & Auth | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

When authenticating or refreshing session tokens in middleware, setting a new cookie must reliably accompany any redirect. Returning a raw `new Response(null, { status: 302, headers: { Location: ... } })` bypasses Astro's internal response pipeline, causing cookies queued via `context.cookies.set()` to be dropped. Using `context.redirect()` ensures queued cookies are automatically serialized into `Set-Cookie` response headers.

## 2. How It Differs From Classic React / Next.js

In Next.js, `NextResponse.redirect()` requires explicitly chaining `.cookies.set()` onto the response object. In Astro, `context.cookies` integrates with `context.redirect()`, serializing all modified cookies into the redirect response.

## 3. Common Mistakes & Anti-Patterns

Using `context.cookies.set()` followed by a manually constructed `new Response(...)`, which drops the `Set-Cookie` header entirely.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  if (context.url.pathname === '/oauth/callback') {
    const newSessionToken = 'xyz123'
    context.cookies.set('session', newSessionToken, { path: '/' })

    // BUG: Raw Response bypasses Astro cookie serializer; session cookie is lost!
    return new Response(null, {
      status: 302,
      headers: { Location: '/dashboard' },
    })
  }

  return next()
})
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  if (context.url.pathname === '/oauth/callback') {
    const newSessionToken = 'xyz123'

    // Set cookie with secure attributes
    context.cookies.set('session', newSessionToken, {
      path: '/',
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 7, // 7 days
    })

    // context.redirect automatically serializes context.cookies to Set-Cookie headers
    return context.redirect('/dashboard', 302)
  }

  return next()
})
```

## 4. Verification & Audit

Verify that redirect responses contain the expected `Set-Cookie` header:

```bash
curl -i http://localhost:4321/oauth/callback
# Response must contain HTTP/1.1 302 and Set-Cookie: session=...; Path=/; HttpOnly; Secure
```
