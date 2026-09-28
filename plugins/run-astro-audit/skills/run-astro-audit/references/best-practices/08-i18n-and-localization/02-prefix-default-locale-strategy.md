# Align File Structure with prefixDefaultLocale Routing Policy

> **Context:** i18n & Localization | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro strictly enforces symmetry between your physical directory tree under `src/pages/` and the `routing.prefixDefaultLocale` configuration setting. If `prefixDefaultLocale` is set to `true`, all page routes (including the default language) require a prefix (e.g. `/en/about/`). If set to `false`, default language pages must reside at the root of `src/pages/`. Mismatching directory placement causes missing route errors or duplicate route collisions during compilation.

## 2. How It Differs From Classic React / Next.js

In Next.js App Router, routing is usually wrapped inside a single top-level dynamic folder `app/[locale]/layout.tsx`, forcing every single route to have a prefix unless complex rewrite middleware strips it. Astro gives you native declarative control: you choose whether the default locale lives at root (`/about`) or with a prefix (`/en/about`) without any runtime rewrite hacks.

## 3. Common Mistakes & Anti-Patterns

A common mistake is placing default language pages inside `src/pages/en/` while leaving `prefixDefaultLocale: false` (the default). Astro will treat `en` as an ordinary subdirectory, generating `/en/en/` or conflicting route lookups. Another frequent trap is setting `prefixDefaultLocale: true` but forgetting to provide the mandatory `src/pages/index.astro` root redirector.

### ❌ Bad Practice / Anti-Pattern

```js
// astro.config.mjs
export default defineConfig({
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'es'],
    routing: { prefixDefaultLocale: true }, // Prefixed mode enabled
  },
})
// Developer fails to create src/pages/index.astro, causing Astro build error:
// "missing-index-for-internationalization"
```

```
// File tree mismatch when prefixDefaultLocale: false
src/pages/
├── en/           <-- INCORRECT: defaultLocale placed in subfolder
│   ├── index.astro
│   └── about.astro
└── es/
    ├── index.astro
    └── about.astro
```

### ✅ Best Practice / Idiomatic

```
// File tree when prefixDefaultLocale: true
src/pages/
├── index.astro   <-- REQUIRED root redirector (e.g. Astro.redirect('/en/'))
├── en/           <-- Default locale folder
│   ├── index.astro
│   └── about.astro
└── es/           <-- Localized folder
    ├── index.astro
    └── about.astro
```

```astro
---
// src/pages/index.astro - Root landing redirector when prefixDefaultLocale: true
import { getRelativeLocaleUrl } from "astro:i18n";
return Astro.redirect(getRelativeLocaleUrl("en", "/"));
---
```

## 4. Verification & Audit

Run a production build dry run to confirm no missing index or route collision errors occur:

```bash
npx astro build --check
```

Verify route output in console: ensure `/en/` and `/es/` routes are rendered, and `/` cleanly issues a 302/301 redirect or renders your intended root landing.
