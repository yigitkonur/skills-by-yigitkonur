# Middleware Proxy

> Documents the request-time proxy in `apps/web/proxy.ts`. Consult this when a request is redirected before React renders, when locale handling behaves unexpectedly, or when feature flags change how `/app`, `/auth`, or marketing routes are reached.

> ⚠️ **Middleware matcher.** If `/api/rpc/...` calls fail with 404, check the matcher that controls the proxy entrypoint. API routes must pass through without locale or auth rewrites.

## Key file

- `apps/web/proxy.ts`

## Decision order

The exported `proxy` function runs on every matched request and applies a fixed sequence:

1. guard `/app` routes behind the session cookie
2. redirect `/app` and `/auth` back to `/` when SaaS is disabled
3. allow helper paths like `/onboarding` and `/choose-plan` to bypass locale middleware
4. redirect all remaining requests to `/app` when marketing is disabled
5. otherwise hand the request to `next-intl` middleware

```ts
if (pathname.startsWith("/app")) {
  if (!appConfig.saas.enabled) {
    return NextResponse.redirect(new URL("/", origin));
  }

  if (!sessionCookie) {
    return NextResponse.redirect(
      new URL(withQuery("/auth/login", { redirectTo: pathname }), origin),
    );
  }

  return NextResponse.next();
}
```

## What belongs here vs in layouts

The proxy only performs broad request-time routing decisions based on path prefixes, cookies, and top-level feature flags. Deeper product logic still lives in the App Router tree:

- onboarding completion checks happen in the SaaS `/app` layout
- organization-required and billing-required redirects happen in server layouts/pages
- page chrome such as `AppWrapper`, `NavBar`, and organization switching is not part of the proxy

That split is important: if a redirect happens before any layout renders, inspect `proxy.ts` first; if the request reaches `/app` and then redirects, inspect the server layouts.

## Pass-through paths

These helper routes intentionally bypass locale middleware in `proxy.ts`:

- `/onboarding`
- `/new-organization`
- `/choose-plan`
- `/organization-invitation`

They still live inside the SaaS App Router tree, but they skip locale rewriting because they are prerequisite flows rather than marketing pages.

## Matcher scope

The matcher excludes API routes, image/font assets, and well-known static files so they avoid middleware overhead:

- `/api`
- `/image-proxy`
- `/images`
- `/fonts`
- `/_next/static`
- `/_next/image`
- `favicon.ico`, `icon.png`, `sitemap.xml`, `robots.txt`

## Practical notes

- unauthenticated `/app` visits are redirected to `/auth/login` with `redirectTo` preserved
- when `marketing.enabled` is `false`, non-SaaS traffic is funneled into `/app`
- next-intl locale detection only runs after the earlier SaaS and marketing checks pass
- proxy logic should stay coarse-grained; feature-specific access rules belong in layouts and pages

## Debugging checklist

1. Check `/api/rpc/...` reaches Next.js (check the matcher that controls the proxy entrypoint)
2. Verify env vars for any proxy target
3. Check the matcher patterns that control the proxy entrypoint
4. Ensure no auth guard interferes with API routes
5. Check CORS headers if calling from a different origin

---

**Related references:**
- `references/routing/access-guards.md` — server-side redirects that run after the proxy allows the request through
- `references/routing/routing-saas.md` — SaaS route placement for helper pages and `/app`
- `references/routing/routing-marketing.md` — locale-aware public routing after next-intl middleware runs
- `references/i18n/locale-routing.md` — routing configuration used by next-intl
