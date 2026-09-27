# Canonicalize Pathnames to Prevent Auth Bypass Vulnerabilities

> **Context:** Middleware & Auth | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Security vulnerability GHSA-vj59-8hwv-xxmv (CVE-2026-59731) proved that naive path prefix checks in authorization middleware can be bypassed via iterative percent-encoding (e.g., `%252fadmin` or trailing slashes). If authorization middleware evaluates a partially decoded path while downstream router logic performs further decoding, a canonicalization mismatch occurs. Unauthenticated attackers can bypass route guards and access protected endpoints.

## 2. How It Differs From Classic React / Next.js

In Next.js, pathname normalization is handled before `middleware.ts` runs. In Astro and edge runtimes, `context.url.pathname` provides the URI-decoded path according to standard URL parsing, but multi-encoded or non-normalized paths (e.g. `/admin/..%2fadmin`) require disciplined validation before security decisions.

## 3. Common Mistakes & Anti-Patterns

Performing naive `.startsWith()` matching on raw pathnames without normalizing slashes or handling encoded characters.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  // VULNERABLE: %2fadmin or //admin or /admin/.. can bypass this check
  if (context.url.pathname.startsWith('/admin')) {
    if (!context.locals.user) {
      return context.redirect('/login')
    }
  }
  return next()
})
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

function getCanonicalPath(pathname: string): string {
  try {
    // Decode percent-encoding and normalize slashes
    const decoded = decodeURIComponent(pathname)
    // Collapse duplicate slashes and strip trailing slash
    return decoded.replace(/\/+/g, '/').toLowerCase()
  } catch {
    return pathname.toLowerCase()
  }
}

export const onRequest = defineMiddleware(async (context, next) => {
  const canonicalPath = getCanonicalPath(context.url.pathname)

  // Check against normalized, canonicalized path
  const isProtected = canonicalPath === '/admin' || canonicalPath.startsWith('/admin/')

  if (isProtected) {
    const user = context.locals.user
    if (!user) {
      return context.redirect('/login', 302)
    }
  }

  return next()
})
```

## 4. Verification & Audit

Adversarial test using encoded and non-standard URL path variants:

```bash
# Test URL-encoded and multi-slash path variants
curl -i http://localhost:4321/%2fadmin
curl -i http://localhost:4321//admin/dashboard
curl -i http://localhost:4321/admin/..%2fadmin
# All variations must return 302 to /login, never HTTP 200 or 500
```
