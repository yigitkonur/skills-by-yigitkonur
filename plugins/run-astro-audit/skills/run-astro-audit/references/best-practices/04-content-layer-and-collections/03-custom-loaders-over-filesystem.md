# Implement Custom Loaders Using DataStore, parseData, and generateDigest

> **Context:** Content Layer & Collections | **Impact:** Critical | **Target:** Astro 5

## 1. Why We Do This

Astro 5 allows loading content from external headless CMSs, REST APIs, or databases using custom loaders. Rather than fetching data ad-hoc across various components, a custom loader normalizes and loads data directly into Astro's reactive DataStore. By passing fetched records through `parseData()` for schema validation and computing a `digest` via `generateDigest()`, the DataStore can skip updates for unchanged entries, drastically reducing build times and eliminating unnecessary downstream page rerenders.

## 2. How It Differs From Classic React / Next.js

In Next.js, fetching remote content typically occurs inside individual React Server Components or `generateStaticParams()` using `fetch()`. If ten pages need the same CMS dataset, developers must rely on React's request memoization or Next.js `unstable_cache`. In Astro 5, a loader executes once during the Content Layer sync phase, validating and storing entries in the local datastore before any page template executes.

## 3. Common Mistakes & Anti-Patterns

Bypassing `parseData()` inserts unvalidated data into the store, allowing malformed remote records to crash page rendering. Omitting `digest` causes `store.set()` to treat every entry as dirty on every build, defeating incremental caching.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/loaders/naiveCmsLoader.ts (Uncached and unvalidated)
export function naiveCmsLoader() {
  return {
    name: 'naive-cms-loader',
    load: async ({ store }) => {
      const res = await fetch('https://api.example.com/posts')
      const posts = await res.json()
      store.clear()
      for (const post of posts) {
        // ❌ Stored without parseData validation or content digest hashing
        store.set({ id: post.slug, data: post })
      }
    },
  }
}
```

### ✅ Best Practice / Idiomatic

```ts
// src/loaders/strapiLoader.ts (Idiomatic Astro 5 custom loader)
import type { Loader } from 'astro/loaders'

export function strapiLoader({ endpoint }: { endpoint: string }): Loader {
  return {
    name: 'strapi-loader',
    load: async ({ store, logger, parseData, generateDigest }) => {
      logger.info(`Fetching entries from ${endpoint}`)
      const res = await fetch(endpoint)
      if (!res.ok) throw new Error(`CMS fetch failed: ${res.statusText}`)

      const { data: posts } = await res.json()

      for (const item of posts) {
        const id = String(item.id)
        // ✅ Validate data against the collection schema
        const data = await parseData({ id, data: item.attributes })
        // ✅ Generate content digest for incremental cache invalidation
        const digest = generateDigest(data)

        store.set({
          id,
          data,
          digest,
          rendered: { html: item.attributes.contentHtml ?? '' },
        })
      }
    },
  }
}
```

## 4. Verification & Audit

Run `pnpm astro sync` and inspect CLI logs:

```bash
pnpm astro sync
```

Verify that the loader logs output via `logger.info()` and that secondary runs complete almost instantaneously due to digest cache hits.
