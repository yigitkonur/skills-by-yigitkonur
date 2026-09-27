# Cache API Sync State and ETag Headers with MetaStore

> **Context:** Content Layer & Collections | **Impact:** High | **Target:** Astro 5

## 1. Why We Do This

When fetching content from remote headless CMSs or third-party APIs during CI/CD builds, making full re-fetches for unchanged data slows down builds and risks triggering API rate limits. Astro 5 equips custom loaders with `meta` (`LoaderContext.meta`), a persistent key-value store preserved between builds. By storing sync tokens, last-modified timestamps, or HTTP ETags in `meta`, a loader can issue conditional HTTP requests (`If-Modified-Since` / `If-None-Match`). If the upstream source returns `304 Not Modified`, the loader terminates early and reuses the existing datastore entries.

## 2. How It Differs From Classic React / Next.js

Next.js offers time-based ISR (`revalidate: 60`) or on-demand tag revalidation, but lacks a built-in persistent metadata store for loaders to negotiate delta syncs during static builds. In CI, Next.js rebuilds start with a clean slate, repeatedly downloading identical data payloads. Astro's `meta` store persists alongside `.astro/`, giving custom loaders durable memory across runs.

## 3. Common Mistakes & Anti-Patterns

Failing to persist sync headers forces the loader to download and parse the entire remote dataset on every build, even when zero articles were updated.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/loaders/statelessLoader.ts (No persistence)
export function statelessLoader(url: string) {
  return {
    name: 'stateless-loader',
    load: async ({ store }) => {
      // ❌ Always downloads full payload on every build; hits API limits
      const res = await fetch(url)
      const data = await res.json()
      store.clear()
      // ...inserts all data again
    },
  }
}
```

### ✅ Best Practice / Idiomatic

```ts
// src/loaders/conditionalFeedLoader.ts (Using MetaStore)
import type { Loader } from 'astro/loaders'

export function conditionalFeedLoader(url: string): Loader {
  return {
    name: 'conditional-feed-loader',
    load: async ({ store, meta, logger }) => {
      const lastModified = meta.get('last-modified')
      const headers = lastModified ? { 'If-Modified-Since': lastModified } : {}

      const res = await fetch(url, { headers })

      // ✅ Remote source unchanged; skip update and retain cached store
      if (res.status === 304) {
        logger.info('Remote content unchanged (HTTP 304); using cached entries.')
        return
      }

      if (!res.ok) throw new Error(`Feed fetch failed: ${res.status}`)

      const newLastModified = res.headers.get('last-modified')
      if (newLastModified) {
        // ✅ Persist new timestamp for subsequent builds
        meta.set('last-modified', newLastModified)
      }

      const items = await res.json()
      store.clear()
      // ...validate and populate store
    },
  }
}
```

## 4. Verification & Audit

Verify conditional caching by running subsequent builds:

```bash
pnpm astro build && pnpm astro build
```

Check build logs to confirm that the second build logs `Remote content unchanged (HTTP 304)` and completes without network payload downloads.
