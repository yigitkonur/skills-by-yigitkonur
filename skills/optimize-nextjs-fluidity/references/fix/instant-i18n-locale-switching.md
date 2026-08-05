# Fix: instant-i18n-locale-switching

**Corpus lineage:** instant-i18n-locale-switching/04-implementation-next-intl-setup.md,
instant-i18n-locale-switching/05-implementation-switching-static-seo.md,
instant-i18n-locale-switching/07-pitfalls.md,
instant-i18n-locale-switching/08-version-lockin-seo-vercel-practitioner.md
**Knowledge baseline:** verified 2026-08-05 against Next.js 16.3.0 docs. Confirm any
config key against the installed package first — see `references/gating/capability-probe.md`.

**This domain is library-optional.** The App Router has no built-in i18n routing —
`next-intl` implements a documented *pattern* (`[locale]` segment, `proxy.ts`
negotiation, static rendering, hreflang metadata), it does not own the pattern. A
repo with no `next-intl` dependency but a working `[locale]` segment + `proxy.ts` +
custom dictionary loader (e.g. `src/lib/i18n/`) already implements this pattern —
the `APPLICABLE-CUSTOM` verdict means **adapt the mechanism to the existing
implementation**, never "replace your custom `src/lib/i18n/` with next-intl." Every
recipe below carries a Library variant and a Custom variant.

## Recipe index

| Recipe | Requires | Reversibility | Triggered by |
|---|---|---|---|
| `proxy.ts` locale negotiation | Next.js ≥16.0.0; Node.js runtime | fully-reversible (codemod-assisted rename) | `middleware.ts` still used for locale negotiation on Next.js ≥16.0.0 |
| Root layout under `[locale]` | App Router, `[locale]`/`[lang]` segment | component-level-revert | `next/root-params` returns empty object; a layout exists above the locale segment |
| Static rendering via `next/root-params` | Next.js ≥16.3.0 | fully-reversible | No `generateStaticParams`, or locale read via `headers()`/prop-drilling on 16.3+ |
| Static rendering — legacy `setRequestLocale` | next-intl only, Next.js <16.3.0 or not yet migrated | fully-reversible | Same need, installed Next.js below the root-params floor |
| Cache-key narrowing with `next/root-params` | Next.js ≥16.3.0, `cacheComponents: true` | fully-reversible | Locale read via `headers()` inside a `'use cache'` scope; unnecessary cache fragmentation |
| Soft locale switch (`router.replace` + `startTransition`) | Locale-aware navigation wrapper (library) or equivalent (custom) | fully-reversible | Locale switch causes a full document reload (`window.location` assignment) |
| hreflang via `alternates.languages` (metadata + sitemap) | Next.js 13.2.0+ (metadata), 14.2.0+ (sitemap) | fully-reversible | Missing or hand-written (non-derived) hreflang entries |
| `<html lang>` correctness | `[locale]` segment resolving the actual served locale | fully-reversible | Hardcoded `<html lang>` literal on a multi-locale repo |

## `proxy.ts` locale negotiation — requires Next.js ≥16.0.0, Node.js runtime

**When to apply:** detect found locale-negotiation logic still in `middleware.ts`
on a Next.js ≥16.0.0 install — the documented cause of `"Unable to find next-intl
locale"` (library) or the equivalent silent-negotiation failure (custom), because
Next.js 16 no longer loads `middleware.ts` for this hook.

### Library variant — `next-intl`

```ts
// src/i18n/routing.ts — next-intl 4.x
import { defineRouting } from 'next-intl/routing'

export const routing = defineRouting({
  locales: ['en', 'de'],
  defaultLocale: 'en',
})
```

```ts
// src/proxy.ts — Next.js 16: this file is proxy.ts, NOT middleware.ts.
import createMiddleware from 'next-intl/middleware'
import { routing } from './i18n/routing'

export default createMiddleware(routing)

export const config = {
  // Match all pathnames except:
  // - those starting with /api, /trpc, /_next, /_vercel
  // - those containing a dot (e.g. favicon.ico)
  matcher: '/((?!api|trpc|_next|_vercel|.*\\..*).*)',
}
```

**Why each non-obvious line exists:**
- `defineRouting` centralizes locale/prefix/domain config so the proxy and the
  navigation APIs stay in sync automatically.
- The import path stays `next-intl/middleware` even though the file is now
  `proxy.ts` — the package's internal module name was not renamed alongside the
  Next.js file-convention rename.
- If pathnames contain literal dots (e.g. `/users/jane.doe`), add a second matcher
  entry: `'/([\\w-]+)?/users/(.+)'` — the default matcher skips them.

### Custom variant — adapt the existing negotiator, rename the file only

```ts
// src/proxy.ts — Next.js 16.3.0, custom implementation
// Rename from middleware.ts. Logic is unchanged — only the file name
// and the default export's role change; Next.js 16 looks for proxy.ts.
import { NextRequest, NextResponse } from 'next/server'

const locales = ['en', 'de'] as const
const defaultLocale = 'en'

export default function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  const hasLocale = locales.some(
    (locale) => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  )
  if (hasLocale) return NextResponse.next()

  // Existing negotiation order (cookie → Accept-Language → default) is preserved
  // verbatim — only the file location changed.
  const cookieLocale = request.cookies.get('NEXT_LOCALE')?.value
  const locale =
    (locales as readonly string[]).includes(cookieLocale ?? '')
      ? cookieLocale
      : defaultLocale

  return NextResponse.redirect(
    new URL(`/${locale}${pathname}`, request.url)
  )
}

export const config = {
  matcher: '/((?!api|trpc|_next|_vercel|.*\\..*).*)',
}
```

**Why this is a rename, not a rewrite:** the negotiation logic itself (cookie →
header → default priority) is whatever the repo already implemented — only the
file's name and its role as the Next.js network-boundary hook change. Do not
restructure the negotiation order while performing this fix; that is a separate
change.

**Verify after applying:** hit an unprefixed URL (e.g. `/about`) with dev tools
open; confirm a redirect to `/en/about` (or the default locale) occurs, and that a
locale cookie (`NEXT_LOCALE` or the repo's equivalent) is set on the response.

**Lock-in / reversibility:** fully-reversible — `middleware.ts` → `proxy.ts` is a
codemod-assisted, forward-expected rename per
`references/gating/lockin-reversibility.md`.

**Rollback:** rename `proxy.ts` back to `middleware.ts` — only meaningful if
downgrading below Next.js 16, which is not a normal rollback path.

## Root layout under `[locale]` — requires App Router, `[locale]`/`[lang]` dynamic segment

**When to apply:** `next/root-params` (or the repo's equivalent locale-prop read)
returns an empty object or the wrong value — the documented cause is a layout file
existing at `app/layout.tsx`, **above** the `[locale]` segment.

### Library variant — `next-intl`

```tsx
// src/app/[locale]/layout.tsx — Next.js 16.3.0, next-intl 4.13.5
import { NextIntlClientProvider } from 'next-intl'
import { getMessages } from 'next-intl/server'
import { locale } from 'next/root-params' // getter name matches the folder: [locale] -> `locale`
import type { ReactNode } from 'react'

export default async function LocaleLayout({
  children,
}: {
  children: ReactNode
}) {
  const messages = await getMessages()

  return (
    <html lang={await locale()}>
      <body>
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  )
}
```

**Do not also create `app/layout.tsx` above this one** — a root layout above the
`[locale]` segment is the documented, maintainer-confirmed cause of
`next/root-params` returning an empty object.

### Custom variant — adapt to a hand-rolled dictionary provider

```tsx
// src/app/[locale]/layout.tsx — Next.js 16.3.0, custom implementation
import { locale } from 'next/root-params'
import { getDictionary } from '@/lib/i18n/get-dictionary' // repo's existing loader
import type { ReactNode } from 'react'

export default async function LocaleLayout({
  children,
}: {
  children: ReactNode
}) {
  const currentLocale = await locale()
  const dictionary = await getDictionary(currentLocale) // existing custom loader, unchanged

  return (
    <html lang={currentLocale}>
      <body>{children}</body>
    </html>
  )
}
```

**Why each non-obvious line exists:**
- Moving every layout/page under `app/[locale]/...` is what makes `locale` a
  **root parameter** in the `next/root-params` sense — accessible from any Server
  Component without prop-drilling.
- `<html lang={...}>` binds the document's declared language directly to the
  resolved locale — required for the SEO/accessibility obligation this domain
  tracks separately below.
- The `next/root-params` getter-name convention: the export name matches the
  dynamic segment folder name verbatim (`[locale]` → `locale`, `[lang]` → `lang`)
  — this is not configurable.

**Verify after applying:** View source (not DevTools' live DOM, since this is a
Server Component) on `/de/...` and confirm `<html lang="de">` is present in the raw
HTML response, not just applied client-side. Call the getter from a deeply nested
Server Component with no `params` prop passed down and confirm it resolves
correctly.

**Lock-in / reversibility:** component-level-revert — restructuring the layout
tree is bounded to the layout files themselves, not a data-migration.

**Rollback:** move the root layout back above `[locale]` — this reintroduces the
empty-object bug, so only do this if reverting the whole root-params adoption.

## Static rendering via `next/root-params` — requires Next.js ≥16.3.0

**When to apply:** detect found no `generateStaticParams` over locales, or a
locale read via `headers()` (library default before root-params) or manual
prop-drilling (custom) on an install that supports 16.3's root-params.

### Library variant — `next-intl`

```ts
// src/app/[locale]/layout.tsx — Next.js 16.3.0 (or any layout/page to statically render)
import { routing } from '@/i18n/routing'

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }))
}
```

```ts
// src/i18n/request.ts — requires next/root-params, default in Next.js 16.3+
import * as rootParams from 'next/root-params'
import { notFound } from 'next/navigation'
import { getRequestConfig } from 'next-intl/server'
import { hasLocale } from 'next-intl'
import { routing } from './routing'

export default getRequestConfig(async ({ locale }) => {
  if (!locale) {
    const paramValue = await rootParams.locale()
    if (hasLocale(routing.locales, paramValue)) {
      locale = paramValue
    } else {
      notFound()
    }
  }
  return { locale }
})
```

**Why this line exists:** when this root-params-based setup is followed, static
rendering eligibility is **automatic** — no per-page API call is required beyond
`generateStaticParams`. This is next-intl's current-recommended path, superseding
the `headers()`-based default that forced dynamic rendering.

### Custom variant — adapt to the existing route structure

```ts
// src/app/[locale]/layout.tsx — Next.js 16.3.0, custom implementation
const locales = ['en', 'de'] as const

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }))
}
```

```ts
// app/[locale]/components/greeting.tsx — Next.js 16.3.0 (any Server Component, no prop-drilling)
import { locale } from 'next/root-params'

export async function getTranslatedGreeting() {
  const currentLocale = await locale()
  return currentLocale === 'de' ? 'Hallo' : 'Hello'
}
```

**Why this is the fix regardless of library:** the mechanism is identical —
`generateStaticParams` enumerates the locales, and `next/root-params` replaces
whatever prop-drilling or `headers()`-based read previously forced dynamic
rendering. Adapt the existing dictionary-loading calls to read from the root-params
getter instead of a passed-down `params` prop or a request header.

**Verify after applying:** run `next build` and check the route output table —
locale routes should be marked static (○), not dynamic (λ). Add a temporary
`console.log(locale)` and hit `/en/somepage` and `/de/somepage` to confirm the
correct locale is resolved per request without forcing a dynamic render.

**Lock-in / reversibility:** fully-reversible — `generateStaticParams` is one
function export per layout/page; removing it reverts the route to dynamic.

**Rollback:** remove the `generateStaticParams` export; the route reverts to
dynamic rendering (or errors if nothing else resolves the locale — verify against
whichever locale-read mechanism remains).

## Static rendering — legacy `setRequestLocale` — requires next-intl, Next.js <16.3.0 or not yet migrated

**When to apply:** the capability probe confirms installed Next.js is below
16.3.0 (root-params unavailable without `experimental.rootParams`), or the repo is
on next-intl and has not yet migrated to root-params. **next-intl's own docs label
this legacy** — prefer the root-params recipe above whenever the version floor
allows it.

```tsx
// app/[locale]/layout.tsx — LEGACY path, next-intl only
import { setRequestLocale } from 'next-intl/server'
import { hasLocale } from 'next-intl'
import { notFound } from 'next/navigation'
import { routing } from '@/i18n/routing'

type Props = {
  children: React.ReactNode
  params: Promise<{ locale: string }>
}

export default async function LocaleLayout({ children, params }: Props) {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) {
    notFound()
  }

  // Enable static rendering
  setRequestLocale(locale)

  return (
    <html lang={locale}>
      <body>{children}</body>
    </html>
  )
}
```

**Rules for this legacy path, verbatim from next-intl's docs:** (1) the locale
passed to `setRequestLocale` must be validated in the root layout; (2) it must be
called in **every** page and **every** layout you want static-rendering eligibility
for, since Next.js can render layouts and pages independently; (3) it must be
called before any next-intl function (`useTranslations`, `getMessages`, etc.).

**No custom-variant equivalent exists for this recipe** — `setRequestLocale` is a
next-intl API specifically. A custom implementation targeting a pre-16.3 install
should read the locale from the awaited `params` prop directly (standard Next.js
Server Component pattern) instead of adopting this API.

**Verify after applying:** run `next build` and confirm locale routes are marked
static (○). Confirm `setRequestLocale` is called before any `useTranslations`/
`getMessages` call in the same component tree.

**Lock-in / reversibility:** fully-reversible, additive — migrating to
`next/root-params` later requires restructuring `i18n/request.ts` and removing
per-page `setRequestLocale` calls; both paths can coexist during migration.

**Rollback:** remove the `setRequestLocale` call; the route reverts to dynamic
rendering (the pre-3.22 default for next-intl Server Component APIs).

## Cache-key narrowing with `next/root-params` — requires Next.js ≥16.3.0, `cacheComponents: true`

**When to apply:** a `'use cache'` function reads the locale via `headers()` or an
unrelated route param instead of a root-params getter, unnecessarily fragmenting
the cache key across params the function doesn't actually depend on.

```tsx
// app/[lang]/components/cached-nav.tsx — Next.js 16.3.0
import { lang } from 'next/root-params'

// The cache key for this function only includes `lang`, not every dynamic
// segment in the route (e.g. an unrelated [slug]).
async function getNavigation() {
  'use cache'
  const language = await lang()
  const res = await fetch(`https://api.example.com/nav?lang=${language}`)
  return res.json()
}

export default async function CachedNav() {
  const nav = await getNavigation()
  return <nav>{/* render nav items */}</nav>
}
```

**Why this line exists:** because root parameter getters are imported functions,
Next.js can track which ones a cached function actually calls — only those
parameters become part of the cache key. A cached navigation/data function that
only depends on locale (not a nested `[slug]`) produces one cache entry per locale,
not one per `locale × slug` combination.

**Restrictions, verbatim:** `next/root-params` can be used in Server Components
only — not Client Components, Server Actions, or Route Handlers (Route Handler
support is planned for a future release). Calling a root-parameter getter inside
`unstable_cache` throws a runtime error — use `'use cache'` instead.

**Verify after applying:** confirm the cached function's output is shared across
different `[slug]` values under the same locale (one cache entry, not N) by
inspecting cache-hit behavior or adding temporary logging inside the cached
function.

**Lock-in / reversibility:** fully-reversible — reverting to a `headers()`-based
read (with the associated dynamic-rendering cost) is a straight function-body
swap.

**Rollback:** replace the `next/root-params` getter call with the previous
`headers()`-based read; accept the reintroduced dynamic-rendering cost.

## Soft locale switch (`router.replace` + `startTransition`) — requires a locale-aware navigation wrapper

**When to apply:** detect found a locale switch implemented via `window.location`
assignment (full-document reload) instead of client-side router navigation.

**The honest limit, state this in the task and to the user:** this eliminates the
full-document-reload class of failure. It does **not** eliminate the network
round-trip for the new locale's RSC payload — server-rendered translations were
never shipped to the client as a swappable dictionary. Never describe this as
zero-network; the correct framing is "as fast as any other client-side navigation
in this app," bounded by the same prefetch/cache mechanics as regular navigation.

### Library variant — `next-intl`

```ts
// src/i18n/navigation.ts — Next.js 16.3.0, next-intl 4.13.5
import { createNavigation } from 'next-intl/navigation'
import { routing } from './routing'

export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing)
```

```tsx
// src/components/LocaleSwitcherSelect.tsx — next-intl 4.x / Next.js 16.x
'use client'

import { useTransition, type ChangeEvent } from 'react'
import { useParams } from 'next/navigation'
import { useRouter, usePathname } from '@/i18n/navigation'
import type { Locale } from 'next-intl'

const locales: Locale[] = ['en', 'de']

export default function LocaleSwitcherSelect({
  defaultValue,
}: {
  defaultValue: Locale
}) {
  const router = useRouter()
  const pathname = usePathname()
  const params = useParams()
  const [isPending, startTransition] = useTransition()

  function onSelectChange(event: ChangeEvent<HTMLSelectElement>) {
    const nextLocale = event.target.value as Locale
    startTransition(() => {
      router.replace(
        // @ts-expect-error -- params always match pathname for the active route
        { pathname, params },
        { locale: nextLocale }
      )
    })
  }

  return (
    <select
      defaultValue={defaultValue}
      disabled={isPending}
      onChange={onSelectChange}
      aria-label="Select language"
    >
      {locales.map((cur) => (
        <option key={cur} value={cur}>
          {cur}
        </option>
      ))}
    </select>
  )
}
```

**Why each non-obvious line exists:**
- `useRouter`/`usePathname` come from `@/i18n/navigation` (the `createNavigation`
  output), **not** `next/navigation` — only the locale-aware wrapper accepts the
  `{locale}` second argument to `router.replace`.
- `useParams()` (raw `next/navigation`) captures the current route's dynamic
  params so the switch preserves the current page, not just the locale.
- `startTransition` wraps the navigation so `isPending` can drive a `disabled`
  state instead of the UI looking frozen during the RSC payload fetch.

### Custom variant — adapt to a hand-rolled locale-aware router

```tsx
// src/components/LocaleSwitcherSelect.tsx — Next.js 16.3.0, custom implementation
'use client'

import { useTransition, type ChangeEvent } from 'react'
import { useRouter, usePathname } from 'next/navigation'

const locales = ['en', 'de'] as const

export default function LocaleSwitcherSelect({
  defaultValue,
}: {
  defaultValue: string
}) {
  const router = useRouter()
  const pathname = usePathname()
  const [isPending, startTransition] = useTransition()

  function onSelectChange(event: ChangeEvent<HTMLSelectElement>) {
    const nextLocale = event.target.value
    // Preserve the current page: swap only the leading locale segment.
    const segments = pathname.split('/')
    segments[1] = nextLocale
    const nextPathname = segments.join('/')

    startTransition(() => {
      router.replace(nextPathname)
    })
  }

  return (
    <select
      defaultValue={defaultValue}
      disabled={isPending}
      onChange={onSelectChange}
      aria-label="Select language"
    >
      {locales.map((cur) => (
        <option key={cur} value={cur}>
          {cur}
        </option>
      ))}
    </select>
  )
}
```

**Why this is the fix regardless of library:** the mechanism — a client-side
`router.replace` to the locale-prefixed equivalent of the current path, wrapped in
`startTransition` for a non-blocking pending state — is the fix. The library
variant's `{locale}` option on `router.replace` is a convenience; the custom
variant achieves the identical navigation by rewriting the pathname's locale
segment directly with `next/navigation`'s standard router.

**Verify after applying:** click through the switcher with the Network tab open —
confirm exactly one request fires (the RSC payload for the target locale route),
the address bar updates with no full document reload (no favicon flicker), and
`isPending` visibly disables the control for the duration.

**Lock-in / reversibility:** fully-reversible — reverting to `window.location`
restores the full-reload behavior (regression, but mechanically reversible).

**Rollback:** replace `router.replace(...)` with a `window.location.href`
assignment to restore the pre-fix (full-reload) behavior.

## hreflang via `alternates.languages` (metadata + sitemap) — requires Next.js 13.2.0+ (metadata), 14.2.0+ (sitemap)

**When to apply:** detect found missing `alternates.languages`, or hreflang URLs
hand-written as string literals instead of derived from the locale list.

### Library variant — `next-intl`

```tsx
// app/[locale]/page.tsx — Next.js 16.3.0, next-intl 4.13.5
import type { Metadata } from 'next'
import { getPathname } from '@/i18n/navigation'

const host = 'https://acme.com'

export async function generateMetadata(): Promise<Metadata> {
  return {
    alternates: {
      canonical: host,
      languages: {
        en: host + (await getPathname({ locale: 'en', href: '/' })),
        de: host + (await getPathname({ locale: 'de', href: '/' })),
      },
    },
  }
}
```

```ts
// app/sitemap.ts — Next.js 16.3.0, next-intl 4.13.5
import type { MetadataRoute } from 'next'
import { getPathname } from '@/i18n/navigation'
import { routing } from '@/i18n/routing'

const host = 'https://acme.com'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  return [
    {
      url: host,
      lastModified: new Date(),
      alternates: {
        languages: Object.fromEntries(
          await Promise.all(
            routing.locales.map(async (locale) => [
              locale,
              host + (await getPathname({ locale, href: '/' })),
            ])
          )
        ),
      },
    },
  ]
}
```

### Custom variant — derive from the existing locale list

```tsx
// app/[locale]/page.tsx — Next.js 16.3.0, custom implementation
import type { Metadata } from 'next'

const host = 'https://acme.com'
const locales = ['en', 'de'] as const

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  return {
    alternates: {
      canonical: `${host}/${locale}`,
      languages: Object.fromEntries(
        locales.map((l) => [l, `${host}/${l}`])
      ),
    },
  }
}
```

```ts
// app/sitemap.ts — Next.js 16.3.0, custom implementation
import type { MetadataRoute } from 'next'

const host = 'https://acme.com'
const locales = ['en', 'de'] as const

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: host,
      lastModified: new Date(),
      alternates: {
        languages: Object.fromEntries(locales.map((l) => [l, `${host}/${l}`])),
      },
    },
  ]
}
```

**Why each non-obvious line exists:**
- Every hreflang URL is derived from the same locale list (`routing.locales` or
  the repo's own `locales` constant), never hand-typed per page — this is the
  fix for the "drift risk" pitfall: hand-written literals silently diverge from
  the actual routing config as locales are added or renamed.
- Metadata (`generateMetadata`) and sitemap (`sitemap.ts`) entries are
  complementary, not redundant — metadata tags serve the page-load path, sitemap
  entries serve discovery/crawl-budget efficiency; both are required.
- `alternates.canonical` must point to a genuinely per-locale URL, not collapse
  every locale to one canonical target — collapsing tells search engines the
  locale variants are duplicates, undermining the purpose of `alternates.languages`.

**Verify after applying:** View source on a locale route and confirm one `<link
rel="alternate" hreflang="...">` per configured locale in the raw HTML `<head>`,
plus a `<link rel="canonical">`. Fetch `/sitemap.xml` directly and confirm one
`<xhtml:link rel="alternate" hreflang="...">` entry per locale per `<url>` block,
with hreflang codes matching the locale list exactly.

**Lock-in / reversibility:** fully-reversible — metadata/sitemap fields, no schema
migration.

**Rollback:** remove the `alternates.languages` blocks; locale variants become
invisible to crawlers again (regression, not a build risk).

## `<html lang>` correctness — requires the `[locale]` segment resolving the actual served locale

**When to apply:** `<html lang>` is a hardcoded literal on a multi-locale repo
instead of derived from the resolved locale.

```diff
 // app/[locale]/layout.tsx — Next.js 16.3.0
-<html lang="en">
+<html lang={await locale()}>  {/* library: next/root-params getter, or the
+                                  awaited params.locale for a custom implementation */}
```

This is the same fix as the "Root layout under `[locale]`" recipe above — `<html
lang>` correctness and root-params placement are the same change; do not treat
them as two separate edits if both findings point at the same layout file.

**Verify after applying:** View source (not DevTools) on every locale route and
confirm `<html lang="...">` matches the URL's locale segment exactly.

**Lock-in / reversibility:** fully-reversible — a single attribute binding.

**Rollback:** hardcode `<html lang>` back to a single literal value.

## Ordering within this domain

1. **Fix the `proxy.ts` rename first** if `middleware.ts` is still present on
   Next.js ≥16.0.0 — every other recipe assumes locale negotiation actually runs.
2. **Fix root-layout placement** (`[locale]` segment structure) next — this is a
   hard prerequisite for `next/root-params` to work at all, including inside the
   static-rendering and cache-narrowing recipes below it.
3. **Add `generateStaticParams` + the appropriate locale-read recipe** (root-params
   on 16.3+, legacy `setRequestLocale` below that floor) — this is the largest
   cost/performance lever in the domain and a prerequisite for the "instant
   ceiling" the soft-switch recipe depends on.
4. **Fix the soft locale switch** (`router.replace` + `startTransition`) once
   static rendering is in place — a soft switch to a still-dynamic route will not
   feel meaningfully faster, so sequence this after step 3, not before.
5. **Add hreflang metadata + sitemap entries and `<html lang>` correctness** last,
   deriving both from the same locale list used in step 3 — this closes the SEO
   obligations this domain owns per `references/gating/priority-matrix.md`'s
   dependency graph (`instant-i18n-locale-switching` → `seo-metadata`).

## Conflicts to watch

- `references/gating/conflicts.md` §7 — locale soft navigation cannot be
  zero-network; never promise it in a task description or to the user.
- Shares the root-`<html>`-attribute-cannot-be-Suspended constraint with
  `dark-light-theme-switching` — a fix touching `<html lang>` should stay
  consistent with any co-located theme-attribute fix in the same root layout; do
  not propose wrapping the root layout in `<Suspense>` to resolve either.
- A `localePrefix: 'never'`-style URL-less strategy (library or custom) forfeits
  automatic hreflang generation — never recommend it for an indexable
  content/marketing archetype; it is only a valid choice for a logged-in,
  non-indexable app.
