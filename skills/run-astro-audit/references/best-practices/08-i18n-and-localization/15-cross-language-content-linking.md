# Cross-Link Localized Content Entries Using Shared Canonical Keys

> **Context:** i18n & Localization | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

A major source of user frustration on international websites is switching languages while reading an article and being dumped back onto the localized homepage. A professional language switcher must preserve reading context: switching from an English article (`/en/blog/web-performance/`) should navigate directly to its Spanish counterpart (`/es/blog/rendimiento-web/`), or fall back to the section index if untranslated.

## 2. How It Differs From Classic React / Next.js

In Next.js, content relationships typically require GraphQL queries or relational database joins via Prisma or Supabase at runtime. In Astro, content relationships can be resolved at build time using Content Layer collection queries, embedding reciprocal target URLs directly into static HTML without runtime database lookups.

## 3. Common Mistakes & Anti-Patterns

The most common anti-pattern is blindly swapping the language prefix in the current pathname (`path.replace('/en/', '/es/')`). When localized articles have different translated URL slugs (e.g. `web-performance` vs `rendimiento-web`), string replacement produces a broken 404 URL.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/LanguagePicker.astro - Naive prefix replacement
const currentPath = Astro.url.pathname;
const targetLangs = ["en", "es", "fr"];
---
<ul>
  {targetLangs.map((lang) => (
    <!-- BUG: Replaces prefix but leaves original English slug intact,
         causing 404 when Spanish slug is translated differently! -->
    <li><a href={currentPath.replace(/^\/[a-z]{2}/, `/${lang}`)}>{lang}</a></li>
  ))}
</ul>
```

### ✅ Best Practice / Idiomatic

```ts
// src/content.config.ts - Schema with cross-language translation key
import { defineCollection } from 'astro:content'
import { z } from 'astro/zod'

export const collections = {
  blog: defineCollection({
    schema: z.object({
      title: z.string(),
      translationKey: z.string(), // Shared across language versions of the same post
    }),
  }),
}
```

```astro
---
// src/components/ArticleLanguagePicker.astro - Context-preserving switcher
import { getCollection } from "astro:content";
import { getRelativeLocaleUrl } from "astro:i18n";

interface Props {
  translationKey: string;
  currentLang: string;
}

const { translationKey, currentLang } = Astro.props;
const allPosts = await getCollection("blog");

// Find all translations sharing the exact same translationKey
const translations = allPosts.filter(
  (p) => p.data.translationKey === translationKey
);

const supportedLocales = ["en", "es", "fr"] as const;
---
<ul class="flex gap-4">
  {supportedLocales.map((locale) => {
    const match = translations.find((p) => p.id.startsWith(`${locale}/`));
    const slug = match ? match.id.split("/")[1]?.replace(/\.[^/.]+$/, "") : "blog";
    const href = getRelativeLocaleUrl(locale, match ? `blog/${slug}` : "blog");

    return (
      <li>
        <a href={href} class={locale === currentLang ? "font-bold" : "underline"}>
          {locale.toUpperCase()}
        </a>
      </li>
    );
  })}
</ul>
```

## 4. Verification & Audit

In your browser or test suite:

1. Navigate to a translated blog post (e.g. `/en/blog/first-post/`).
2. Click the Spanish language option in the switcher.
3. Confirm the browser navigates directly to `/es/blog/primer-post/` rather than returning a 404 or redirecting to `/es/`.
