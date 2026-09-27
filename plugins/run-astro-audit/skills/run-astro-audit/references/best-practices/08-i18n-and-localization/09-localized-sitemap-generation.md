# Configure @astrojs/sitemap with i18n Mappings for Automatic Alternate Links

> **Context:** i18n & Localization | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Submitting localized URLs inside XML sitemaps informs search engines of all page translations in a single crawl, without waiting for bots to discover on-page hreflang tags. The official `@astrojs/sitemap` integration provides an `i18n` configuration block that automatically cross-links all translated URLs inside each `<url>` entry using standard `<xhtml:link rel="alternate">` tags.

## 2. How It Differs From Classic React / Next.js

In Next.js, developers often write complex custom API routes (`app/sitemap.ts`) to query database translations, construct XML strings manually, and pair alternate links. In Astro, `@astrojs/sitemap` hooks into the build pipeline, inspects generated static pages, and computes all reciprocal XML alternates automatically.

## 3. Common Mistakes & Anti-Patterns

A common mistake is adding `sitemap()` without the `i18n` property on multilingual sites. This outputs a flat list of isolated URLs without any `<xhtml:link>` cross-references, leaving search engines blind to relationship pairings between localized pages. Another mistake is using language codes not matching standard BCP-47 / ISO-639 tags.

### ❌ Bad Practice / Anti-Pattern

```js
// astro.config.mjs - Unconfigured sitemap missing i18n cross-links
import { defineConfig } from 'astro/config'
import sitemap from '@astrojs/sitemap'

export default defineConfig({
  site: 'https://example.com',
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'es'],
  },
  integrations: [
    sitemap(), // BUG: Outputs flat XML without <xhtml:link> hreflang alternates!
  ],
})
```

### ✅ Best Practice / Idiomatic

```js
// astro.config.mjs - Fully configured multilingual sitemap
import { defineConfig } from 'astro/config'
import sitemap from '@astrojs/sitemap'

export default defineConfig({
  site: 'https://example.com',
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'es', 'fr'],
  },
  integrations: [
    sitemap({
      i18n: {
        defaultLocale: 'en',
        locales: {
          en: 'en-US', // Maps URL prefix to BCP-47 tag in sitemap XML
          es: 'es-ES',
          fr: 'fr-FR',
        },
      },
    }),
  ],
})
```

## 4. Verification & Audit

After building your site, inspect the generated sitemap XML:

```bash
npx astro build && grep -A 5 "xhtml:link" dist/sitemap-0.xml
```

Verify that every `<url>` entry contains `<xhtml:link rel="alternate" hreflang="..." href="..."/>` tags for each configured language.
