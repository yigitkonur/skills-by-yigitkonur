# Centralize Content Ingestion in the Astro 5 Content Layer Over Ad-Hoc Fetches

> **Context:** Architecture & Philosophy | **Impact:** High | **Target:** Astro 5

## 1. Why We Do This

The Astro 5 Content Layer (`src/content.config.ts`) unifies all local and remote data sources into a single, type-safe, build-time cache store. Using pluggable loaders (e.g., `glob`, API loaders) isolates data synchronization from page rendering, accelerates builds up to 5x through incremental caching, and guarantees consistent schema validation via Zod.

## 2. How It Differs From Classic React / Next.js

In Next.js App Router, developers often scatter `fetch()` calls with intricate `revalidate` tags and unstable cache directives across individual server components. In Astro 5, content ingestion is cleanly separated from page templates into a centralized content data store queried via `getCollection()` and `getEntry()`.

## 3. Common Mistakes & Anti-Patterns

Scattering ad-hoc API fetches to headless CMSs or external REST endpoints inside multiple page frontmatter scripts causes redundant network requests during builds and leaves data unvalidated.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/news/[id].astro
// Anti-pattern: Ad-hoc remote fetching in page frontmatter without caching or schema safety
const { id } = Astro.params;
// Fetched on every page build; slow, redundant, and error-prone if API is flaky
const res = await fetch(`https://api.cms.internal/articles/${id}`);
if (!res.ok) throw new Error("Failed to load article");
const article = await res.json();
---
<article>
  <h1>{article.title}</h1>
  <div>{article.body}</div>
</article>
```

### ✅ Best Practice / Idiomatic

```typescript
// src/content.config.ts
// Idiomatic (Astro 5): Centralized content store with loader and schema validation
import { defineCollection, z } from 'astro:content'

const news = defineCollection({
  loader: async () => {
    const res = await fetch('https://api.cms.internal/articles')
    const data = await res.json()
    return data.map((item: any) => ({ id: item.slug, ...item }))
  },
  schema: z.object({
    title: z.string(),
    body: z.string(),
    publishedDate: z.coerce.date(),
  }),
})

export const collections = { news }
```

```astro
---
// src/pages/news/[slug].astro
import { getEntry } from 'astro:content';
const article = await getEntry('news', Astro.params.slug);
if (!article) return Astro.redirect('/404');
---
<article>
  <h1>{article.data.title}</h1>
  <div>{article.data.body}</div>
</article>
```

## 4. Verification & Audit

Audit content collection cache synchronization:

```bash
npx astro sync
# Validates all content schemas and writes type definitions to .astro/types.d.ts
npx astro check
# Confirms type safety across all getCollection and getEntry calls
```
