# `generateStaticParams`

Pre-render every page at build time. Faster than runtime SSR for content that doesn't change often.

## Basic pattern

```tsx
// app/[slug]/page.tsx
import { client } from '@/tina/__generated__/client'

export async function generateStaticParams() {
  const result = await client.queries.pageConnection()
  return (
    result.data.pageConnection.edges?.map((edge) => ({
      slug: edge?.node?._sys.filename ?? '',
    })) ?? []
  )
}
```

Next.js calls this at build time, generates static HTML for each returned param object.

## Nested paths via `breadcrumbs`

For paths like `/docs/guide/installation`:

```tsx
// app/docs/[...path]/page.tsx
export async function generateStaticParams() {
  const result = await client.queries.docConnection()
  return (
    result.data.docConnection.edges?.map((edge) => ({
      path: edge?.node?._sys.breadcrumbs ?? [],  // array becomes /docs/guide/installation
    })) ?? []
  )
}
```

`breadcrumbs` reflects the file's nested folder structure. `content/docs/guide/installation.md` → `['guide', 'installation']`.

## Filtering at build

Skip drafts in production builds:

```tsx
export async function generateStaticParams() {
  const result = await client.queries.postConnection({
    filter: process.env.NODE_ENV === 'production' ? { draft: { eq: false } } : undefined,
  })
  return (
    result.data.postConnection.edges?.map((edge) => ({
      slug: edge?.node?._sys.filename ?? '',
    })) ?? []
  )
}
```

In dev, drafts appear; in production, they don't.

## `dynamicParams` config

```tsx
export const dynamicParams = false  // 404 for slugs not returned by generateStaticParams
// OR
export const dynamicParams = true   // generate on-demand for unknown slugs (SSR fallback)
```

For TinaCMS sites, `dynamicParams = true` is usually right — content can be added between deploys, and you want it served immediately (with eventual rebuild via deploy hook).

## Pagination considerations

`pageConnection` returns up to 50 results by default. For sites with > 50 pages:

```tsx
export async function generateStaticParams() {
  let allEdges: any[] = []
  let cursor: string | null = null

  do {
    const result = await client.queries.pageConnection({
      first: 50,
      after: cursor,
    })
    const edges = result.data.pageConnection.edges ?? []
    allEdges = [...allEdges, ...edges]
    cursor = result.data.pageConnection.pageInfo.hasNextPage
      ? result.data.pageConnection.pageInfo.endCursor
      : null
  } while (cursor)

  return allEdges.map((edge) => ({ slug: edge?.node?._sys.filename ?? '' }))
}
```

## Performance

`generateStaticParams` runs once at build time. For sites with 1000+ pages, this can take a minute. Acceptable for most sites — use ISR (`revalidate`) if you can't tolerate the build time.

## Common patterns

### Combined sitemap + static params

```tsx
async function getAllPages() {
  const result = await client.queries.pageConnection()
  return result.data.pageConnection.edges?.map((edge) => edge?.node).filter(Boolean) ?? []
}

// Use in generateStaticParams:
export async function generateStaticParams() {
  const pages = await getAllPages()
  return pages.map((page) => ({ slug: page._sys.filename }))
}

// Use in app/sitemap.ts:
export default async function sitemap() {
  const pages = await getAllPages()
  return pages.map((page) => ({ url: `https://example.com/${page._sys.filename}` }))
}
```

DRY — fetch once, use for both.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `?? []` defaults | Crash if connection returns null | Always default to `[]` |
| Returned strings instead of `{ slug }` objects | Type error | Wrap each in object: `{ slug: '...' }` |
| Used `params: { slug }` instead of `{ slug }` | Wrong shape — `params` is the wrapping key in fetch handlers, not generateStaticParams | Just `{ slug: '...' }` |
| Generated params for drafts in production | Drafts publicly accessible | Filter `draft: { eq: false }` in production |
| Missed pagination, only got first 50 | Pages 51+ return 404 | Implement cursor pagination |
