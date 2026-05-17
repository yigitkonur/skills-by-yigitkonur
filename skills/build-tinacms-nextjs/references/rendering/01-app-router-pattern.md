# App Router Pattern

The canonical Next.js App Router rendering pattern for TinaCMS. App Router is the **⭐ Recommended** path; Pages Router is a legacy fallback (`references/rendering/02-pages-router-pattern.md`).

## The two-component split

Visual editing requires this. Server Component fetches data; Client Component subscribes to live edits via `useTina()`.

```
app/[slug]/
├── page.tsx        ← Server Component (fetches + delegates)
└── client-page.tsx ← Client Component (uses useTina + renders)
```

## Server Component

```tsx
// app/[slug]/page.tsx
import { client } from '@/tina/__generated__/client'
import PageClient from './client-page'

export default async function Page({
  params,
}: {
  params: Promise<{ slug: string }>  // Next.js 16: params is a Promise
}) {
  const { slug } = await params

  const result = await client.queries.page(
    { relativePath: `${slug}.md` },
    { fetchOptions: { next: { revalidate: 60 } } },
  )

  return (
    <PageClient
      query={result.query}
      variables={result.variables}
      data={result.data}
    />
  )
}
```

**Key points:**

- `params` is a **Promise** in Next.js 16 — `await params` is mandatory
- Pass all three of `query`, `variables`, `data` to the client component
- The `fetchOptions: { next: { revalidate: 60 } }` works around Vercel's aggressive caching — see `references/rendering/11-vercel-cache-caveat.md`

## Client Component

```tsx
// app/[slug]/client-page.tsx
'use client'

import { useTina, tinaField } from 'tinacms/dist/react'
import { BlockRenderer } from '@/components/blocks/BlockRenderer'

type Props = {
  query: string
  variables: Record<string, unknown>
  data: any  // type with the generated PageQuery type
}

export default function PageClient(props: Props) {
  const { data } = useTina(props)
  const page = data.page

  return (
    <main>
      <h1 data-tina-field={tinaField(page, 'title')}>{page.title}</h1>
      {page.blocks && <BlockRenderer blocks={page.blocks} />}
    </main>
  )
}
```

**Key points:**

- `"use client"` is mandatory — `useTina()` requires it
- All three of `query`, `variables`, `data` must be passed in
- `tinaField()` attached to **DOM elements**, not React component wrappers
- `useTina` returns `props.data` unchanged in production (zero overhead)
- In edit mode (Draft Mode active), `useTina` subscribes to GraphQL updates

## Static generation

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

For nested paths use `_sys.breadcrumbs`. See `references/rendering/09-static-params.md`.

## generateMetadata

```tsx
import type { Metadata } from 'next'

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
    // ...
  }
}
```

See `references/seo/01-generate-metadata.md` for the full pattern.

## Multiple-collection routing

For routing to different collections at different paths:

```
app/
├── [slug]/page.tsx          ← collection: page
├── blog/[slug]/page.tsx     ← collection: post
└── docs/[...path]/page.tsx  ← collection: doc (nested paths)
```

Each route fetches from its own collection.

## Caching with `"use cache"`

```tsx
import { cacheLife } from 'next/cache'

async function getPage(slug: string) {
  'use cache'
  cacheLife('hours')
  const { data } = await client.queries.page({ relativePath: `${slug}.md` })
  return data
}
```

Requires `cacheComponents: true` in `next.config.ts`. See `references/rendering/10-caching-use-cache.md`.

## Rendering MDX content

```tsx
// In the Client Component:
import { TinaMarkdown } from 'tinacms/dist/rich-text'
import { mdxComponents } from '@/components/MdxComponents'

<TinaMarkdown content={data.post.body} components={mdxComponents} />
```

See `references/rendering/04-tinamarkdown.md` and `references/rendering/05-mdx-component-mapping.md`.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `useTina()` in Server Component | "Hooks can only be used in Client Components" | Wrap in `"use client"` Client Component |
| Sync `params` access | Build error in Next.js 16 | `await params` |
| Missing one of `query`/`variables`/`data` | Edit-mode subscription doesn't fire | Pass all three |
| `data-tina-field` on `<MyComponent>` (not DOM) | Click-to-edit ignores it | Place on DOM element |
| Forgot `next: { revalidate: 60 }` | Stale content on Vercel for hours | Add to fetchOptions |
| Calling `useTina` without `"use client"` | Build fails | Add directive |
