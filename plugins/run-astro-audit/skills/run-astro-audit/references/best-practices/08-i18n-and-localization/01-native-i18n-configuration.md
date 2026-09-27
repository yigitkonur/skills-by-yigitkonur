# Configure Native i18n in astro.config.mjs Instead of Ad-Hoc Routing

> **Context:** i18n & Localization | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro provides a built-in internationalization routing engine initialized directly inside `astro.config.mjs`. Configuring native i18n gives Astro compile-time awareness of every supported locale, default language, and route prefix rule. This enables automated relative/absolute URL computation via `astro:i18n`, static path validation, and automatic `Accept-Language` header negotiation without third-party dependencies or runtime overhead.

## 2. How It Differs From Classic React / Next.js

In Next.js (App Router) or classic React applications, developers typically install heavy runtime packages (`next-intl`, `react-i18next`) or write custom root middleware regex matching (`middleware.ts`) to intercept routes and rewrite subpaths. In Astro, i18n is declarative at the build configuration level: Astro injects its own optimized internal i18n middleware, automatically computing static routes at compile time.

## 3. Common Mistakes & Anti-Patterns

Developers migrating from Next.js often leave `i18n` empty in `astro.config.mjs` and attempt to build ad-hoc middleware or dynamic catch-all route handlers (`[...lang].astro`) manually. This breaks all `astro:i18n` virtual imports, invalidates `Astro.currentLocale`, and prevents automated sitemap hreflang generation.

### ❌ Bad Practice / Anti-Pattern

```js
// astro.config.mjs - Missing native i18n config
import { defineConfig } from 'astro/config'

export default defineConfig({
  // No i18n block configured.
  // Developer attempts to handle all locale routing manually in custom middleware
})
```

```ts
// src/middleware.ts - Fragile manual path parsing
export function onRequest(context, next) {
  const pathname = context.url.pathname
  if (!pathname.startsWith('/en') && !pathname.startsWith('/es')) {
    return context.redirect(`/en${pathname}`) // Breaks static generation & assets
  }
  return next()
}
```

### ✅ Best Practice / Idiomatic

```js
// astro.config.mjs - Idiomatic native i18n declaration
import { defineConfig } from 'astro/config'

export default defineConfig({
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'es', 'fr'],
    routing: {
      prefixDefaultLocale: false,
    },
  },
})
```

```astro
---
// src/pages/index.astro - Automatically aware of locale context
const currentLocale = Astro.currentLocale; // "en"
---
<html lang={currentLocale}>
  <h1>Current language: {currentLocale}</h1>
</html>
```

## 4. Verification & Audit

Verify that `astro:i18n` is active by running a check or build:

```bash
# Astro will throw error "i18nNotEnabled" if astro:i18n is imported without config
npx astro check
```

In browser DevTools, inspect the generated HTML root tag to verify that `Astro.currentLocale` evaluates correctly for all localized subpaths.
