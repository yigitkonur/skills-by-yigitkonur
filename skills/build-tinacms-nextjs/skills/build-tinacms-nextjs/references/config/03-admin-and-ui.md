# `admin` and `ui` Config

The admin route, UI customizations, and the `previewUrl` function for editorial workflow.

## Admin route (App Router)

The admin SPA at `public/admin/index.html` is served as a static asset. To make `/admin` (no `.html`) work and to gate it server-side, use the App Router catch-all route TinaCMS init creates:

```tsx
// app/admin/[[...index]]/page.tsx
'use client'
import { useEffect, useRef } from 'react'

export default function AdminPage() {
  const ref = useRef<HTMLIFrameElement>(null)
  useEffect(() => {
    // TinaCMS provides admin.html under public/admin/
    if (ref.current) ref.current.src = '/admin/index.html'
  }, [])
  return (
    <iframe
      ref={ref}
      style={{ position: 'fixed', inset: 0, width: '100%', height: '100%', border: 0 }}
    />
  )
}
```

Or use a redirect:

```tsx
// app/admin/page.tsx
import { redirect } from 'next/navigation'
export default function Admin() {
  redirect('/admin/index.html')
}
```

The TinaCMS CLI typically generates this for you on `init`.

## `ui` section

```typescript
ui: {
  previewUrl: (context) => ({
    url: `https://my-app-git-${context.branch}.vercel.app`,
  }),
}
```

| Property | Purpose |
|---|---|
| `previewUrl` | Function returning a preview URL per branch (Editorial Workflow) |

## Editorial Workflow `previewUrl`

For Team Plus+ users, `previewUrl` is the function TinaCloud calls to get the preview link for a non-protected branch:

```typescript
ui: {
  previewUrl: (context) => {
    // For Vercel preview deployments:
    // pattern: https://<project-name>-git-<branch-name>-<team>.vercel.app
    return {
      url: `https://my-app-git-${context.branch}-myteam.vercel.app`,
    }
  },
}
```

What `context` provides:

- `branch` — the editor's branch name (e.g. `tina/draft-2026-05-08-abc123`)

The function should return `{ url: string }`. Tina puts this URL into the "Preview" link in the admin so editors can click through to the live preview.

If you don't set `previewUrl`, the editorial workflow still works but editors don't see preview links.

## Vercel preview-URL patterns

Vercel generates preview URLs by combining project name, branch name, and (sometimes) team name. The exact pattern depends on Vercel team settings:

```
https://<project>-git-<branch>.vercel.app           # personal account
https://<project>-git-<branch>-<team>.vercel.app    # team account with custom domains
```

Check a Vercel Preview Deployment URL once and use it as the template. Branch slugs are sanitized (slashes become hyphens).

## Custom CMS title and logo

You can customize the admin's branding:

```typescript
ui: {
  previewUrl: /* ... */,

  // No first-class API for title/logo at the time of writing — done via
  // CSS overrides in your admin route component or via tinacms-clerk's
  // OrganizationSwitcher pattern.
}
```

For most projects the default branding is fine.

## `cmsCallback` for advanced UI plugins

For toolkit-level plugin registration (custom field components, custom toolbars), use `cmsCallback`:

```typescript
import type { TinaCMS } from 'tinacms'

export default defineConfig({
  // ...
  cmsCallback: (cms: TinaCMS) => {
    cms.fields.add({
      name: 'my-custom-field',
      Component: MyCustomFieldComponent,
    })
    return cms
  },
})
```

See `references/toolkit-fields/07-custom-field-component.md` for the field plugin pattern.

## Protecting the admin route

The static admin SPA at `/admin/index.html` is publicly served — anyone can load the SPA. Auth happens at the GraphQL level (TinaCloud or your self-hosted auth provider rejects unauthenticated mutations).

If you want to also gate the page-load itself:

```typescript
// proxy.ts (Next.js 16) or middleware.ts (Next.js 15)
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (pathname.startsWith('/admin') && process.env.NODE_ENV === 'production') {
    // Add your auth check; redirect to login if unauthorized
    const cookie = request.cookies.get('session')
    if (!cookie) {
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }
}

export const config = {
  matcher: ['/admin/:path*'],
}
```

This is optional — TinaCloud's auth at the API level is enough for most cases.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `previewUrl` returns just a string | Type error — must return `{ url }` | Wrap in object: `{ url: ... }` |
| `previewUrl` hardcoded to one branch | Preview link wrong for non-default branches | Interpolate `context.branch` |
| Forgot to add `app/admin/[[...index]]/page.tsx` | `/admin` 404 | Either add the route or visit `/admin/index.html` directly |
| Auth-gated `/admin` blocks the GraphQL endpoint too | Can't read content from server components | Match on `/admin` only, not `/api/tina` |
