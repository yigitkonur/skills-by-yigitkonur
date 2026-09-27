# Implement Manual Routing Middleware Only When Astro Default Router Cannot Suffice

> **Context:** i18n & Localization | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro’s native i18n router handles 95% of internationalization scenarios automatically. However, enterprise sites with cookie-based language persistence, auth-gated regional content, or custom session routing require granular control. Astro 4.6+ provides `routing: "manual"`, disabling the automatic i18n middleware while exposing low-level utilities (`redirectToDefaultLocale`, `redirectToFallback`, `middleware`) for custom pipeline composition.

## 2. How It Differs From Classic React / Next.js

In Next.js, developers have no choice but to write custom routing middleware for even simple i18n tasks. In Astro, `routing: "manual"` is an explicit opt-in escape hatch. You keep type-safe access to `astro:i18n` helpers while gaining complete authority over response headers, cookies, and rewrite sequences.

## 3. Common Mistakes & Anti-Patterns

Setting `routing: "manual"` without implementing custom middleware triggers the `MissingMiddlewareForInternationalization` error. Another mistake is rewriting the entire routing logic from scratch instead of composing Astro’s built-in `middleware()` helper using `sequence()`.

### ❌ Bad Practice / Anti-Pattern

```js
// astro.config.mjs
export default defineConfig({
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'es'],
    routing: 'manual', // Enables manual mode...
  },
})
// Developer forgets to create src/middleware.ts!
// Result: FATAL BUILD ERROR "MissingMiddlewareForInternationalization"
```

### ✅ Best Practice / Idiomatic

```ts
// src/middleware.ts - Composing custom cookie logic with Astro i18n middleware
import { defineMiddleware, sequence } from 'astro:middleware'
import { middleware, redirectToDefaultLocale } from 'astro:i18n'

const cookieLocaleMiddleware = defineMiddleware(async (context, next) => {
  const preferredCookie = context.cookies.get('user-locale')?.value
  const { pathname } = context.url

  // Custom exception: redirect root visitors if user previously saved a cookie preference
  if (pathname === '/' && preferredCookie && preferredCookie !== 'en') {
    return context.redirect(`/${preferredCookie}/`, 302)
  }

  return next()
})

export const onRequest = sequence(
  cookieLocaleMiddleware,
  // Seamlessly chain Astro's official i18n middleware
  middleware({
    redirectToDefaultLocale: false,
    prefixDefaultLocale: false,
    fallbackType: 'rewrite',
  }),
)
```

## 4. Verification & Audit

Verify that custom middleware chains correctly without crashing on startup:

```bash
npx astro dev --port 4321
```

Use curl to verify cookie-driven redirection:

```bash
curl -I --cookie "user-locale=es" http://localhost:4321/
```

Verify that the response returns `302 Found` with `Location: /es/`.
