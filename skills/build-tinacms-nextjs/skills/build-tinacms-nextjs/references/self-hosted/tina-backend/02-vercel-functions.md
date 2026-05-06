# Vercel Functions Deployment

Deploying the self-hosted TinaCMS backend on Vercel Functions. The default and recommended path.

## Why Vercel Functions

- Native Node.js runtime
- Auto-scaling
- Easy env var management
- Same domain as your Next.js app (no CORS)
- Free tier covers small projects

## Default behavior

The `app/api/tina/[...routes]/route.ts` route runs as a Vercel Function automatically when deployed. No special config needed.

## Function size limits

| Plan | Per-function size | Per-function timeout |
|---|---|---|
| Hobby | 50 MB | 10s |
| Pro | 50 MB | 60s (or 300s for Background Functions) |
| Enterprise | 250 MB | 900s |

The TinaCMS backend bundle is around 5-15 MB depending on your DB adapter. Well within limits.

For very long indexing operations (initial reindex of 10k+ docs), the 10s timeout on Hobby may be tight. Use Background Functions or Pro for large content sets.

## Memory

```typescript
// app/api/tina/[...routes]/route.ts
export const maxDuration = 60   // up to 60s on Pro
```

For DB indexing during heavy save operations, increase `maxDuration` to avoid timeouts.

## Cold start

First request to a cold function takes 200-500ms longer. For TinaCMS specifically:

- DB connection takes ~50-100ms cold
- GitHub PAT validation takes ~20ms cold
- Total cold start: ~300-500ms

Mitigate with Vercel's "Function Optimization" or the older "Pre-warming" settings.

## Edge runtime — DO NOT use

```typescript
// ❌ DO NOT
export const runtime = 'edge'
```

The backend requires Node.js APIs. Edge runtime fails at build with module-resolution errors.

## Region

```typescript
export const preferredRegion = 'iad1'  // Washington DC
```

Pin the function to a specific region. For DB-heavy backends, match the region to your DB:

| DB | Region |
|---|---|
| Vercel KV (Upstash) | Same as Upstash region |
| MongoDB Atlas | Closest Atlas region |

Cross-region calls add 50-200ms latency.

## Deployment env vars

Set in Vercel Project Settings:

```env
TINA_PUBLIC_IS_LOCAL=false
NEXTAUTH_SECRET=<32 random chars>
GITHUB_OWNER=<owner>
GITHUB_REPO=<repo>
GITHUB_BRANCH=main
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx
KV_REST_API_URL=<auto-injected by Vercel KV>
KV_REST_API_TOKEN=<auto-injected>
```

Scope to Production + Preview.

## Deployment via CLI or git push

```bash
# Push to GitHub:
git push origin main
# Vercel auto-deploys

# Or manually trigger:
vercel deploy --prod
```

## Logs

Vercel Functions → Logs (live) or Vercel Dashboard → Functions → Logs (historical). Useful for debugging:

- Auth failures
- DB connection issues
- GitHub API errors

## Webhook for revalidation

Wire a route handler that revalidates Next.js cache when TinaCloud webhooks fire (or your own write-detection):

```typescript
// app/api/revalidate/route.ts
import { revalidatePath } from 'next/cache'
export async function POST(req: Request) {
  const body = await req.json()
  for (const path of body.paths ?? []) {
    revalidatePath(`/${path.replace(/^content\//, '').replace(/\.md$/, '')}`)
  }
  return Response.json({ ok: true })
}
```

For self-hosted, this is required if you use `revalidate` cache strategies — the backend writes don't auto-trigger ISR.

## Concurrency

Vercel Functions handle concurrent requests automatically. The DB connection pooling is handled by the upstash-redis-level / mongodb-level adapters.

For very high concurrency (1000+ rps), monitor for connection pool exhaustion:

- Vercel KV: rate limits on Upstash side
- MongoDB Atlas: connection pool size

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `runtime: 'edge'` | Build fails | Remove |
| Forgot env vars | Function returns 500 | Add all in Vercel project settings |
| Wrong region | Slow cross-region calls | Match function region to DB region |
| Hit 10s Hobby timeout on indexing | Initial reindex fails | Upgrade to Pro or use background |
| Cold start latency on user-facing routes | TTFB up by ~500ms | Pre-warm or accept |
