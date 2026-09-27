# Configure i18n.domains for Multi-TLD Deployments in Server Mode

> **Context:** i18n & Localization | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Global brands often serve content from dedicated top-level domains (ccTLDs) or subdomains (e.g. `example.es`, `fr.example.com`, `example.com`). Rather than deploying separate repositories or distinct site builds for each domain, Astro 4.9+ introduces `i18n.domains`. This allows a single Astro SSR codebase to handle all incoming domains, routing requests based on host headers while automatically adjusting `getAbsoluteLocaleUrl()` links.

## 2. How It Differs From Classic React / Next.js

Next.js supports multi-domain i18n in its legacy pages router, but required complex edge rewrite middleware in the App Router. Astro provides native declarative domain mapping in `astro.config.mjs`, binding domain hostnames directly to locales while automatically generating cross-domain canonical and alternate URLs.

## 3. Common Mistakes & Anti-Patterns

Enabling `i18n.domains` on static (prerendered) sites triggers the `NoPrerenderedRoutesWithDomains` compiler error: static sites cannot dynamically negotiate domain headers. Another mistake is forgetting to pass reverse proxy headers (`Host` and `X-Forwarded-Host`) from Nginx/Cloudflare to the Node/SSR adapter.

### ❌ Bad Practice / Anti-Pattern

```js
// astro.config.mjs - Broken multi-domain configuration
import { defineConfig } from 'astro/config'

export default defineConfig({
  output: 'static', // BUG: Prerendered static sites cannot use i18n.domains!
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'es'],
    domains: {
      es: 'https://example.es',
    },
  },
})
```

### ✅ Best Practice / Idiomatic

```js
// astro.config.mjs - Compliant multi-domain SSR configuration
import { defineConfig } from 'astro/config'
import node from '@astrojs/node'

export default defineConfig({
  site: 'https://example.com',
  output: 'server', // Mandatory for multi-domain routing
  adapter: node({ mode: 'standalone' }),
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'es', 'fr'],
    routing: {
      prefixDefaultLocale: false,
    },
    domains: {
      es: 'https://example.es',
      fr: 'https://fr.example.com',
    },
  },
})
```

```astro
---
// src/pages/index.astro
import { getAbsoluteLocaleUrl } from "astro:i18n";

// Emits "https://example.es/about"
const spanishAbout = getAbsoluteLocaleUrl("es", "about");
// Emits "https://fr.example.com/about"
const frenchAbout = getAbsoluteLocaleUrl("fr", "about");
---
<a href={spanishAbout}>Sitio en Español</a>
<a href={frenchAbout}>Site Français</a>
```

## 4. Verification & Audit

Simulate different domain requests locally using curl with Host headers:

```bash
curl -I -H "Host: example.es" http://localhost:4321/about/
```

Verify that `Astro.currentLocale` evaluates to `es` and absolute links point to `https://example.es/`.
