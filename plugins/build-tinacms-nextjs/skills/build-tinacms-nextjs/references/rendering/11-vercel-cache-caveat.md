# Vercel Cache Caveat

Vercel's data cache stores `fetch()` responses (including TinaCloud GraphQL calls) for up to a year by default. Without explicit `revalidate`, content goes stale and editors see "my edits aren't showing up."

## Symptoms

- Editor saves a change, deploy succeeds, but the deployed site still shows old content
- Content updates appear after long delays (hours to days)
- Vercel's cache hit ratio is suspiciously high

## The fix

Pass an explicit `revalidate` to client queries:

```tsx
const result = await client.queries.page(
  { relativePath: `${slug}.md` },
  { fetchOptions: { next: { revalidate: 60 } } },
)
```

`revalidate: 60` — refresh once every 60 seconds.

## How aggressive should `revalidate` be?

| Value | Use case |
|---|---|
| `0` | Always fresh (every request hits TinaCloud) |
| `60` (1 min) | Fresh content critical, traffic acceptable |
| `300` (5 min) | Default — good freshness, low load |
| `3600` (1 hour) | Slow-changing content |
| Skip / `false` | Cache forever (don't do this for editorial content) |

Most projects: **`revalidate: 60` to `300`**.

## Combining with TinaCloud webhooks

Even better: use TinaCloud webhooks to trigger Vercel rebuilds when content changes. Then your `revalidate` can be longer (an hour, day) since explicit changes trigger immediate rebuilds.

```
Editor saves → TinaCloud webhook → Vercel Deploy Hook → rebuild
```

See `references/deployment/03-deploy-hooks.md`.

## Combining with `"use cache"`

```tsx
async function getPage(slug: string) {
  'use cache'
  cacheLife('hours')

  const result = await client.queries.page(
    { relativePath: `${slug}.md` },
    { fetchOptions: { next: { revalidate: 60 } } },  // Vercel data cache
  )

  return result
}
```

Two cache layers:

1. `"use cache"` — Next.js framework cache (in-memory)
2. `revalidate: 60` — Vercel data cache (persistent)

Both apply. Pick `revalidate` based on the underlying source freshness; pick `cacheLife` based on the framework cache strategy.

## Per-page override

For low-traffic pages where freshness doesn't matter:

```tsx
const result = await client.queries.page(
  { relativePath: `${slug}.md` },
  { fetchOptions: { next: { revalidate: 3600 } } },  // 1 hour
)
```

For high-priority pages (homepage, product launch):

```tsx
const result = await client.queries.page(
  { relativePath: 'home.md' },
  { fetchOptions: { next: { revalidate: 0 } } },  // always fresh
)
```

`revalidate: 0` always hits TinaCloud — use sparingly.

## Verifying the fix

After adding `revalidate: 60`:

1. Edit a page in admin, save
2. Wait ~60 seconds
3. Reload the deployed site — change should appear

If it still doesn't appear:

- Check `next` cache headers in browser dev tools — should show `s-maxage=60` or similar
- Check Vercel build logs — `revalidate` value should appear in cache config
- Verify `client.queries.X(args, options)` syntax — second arg is options object

## Self-hosted projects

Self-hosted backends don't go through TinaCloud, so the issue is different. Vercel still caches your `/api/tina/gql` route. The fix is the same — pass `revalidate` to client queries.

For database direct reads (using `databaseClient` server-side), bypass Vercel cache entirely — direct DB reads aren't fetch calls.

## On-demand revalidation pattern

For sites where `revalidate` adds too much latency, use webhook-driven revalidation:

```tsx
// app/api/revalidate/route.ts
import { revalidatePath } from 'next/cache'
import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  // Verify TinaCloud webhook signature
  // ...

  const { paths } = await req.json()
  for (const path of paths) {
    const slug = path.replace('content/pages/', '').replace('.md', '')
    revalidatePath(`/${slug}`)
  }

  return NextResponse.json({ revalidated: true })
}
```

Wire this URL into TinaCloud's webhook config. Now content changes trigger immediate revalidation; `revalidate` becomes a fallback only.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `revalidate` entirely | Content stale for up to 1 year | Add `revalidate: 60` |
| `next: { revalidate: 60 }` (correct) vs `revalidate: 60` (wrong) | Ignored | Must be inside `fetchOptions: { next: { ... } }` |
| Set `revalidate: 0` everywhere | Every request hits TinaCloud — slow + expensive | Use `60`–`300` for most pages |
| Webhook configured but no `/api/revalidate` route | Webhook fires, nothing happens | Add the route handler |
| Multiple Vercel projects share the same TinaCloud project | Stale-cache issues per-project | Use Team Env Vars + ensure each project has its own webhook |
