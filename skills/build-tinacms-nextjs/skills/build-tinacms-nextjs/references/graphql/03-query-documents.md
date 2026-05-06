# Query Multiple Documents (Connection)

Fetch a list of documents from a collection. Supports filtering, sorting, and pagination.

## Basic

```tsx
const result = await client.queries.postConnection()
result.data.postConnection.edges?.forEach((edge) => {
  console.log(edge?.node?.title)
})
```

## With filter / sort / pagination

```tsx
const result = await client.queries.postConnection({
  filter: { draft: { eq: false } },
  sort: 'date',
  first: 10,
})
```

| Argument | Purpose |
|---|---|
| `filter` | Filter the result set — see `references/graphql/04-filter-documents.md` |
| `sort` | Sort by a field — see `references/graphql/05-sorting.md` |
| `first` | First N results (forward pagination) |
| `last` | Last N results (reverse pagination) |
| `after` | Cursor — start after this document |
| `before` | Cursor — end before this document |

## Result shape

```typescript
{
  data: {
    postConnection: {
      edges: Array<{
        cursor: string,
        node: <Document>,
      }>,
      pageInfo: {
        hasNextPage: boolean,
        hasPreviousPage: boolean,
        startCursor: string,
        endCursor: string,
      },
      totalCount: number,
    },
  },
  query: string,
  variables: {...},
}
```

## Iterating

```tsx
const result = await client.queries.postConnection({ first: 10 })
const posts = result.data.postConnection.edges?.map((edge) => edge?.node).filter(Boolean) ?? []

posts.forEach((post) => {
  console.log(post.title, post.date)
})
```

## With pagination cursor

```tsx
let cursor: string | null = null
const allPosts: any[] = []

while (true) {
  const result = await client.queries.postConnection({
    first: 50,
    after: cursor,
  })
  const edges = result.data.postConnection.edges ?? []
  allPosts.push(...edges.map((edge) => edge?.node).filter(Boolean))

  if (!result.data.postConnection.pageInfo.hasNextPage) break
  cursor = result.data.postConnection.pageInfo.endCursor
}
```

For large collections, paginate. See `references/graphql/06-pagination.md`.

## Cross-collection queries

There's no first-class join. Fetch separately and combine in JS:

```tsx
const [posts, authors] = await Promise.all([
  client.queries.postConnection({ first: 10 }),
  client.queries.authorConnection(),
])

const authorMap = new Map(
  authors.data.authorConnection.edges?.map((e) => [e?.node?._sys.filename, e?.node]) ?? [],
)

const enriched = posts.data.postConnection.edges?.map((edge) => ({
  post: edge?.node,
  author: authorMap.get(edge?.node?.authorId),
}))
```

For posts that already use `reference` fields, the author resolves automatically — no manual join needed.

## Limit `first` to a sensible number

```tsx
// ❌ Don't fetch all 1000 posts at once
const all = await client.queries.postConnection({ first: 1000 })

// ✅ Paginate
const page1 = await client.queries.postConnection({ first: 50 })
```

The default is 50 — adjust based on the route's needs. Listing pages benefit from `first: 20–30`; sitemaps and RSS may pull all docs but must paginate to avoid timeouts.

## TotalCount (if supported)

```tsx
const result = await client.queries.postConnection({ first: 0 })
console.log(result.data.postConnection.totalCount)  // total count
```

`totalCount` is available on most setups. For very large collections, computing totalCount can be slow — use only when you need it.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `first: 1000` to fetch all | Slow / 503 | Paginate with `first: 50` and cursor |
| Forgot `?? []` defaults | Crash if connection returns null | Always default arrays |
| Querying `posts` (plural) instead of `postConnection` | Type error | Use the auto-generated `<collection>Connection` |
| Used `filter: { tags: { in: 'react' } }` (string instead of array) | Wrong filter | Use `{ in: ['react'] }` |
| Forgot `sort` argument | Default sort may not be what you want | Always specify if order matters |
