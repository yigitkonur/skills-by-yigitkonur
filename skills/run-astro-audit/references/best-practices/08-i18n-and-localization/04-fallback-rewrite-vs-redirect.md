# Configure Fallback Routing with fallbackType Rewrite for Seamless UX

> **Context:** i18n & Localization | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Multilingual sites rarely have 100% of their content translated on launch day. Without a fallback strategy, requests for untranslated routes return 404 Not Found, alienating users and losing organic traffic. Astro provides a declarative `fallback` dictionary in `astro.config.mjs`. In Astro 4.15+, configuring `routing.fallbackType: "rewrite"` serves fallback content under the requested locale URL with HTTP 200, avoiding jarring browser URL jumps.

## 2. How It Differs From Classic React / Next.js

In Next.js, fallback routing typically requires complex custom middleware code or external headless CMS query logic returning default translations when localized slugs fail. In Astro, the build compiler and server middleware handle fallback routes automatically. If `fallback: { fr: "en" }` is defined, Astro automatically generates or rewrites missing `/fr/` routes using `/en/` content at build time.

## 3. Common Mistakes & Anti-Patterns

Leaving `fallbackType` at its default (`"redirect"`) causes visitors who clicked a French link to be visibly bounced to English (`/en/...`), breaking the visitor's browsing context and confusing language selectors. Alternatively, not configuring fallbacks at all results in broken 404 pages for newly added locales.

### ❌ Bad Practice / Anti-Pattern

```js
// astro.config.mjs - Default redirect fallback
import { defineConfig } from 'astro/config'

export default defineConfig({
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'fr', 'es'],
    fallback: {
      fr: 'en', // By default, missing /fr/page redirects to /en/page!
    },
    // Missing routing.fallbackType defaults to "redirect", causing URL flashing
  },
})
```

### ✅ Best Practice / Idiomatic

```js
// astro.config.mjs - Transparent rewrite fallback
import { defineConfig } from 'astro/config'

export default defineConfig({
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'fr', 'es'],
    fallback: {
      fr: 'en', // Missing French pages borrow English content
      es: 'en',
    },
    routing: {
      fallbackType: 'rewrite', // Serves /fr/page with English content at HTTP 200
    },
  },
})
```

```astro
---
// src/layouts/BaseLayout.astro - Displaying a graceful fallback disclaimer
const isFallback = Astro.currentLocale !== "en" && Astro.url.pathname.includes("/untranslated-slug");
---
{isFallback && (
  <div class="bg-amber-50 text-amber-800 p-2 text-xs text-center">
    This page is not yet available in your language. Showing English version.
  </div>
)}
<slot />
```

## 4. Verification & Audit

Test a missing translation URL in development or staging:

```bash
curl -I http://localhost:4321/fr/untranslated-page/
```

Verify that the server returns `HTTP 200 OK` (rewrite mode) rather than `302 Found` or `404 Not Found`.
