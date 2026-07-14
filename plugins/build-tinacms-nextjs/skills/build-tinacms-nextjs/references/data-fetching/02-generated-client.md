# The Generated Client

Every collection in your schema gets two methods on `client.queries`: a single-doc fetcher and a list fetcher.

## Single-doc fetcher

```tsx
const result = await client.queries.<collectionName>({ relativePath })
// result.data.<collectionName> — the document
```

Examples:

```tsx
const result = await client.queries.page({ relativePath: 'home.md' })
console.log(result.data.page.title)

const result = await client.queries.post({ relativePath: '2026-05-08-launch.md' })
console.log(result.data.post.body)

const result = await client.queries.global({ relativePath: 'global.json' })
console.log(result.data.global.siteName)
```

`relativePath` is the path within the collection's `path` config. For a collection at `content/posts/`, the doc at `content/posts/launch.md` has `relativePath: 'launch.md'`.

For nested paths:

```tsx
const result = await client.queries.doc({ relativePath: 'guide/installation.md' })
```

## List fetcher (Connection)

```tsx
const result = await client.queries.<collectionName>Connection({ first?, last?, after?, before?, filter?, sort? })
// result.data.<collectionName>Connection.edges → array
// result.data.<collectionName>Connection.pageInfo → cursor info
```

```tsx
const list = await client.queries.postConnection({
  filter: { draft: { eq: false } },
  sort: 'date',
  first: 10,
})

list.data.postConnection.edges?.forEach((edge) => {
  console.log(edge?.node?.title)
})
```

See `references/graphql/03-query-documents.md` for filter/sort/pagination details.

## Result shape

Every fetch returns:

```typescript
{
  data: <documentOrConnection>,
  query: string,                    // the GraphQL query string
  variables: Record<string, unknown>,  // the variables object
}
```

`query` and `variables` are needed for `useTina(props)` — pass them through.

## Type safety

The generated client is fully typed against your schema. In TypeScript:

```tsx
const result = await client.queries.post({ relativePath: 'launch.md' })
// result.data.post.<field> — autocompleted from your schema
```

Generated types live at `tina/__generated__/types.ts`:

```tsx
import type { PostQuery, PostConnectionQuery } from '@/tina/__generated__/types'
```

## Multi-shape collections (templates)

For collections with `templates: [...]`, the response is a union. Narrow with `__typename`:

```tsx
const result = await client.queries.page({ relativePath: 'home.md' })

if (result.data.page.__typename === 'PageLanding') {
  // landing-page fields
} else if (result.data.page.__typename === 'PageLegal') {
  // legal-page fields
}
```

## Reference fields are inlined

When a doc has a `reference` field, the response includes the resolved document:

```tsx
const result = await client.queries.post({ relativePath: 'launch.md' })
console.log(result.data.post.author.name)  // resolved from author collection
console.log(result.data.post.author.avatar)
```

For unset references, the field is `null` — defensive null-checks recommended.

## Fetch options

```tsx
const result = await client.queries.page(
  { relativePath: 'home.md' },
  {
    fetchOptions: {
      next: { revalidate: 60, tags: ['page-home'] },
    },
  },
)
```

See `references/data-fetching/04-fetch-options-revalidate.md`.

## Custom queries

For custom GraphQL beyond auto-generated:

```tsx
const result = await client.request({
  query: `query Custom { ... }`,
  variables: { ... },
})
```

See `references/data-fetching/03-custom-queries.md`.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `client.queries.page('home.md')` (string arg) | Type error | Pass object: `{ relativePath: 'home.md' }` |
| Forgot `.md` extension | "Document not found" | Include extension in relativePath |
| Used `client.queries.posts` (plural) | No method | Use the collection's `name` exactly: `client.queries.post` |
| Used `postsConnection` | Type error | Auto-pluralization: collection `post` → `postConnection` |
| Tried to use generated client without `tinacms build` | Module not found | Run build to generate the client |
