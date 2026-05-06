# Deploy Hooks and Webhooks

Trigger rebuilds and revalidations on content changes.

## Two patterns

| Pattern | When | How |
|---|---|---|
| **Vercel Deploy Hook** | Pure static / ISR fallback | TinaCloud webhook → Vercel rebuild URL |
| **Next.js revalidation route** | ISR / `cacheComponents` | TinaCloud webhook → `/api/revalidate` route |

For most TinaCMS projects, either works. For projects with `cacheComponents`, the revalidation route is more granular.

## Vercel Deploy Hook (Pattern 1)

### Setup

1. Vercel Project Settings → Git → Deploy Hooks → Create Hook
2. Name it (e.g. "TinaCloud content update")
3. Pick a branch (e.g. `main`)
4. Copy the URL

### Wire to TinaCloud

1. TinaCloud Project Settings → Webhooks → Add Webhook
2. Server URL = the Vercel Deploy Hook URL
3. Target branches = `main` (or your prod branch)

### Result

Every content commit on `main` triggers a Vercel deploy. Site rebuilds with fresh content.

### Trade-offs

- ✅ Simple, no code
- ❌ Slow — full rebuild on every save (5-30+ seconds)
- ❌ Doesn't help during the rebuild window

## Next.js revalidation route (Pattern 2)

### Add the route

```typescript
// app/api/revalidate/route.ts
import { revalidatePath, revalidateTag } from 'next/cache'
import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  // Verify signature
  const auth = req.headers.get('authorization')
  if (auth !== `Bearer ${process.env.WEBHOOK_SECRET}`) {
    return new Response('Unauthorized', { status: 401 })
  }

  const body = await req.json()
  // Body: { clientId, branch, paths[], type, eventId }

  for (const path of body.paths ?? []) {
    // Map content path to URL
    // content/pages/home.md → /
    // content/pages/about.md → /about
    // content/posts/launch.md → /blog/launch
    if (path.startsWith('content/pages/')) {
      const slug = path.replace('content/pages/', '').replace(/\.md$/, '')
      revalidatePath(`/${slug === 'home' ? '' : slug}`)
    } else if (path.startsWith('content/posts/')) {
      const slug = path.replace('content/posts/', '').replace(/\.md$/, '')
      revalidatePath(`/blog/${slug}`)
    }
  }

  return NextResponse.json({ ok: true })
}
```

### Wire to TinaCloud

1. TinaCloud Project Settings → Webhooks → Add Webhook
2. Server URL = `https://your-site.com/api/revalidate`
3. Custom headers: `Authorization: Bearer <your-secret>`
4. Target branches = `main`

Add `WEBHOOK_SECRET` to Vercel env vars.

### Result

Content changes invalidate Next.js cache for affected pages. Next request rebuilds those pages from fresh data. No full deploy.

### Trade-offs

- ✅ Fast (only affected pages rebuild)
- ✅ No deployment downtime
- ❌ Requires `cacheComponents` or `revalidate` strategy already configured
- ❌ More code to maintain

## Combining both

For maximum reliability:

1. Wire both
2. Vercel Deploy Hook → gets the latest content into the build
3. Revalidation route → handles the gap between webhook and full rebuild

Most projects don't need this combination. Pick one based on freshness requirements.

## Webhook signature verification

TinaCloud sends webhooks with optional shared-secret headers. Verify:

```typescript
const auth = req.headers.get('authorization')
if (auth !== `Bearer ${process.env.WEBHOOK_SECRET}`) {
  return new Response('Unauthorized', { status: 401 })
}
```

Without verification, anyone can trigger rebuilds (DoS via deploy waste).

## Self-hosted: where do webhooks come from?

Self-hosted projects have no TinaCloud webhook. Trigger rebuilds via:

1. **GitHub webhook → Vercel Deploy Hook** (when a commit lands)
2. **Internal webhook from your backend's mutation handler** (after each save)
3. **No webhook — rely on `revalidate` cache TTL**

Pick based on how immediate freshness needs to be.

## Webhook payload fields

```json
{
  "clientId": "276...",
  "branch": "main",
  "paths": ["content/posts/launch.md"],
  "type": "content.modified",
  "eventId": "472..."
}
```

`type` values: `'content.added'`, `'content.modified'`, `'content.removed'`.

## Webhook logs

TinaCloud Project → Webhooks → Logs:

- Date/time of attempts
- HTTP status from your destination
- Request payload sent
- Response body received

Use to debug failed webhooks.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Missing webhook signature check | Anyone can trigger rebuilds | Add `Bearer` header check |
| Path mapping in revalidate route is wrong | Wrong page invalidated | Verify the mapping logic |
| Deploy hook fires but no env var changed | Useless rebuild | Don't trigger on every change; gate by branch |
| Webhook URL is HTTP not HTTPS | Browsers/some hosts reject | Always HTTPS |
| Hit Vercel deploy quota (Hobby tier limit) | Rebuilds throttled | Upgrade plan |
