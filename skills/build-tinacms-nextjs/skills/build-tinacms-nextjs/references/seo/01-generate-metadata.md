# `generateMetadata`

Per-page metadata for Next.js App Router. Streams in Next.js 16 (doesn't block render).

## Basic

```typescript
import type { Metadata } from 'next'
import { client } from '@/tina/__generated__/client'

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const { slug } = await params
  const result = await client.queries.page({ relativePath: `${slug}.md` })
  const page = result.data.page

  return {
    title: page.seo?.metaTitle || page.title,
    description: page.seo?.metaDescription || 'A page',
  }
}
```

## Full pattern with global fallbacks

```typescript
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  const [pageResult, globalResult] = await Promise.all([
    client.queries.page({ relativePath: `${slug}.md` }),
    client.queries.global({ relativePath: 'global.json' }),
  ])
  const page = pageResult.data.page
  const global = globalResult.data.global

  const title = page.seo?.metaTitle || page.title
  const description = page.seo?.metaDescription || global.siteDescription
  const url = `${global.siteUrl}/${slug === 'home' ? '' : slug}`
  const ogImage = page.seo?.ogImage || global.defaultOgImage

  return {
    title: global.titleTemplate?.replace('%s', title) || title,
    description,
    openGraph: {
      title,
      description,
      url,
      siteName: global.siteName,
      type: 'website',
      locale: global.locale || 'en_US',
      images: ogImage ? [{ url: ogImage, width: 1200, height: 630, alt: title }] : [],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: ogImage ? [ogImage] : [],
      site: global.twitterHandle,
    },
    robots: {
      index: !page.seo?.noIndex,
      follow: !page.seo?.noFollow,
    },
    alternates: {
      canonical: page.seo?.canonicalUrl || url,
    },
  }
}
```

## Async-streaming in Next.js 16

In Next.js 16, `generateMetadata` is **streamed** — it doesn't block initial page rendering. The HTML response starts streaming, and metadata appears in the `<head>` as it resolves. This means you can do TinaCloud calls inside `generateMetadata` without slowing TTFB.

## Reusing data between page and metadata

If both `page()` and `generateMetadata()` fetch the same content, request dedupes via Next.js fetch cache:

```typescript
async function getPage(slug: string) {
  const result = await client.queries.page(
    { relativePath: `${slug}.md` },
    { fetchOptions: { next: { revalidate: 60 } } },
  )
  return result.data.page
}

// generateMetadata + Page component both call getPage()
// Next.js dedupes the underlying fetch
```

## Metadata for a list page

```typescript
export async function generateMetadata(): Promise<Metadata> {
  const global = (await client.queries.global({ relativePath: 'global.json' })).data.global
  return {
    title: `Blog | ${global.siteName}`,
    description: 'All posts.',
    openGraph: { /* ... */ },
  }
}
```

## Static metadata (no fetch)

For pages where metadata doesn't need TinaCMS:

```typescript
export const metadata: Metadata = {
  title: 'About',
  description: 'About us',
}
```

Static metadata is lighter — use when content doesn't drive metadata.

## See also

- `references/seo/02-description-waterfall.md` — fallback chain for descriptions
- `references/seo/03-og-image-waterfall.md` — fallback chain for OG images
- `references/seo/04-json-ld-structured-data.md` — Schema.org markup
- `references/seo/05-dynamic-og-images.md` — generated OG images via `next/og`
- `references/seo/06-sitemap-and-robots.md` — sitemap + robots
- `references/seo/07-rss-feed.md` — RSS feed

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Sync `params` access | Build error | `await params` |
| Empty description | SEO score drops | Implement waterfall |
| No `og:image` | Social shares look bad | Implement OG image waterfall + dynamic generation |
| `canonical` missing | Duplicate-content penalty | Set `alternates.canonical` |
| Forgot `noIndex` for drafts | Drafts appear in search | Wire `seo.noIndex` to `robots.index` |
