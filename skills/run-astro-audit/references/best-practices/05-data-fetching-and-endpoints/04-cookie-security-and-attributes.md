# Enforce Secure Cookie Attributes in Server Endpoints and Frontmatter

> **Context:** Data Fetching & Endpoints | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro provides the `AstroCookies` interface through `Astro.cookies` (in `.astro` pages) and `context.cookies` (in `APIRoute` endpoints). Cookies store sensitive session identifiers, authentication tokens, and user preferences. Omitting essential security flags (`httpOnly`, `secure`, and `sameSite`) exposes tokens to Cross-Site Scripting (XSS) extraction via `document.cookie` or Cross-Site Request Forgery (CSRF) in cross-origin requests. Explicit security options must always be passed when persisting stateful cookies.

## 2. How It Differs From Classic React / Next.js

In Next.js, `cookies()` from `next/headers` is an asynchronous call (`await cookies()`) in Next 15, or accessed via middleware response mutations. In Astro, `Astro.cookies` and `context.cookies` are synchronous interfaces offering parsed helpers: `.value`, `.json()`, `.number()`, and `.boolean()`. Astro automatically serializes `Set-Cookie` headers into the outgoing HTTP response without requiring manual string formatting or external cookie libraries.

## 3. Common Mistakes & Anti-Patterns

Setting cookies with default insecure flags or reading without safe type conversions.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/pages/api/login.ts
import type { APIRoute } from 'astro'
export const prerender = false

export const POST: APIRoute = async ({ request, cookies }) => {
  const { sessionToken } = await request.json()

  // ❌ Insecure: No httpOnly, no secure flag, no sameSite protection!
  // JavaScript on the client can read this sensitive auth token via XSS.
  cookies.set('session', sessionToken)

  return Response.json({ success: true })
}
```

### ✅ Best Practice / Idiomatic

```ts
// src/pages/api/login.ts
import type { APIRoute } from 'astro'
export const prerender = false

export const POST: APIRoute = async ({ request, cookies }) => {
  const { sessionToken } = await request.json()

  // ✅ Secure: Strict defense-in-depth cookie configuration
  cookies.set('session', sessionToken, {
    path: '/',
    httpOnly: true, // Prevents client-side JS access
    secure: import.meta.env.PROD, // Transmitted only via HTTPS in production
    sameSite: 'lax', // Protects against CSRF on top-level navigations
    maxAge: 60 * 60 * 24 * 7, // 7 days in seconds
  })

  return Response.json({ success: true }, { status: 200 })
}

// Deleting cookies safely requires matching path:
export const DELETE: APIRoute = async ({ cookies }) => {
  cookies.delete('session', { path: '/' })
  return Response.json({ loggedOut: true }, { status: 200 })
}
```

## 4. Verification & Audit

Verify outgoing `Set-Cookie` headers via curl:

```bash
curl -i -X POST -H "Content-Type: application/json" \
  -d '{"sessionToken":"xyz123"}' http://localhost:4321/api/login
```

Confirm the header contains `HttpOnly`, `SameSite=Lax`, and `Path=/`.
