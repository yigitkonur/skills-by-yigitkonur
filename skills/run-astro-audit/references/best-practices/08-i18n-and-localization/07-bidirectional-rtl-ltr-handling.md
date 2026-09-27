# Enforce Bidirectional (RTL/LTR) HTML Attributes and Logical CSS Properties

> **Context:** i18n & Localization | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Languages like localized secondary locale, Hebrew, and Persian render from right to left (RTL). Setting `dir="rtl"` on the root `<html>` element signals browser layout engines, accessibility APIs, and screen readers to mirror reading order, scrolling flow, and punctuation. Combining dynamic `dir` attributes with CSS logical properties ensures layouts automatically adapt without duplicate mirrored stylesheets.

## 2. How It Differs From Classic React / Next.js

In React SPAs, RTL toggling often requires client-side CSS-in-JS theme providers or plugins (`stylis-plugin-rtl`) that flip styles at runtime. In Astro, the `dir` and `lang` attributes are compiled directly into static HTML during SSR or build time, guaranteeing zero-flash, instantly correct bidirectional rendering before CSS paints.

## 3. Common Mistakes & Anti-Patterns

Using physical coordinates (`margin-left`, `padding-right`, `left-4`, `text-left`) breaks layout symmetry when switching to an RTL locale. Another mistake is hardcoding `dir="ltr"` in the root layout, rendering RTL text misaligned and causing punctuation to detach to the wrong side of sentences.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/layouts/BaseLayout.astro - Hardcoded physical layout
const locale = Astro.currentLocale ?? "en";
---
<!-- BUG: Hardcoded ltr breaks localized secondary locale and Hebrew layouts -->
<html lang={locale} dir="ltr">
  <body class="text-left">
    <!-- BUG: ml-6 and pl-4 push elements to the wrong side in RTL -->
    <div class="ml-6 pl-4 border-l-2">
      <slot />
    </div>
  </body>
</html>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/layouts/BaseLayout.astro - Dynamic bidirectional layout
const locale = Astro.currentLocale ?? "en";
const RTL_LOCALES = new Set(["ar", "he", "fa", "ur"]);
const dir = RTL_LOCALES.has(locale) ? "rtl" : "ltr";
---
<html lang={locale} dir={dir}>
  <head>
    <meta charset="utf-8" />
  </head>
  <body class="text-start">
    <!-- Uses CSS logical properties: ms (margin-inline-start), ps (padding-inline-start), border-s -->
    <div class="ms-6 ps-4 border-s-2">
      <slot />
      <!-- Reverses navigational icon orientation only in RTL -->
      <span class="inline-block rtl:rotate-180">→</span>
    </div>
  </body>
</html>
```

## 4. Verification & Audit

Audit your templates for hardcoded physical CSS coordinates:

```bash
grep -rnE '(text-left|text-right|ml-|mr-|pl-|pr-|left-|right-)' src/components/
```

In browser DevTools, switch the URL to an RTL locale (e.g. `/ar/`) and inspect `document.documentElement.dir`. Verify that all inline padding, margins, borders, and chevrons mirror appropriately.
