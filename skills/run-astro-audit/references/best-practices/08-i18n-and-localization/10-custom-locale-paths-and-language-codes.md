# Map Multiple BCP-47 Language Codes to Unified URL Paths

> **Context:** i18n & Localization | **Impact:** Medium | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

International audiences frequently share a common language with regional variations (e.g. Canadian French `fr-CA`, Belgian French `fr-BE`, and France `fr`). Creating separate directories for each regional dialect leads to duplicate content penalties and maintenance nightmares. Astro allows mapping multiple browser-recognized BCP-47 `codes` to a single consolidated URL `path` in `astro.config.mjs`.

## 2. How It Differs From Classic React / Next.js

In Next.js, mapping multiple locale codes to one slug requires custom rewrite rules in `middleware.ts` or edge functions. Astro provides first-class support for path-to-code mapping in its core configuration, with helpers `getPathByLocale()` and `getLocaleByPath()` exported directly from `astro:i18n`.

## 3. Common Mistakes & Anti-Patterns

A common mistake is creating separate folders for every regional dialect (`src/pages/fr/`, `src/pages/fr-CA/`, `src/pages/fr-BE/`) with identical copies of pages. Another trap is passing codes that do not match browser `Accept-Language` headers, breaking language negotiation.

### ❌ Bad Practice / Anti-Pattern

```
// Bloated, redundant directory structure
src/pages/
├── fr/
│   └── index.astro
├── fr-be/
│   └── index.astro   <-- Duplicate content!
└── fr-ca/
    └── index.astro   <-- Duplicate content!
```

### ✅ Best Practice / Idiomatic

```js
// astro.config.mjs - Consolidated locale path mapping
import { defineConfig } from 'astro/config'

export default defineConfig({
  i18n: {
    defaultLocale: 'en',
    locales: [
      'en',
      'es',
      {
        path: 'french', // Folder name under src/pages/french/
        codes: ['fr', 'fr-CA', 'fr-BE', 'fr-CH'], // Browser Accept-Language codes
      },
    ],
  },
})
```

```astro
---
// src/pages/index.astro - Programmatically resolving path and codes
import { getPathByLocale, getLocaleByPath, getRelativeLocaleUrl } from "astro:i18n";

const frenchPath = getPathByLocale("fr-CA"); // Returns "french"
const defaultCode = getLocaleByPath("french"); // Returns "fr" (first code in array)
const frenchUrl = getRelativeLocaleUrl("french", "about"); // Returns "/french/about"
---
<a href={frenchUrl}>Français</a>
```

## 4. Verification & Audit

Simulate a request with a regional dialect header:

```bash
curl -I -H "Accept-Language: fr-CA,fr;q=0.9" http://localhost:4321/
```

Verify that the browser is accurately routed to `/french/` without creating duplicate `/fr-CA/` routes.
