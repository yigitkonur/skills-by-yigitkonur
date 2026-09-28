# Leverage Server-Side Browser Language Detection via Astro.preferredLocale

> **Context:** i18n & Localization | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Detecting a visitor's language on the server during the initial HTTP handshake eliminates Flash of Wrong Language (FOWL), content layout shifts (CLS), and SEO crawling errors. Astro automatically parses the incoming `Accept-Language` header against your configured `locales` and exposes `Astro.preferredLocale` and `Astro.preferredLocaleList` in SSR mode.

## 2. How It Differs From Classic React / Next.js

In single-page React apps, language detection typically runs in `useEffect()` or client-side storage checks (`localStorage.getItem('lang')`), downloading the wrong language bundle before flashing over to the translated bundle. Astro performs language negotiation server-side or at the edge before sending the first byte of HTML.

## 3. Common Mistakes & Anti-Patterns

A common mistake is injecting client-side inline scripts that read `navigator.language` and execute `window.location.replace()`. This breaks search engine indexing (bots may get stuck in redirection loops) and triggers layout shift penalties in Core Web Vitals.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/layouts/BaseLayout.astro - Flash of wrong language via client script
---
<html>
  <head>
    <script is:inline>
      // ANTI-PATTERN: Client-side redirect causes flicker and breaks SEO crawlers
      const userLang = navigator.language.slice(0, 2);
      if (userLang === 'es' && !window.location.pathname.startsWith('/es')) {
        window.location.replace('/es' + window.location.pathname);
      }
    </script>
  </head>
  <body><slot /></body>
</html>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/index.astro (SSR mode) - Clean server-side redirect
import { getRelativeLocaleUrl } from "astro:i18n";

// In SSR mode, Astro inspects Accept-Language against configured locales
const preferred = Astro.preferredLocale;
const targetLocale = preferred ?? "en";

if (targetLocale !== "en") {
  return Astro.redirect(getRelativeLocaleUrl(targetLocale, "/"), 302);
}
---
<html lang="en">
  <!-- Default language content rendered if preferred matches default -->
  <body>
    <h1>Welcome to our site</h1>
  </body>
</html>
```

## 4. Verification & Audit

Simulate different browser language preferences using curl:

```bash
# Test Spanish Accept-Language header negotiation
curl -I -H "Accept-Language: es-ES,es;q=0.9" http://localhost:4321/
```

Verify that the server response headers issue an immediate `302 Found` with `Location: /es/` without any client-side JavaScript execution.
