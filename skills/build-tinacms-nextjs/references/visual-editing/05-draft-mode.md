# Draft Mode

Next.js's mechanism for previewing edits without affecting production caching. Required for visual editing in deployed environments.

## The preview route

```typescript
// app/api/preview/route.ts
import { draftMode } from 'next/headers'
import { redirect } from 'next/navigation'

export async function GET(request: Request) {
  const url = new URL(request.url)
  const slug = url.searchParams.get('slug') || '/'
  const redirectUrl = new URL(slug, url.origin)
  const redirectPath =
    redirectUrl.origin === url.origin
      ? `${redirectUrl.pathname}${redirectUrl.search}`
      : '/'

  // Next.js 16: draftMode() returns a Promise
  ;(await draftMode()).enable()

  redirect(redirectPath)
}
```

Visit `/api/preview?slug=/some-page` → sets a `__prerender_bypass` cookie → redirects to `/some-page` with Draft Mode active.

## Disable route (optional)

```typescript
// app/api/preview/disable/route.ts
import { draftMode } from 'next/headers'
import { redirect } from 'next/navigation'

export async function GET() {
  ;(await draftMode()).disable()
  redirect('/')
}
```

## What Draft Mode does

| Mode | Behavior |
|---|---|
| **Off** (default) | Pages serve static/cached. `useTina` is a no-op. |
| **On** (after visiting `/api/preview`) | All `"use cache"` scopes bypass. `useTina` subscribes to live edits. |

Draft Mode is a per-browser cookie. Editors visit `/api/preview` once, then can navigate anywhere on the site with edit-mode active.

## How TinaCloud knows to use Draft Mode

When the admin opens a live page in the iframe, it appends `?slug=<path>` to `/api/preview` so the redirect lands on the right page. The cookie persists across navigations.

For local dev, the local TinaCMS GraphQL server detects Draft Mode and serves edit-mode data.

## Async `draftMode()` (Next.js 16)

```typescript
// ❌ Wrong (Next.js 15-style)
const draft = draftMode()
draft.enable()

// ✅ Right (Next.js 16)
const draft = await draftMode()
draft.enable()
```

Same as `cookies()` and `headers()` — these became async in Next.js 16.

## Cookie semantics

The cookie is `__prerender_bypass`. It's:

- HttpOnly (not readable from JS)
- Same-origin
- Lasts for the browser session (no explicit expiry)

To force-disable for a specific browser, visit the disable route or clear cookies for the domain.

## Combining with `"use cache"`

Draft Mode bypasses all `"use cache"` scopes automatically. No extra wiring:

```typescript
async function getPage(slug: string) {
  'use cache'
  cacheLife('hours')
  // ... fetch
}

// In Draft Mode: 'use cache' is skipped, fetch runs every render
// In production: 'use cache' applies, fetch runs every cacheLife
```

## Combining with Vercel cache

Vercel data cache also bypasses on Draft Mode requests automatically. Same with TinaCloud responses.

## Verifying

After visiting `/api/preview`:

1. Check browser cookies — `__prerender_bypass` should be set
2. Open dev tools network tab — page requests should show `Cache-Control: private, no-store`
3. Edit a value in the admin and watch the preview iframe — content should update live

If cookies don't persist:

- Check that the route is `app/api/preview/route.ts` (not `app/api/preview.ts`)
- Check the redirect target is on the same origin
- Check no Service Worker is intercepting

## Securing Draft Mode

Anyone who hits `/api/preview` enables Draft Mode. For most projects this is fine — Draft Mode just shows current content; it doesn't expose private data.

For sites where draft content must stay private, gate the preview route:

```typescript
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const secret = searchParams.get('secret')

  if (secret !== process.env.PREVIEW_SECRET) {
    return new Response('Forbidden', { status: 403 })
  }

  // ... enable Draft Mode
}
```

TinaCloud passes the secret if you configure one. For most sites the unsecured version is fine.

## Troubleshooting

| Symptom | Cause |
|---|---|
| Preview iframe shows static page | Draft Mode never enabled — visit `/api/preview` |
| Editor edits don't show | useTina not subscribing — check `"use client"` and props |
| Draft Mode enabled but content stale | Browser caching — disable in dev tools network tab |
| Different domain renders differently | Cookie scoped per-origin |

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Sync `draftMode()` access | Build error in Next.js 16 | `await draftMode()` |
| Route at `/preview/route.ts` (no `api` prefix) | 404 in some setups | Use `app/api/preview/route.ts` |
| Forgot the `redirect()` call | Returns empty 200 | Add redirect |
| Draft Mode forces `revalidate: 0` everywhere | Confusing fresh-mode in production | Production users don't have the cookie — only editors |
