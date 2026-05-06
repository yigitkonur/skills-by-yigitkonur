# `proxy.ts` (Next.js 16)

Next.js 16 replaces `middleware.ts` with `proxy.ts`. Same purpose, slightly different API. TinaCMS-specific concerns: gating `/admin`, redirecting old URLs, draft-mode auth.

## Basic structure

```typescript
// proxy.ts (at project root)
import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl

  // ... your logic
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
```

Lives at the project root (next to `tina/`, not inside `app/` or `pages/`). Runs on **Node.js runtime only** (no Edge).

## Migrating from `middleware.ts`

```bash
pnpm dlx @next/codemod@canary middleware-to-proxy .
```

The codemod renames the file and adjusts the function signature.

Manual steps:

1. Rename `middleware.ts` → `proxy.ts`
2. Rename function: `middleware()` → `proxy()`
3. Verify the export shape matches Next.js 16's expectations

## TinaCMS use cases

### Gate `/admin` route in production

```typescript
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (pathname.startsWith('/admin') && process.env.NODE_ENV === 'production') {
    // Add your auth check, e.g. session cookie:
    const session = request.cookies.get('session')
    if (!session) {
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }
}
```

Note: TinaCloud's auth happens at the GraphQL level (mutations require auth), so gating `/admin` page-load is **optional**. The static admin SPA is publicly served.

### Redirect old URLs

```typescript
const REDIRECTS: Record<string, string> = {
  '/old-blog': '/blog',
  '/about-us': '/about',
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  if (REDIRECTS[pathname]) {
    return NextResponse.redirect(new URL(REDIRECTS[pathname], request.url), 301)
  }
}
```

For redirects derived from CMS content, fetch the redirect map at build time and bake it into the proxy:

```typescript
// Or read from a generated redirects file:
import redirects from './redirects.json'
```

### Allow `/api/tina/gql` to bypass auth (self-hosted)

```typescript
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Skip auth checks for the GraphQL endpoint:
  if (pathname.startsWith('/api/tina')) return

  // ... other auth checks
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
```

Otherwise self-hosted backends can fail to receive auth-bearing requests.

## Don't gate `/api/tina/*`

The TinaCMS GraphQL endpoint at `/api/tina/gql` (self-hosted) needs to be reachable from the admin SPA without a session cookie — TinaCMS uses its own auth headers. Don't redirect this route to a login page.

## Don't gate `/admin/*` static assets

The static admin SPA serves `/admin/index.html` and `/admin/assets/*`. Gating these breaks the admin loading. The matcher above (`(?!_next/static|...)`) handles this for static paths but you need similar exclusions for `/admin`:

```typescript
export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|admin).*)'],
}
```

The `admin` exclusion lets the SPA load even when other paths are gated.

## Redirect editor to live page after login

```typescript
export function proxy(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl

  if (pathname === '/api/preview') {
    const slug = searchParams.get('slug') || '/'
    // ... draft mode logic, then redirect to the live page
  }
}
```

In practice, the `/api/preview` route handler does this; you don't need proxy.ts for it.

## Edge runtime exclusion

`proxy.ts` runs on Node.js runtime. **It does NOT run on Edge runtime.** This is fine for TinaCMS — the backend is Node-only anyway.

If you have other code in proxy.ts that needs Edge (KV access for rate limiting, etc.), you cannot. Move that logic to a different boundary (Vercel function, or app-router route handler).

## Verifying

After deploying:

```bash
curl -I https://your-site.com/admin/
# Should return 200 OK (not 302 to /login)

curl -I https://your-site.com/api/tina/gql
# Should return 200 OK (not 302)

curl -I https://your-site.com/old-blog
# Should return 301 → /blog
```

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Stale `middleware.ts` after migration | Both files conflict | Delete the old one |
| Matcher includes `/admin` and gates it | Admin SPA can't load | Exclude `/admin` from matcher |
| Returns response without `next: { Pathname }` headers | Possible mismatch with Next.js conventions | Use `NextResponse.redirect()` and `NextResponse.next()` |
| Tried Edge runtime | Build fails | Use Node.js runtime (default for proxy.ts) |
| Used in Pages Router project | proxy.ts is App Router only | Use `middleware.ts` for Pages Router |
