# Configure ClientRouter and Control Navigation Interception

> **Context:** Routing & Pages | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

In Astro 5, `<ClientRouter />` (formerly `<ViewTransitions />` in Astro 4) transforms standard multi-page applications into client-side routed apps with smooth SPA-like transitions while maintaining an MPA foundation. It intercepts internal `<a>` clicks, fetches the next page HTML over `fetch()`, swaps document nodes, and updates the URL.

## 2. How It Differs From Classic React / Next.js

Next.js provides a custom `<Link href="...">` component for client routing. Astro uses standard HTML `<a>` tags. The `<ClientRouter />` component in `<head>` automatically listens to all internal link clicks. Navigation can be customized with standard HTML attributes: `data-astro-reload` forces full browser reload, and `data-astro-history="replace"` updates the URL without pushing to browser history.

## 3. Common Mistakes & Anti-Patterns

Importing `<ViewTransitions />` in Astro 5 (deprecated and removed in future releases), or inventing custom wrappers instead of using standard HTML `<a>` tags. Another trap is passing untrusted user input directly to `navigate()` without validation, creating open redirect vulnerabilities.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/layouts/Layout.astro (Astro 5)
// Outdated import from Astro 4
import { ViewTransitions } from "astro:transitions";
---
<head>
  <ViewTransitions /> <!-- Deprecated in v5 -->
</head>

<!-- src/pages/index.astro -->
<!-- Unsanitized client navigation -->
<script>
  import { navigate } from 'astro:transitions/client';
  const target = new URLSearchParams(window.location.search).get('next');
  if (target) navigate(target); // Vulnerable to open redirects!
</script>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/layouts/Layout.astro
import { ClientRouter } from "astro:transitions";
---
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Astro Site</title>
    <!-- Idiomatic Astro 5 Client Router -->
    <ClientRouter fallback="animate" />
  </head>
  <body>
    <nav>
      <!-- Standard internal link: intercepted by ClientRouter -->
      <a href="/about">About</a>
      <!-- Opt-out of client routing on a per-link basis -->
      <a href="/external-app" data-astro-reload>Legacy App</a>
      <!-- Replace history entry instead of pushing -->
      <a href="/step-2" data-astro-history="replace">Continue</a>
    </nav>
    <slot />
  </body>
</html>
```

## 4. Verification & Audit

Open DevTools Network tab. Click internal links and verify that subsequent navigations trigger background HTML document fetches rather than full-page browser refreshes, and check that `data-astro-reload` links trigger a standard browser reload.
