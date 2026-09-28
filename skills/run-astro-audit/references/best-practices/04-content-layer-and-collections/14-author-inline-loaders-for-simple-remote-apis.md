# Fetch Simple Remote Feeds with Async Inline Loaders

> **Context:** Content Layer & Collections | **Impact:** Medium | **Target:** Astro 5

## 1. Why We Do This

Not every remote content integration requires the full complexity of an object loader with custom parsers and incremental ETag caching. When ingesting simple REST APIs, GitHub releases, or public data feeds, Astro 5 supports inline loaders: an async function assigned directly to `loader`. Astro automatically executes the loader during the sync phase, enforces schema validation, and populates the collection, making the data instantly queryable via `getCollection()`.

## 2. How It Differs From Classic React / Next.js

In Next.js, developers often write top-level `fetch()` calls inside layout files or page components, requiring React `cache()` or Next.js fetch cache configuration to avoid duplicate requests. In Astro 5, an inline loader separates data ingestion from presentation. Data is fetched once at build time, validated against a Zod schema, and stored in the collection datastore.

## 3. Common Mistakes & Anti-Patterns

Returning an array of records without an `id` property causes the inline loader to fail with a validation error. Another mistake is performing ad-hoc `fetch()` calls inside `.astro` component frontmatters across multiple pages, multiplying network overhead.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/changelog.astro (Ad-hoc component fetching)
// ❌ Re-fetches remote API every time this page is evaluated
const res = await fetch('https://api.github.com/repos/example/repo/releases');
const releases = await res.json();
---
<ul>
  {releases.map((rel: any) => <li>{rel.name}</li>)}
</ul>
```

### ✅ Best Practice / Idiomatic

```ts
// src/content.config.ts (Declarative async inline loader)
import { defineCollection, z } from 'astro:content'

const releases = defineCollection({
  // ✅ Async inline function returning an array of entries with unique IDs
  loader: async () => {
    const res = await fetch('https://api.github.com/repos/example/repo/releases')
    if (!res.ok) throw new Error(`Failed to fetch releases: ${res.statusText}`)
    const data = await res.json()

    return data.map((rel: any) => ({
      id: String(rel.id),
      name: rel.name ?? rel.tag_name,
      publishedAt: rel.published_at,
      body: rel.body ?? '',
      htmlUrl: rel.html_url,
    }))
  },
  schema: z.object({
    id: z.string(),
    name: z.string(),
    publishedAt: z.coerce.date(),
    body: z.string(),
    htmlUrl: z.string().url(),
  }),
})

export const collections = { releases }
```

## 4. Verification & Audit

Run `pnpm astro sync` to verify that the inline loader retrieves data and passes schema validation:

```bash
pnpm astro sync
```

Check that the collection is queryable with `await getCollection('releases')` with complete TypeScript autocompletion.
