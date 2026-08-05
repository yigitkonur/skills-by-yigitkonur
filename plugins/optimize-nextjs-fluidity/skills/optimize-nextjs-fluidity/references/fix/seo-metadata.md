# Fix: seo-metadata

**Corpus lineage:** seo-metadata/04-implementation-metadata.md,
seo-metadata/05-implementation-files-og-jsonld.md, seo-metadata/07-pitfalls-anti-patterns.md,
seo-metadata/08-version-lockin-seo-vercel-practitioner.md
**Knowledge baseline:** verified 2026-08-05 against Next.js 16.3.0 docs. Confirm any
config key against the installed package first — see `references/gating/capability-probe.md`.

CWV symptom-to-fix triage lives in `references/detect/measurement-regression-guardrails.md`
— this file does not duplicate it. This domain's release checklist is
`references/gating/seo-obligations.md`; every recipe below closes one or more of its items.

## Recipe index

| Recipe | Requires | Reversibility | Triggered by |
|---|---|---|---|
| Gold-standard root layout metadata | Metadata API, v13.2.0 | fully-reversible | Missing/incomplete root `metadata`, missing `metadataBase`, malformed title template |
| `generateMetadata` with async params + dedup | Next.js ≥16 (async signature); React `cache` ≥19 | fully-reversible | Sync `params` access on install ≥16; duplicate metadata/page data fetch |
| `generateMetadata` under Cache Components | `cacheComponents: true` | fully-reversible | `blocking-prerender-metadata-*` build error |
| Streaming metadata & `htmlLimitedBots` | v15.2.0 | config-only revert | Custom/narrowed `htmlLimitedBots`; untested bot path |
| `sitemap.ts` with locale alternates + `generateSitemaps` | v13.3.0; locales v14.2.0; async `id` v16.0.0 | fully-reversible | Missing sitemap; hand-written hreflang; >50,000 URLs unsplit |
| `robots.ts` + metadata-file proxy exclusions | v13.3.0; `other` v16.3.0 | fully-reversible | Missing `robots.ts`; OG route blocked; broad `proxy.ts` matcher |
| Dynamic OG image via `ImageResponse` | `next/og` since v14.0.0 | fully-reversible | Stale `next/server` import; missing route-specific card |
| JSON-LD component with sanitization | current recommended pattern | fully-reversible | Missing/unsanitized structured data |
| Existence-before-streaming ordering | v13.0.0 (`notFound`/`redirect`/`permanentRedirect`) | fully-reversible | Late `notFound()`/`redirect()` after stream start; soft-404 or broken embed |
| Cache Components shell — request-time reachability | `cacheComponents: true` | component-level-revert (data-source dependent) | A confirmed (bot-UA-probed) shell dependency only reachable at build time |

## Gold-standard root layout metadata — requires Metadata API (v13.2.0+)

**When to apply:** the root layout is missing `metadataBase`, has no title template/default
pair, no canonical, no `openGraph`/`twitter`/`robots` block, or `viewport`/`themeColor` is
still nested inside `metadata` instead of exported separately (deprecated location since v14).

```tsx
// app/layout.tsx — Next.js 16.3.0
import type { Metadata, Viewport } from 'next'

export const metadata: Metadata = {
  metadataBase: new URL('https://acme.com'),
  title: {
    default: 'Acme',
    template: '%s | Acme',
  },
  description: 'Acme builds fast, fluid, and crawlable Next.js apps.',
  alternates: {
    canonical: '/',
    languages: {
      'en-US': '/en-US',
      'de-DE': '/de-DE',
    },
  },
  openGraph: {
    title: 'Acme',
    description: 'Acme builds fast, fluid, and crawlable Next.js apps.',
    url: 'https://acme.com',
    siteName: 'Acme',
    images: [{ url: '/og-image.png', width: 1200, height: 630 }],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    site: '@acme',
    creator: '@acme',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-image-preview': 'large',
      'max-snippet': -1,
      'max-video-preview': -1,
    },
  },
}

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: 'cyan' },
    { media: '(prefers-color-scheme: dark)', color: 'black' },
  ],
  colorScheme: 'dark light',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
```

**Why each non-obvious line exists:**
- `metadataBase` resolves every relative canonical/OG/Twitter URL in the tree — omit it and a
  relative field either build-errors or resolves to a wrong absolute origin.
- `title.default` is **required** whenever `title.template` is set; the template applies only
  to descendant segments, never the segment that declares it — a page one level down without
  its own title inherits `default`, not the raw template string.
- `viewport`/`themeColor`/`colorScheme` are a **separate export**, not nested fields inside
  `metadata` — that nested location was deprecated in v14.
- `alternates.languages` here is the metadata half of hreflang; it must stay reciprocal with
  the sitemap half (see the sitemap recipe below) and with whatever locale-routing layer
  supplies the URL list (owned by `instant-i18n-locale-switching`).

**Verify after applying:**
- `curl -s https://your-deploy.vercel.app/ | grep -E 'canonical|og:|twitter:|theme-color'` —
  confirm `<link rel="canonical">`, `<link rel="alternate" hreflang>`, `og:*`, `twitter:*`,
  and `theme-color` all appear in the raw HTML.
- Run the deployed root URL through the [Rich Results Test](https://search.google.com/test/rich-results); confirm no metadata-related errors.
- `curl -A Twitterbot -s https://your-deploy.vercel.app/child-page | grep '<title'` — child
  page title must read `"<Page Title> | Acme"`.

**Lock-in / reversibility:** fully-reversible — every field is a config object; delete or
edit any key with no schema migration.

**Rollback:** revert the `metadata`/`viewport` export objects to their prior values (or
remove them); title/canonical/OG regressions take effect on next crawl, not immediately.

## `generateMetadata` with async params + dedup — requires Next.js ≥16 (async signature)

**When to apply:** the detect audit found sync `params`/`searchParams` access on an install
≥16, or `generateMetadata` and the page component each fetch the same record independently.

```ts
// app/lib/data.ts — Next.js 16.3.0
import { cache } from 'react'
import { db } from '@/app/lib/db'

// getPost will be used twice (metadata + page render), but execute only once
export const getPost = cache(async (slug: string) => {
  const res = await db.query.posts.findFirst({ where: eq(posts.slug, slug) })
  return res
})
```

```tsx
// app/blog/[slug]/page.tsx — Next.js 16.3.0
import type { Metadata, ResolvingMetadata } from 'next'
import { getPost } from '@/app/lib/data'
import { notFound } from 'next/navigation'

type Props = {
  params: Promise<{ slug: string }>
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}

export async function generateMetadata(
  { params }: Props,
  parent: ResolvingMetadata
): Promise<Metadata> {
  const { slug } = await params
  const post = await getPost(slug)

  if (!post) {
    // notFound() is allowed inside generateMetadata.
    notFound()
  }

  // extend, not replace, parent Open Graph images
  const previousImages = (await parent).openGraph?.images ?? []

  return {
    title: post.title,
    description: post.description,
    alternates: {
      canonical: `/blog/${slug}`,
    },
    openGraph: {
      title: post.title,
      description: post.description,
      images: [`/blog/${slug}/opengraph-image`, ...previousImages],
      type: 'article',
      publishedTime: post.publishedAt,
      authors: [post.authorName],
    },
  }
}

export default async function Page({ params }: Props) {
  const { slug } = await params
  const post = await getPost(slug)

  if (!post) {
    notFound()
  }

  return (
    <article>
      <h1>{post.title}</h1>
      <p>{post.content}</p>
    </article>
  )
}
```

**Why each non-obvious line exists:**
- `params`/`searchParams` are typed `Promise<...>` and must be `await`ed — this is a breaking
  signature change in Next.js 16, not a style preference. `searchParams` only exists in
  `page.js` segments, never layouts.
- `getPost` is wrapped once with `React.cache()` and imported by both `generateMetadata` and
  `Page` — same function, same request, executed once. `fetch` calls get this deduplication
  automatically across `generateMetadata`, `generateStaticParams`, layouts, pages, and Server
  Components; `React.cache()` is the equivalent for ORM/database calls.
- `(await parent).openGraph?.images` extends rather than replaces the parent's OG images —
  metadata objects **shallowly merge** across segments, so a child that sets `openGraph.title`
  without reading the parent's `images` silently erases them.
- `notFound()`/`redirect()` are explicitly supported inside `generateMetadata` — calling
  either here is documented, not a workaround.

**Practitioner caveat:** calling `redirect()`/`permanentRedirect()` inside `generateMetadata`
on a route that has already begun streaming can ship a page with missing social metadata,
because the redirect cannot rewrite already-sent headers. Prefer checking existence/redirect
targets before the route begins streaming (`proxy.ts` or `next.config.ts`) when the resource's
existence is knowable cheaply — see the existence-before-streaming recipe below.

**Verify after applying:**
- `curl -s https://your-deploy.vercel.app/blog/my-post | grep '<title'` shows the post title,
  not the fallback title.
- Confirm in server logs (or `NEXT_PRIVATE_DEBUG_CACHE=1`) that the underlying data function
  executes once per request, not twice.
- Deleted-slug case: request `/blog/does-not-exist`; confirm `not-found.tsx` renders and a
  `<meta name="robots" content="noindex">` tag is present in the HTML.

**Lock-in / reversibility:** fully-reversible — revert to a static `metadata` export if the
request-dependence is later removed, or unwrap `React.cache` back to a plain async function.

**Rollback:** restore sync destructuring only on an install <16 (never on ≥16 — that reverts
into a type/runtime error); remove the `cache()` wrapper and call the data function directly
at each site if dedup is no longer needed.

## `generateMetadata` under Cache Components — requires `cacheComponents: true`

**When to apply:** `next build` raises a `blocking-prerender-metadata-runtime` or
`blocking-prerender-metadata-dynamic` error, or `generateMetadata` needs runtime data
(`cookies()`, `headers()`) on a route whose static shell should otherwise prerender.

**Metadata that depends on external (not runtime) data — cache it:**

```tsx
// app/products/[id]/generateMetadata source — Next.js 16.3.0
export async function generateMetadata() {
  'use cache'
  const { title, description } = await db.query('site-metadata')
  return { title, description }
}
```

**Metadata that genuinely needs runtime data — add an explicit dynamic marker so the rest of
the shell still prerenders:**

```tsx
// app/products/[id]/page.tsx — Next.js 16.3.0
import { Suspense } from 'react'
import { cookies } from 'next/headers'
import { connection } from 'next/server'

export async function generateMetadata() {
  const token = (await cookies()).get('token')?.value
  // ... use token to fetch personalized metadata
  return { title: 'Personalized Title' }
}

const Connection = async () => {
  await connection()
  return null
}

async function DynamicMarker() {
  return (
    <Suspense>
      <Connection />
    </Suspense>
  )
}

export default function Page() {
  // DO NOT place await connection() here — doing so prevents the
  // <article> content from being included in the static shell
  return (
    <>
      <article>Static content</article>
      <DynamicMarker />
    </>
  )
}
```

**Why each non-obvious line exists:**
- `'use cache'` on the site-metadata `generateMetadata` moves it into the static shell — the
  same rule as any other cached function under Cache Components.
- `DynamicMarker`'s `<Suspense>`-wrapped `connection()` call isolates the dynamic marker from
  the page body — placing `await connection()` directly in `Page` would force the whole page
  dynamic, defeating the point of keeping `<article>` in the shell.

**Verify after applying:** with `cacheComponents: true`, run `next build` and confirm no
`blocking-prerender-metadata-runtime`/`-dynamic` error; if one appears, apply `'use cache'` or
the `DynamicMarker` pattern per the corresponding [error page](https://nextjs.org/docs/messages/blocking-prerender-metadata-runtime).

**Lock-in / reversibility:** fully-reversible — remove `'use cache'` or the `DynamicMarker`
wrapper to return to unconditional dynamic metadata resolution.

**Rollback:** delete the `'use cache'` directive, or delete `DynamicMarker` and its `Suspense`
wrapper; the page reverts to opting fully dynamic if `generateMetadata` reads runtime APIs.

## Streaming metadata & `htmlLimitedBots` — requires v15.2.0

**When to apply:** the detect audit found a custom `htmlLimitedBots` value that narrows the
framework default, or no bot-path test exists for a dynamically rendered route.

**Default: do nothing.** Streaming metadata is on by default for dynamic routes in 16.3 — no
code is required. HTML-limited bots (Twitterbot, Slackbot, Bingbot, Googlebot's
non-JS-rendering path, and the rest of the documented default list) already receive blocking
metadata in `<head>`; JS-capable clients receive an initial UI paint with metadata tags
appended to `<body>` once `generateMetadata` resolves.

**Only if a specific, reproduced crawler failure exists** — narrow the list while explicitly
retaining the default:

```ts
// next.config.ts — Next.js 16.3.0
import type { NextConfig } from 'next'

const config: NextConfig = {
  // Overrides — does not extend — the framework default. Never set this to add
  // one crawler without also reconstructing the default list here.
  htmlLimitedBots: /MySpecialBot|MyAnotherSpecialBot|SimpleCrawler/,
}

export default config
```

**Full disable (every request gets blocking metadata) — last resort, TTFB/LCP cost:**

```ts
// next.config.ts — Next.js 16.3.0
import type { NextConfig } from 'next'

const config: NextConfig = {
  htmlLimitedBots: /.*/,
}

export default config
```

**Why each non-obvious line exists:**
- `htmlLimitedBots` **replaces** the framework's default regex; it does not add to it. A
  narrow custom pattern that omits the built-in bots silently moves Twitter, Facebook,
  LinkedIn, Slack, and other social/search crawlers onto the streamed-body path they were
  never designed to receive.
- `/.*/`  is documented but explicitly discouraged: "Overriding `htmlLimitedBots` could lead
  to longer response times. Streaming metadata is an advanced feature, and the default should
  be sufficient for most cases."

**Verify after applying (do all three — a single curl is not sufficient):**

```bash
# 1. Plain browser UA — may receive streamed metadata (tags appended near </body>)
curl -s -A "Mozilla/5.0" https://your-deploy.vercel.app/blog/my-post | grep -A2 '<head'

# 2. Known HTML-limited bot — must receive full metadata in <head>
curl -s -A "Twitterbot" https://your-deploy.vercel.app/blog/my-post | grep -A5 '<head'

# 3. Googlebot — verified separately as receiving correctly-interpreted metadata
#    even though it is JS-capable
curl -s -A "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" \
  https://your-deploy.vercel.app/blog/my-post | grep -E 'og:title|<title'
```

Confirm case 2's `og:title`/`twitter:title`/canonical tags are inside `<head>`, not appended
near `<body>` — a regression here has shipped in stable Next.js before (metadata rendered in
`<body>` instead of `<head>`, and a resolve-mismatch when `/.*/ ` was combined with Cache
Components resume). Re-run this three-probe check after every Next.js upgrade.

**Lock-in / reversibility:** config-only revert — delete the `htmlLimitedBots` key to restore
the default list. Regression exposure may persist until cached bot responses (social
platforms cache OG scrapes) expire and are re-fetched.

**Rollback:** remove the `htmlLimitedBots` key entirely.

## `sitemap.ts` with locale alternates + `generateSitemaps` — requires v13.3.0; locales v14.2.0; async `id` v16.0.0

**When to apply:** `app/sitemap.ts` is missing on an indexable archetype, hreflang entries are
hand-written instead of derived from a locale list, or the site has more than 50,000 URLs
with no `generateSitemaps()` split.

```ts
// app/sitemap.ts — Next.js 16.3.0
import type { MetadataRoute } from 'next'

const BASE_URL = 'https://acme.com'
const LOCALES = ['en-US', 'de-DE'] as const

type Route = {
  path: string
  lastModified: Date
  changeFrequency: 'daily' | 'weekly' | 'monthly' | 'yearly'
  priority: number
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticRoutes: Route[] = [
    { path: '', lastModified: new Date('2026-08-05'), changeFrequency: 'weekly', priority: 1 },
    { path: '/about', lastModified: new Date('2026-08-05'), changeFrequency: 'monthly', priority: 0.7 },
  ]

  return staticRoutes.map((route) => ({
    url: `${BASE_URL}${route.path}`,
    lastModified: route.lastModified,
    changeFrequency: route.changeFrequency,
    priority: route.priority,
    alternates: {
      languages: Object.fromEntries(
        LOCALES.map((locale) => [locale, `${BASE_URL}/${locale}${route.path}`])
      ),
    },
  }))
}
```

**Above 50,000 URLs — split with `generateSitemaps()`; `id` is a Promise in v16:**

```ts
// app/product/sitemap.ts — Next.js 16.3.0
import type { MetadataRoute } from 'next'

export async function generateSitemaps() {
  return [{ id: 0 }, { id: 1 }, { id: 2 }]
}

export default async function sitemap(props: {
  id: Promise<string>
}): Promise<MetadataRoute.Sitemap> {
  const id = Number(await props.id)
  const start = id * 50_000
  const products = await getProducts({ offset: start, limit: 50_000 })

  return products.map((product) => ({
    url: `https://acme.com/product/${product.slug}`,
    lastModified: product.updatedAt,
  }))
}
```

**Why each non-obvious line exists:**
- `alternates.languages` inside each URL entry is the sitemap half of hreflang — it must stay
  reciprocal with the metadata half (`alternates.languages` in `generateMetadata`) and derived
  from the same `LOCALES`/locale-list constant so the two never drift independently.
- `id` is `Promise<string>` in v16 — a sync destructure (`props.id`) is a type error on that
  install. Google's limit is 50,000 URLs per sitemap; split before that ceiling, not after.

**Verify after applying:**
- Open `/sitemap.xml`; validate XML and confirm every canonical page appears exactly once.
- Check a localized entry contains `<xhtml:link ... hreflang="en-US">` and `de-DE`.
- For multiple sitemaps, request `/product/sitemap/0.xml` and confirm no file exceeds 50,000 URLs.

**Lock-in / reversibility:** fully-reversible — delete or edit the file; no schema/URL
migration involved (unlike the URLs themselves, which are).

**Rollback:** revert `app/sitemap.ts` to its prior contents, or remove it.

## `robots.ts` + metadata-file proxy exclusions — requires v13.3.0; `other` v16.3.0

**When to apply:** `app/robots.ts` is missing on an indexable archetype, the OG image route
is blocked from crawlers, or a broad `proxy.ts` matcher intercepts `/robots.txt`,
`/sitemap.xml`, icon, or OG URLs.

```ts
// app/robots.ts — Next.js 16.3.0
import type { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: ['/', '/api/og/'],
        disallow: ['/private/', '/api/internal/'],
      },
      {
        userAgent: ['Applebot', 'Bingbot'],
        allow: '/',
        disallow: '/private/',
      },
    ],
    sitemap: 'https://acme.com/sitemap.xml',
    host: 'https://acme.com',
  }
}
```

**Exclude metadata files from a broad `proxy.ts` matcher:**

```ts
// proxy.ts — Next.js 16.3.0 (excerpt)
export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml|opengraph-image|twitter-image).*)',
  ],
}
```

**Why each non-obvious line exists:**
- `allow: ['/', '/api/og/']` explicitly allows the OG image API route — Vercel recommends
  adding OG image route(s) to `Allow` so social providers can fetch them; without this, a
  broader `disallow` on `/api/` can silently block social preview generation.
- The `proxy.ts` matcher's negative lookahead excludes metadata-file routes by name — the
  metadata files index explicitly warns to configure the matcher this way when `proxy.ts` is
  in use, because these routes are cached Route Handlers that must stay directly reachable.

**Verify after applying:** request `/robots.txt`; confirm only intended private/API paths are
disallowed and `/api/og/` is reachable. Test the deployed OG URL with a social-bot UA.

**Lock-in / reversibility:** fully-reversible — edit or delete `robots.ts`; adjust or remove
the matcher exclusion.

**Rollback:** revert `robots.ts` to its prior rule set; revert the `proxy.ts` matcher.

## Dynamic OG image via `ImageResponse` — requires `next/og` since v14.0.0

**When to apply:** the detect audit found `ImageResponse` imported from `next/server` (stale
path), or a route-specific social card is needed and a static file cannot express it.

```tsx
// app/blog/[slug]/opengraph-image.tsx — Next.js 16.3.0
import { ImageResponse } from 'next/og'
import { getPost } from '@/app/lib/data'

export const alt = 'Acme article cover'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const post = await getPost(slug)

  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          background: '#0a0a0a',
          color: '#ffffff',
          padding: 72,
        }}
      >
        <div style={{ display: 'flex', fontSize: 32 }}>Acme</div>
        <div style={{ display: 'flex', fontSize: 72, fontWeight: 700 }}>{post.title}</div>
        <div style={{ display: 'flex', fontSize: 28 }}>{post.authorName}</div>
      </div>
    ),
    { ...size }
  )
}
```

**Why each non-obvious line exists:**
- `import { ImageResponse } from 'next/og'` — the import moved from `next/server` in v14.0.0;
  a stale `next/server` import is the exact detect finding this recipe answers.
- `params` is `Promise<{ slug: string }>` and awaited — the same v16 async-props rule as
  page-level `generateMetadata`.
- 500 KB is the hard bundle ceiling including JSX, CSS, fonts, images, and assets. Flexbox and
  a CSS subset are supported; `display: grid` is not. Fonts: `ttf`/`otf`/`woff` — prefer
  `ttf`/`otf` for parsing speed.
- The image is statically optimized (generated at build time and cached) by default unless it
  reads request-time APIs or uncached data — set the underlying data fetch's cache lifetime to
  match the page's, or the OG card and the page content go stale independently.

**Verify after applying:**
- Open `/blog/my-post/opengraph-image` directly; expect a 1200×630 PNG and HTTP 200.
- `curl -I` twice and inspect cache headers; on Vercel, confirm CDN caching rather than
  recomputation on every request.
- Run a social preview inspector against the page URL, not only the image URL directly.
- On stable 16.3.0, run one uncached `/_next/image` optimization then request the OG image
  again — a documented open issue reports an empty response after an optimizer cache miss;
  treat repeated verification (not a single request after startup) as the standard here.

**Lock-in / reversibility:** fully-reversible — swap back to a static file-based
`opengraph-image.png`/`.jpg`, or revert the import/JSX.

**Rollback:** change the import back only if genuinely targeting a pre-14 install (otherwise
`next/server` is simply wrong); delete the file to fall back to no OG image or a static one.

## JSON-LD component with sanitization — requires current recommended pattern

**When to apply:** structured data is missing, or is injected via `next/script` or a client
effect instead of a native server-rendered `<script>` tag, or uses raw `JSON.stringify` with
no sanitization.

```tsx
// app/components/json-ld.tsx — Next.js 16.3.0
import type { Thing, WithContext } from 'schema-dts'

type JsonLdProps<T extends Thing> = {
  data: WithContext<T>
}

export function JsonLd<T extends Thing>({ data }: JsonLdProps<T>) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify(data).replace(/</g, '\\u003c'),
      }}
    />
  )
}
```

```tsx
// app/products/[id]/page.tsx — Next.js 16.3.0
import type { Product, WithContext } from 'schema-dts'
import { JsonLd } from '@/app/components/json-ld'

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const product = await getProduct(id)

  const jsonLd: WithContext<Product> = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: product.name,
    image: product.image,
    description: product.description,
  }

  return (
    <section>
      <JsonLd data={jsonLd} />
      <h1>{product.name}</h1>
      <p>{product.description}</p>
    </section>
  )
}
```

**Why each non-obvious line exists:**
- A native `<script type="application/ld+json">` from a Server Component is the current
  recommended pattern — JSON-LD is structured data, not executable code, so `next/script`
  (which manages script *execution* strategy) is the wrong tool.
- `.replace(/</g, '\\u003c')` is the documented minimum sanitization — plain `JSON.stringify`
  does not sanitize malicious strings used in XSS injection; replacing `<` with its Unicode
  escape blocks the most direct script-breakout vector. Follow project-approved sanitization
  or a maintained serializer for untrusted content beyond this floor.
- The `jsonLd` object's fields must match visible page content — schema validators and search
  engines penalize structured data that claims facts not present in the rendered page.

**Verify after applying:**
- View source and confirm the JSON-LD appears in server HTML (not only in the hydrated DOM).
- Test a payload containing `<script>` and confirm the serialized text contains
  `\\u003cscript`, never a literal opening tag.
- Validate the deployed page in [Google Rich Results Test](https://search.google.com/test/rich-results) and [Schema Markup Validator](https://validator.schema.org/).

**Lock-in / reversibility:** fully-reversible — delete the `<JsonLd>` component usage; rich
result eligibility may take time to disappear after the next recrawl, but nothing breaks.

**Rollback:** remove the `<JsonLd data={...} />` call site; delete the schema object.

## Existence-before-streaming ordering — requires v13.0.0 (`notFound`/`redirect`/`permanentRedirect`)

**When to apply:** the detect audit found `notFound()` or `redirect()`/`permanentRedirect()`
called from a component nested below a `<Suspense>` boundary on a route where a literal HTTP
status matters (link-checker tooling, compliance requirements, or a durable URL migration).

**The constraint, stated once:** once streaming sends response headers, the HTTP status code
cannot change. A `notFound()` that fires after the stream has started still injects
`<meta name="robots" content="noindex">` — search engines correctly skip indexing it — but the
literal status stays 200, which some non-search tooling (Search Console's 404 tracker, link
checkers) reports as a soft 404. A `redirect()` fired after streaming starts becomes an
in-document mechanism rather than a real 307/308, which can drop social embeds entirely
(observed: Discord shows no embed for a page whose redirect fired mid-stream).

```tsx
// app/blog/[slug]/page.tsx — Next.js 16.3.0
import { notFound } from 'next/navigation'
import { getPost } from '@/app/lib/data'

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  // Check existence BEFORE any Suspense boundary or slow child renders —
  // this keeps notFound()'s effect inside the pre-stream response.
  const post = await getPost(slug)
  if (!post) {
    notFound()
  }

  return (
    <article>
      <h1>{post.title}</h1>
      <p>{post.content}</p>
    </article>
  )
}
```

**For a durable URL migration where the true redirect must be a real HTTP 307/308, not an
in-render `redirect()` call**, perform it before rendering — in `next.config.ts` (`redirects`
key) or `proxy.ts` — rather than deep inside a component that may render after streaming
begins. That mechanism belongs to `vercel-platform-deployment`; this domain's obligation is
only to avoid triggering the pitfall from inside `generateMetadata`/`page.tsx`.

**Why each non-obvious line exists:**
- `await getPost(slug)` and its `notFound()` check happen in the top-level `Page` function,
  before any `<Suspense>`-wrapped child — this is what keeps the check "before streaming
  starts" in the documented sense.
- Redirects triggered from inside `generateMetadata` are explicitly supported by the API but
  carry the same streaming-order caveat as `notFound()` — prefer resolving the redirect target
  before the route begins rendering when the resource's existence is cheap to check early.

**Verify after applying:**
- `curl -i https://your-deploy.vercel.app/blog/does-not-exist` — confirm the response and
  whether `noindex` is present; for routes requiring a literal 404, confirm the status code
  itself, not just the meta tag.
- `curl -i -A Googlebot https://your-deploy.vercel.app/blog/does-not-exist` — confirm parity
  with the browser-UA probe.
- For a redirect: `curl -i https://your-deploy.vercel.app/old-path` — confirm a real 307/308
  status and `Location` header, not an HTML body containing a meta-refresh.

**Lock-in / reversibility:** fully-reversible — moving the existence check earlier in the
component tree is a pure code reorder; no schema or URL change.

**Rollback:** move the `notFound()`/`redirect()` call back to wherever it previously lived;
this reintroduces the soft-404/broken-embed risk, which is the reason to avoid rolling back
without cause.

## Cache Components shell — request-time reachability — requires `cacheComponents: true`

**When to apply:** the detect audit filed an `informational` Cache Components bot-path
candidate (a build-time-only read inside a static-shell scope), and the live bot-UA probe
(`curl -A Googlebot ...` against the deployed origin) confirmed the shell content fails or is
incomplete for the bot request while the human-facing shell renders fine. Mechanism recap: see
`references/detect/seo-metadata.md`'s headline section and `references/gating/seo-obligations.md`.

```tsx
// app/products/page.tsx — Next.js 16.3.0
// BEFORE: a build-time-only local catalog read backs the shell — works during
// prerender, fails when a bot forces a full request-time re-render.
// import catalog from '../../data/catalog.json'

// AFTER: the same data is reachable through a request-time-capable path (a
// 'use cache' wrapped fetch, or a database/API call), so both the prerendered
// shell AND a bot's request-time re-render can resolve it.
import { cacheLife, cacheTag } from 'next/cache'

async function getCatalog() {
  'use cache'
  cacheTag('catalog')
  cacheLife('hours')
  const res = await fetch('https://api.acme.com/catalog')
  return res.json()
}

export default async function ProductsPage() {
  const catalog = await getCatalog()
  return (
    <ul>
      {catalog.map((item: { id: string; name: string }) => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  )
}
```

**Why each non-obvious line exists:**
- Replacing a local, build-time-only import with a `'use cache'`-wrapped fetch means the same
  function that supplies the prerendered shell can also resolve correctly when a bot forces a
  full request-time render — the data source itself becomes reachable at both times, not just
  one.
- This recipe is intentionally general: the specific fix depends entirely on what the
  build-time-only dependency actually is (a file, an env var, a build script's output). The
  invariant is the one to hold: whatever data contributes to crawl-relevant shell content must
  resolve when fetched again outside the build process, not only during it.

**Verify after applying (this is the release gate — always test the deployed origin, never
localhost or a preview inferred from source):**

```bash
# Human/browser path
curl -s https://your-deploy.vercel.app/products | grep -E '<h1|<li'

# Bot path — must independently succeed and contain the same crawl-relevant content
curl -s -A "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" \
  https://your-deploy.vercel.app/products | grep -E '<h1|<li'
```

Both responses must contain the same crawl-relevant headings/content. A browser-path success
with a bot-path error or truncation is exactly the regression this recipe exists to close.

**Lock-in / reversibility:** component-level-revert — the reversibility depends on what the
original data source was; reverting to a build-time-only source reintroduces the exact failure
mode this recipe fixes, so treat rollback as a deliberate regression, not a neutral undo.

**Rollback:** restore the original build-time-only import/data source; re-run the two-probe
verification above to confirm the regression is reproduced (expected) before treating rollback
as complete.

## Ordering within this domain

1. **Establish `metadataBase` and the root layout metadata block first** — every other
   recipe in this domain (canonical, OG, sitemap alternates) assumes a resolvable base origin.
2. **Fix async `params`/`searchParams` and dedup before adding new dynamic metadata** — an
   install ≥16 with sync access is a build/type error that blocks everything downstream of it.
3. **Add sitemap/robots and validate index scope** before customizing `htmlLimitedBots` or
   adding JSON-LD — establish the baseline crawl surface first.
4. **Test the default `htmlLimitedBots` path (three-UA probe) before considering an
   override** — most repos need no change here at all.
5. **Resolve the Cache Components shell-reachability check last, and only after
   `rendering-strategy-caching` confirms `cacheComponents: true`** — this recipe is
   meaningless without that prerequisite domain already enabled.

## Conflicts to watch

- **A View Transition layered onto a route with an unresolved waterfall or missing-Suspense
  finding is not cache-hot** — `references/gating/conflicts.md` §1. Sequence
  `data-fetching-patterns`/`rendering-strategy-caching` fixes before any
  `page-transitions-view-transitions` work on the same route.
- **`<html lang>` under a locale-routing layer is owned by `instant-i18n-locale-switching`**
  — do not duplicate hreflang/canonical fixes here once that domain's `[locale]` segment
  pattern is in place; keep this domain's root-layout recipe scoped to the single-locale or
  no-i18n case.
- **Durable canonical/URL changes and their 307/308 redirects are a `migration-required`
  one-way door** (`references/gating/lockin-reversibility.md` #2, #8) — never auto-apply a
  canonical/URL change from this domain; write it as `blocked-needs-human` per
  `references/workflow/safety-rails.md` rail 1.
- **Cache Components shell reachability depends on `rendering-strategy-caching`'s
  `cacheComponents` state** — if that domain reports the flag absent, downgrade every finding
  in this domain's Cache Components section to NOT APPLICABLE.
