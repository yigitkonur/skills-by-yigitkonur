# Fetch Options and `revalidate`

Pass Next.js fetch options to TinaCMS client queries. Controls Vercel data cache, request tags, and request mode.

## Basic

```tsx
const result = await client.queries.page(
  { relativePath: 'home.md' },
  { fetchOptions: { next: { revalidate: 60 } } },
)
```

The second argument is a fetch options object. Inside, `next` holds Next.js-specific options.

## Options

| Option | Purpose | Common values |
|---|---|---|
| `next.revalidate` | Cache TTL (seconds) | `0` (always fresh), `60` (1 min), `300` (5 min), `3600` (1 hr) |
| `next.tags` | Tag the cached entry for selective revalidation | `['page-home', 'all-pages']` |
| `cache` | Cache mode | `'no-store'`, `'force-cache'` |

## Why this matters

Vercel's data cache stores responses for up to a year by default. Without explicit `revalidate`, edits don't propagate to deployed sites.

See `references/rendering/11-vercel-cache-caveat.md` for the full cache caveat discussion.

## Recommended defaults

```tsx
// Most pages — 60-second freshness:
{ fetchOptions: { next: { revalidate: 60 } } }

// Critical pages (homepage, launch page) — always fresh:
{ fetchOptions: { next: { revalidate: 0 } } }

// Slow-changing pages (about, terms) — longer cache:
{ fetchOptions: { next: { revalidate: 3600 } } }

// Combined with tags for on-demand revalidation:
{ fetchOptions: { next: { revalidate: 3600, tags: ['page-home'] } } }
```

## Tags + on-demand revalidation

```tsx
// Fetch:
const result = await client.queries.page(
  { relativePath: 'home.md' },
  { fetchOptions: { next: { revalidate: 3600, tags: ['page-home', 'all-pages'] } } },
)

// Revalidate elsewhere (Server Action or webhook handler):
import { revalidateTag } from 'next/cache'
revalidateTag('page-home', 'hours')  // refresh next request
```

Pair with a TinaCloud webhook → Next.js route → `revalidateTag(...)` to invalidate immediately on content changes.

## `cache: 'no-store'` for always-fresh

```tsx
const result = await client.queries.page(
  { relativePath: 'home.md' },
  { fetchOptions: { cache: 'no-store' } },
)
```

Equivalent to `revalidate: 0`. Use sparingly — every request hits TinaCloud (slow + counts toward your TinaCloud quota).

## Per-page strategy

Different content has different freshness needs:

| Content | Strategy |
|---|---|
| Marketing landing page | `revalidate: 300` (5 min) |
| Product page | `revalidate: 60` (1 min) — pricing/features change |
| Blog post | `revalidate: 3600` (1 hr) — slow-changing |
| Homepage | `revalidate: 60` |
| About / Terms / Legal | `revalidate: 86400` (1 day) |
| Editorial draft | Always handled via Draft Mode (bypasses cache) |

## Combining with `"use cache"`

```tsx
async function getPage(slug: string) {
  'use cache'
  cacheLife('hours')

  const result = await client.queries.page(
    { relativePath: `${slug}.md` },
    { fetchOptions: { next: { revalidate: 60 } } },
  )

  return result
}
```

Two cache layers:

- `"use cache"` + `cacheLife('hours')` — Next.js framework cache
- `next: { revalidate: 60 }` — Vercel data cache

See `references/rendering/10-caching-use-cache.md`.

## Self-hosted: revalidate still applies

For self-hosted TinaCMS, requests go through `/api/tina/gql` (a regular Next.js route) → Vercel still caches. The same `fetchOptions` apply.

For direct DB access via `databaseClient`, no fetch happens — caching is whatever your DB layer does.

## Verifying

After deploy, inspect response headers:

```bash
curl -I https://your-site.com/some-page
# Look for: cache-control: s-maxage=60, stale-while-revalidate
# (or your revalidate value)
```

If `cache-control: max-age=31536000` (1 year), `revalidate` isn't applied. Check the fetch call and rebuild.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `revalidate` entirely | Up to 1 year stale | Add `next: { revalidate: 60 }` |
| Wrong nesting: `{ revalidate: 60 }` (no `next`) | Ignored | Must be `{ fetchOptions: { next: { revalidate: 60 } } }` |
| `cache: 'no-store'` everywhere | Slow + quota burn | Reserve for truly critical pages |
| Missing `tags` on tagged-fetch + tag-revalidate setup | revalidateTag does nothing | Tag the fetch first |
| `revalidateTag` from Client Component | No effect | Move to Server Action or route handler |
