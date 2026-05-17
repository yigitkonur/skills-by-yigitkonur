# Pages Router Pattern (legacy)

The Next.js Pages Router pattern. **Default is App Router** (`references/rendering/01-app-router-pattern.md`); use Pages Router only when migrating an existing project that can't move to App Router yet.

## The pattern

```tsx
// pages/posts/[slug].tsx
import { client } from '../../tina/__generated__/client'
import { useTina } from 'tinacms/dist/react'
import type { GetStaticPaths, GetStaticProps } from 'next'

export default function PostPage(props: any) {
  const { data } = useTina({
    query: props.query,
    variables: props.variables,
    data: props.data,
  })

  return (
    <article>
      <h1>{data.post.title}</h1>
      <p>{data.post.excerpt}</p>
    </article>
  )
}

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const response = await client.queries.post({
    relativePath: `${params?.slug}.md`,
  })

  return {
    props: {
      data: response.data,
      query: response.query,
      variables: response.variables,
    },
    revalidate: 60,  // ISR — refresh every minute
  }
}

export const getStaticPaths: GetStaticPaths = async () => {
  const response = await client.queries.postConnection()
  const paths =
    response.data.postConnection.edges?.map((edge) => ({
      params: { slug: edge?.node?._sys.filename ?? '' },
    })) ?? []

  return { paths, fallback: 'blocking' }
}
```

## Differences from App Router

| Concern | App Router | Pages Router |
|---|---|---|
| Server/client split | Two files | Single file (uses `useTina` directly in the page component) |
| Data fetching | `await client.queries.X` in Server Component | `getStaticProps` |
| Static generation | `generateStaticParams` | `getStaticPaths` |
| Dynamic params | `Promise<{ slug }>` | `{ params }` (sync) |
| Caching | `"use cache"` directive | `revalidate` in `getStaticProps` |
| Metadata | `generateMetadata()` export | `<Head>` in component |

## `useTina` in Pages Router

Unlike App Router, **Pages Router pages already run as Client Components implicitly** (the page component is a Client Component). So `useTina()` works directly without a separate file.

## Admin route

```tsx
// pages/admin/[[...index]].tsx
'use client'

export default function Admin() {
  return null  // The TinaCMS init script handles redirecting/rendering
}
```

Or simply visit `/admin/index.html` directly — the static admin SPA is served.

## When to migrate to App Router

The official TinaCMS recommendation as of 2026 is App Router. Pages Router still works but:

- Future TinaCMS features (e.g. expanded MDX templates) target App Router first
- Next.js 16+ patterns (`proxy.ts`, async params, `cacheComponents`) are App Router-native
- Most TinaCMS examples show App Router

**Migrate when:**

- Starting a new project (use App Router)
- Existing project ready for the App Router migration anyway
- You want `cacheComponents` / async streaming metadata

**Stay on Pages Router when:**

- You have a large legacy app and migration is too risky right now
- You're using Next.js < 13 (App Router not available)

## Common Pages Router mistakes

| Mistake | Fix |
|---|---|
| Forgot `getStaticPaths` for dynamic routes | Add it; return `{ paths, fallback }` |
| `getStaticProps` returns wrong shape | Must be `{ props: { data, query, variables } }` |
| Missing `revalidate` | Content stays stale until rebuild | Add `revalidate: 60` for ISR |
| Calling `useTina` outside the page component | Hook violation | Move to top-level page component |
| Trying to use `cacheComponents` | Not supported in Pages Router | Migrate to App Router |
