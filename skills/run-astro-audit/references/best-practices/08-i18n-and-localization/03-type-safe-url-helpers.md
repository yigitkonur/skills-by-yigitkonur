# Compute Localized Links with getRelativeLocaleUrl Instead of String Concatenation

> **Context:** i18n & Localization | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Hardcoding locale prefixes with string template literals (e.g. `/${lang}/blog/${slug}`) is fragile and breaks whenever site configuration changes. The `getRelativeLocaleUrl()` and `getAbsoluteLocaleUrl()` helpers imported from `astro:i18n` evaluate your project's `defaultLocale`, `routing.prefixDefaultLocale`, `base` path, and `trailingSlash` settings automatically. They guarantee that links to the default language omit prefixes when configured to do so, preventing broken redirects and crawl loops.

## 2. How It Differs From Classic React / Next.js

In Next.js, `<Link href="/about">` often relies on framework-level router context or middleware rewrites to prepend the active locale. In Astro's static-first island architecture, components render at build time without client router runtime context. Using `astro:i18n` URL helpers ensures every HTML `<a>` tag receives its fully resolved, static target URL during compilation.

## 3. Common Mistakes & Anti-Patterns

Developers frequently build manual string templates like `/${currentLocale}/${targetPath}`. When `prefixDefaultLocale` is `false`, this generates `/en/about` instead of `/about`, forcing search engine crawlers through unnecessary 301/302 redirects. Manual concatenation also frequently causes double slashes (`/en//about`) or drops the configured `base` path.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/Navigation.astro - Fragile manual string concatenation
const currentLocale = Astro.currentLocale ?? "en";
const links = [
  { path: "about", title: "About" },
  { path: "blog", title: "Blog" }
];
---
<nav>
  {links.map((link) => (
    <!-- BUG: If currentLocale is default and prefixDefaultLocale is false,
         this outputs "/en/about", which redirects or returns 404! -->
    <a href={`/${currentLocale}/${link.path}/`}>{link.title}</a>
  ))}
</nav>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/Navigation.astro - Resilient helper computation
import { getRelativeLocaleUrl } from "astro:i18n";

const currentLocale = Astro.currentLocale ?? "en";
const links = [
  { path: "about", title: "About" },
  { path: "blog", title: "Blog" }
];
---
<nav>
  {links.map((link) => (
    <!-- Correctly emits "/about" if default locale without prefix,
         or "/es/about" for Spanish, automatically respecting trailingSlash -->
    <a href={getRelativeLocaleUrl(currentLocale, link.path)}>
      {link.title}
    </a>
  ))}
</nav>
```

## 4. Verification & Audit

Audit your templates for raw interpolated paths using grep:

```bash
# Search for raw slash-interpolated locale links
grep -rn 'href={`/${' src/
```

Inspect rendered HTML links in the build output (`dist/`) to confirm default locale URLs have no unwanted prefixes while secondary locales include them cleanly.
