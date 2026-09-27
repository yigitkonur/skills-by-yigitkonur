# Compose i18n Routing Before Auth Guards to Handle Localized Protected Paths

> **Context:** Middleware & Auth | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

In multilingual applications, protected routes are prefixed by locale codes (e.g. `/tr/dashboard`, `/en/dashboard`, `/es/admin`). If authentication guards evaluate hardcoded static paths (`pathname.startsWith('/dashboard')`) without accounting for locale prefixes, localized routes will completely bypass the auth guard. Composing i18n normalization before auth guards ensures canonical path inspection and preserves user locale across login redirects.

## 2. How It Differs From Classic React / Next.js

In Next.js, `next-intl` or Next.js i18n routing wraps the middleware pipeline in a proprietary middleware factory. In Astro, `sequence()` combines manual or built-in i18n middleware with custom auth guards explicitly.

## 3. Common Mistakes & Anti-Patterns

Hardcoding English route paths in auth guards, leaving localized routes (`/tr/admin`, `/fr/admin`) unprotected, or redirecting non-English users to English `/login`.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts
import { defineMiddleware, sequence } from 'astro:middleware'

const authGuard = defineMiddleware((context, next) => {
  // CRITICAL BUG: /tr/admin or /de/dashboard escapes this check completely!
  if (context.url.pathname.startsWith('/admin')) {
    if (!context.locals.user) {
      return context.redirect('/login') // Loses current user locale!
    }
  }
  return next()
})

export const onRequest = authGuard
```

### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts
import { defineMiddleware, sequence } from 'astro:middleware'

const LOCALES = ['en', 'tr', 'de', 'es']

const authGuard = defineMiddleware(async (context, next) => {
  const { pathname } = context.url

  // Extract locale prefix and canonical path segment
  const segments = pathname.split('/').filter(Boolean)
  const hasLocale = LOCALES.includes(segments[0])
  const currentLocale = hasLocale ? segments[0] : 'en'
  const canonicalPath = '/' + (hasLocale ? segments.slice(1).join('/') : segments.join('/'))

  if (canonicalPath.startsWith('/admin') || canonicalPath.startsWith('/dashboard')) {
    if (!context.locals.user) {
      const returnUrl = encodeURIComponent(pathname)
      return context.redirect(`/${currentLocale}/login?returnTo=${returnUrl}`, 302)
    }
  }

  return next()
})

export const onRequest = sequence(authGuard)
```

## 4. Verification & Audit

Verify localized route protection with curl:

```bash
curl -i http://localhost:4321/tr/admin
# Must return HTTP 302 with Location: /tr/login?returnTo=%2Ftr%2Fadmin
```
