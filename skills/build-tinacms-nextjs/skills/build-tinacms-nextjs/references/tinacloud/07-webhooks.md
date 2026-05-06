# TinaCloud Webhooks

Webhooks fire on content events. Common use: trigger Vercel rebuilds or revalidate Next.js cache.

## Setup

Project Settings → Webhooks → Add Webhook.

| Field | Purpose |
|---|---|
| Name | Display label |
| Server URL | Where to POST (your endpoint) |
| Target branches | Which branches fire this webhook |
| Headers | Custom headers (e.g. shared secret) |

## Payload shape

```json
{
  "clientId": "276...",
  "branch": "main",
  "paths": ["content/posts/launch.md", ...],
  "type": "content.modified",
  "eventId": "472..."
}
```

| Field | Type |
|---|---|
| `clientId` | TinaCloud project's Client ID |
| `branch` | Which branch triggered the event |
| `paths` | List of changed file paths |
| `type` | `'content.added'`, `'content.modified'`, or `'content.removed'` |
| `eventId` | Unique event identifier |

## Common destinations

### Vercel Deploy Hook

For static rebuilds:

1. Vercel Project Settings → Git → Deploy Hooks → Create
2. Copy the URL (looks like `https://api.vercel.com/v1/integrations/deploy/...`)
3. Add as TinaCloud webhook destination
4. Set target branches to `main` (or whichever your prod branch is)

Now content commits trigger Vercel rebuilds.

### Next.js revalidation route

For ISR / `cacheComponents` setups:

```typescript
// app/api/revalidate/route.ts
import { revalidatePath, revalidateTag } from 'next/cache'
import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  // Verify signature
  const signature = req.headers.get('x-webhook-signature')
  if (!verifySignature(signature, process.env.WEBHOOK_SECRET!)) {
    return new Response('Unauthorized', { status: 401 })
  }

  const body = await req.json()

  for (const path of body.paths ?? []) {
    // Map content path to URL path
    const slug = path.replace('content/pages/', '').replace(/\.md$/, '')
    revalidatePath(`/${slug === 'home' ? '' : slug}`)
  }

  return NextResponse.json({ ok: true })
}
```

Wire to TinaCloud webhook — content changes trigger immediate revalidation.

### External services

- Slack notifications on content changes
- Algolia/Meilisearch reindex for full-text search
- Analytics events
- Translation pipelines (auto-translate on save)

## Securing webhooks

Add a custom header in the webhook config:

```
Authorization: Bearer your-shared-secret
```

In your handler:

```typescript
const auth = req.headers.get('authorization')
if (auth !== `Bearer ${process.env.WEBHOOK_SECRET}`) {
  return new Response('Unauthorized', { status: 401 })
}
```

Or use signature verification (HMAC of the body) if your destination supports it.

## Webhook logs

Webhooks → Logs shows recent webhook attempts:

- Date / status code
- Request payload sent
- Response body received

Use this to debug failed webhooks.

## Retries

TinaCloud retries failed webhooks (HTTP 5xx) with exponential backoff. Persistent failures eventually give up — check logs.

For idempotency, your handler should be safe to invoke twice with the same `eventId`. Track processed event IDs if needed.

## Branch-specific webhooks

```
Webhook 1: branches=main, URL=production-rebuild
Webhook 2: branches=staging, URL=staging-rebuild
Webhook 3: branches=*, URL=audit-log
```

Configure as needed.

## When to use webhooks vs `revalidate`

| Approach | Latency | Cost |
|---|---|---|
| Webhook → `revalidatePath` | Immediate | Webhook hits per save |
| Next.js fetch `revalidate: 60` | Up to 60s | One fetch per cache miss |

For high-traffic sites where freshness matters, webhooks are best. For low-traffic sites, `revalidate` alone is enough.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| No signature verification | Anyone can hit your revalidate route | Add `WEBHOOK_SECRET` header check |
| Forgot to map paths to URLs | Wrong page revalidated | Strip prefix and extension |
| Revalidate route returns slow | Webhook timeout | Process async; respond fast |
| Used webhook to your dev URL by accident | Production payloads to localhost | Set per environment |
| No retry logic for downstream | Failed revalidations | TinaCloud retries; ensure idempotency |
