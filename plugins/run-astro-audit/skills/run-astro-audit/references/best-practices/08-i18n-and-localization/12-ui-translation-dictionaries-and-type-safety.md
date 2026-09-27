# Create Type-Safe UI Translation Dictionaries with Compile-Time Key Validation

> **Context:** i18n & Localization | **Impact:** Medium | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Marketing websites require translation for recurring UI elements (buttons, navigation headers, search placeholders, footers). Using an un-typed string map risks broken production pages when keys are misspelled or omitted. By constructing a type-safe `ui.ts` dictionary with TypeScript `as const`, your IDE flags missing keys at compile time while the translation helper automatically falls back to default language strings when translations are intentionally omitted.

## 2. How It Differs From Classic React / Next.js

In React/Next.js client applications, UI translations typically load large JSON namespaces asynchronously via `i18next-http-backend` or `next-intl` context providers, adding tens of kilobytes of JavaScript to the critical bundle. In Astro, UI translation dictionary lookups execute entirely during static build rendering, shipping clean HTML with zero runtime translation JavaScript.

## 3. Common Mistakes & Anti-Patterns

Using unvalidated string arguments (`t("nav.homeee")`) without TypeScript indexing causes silent runtime rendering failures (`undefined` text on buttons). Another common trap is shipping giant translation JSON files inside client islands.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/i18n/utils.ts - Loose un-typed string dictionary
const translations: Record<string, any> = {
  en: { navHome: 'Home' },
  es: { navHome: 'Inicio' },
}

export function t(lang: string, key: string) {
  // BUG: No compile-time validation. Typo in key returns undefined in HTML!
  return translations[lang]?.[key]
}
```

### ✅ Best Practice / Idiomatic

```ts
// src/i18n/ui.ts - Strict literal type dictionary
export const languages = {
  en: 'English',
  es: 'Español',
} as const

export const defaultLang = 'en'

export const ui = {
  en: {
    'nav.home': 'Home',
    'nav.about': 'About',
    'btn.contact': 'Get in touch',
  },
  es: {
    'nav.home': 'Inicio',
    'nav.about': 'Acerca de',
    // "btn.contact" omitted deliberately; will fall back to English!
  },
} as const

// src/i18n/utils.ts - Type-safe translator with fallback
export function useTranslations(lang: keyof typeof ui) {
  return function t(key: keyof (typeof ui)[typeof defaultLang]): string {
    return (ui[lang] as Record<string, string>)[key] ?? ui[defaultLang][key]
  }
}
```

```astro
---
// src/components/Header.astro
import { useTranslations } from "../i18n/utils";

const lang = (Astro.currentLocale ?? "en") as keyof typeof ui;
const t = useTranslations(lang);
---
<a href="/">{t("nav.home")}</a>
<button>{t("btn.contact")}</button>
```

## 4. Verification & Audit

Run TypeScript verification across the project:

```bash
npx astro check
```

Verify that calling `t("invalid.key")` produces a red compile-time error (`Argument of type '"invalid.key"' is not assignable to parameter...`).
