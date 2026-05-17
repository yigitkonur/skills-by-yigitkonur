# Data Fetching Overview

How TinaCMS exposes content to your app — the auto-generated GraphQL clients, custom queries, and the choice between client and databaseClient.

## The two clients

| Client | When | Path |
|---|---|---|
| `client` | Always | `tina/__generated__/client` |
| `databaseClient` | Self-hosted only | `tina/__generated__/databaseClient` |

```tsx
// TinaCloud or self-hosted (HTTP via /api/tina/gql)
import { client } from '@/tina/__generated__/client'
const result = await client.queries.page({ relativePath: 'home.md' })

// Self-hosted only — direct DB access (no HTTP)
import databaseClient from '@/tina/__generated__/databaseClient'
const result = await databaseClient.request({ query, variables })
```

For most app code, use `client`. Use `databaseClient` only inside the self-hosted backend route handler when you want to bypass HTTP.

## What each client provides

### `client.queries.<collection>(args, options)`

Auto-generated method per collection:

```tsx
// Single document by relative path:
const result = await client.queries.post({ relativePath: 'my-post.md' })
// result.data.post — the document
// result.query    — the query string (for useTina)
// result.variables — the vars object (for useTina)

// List of documents (collection connection):
const list = await client.queries.postConnection({
  filter: { draft: { eq: false } },
  sort: 'date',
  first: 10,
})
// list.data.postConnection.edges
// list.data.postConnection.pageInfo
```

### Custom queries via `client.request`

For custom GraphQL not covered by the auto-generated methods:

```tsx
const result = await client.request({
  query: `
    query MyCustomQuery($slug: String!) {
      page(relativePath: $slug) {
        title
        seo { metaTitle }
      }
    }
  `,
  variables: { slug: 'home.md' },
})
```

Mostly you don't need this — auto-generated queries cover 95% of cases.

## Where to call client

| Context | Use |
|---|---|
| Server Component | `client.queries.X(...)` |
| `generateStaticParams` / `generateMetadata` | `client.queries.X(...)` |
| Route handler (`app/api/.../route.ts`) | `client.queries.X(...)` |
| Client Component | Avoid — fetch in parent Server Component, pass via props |
| Inside the self-hosted backend route | `databaseClient.request(...)` |

Client Components can technically call `client`, but it adds bundle weight and forces server roundtrips. Fetch in Server Components and pass props down.

## With `useTina`

The Server-Component pattern:

```tsx
// Server Component
const result = await client.queries.page({ relativePath: 'home.md' })

return (
  <PageClient
    query={result.query}
    variables={result.variables}
    data={result.data}
  />
)

// Client Component
'use client'
import { useTina } from 'tinacms/dist/react'

export default function PageClient(props) {
  const { data } = useTina(props)
  // ...
}
```

Pass all three of `query`, `variables`, `data` through as props.

## Fetch options

```tsx
const result = await client.queries.page(
  { relativePath: 'home.md' },
  { fetchOptions: { next: { revalidate: 60 } } },
)
```

The second argument is a Next.js fetch options object. Pass `revalidate`, `cache`, `tags` as needed.

See `references/rendering/11-vercel-cache-caveat.md`.

## Reading order

| File | When |
|---|---|
| `references/data-fetching/02-generated-client.md` | Auto-generated client API surface |
| `references/data-fetching/03-custom-queries.md` | Custom queries via `tina/queries/` |
| `references/data-fetching/04-fetch-options-revalidate.md` | Cache control via fetchOptions |
| `references/data-fetching/05-graphql-cli.md` | CLI commands for graphql introspection |

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Calling `client` from a Client Component | Adds bundle weight, slows page | Move to Server Component |
| Forgot `await` | Promise leaks | Always `await client.queries.X(...)` |
| Wrong relativePath | Document not found | Match the file path within the collection (e.g. `'home.md'`, not `'home'`) |
| Using `databaseClient` in app code (TinaCloud project) | TinaCloud doesn't generate this client | Use `client` |
| Forgot `fetchOptions` for production | Stale Vercel cache | Add `revalidate` |
