# Caching with `"use cache"`

Next.js 16's caching primitive. Wraps fetches with declarative cache profiles and on-demand revalidation.

## Enable in `next.config.ts`

```typescript
const nextConfig: NextConfig = {
  cacheComponents: true,
}
```

Without `cacheComponents: true`, the `"use cache"` directive is ignored.

## Basic usage

```tsx
import { cacheLife } from 'next/cache'
import { client } from '@/tina/__generated__/client'

async function getPage(slug: string) {
  'use cache'
  cacheLife('hours')

  const { data } = await client.queries.page({ relativePath: `${slug}.md` })
  return data
}
```

The `"use cache"` directive marks the function as cacheable. `cacheLife('hours')` picks a profile.

## Preset profiles

| Profile | Stale | Revalidate | Expire |
|---|---|---|---|
| `'seconds'` | 30s | 1s | 1 min |
| `'minutes'` | 5 min | 1 min | 1 hour |
| `'hours'` | 5 min | 1 hour | 1 day |
| `'days'` | 5 min | 1 day | 1 week |
| `'weeks'` | 5 min | 1 week | 30 days |
| `'max'` | 5 min | 30 days | 1 year |

| Term | Meaning |
|---|---|
| **Stale** | Time after which a request triggers SWR refresh (returns cached, refetches in background) |
| **Revalidate** | Cache TTL — after this, value is no longer served (fetch happens) |
| **Expire** | Hard limit — value is purged from cache |

For TinaCMS sites with editorial content, `'hours'` is usually right — fast reads, content refreshes within an hour of saves.

## Custom profile

```typescript
const nextConfig: NextConfig = {
  cacheComponents: true,
  cacheLife: {
    editorial: { stale: 600, revalidate: 3600, expire: 86400 },
  },
}
```

```tsx
async function getPage(slug: string) {
  'use cache'
  cacheLife('editorial')   // your custom profile
  // ...
}
```

Values in seconds.

## Constraints

You **cannot** access `cookies()`, `headers()`, or `searchParams` inside a `"use cache"` scope. The cache is shared across requests, so request-specific data would corrupt it.

```tsx
// ❌ Wrong
async function getPage(slug: string) {
  'use cache'
  const cookieStore = await cookies()  // throws
  // ...
}

// ✅ Right
async function getPage(slug: string) {
  'use cache'
  // ... no cookies/headers
}

// In the calling Server Component:
const cookieStore = await cookies()  // fine here
const data = await getPage(slug)
```

If you need per-request data, read it outside the cached function and pass as arguments.

## Draft mode bypasses cache

Edit-mode (Draft Mode active) automatically skips `"use cache"` scopes — editors see fresh content. No extra wiring.

## On-demand revalidation

```tsx
import { revalidateTag, updateTag } from 'next/cache'

// SWR-style: revalidate on next request
revalidateTag('content', 'hours')   // profile required in Next.js 16+

// Server Actions only: read-your-writes (user sees update immediately)
await updateTag('content')
```

Tag your fetches to enable selective revalidation:

```tsx
async function getPage(slug: string) {
  'use cache'
  cacheLife('hours')
  cacheTag(`page-${slug}`, 'all-pages')

  const { data } = await client.queries.page({ relativePath: `${slug}.md` })
  return data
}
```

Then revalidate by tag:

```tsx
revalidateTag(`page-${slug}`, 'hours')
revalidateTag('all-pages', 'hours')
```

## TinaCloud webhook + revalidation

Wire a TinaCloud webhook to a Next.js API route that revalidates tags:

```tsx
// app/api/revalidate/route.ts
import { revalidateTag } from 'next/cache'
import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  // Verify the webhook is from TinaCloud (signature check)
  // ...

  const body = await req.json()
  // body: { clientId, branch, paths[], type, eventId }

  for (const path of body.paths ?? []) {
    revalidateTag(`page-${path}`, 'hours')
  }
  revalidateTag('all-pages', 'hours')

  return NextResponse.json({ ok: true })
}
```

See `references/tinacloud/07-webhooks.md`.

## Vercel cache vs `"use cache"`

Distinct layers:

- **Vercel data cache** caches `fetch()` calls automatically (for up to 1 year by default — see `references/rendering/11-vercel-cache-caveat.md`)
- **`"use cache"`** is Next.js's framework-level cache (in-memory + persistent)

Both apply. For TinaCMS, you usually want **both**:

1. `"use cache"` to skip GraphQL parsing on every request
2. `fetchOptions: { next: { revalidate: 60 } }` on the underlying client query to control Vercel's data cache

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `cacheComponents: true` in next.config | `"use cache"` ignored | Enable in config |
| `cacheLife()` not called inside cached function | Default profile applied | Call `cacheLife()` |
| Tried to read cookies inside `"use cache"` | Runtime error | Read outside, pass as args |
| Forgot `'hours'` second arg to `revalidateTag` in Next.js 16+ | Type error | Pass profile as second arg |
| Used `revalidateTag` from a Client Component | Doesn't propagate | Move to Server Action or route handler |
