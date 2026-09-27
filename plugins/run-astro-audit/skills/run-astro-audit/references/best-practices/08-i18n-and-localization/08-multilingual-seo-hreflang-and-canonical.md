# Generate Complete Self-Referencing Hreflang and x-default Alternate Meta Tags

> **Context:** i18n & Localization | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Search engines like Google use `hreflang` tags to serve the correct regional language variant in search results and prevent duplicate content penalties across translations. Search engine specifications mandate that: (1) every localized variant must be linked with a fully qualified absolute URL; (2) hreflang tags must be fully reciprocal (if page A links to page B, page B must link back to page A); (3) each page must include a self-referencing hreflang tag; (4) an `x-default` tag must designate the language-neutral fallback.

## 2. How It Differs From Classic React / Next.js

In Next.js, metadata is often configured via dynamic `generateMetadata()` exports or third-party packages like `next-seo`. In Astro, hreflang tags are generated statically in your root layout header using `getAbsoluteLocaleUrl()` from `astro:i18n`, ensuring zero client runtime overhead and guaranteed compile-time link resolution.

## 3. Common Mistakes & Anti-Patterns

Using relative paths (e.g. `href="/es/about"`) in hreflang or canonical tags violates Google's search specifications and causes Google Search Console to drop the tags entirely. Another critical trap is omitting `x-default` or failing to provide reciprocal links on secondary language pages.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/layouts/SeoHead.astro - Invalid relative and missing x-default tags
const { pathname } = Astro.url;
---
<head>
  <!-- BUG: Canonical and hreflang MUST be absolute URLs, not relative paths! -->
  <link rel="canonical" href={pathname} />
  <link rel="alternate" hreflang="en" href={pathname} />
  <link rel="alternate" hreflang="es" href={`/es${pathname}`} />
  <!-- BUG: Missing hreflang="x-default" tag! -->
</head>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/layouts/SeoHead.astro - Fully compliant, reciprocal absolute hreflang
import { getAbsoluteLocaleUrl } from "astro:i18n";

interface Props {
  subpath?: string;
}

const { subpath = "" } = Astro.props;
const supportedLocales = ["en", "es", "fr"] as const;
const defaultLocale = "en";

// Current page canonical URL
const canonicalURL = new URL(Astro.url.pathname, Astro.site);
---
<head>
  <link rel="canonical" href={canonicalURL.href} />

  <!-- Reciprocal language alternates -->
  {supportedLocales.map((locale) => (
    <link
      rel="alternate"
      hreflang={locale}
      href={getAbsoluteLocaleUrl(locale, subpath)}
    />
  ))}

  <!-- Language-neutral fallback for unmatched user locales -->
  <link
    rel="alternate"
    hreflang="x-default"
    href={getAbsoluteLocaleUrl(defaultLocale, subpath)}
  />
</head>
```

## 4. Verification & Audit

Audit your page head using curl or DevTools:

```bash
curl -s http://localhost:4321/es/about/ | grep -E 'rel="(canonical|alternate)"'
```

Verify that every `href` starts with your full domain (e.g. `https://example.com/`), every supported language is listed, and an `x-default` alternate link exists.
