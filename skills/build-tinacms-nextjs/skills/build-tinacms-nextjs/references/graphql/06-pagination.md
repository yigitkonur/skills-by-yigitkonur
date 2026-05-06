# Pagination

Cursor-based pagination via `first`/`after` (forward) or `last`/`before` (reverse).

## Forward pagination

```tsx
// First page
const page1 = await client.queries.postConnection({
  sort: 'date',
  first: 10,
})

// Next page
const page2 = await client.queries.postConnection({
  sort: 'date',
  first: 10,
  after: page1.data.postConnection.pageInfo.endCursor,
})
```

The `pageInfo` object provides cursors:

```typescript
pageInfo: {
  hasNextPage: boolean,
  hasPreviousPage: boolean,
  startCursor: string,
  endCursor: string,
}
```

## Reverse pagination

```tsx
// Last 10 (oldest in chronological terms when sorted by 'date' desc)
const oldest = await client.queries.postConnection({
  sort: 'date',
  last: 10,
})

// Previous page
const prev = await client.queries.postConnection({
  sort: 'date',
  last: 10,
  before: oldest.data.postConnection.pageInfo.startCursor,
})
```

## Iterating all pages

```tsx
async function fetchAllPosts() {
  const all: any[] = []
  let cursor: string | null = null

  while (true) {
    const result = await client.queries.postConnection({
      first: 50,
      after: cursor,
    })
    const edges = result.data.postConnection.edges ?? []
    all.push(...edges)

    if (!result.data.postConnection.pageInfo.hasNextPage) break
    cursor = result.data.postConnection.pageInfo.endCursor
  }

  return all
}
```

For sites with thousands of docs, use this in `generateStaticParams`, sitemap generation, etc.

## Cursor opacity

Cursors are opaque base64-encoded strings. Don't try to interpret them:

```
cG9zdCNkYXRlIzE2NTUyNzY0MDAwMDAjY29udGVudC9wb3N0cy92b3RlRm9yUGVkcm8uanNvbg==
```

They encode the document's position in the sorted list. Pass them as-is.

## Pagination + filtering combined

```tsx
const result = await client.queries.postConnection({
  filter: { draft: { eq: false }, category: { eq: 'design' } },
  sort: 'date',
  first: 10,
  after: cursor,
})
```

Filtering applies first, then pagination.

## Per-edge cursor

Each edge has its own cursor — useful for "jump to here" patterns:

```tsx
result.data.postConnection.edges?.forEach((edge) => {
  console.log(edge?.cursor)  // unique to this edge
})
```

## "Page X of Y" UI

Cursor-based pagination doesn't natively support page numbers. For "Page 3 of 10" UIs:

1. Fetch totalCount: `result.data.postConnection.totalCount`
2. Calculate page count: `Math.ceil(totalCount / perPage)`
3. Maintain a list of cursors per page (or accept that "skip to page 5" requires fetching 5 sequential pages)

For most blog/listing UIs, "Load more" or infinite-scroll patterns work better than numbered pages.

## Performance considerations

| Operation | Cost |
|---|---|
| Fetch first 50 with sort+filter | Cheap |
| Fetch next 50 by cursor | Cheap |
| Skip 100 via cursor walk | Linear in page count |
| Random access to "page 50" | Expensive (linear walk) |

Stick to forward iteration when possible.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Trying to skip pages numerically (`offset: 50`) | Not supported | Use cursors |
| Not checking `hasNextPage` | Infinite loop | Break when `hasNextPage === false` |
| Using `first` AND `last` simultaneously | Confusing semantics | Pick one direction |
| Storing cursors in URLs as-is | Can break across schema changes | Re-fetch from page 1 if cursor invalid |
| Forgot cursor null on first page | Skips first page | Use `after: null` or omit `after` |
