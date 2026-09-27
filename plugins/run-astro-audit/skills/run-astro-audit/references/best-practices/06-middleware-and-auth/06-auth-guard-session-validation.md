# Protect Authenticated Routes Server-Side via `context.cookies` and `context.redirect`

> **Context:** Middleware & Auth | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Protecting private pages (dashboards, account settings, admin panels) must occur on the server before page rendering begins. Relying on client-side React hydration guards leaks server-rendered HTML markup and private data in the initial HTTP response. Intercepting requests in Astro middleware and calling `context.redirect()` ensures unauthorized users never receive protected content.

## 2. How It Differs From Classic React / Next.js

In single-page React apps, auth guards often run in client-side router wrappers (`<ProtectedRoute>`), flashing sensitive components before redirecting. In Next.js App Router, layout auth guards can trigger waterfall renders. Astro middleware handles the check atomically at the edge or server boundary before any HTML or Island is instantiated.

## 3. Common Mistakes & Anti-Patterns

Rendering protected HTML and using client-side JavaScript or `<script>` tags to redirect unauthenticated visitors.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/admin/dashboard.astro
// UNSECURE: The full admin dashboard HTML is rendered and sent to the client!
const session = Astro.cookies.get("session")?.value;
if (!session) {
  // Client-side script execution leaves page content exposed in source
  return Astro.redirect("/login"); // Works only in SSR; completely leaks in SSG/prerendered
}
---
<AdminSecretsPanel />
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  const { pathname } = context.url

  if (pathname.startsWith('/admin') || pathname.startsWith('/dashboard')) {
    const sessionToken = context.cookies.get('session_token')?.value
    const user = sessionToken ? await validateSession(sessionToken) : null

    if (!user) {
      const returnUrl = encodeURIComponent(pathname)
      return context.redirect(`/login?returnTo=${returnUrl}`, 302)
    }

    // Pass validated session to all pages and endpoints
    context.locals.user = user
  }

  return next()
})
```

## 4. Verification & Audit

Simulate unauthenticated requests to protected paths:

```bash
curl -i -X GET http://localhost:4321/admin/dashboard
# Output must be HTTP/1.1 302 Found with Location: /login?returnTo=%2Fadmin%2Fdashboard
# Response body must not contain any admin dashboard markup
```
