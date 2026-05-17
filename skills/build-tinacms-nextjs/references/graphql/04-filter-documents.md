# Filter Documents

GraphQL filter operators for narrowing connection results.

## Operator table

| Operator | Behavior | Types |
|---|---|---|
| `eq` | Equals | string, number, boolean |
| `in` | One of | string[], number[], boolean[] |
| `gt` | Greater than | string, number |
| `gte` | Greater than or equal | string, number |
| `lt` | Less than | string, number |
| `lte` | Less than or equal | string, number |
| `startsWith` | Starts with | string |
| `after` | After (date) | datetime |
| `before` | Before (date) | datetime |

Only `gt`, `gte`, `lt`, `lte`, `after`, `before` may be used in ternary conditions.

## Single-field filter

```tsx
// Posts where draft === false
const result = await client.queries.postConnection({
  filter: { draft: { eq: false } },
})
```

## Multiple operators on one field

```tsx
// Posts published between two dates
const result = await client.queries.postConnection({
  filter: {
    date: {
      after: '2026-01-01T00:00:00Z',
      before: '2026-12-31T23:59:59Z',
    },
  },
})
```

## Multiple fields (implicit AND)

```tsx
// Drafts in 'design' category
const result = await client.queries.postConnection({
  filter: {
    draft: { eq: true },
    category: { eq: 'design' },
  },
})
```

All conditions must match.

## `in` for multi-select

```tsx
// Posts in any of three categories
const result = await client.queries.postConnection({
  filter: {
    category: { in: ['design', 'engineering', 'product'] },
  },
})
```

## `startsWith` for prefix match

```tsx
// Posts whose title starts with 'How to'
const result = await client.queries.postConnection({
  filter: { title: { startsWith: 'How to' } },
})
```

## Filtering by reference field

```tsx
// Posts by a specific author
const result = await client.queries.postConnection({
  filter: { author: { eq: 'content/authors/jane-doe.json' } },
})
```

The filter value is the author's reference path (relativePath from the project root).

## Filtering by nested object field

GraphQL doesn't natively support deep filters across nested objects. Workaround: filter at fetch, narrow in JS:

```tsx
const result = await client.queries.postConnection({ filter: { draft: { eq: false } } })
const filtered = result.data.postConnection.edges?.filter((edge) =>
  edge?.node?.seo?.noIndex !== true
)
```

## OR queries (not supported natively)

GraphQL filters are AND-only. For OR semantics, run multiple queries and combine:

```tsx
const [a, b] = await Promise.all([
  client.queries.postConnection({ filter: { category: { eq: 'design' } } }),
  client.queries.postConnection({ filter: { category: { eq: 'engineering' } } }),
])

const combined = [
  ...(a.data.postConnection.edges ?? []),
  ...(b.data.postConnection.edges ?? []),
]
```

For up to 5–10 OR conditions, use `in: [...]`.

## Filtering by datetime

```tsx
const recent = await client.queries.postConnection({
  filter: { date: { after: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString() } },
  sort: 'date',
})
```

Datetime filters use `after` and `before`; `gt`/`gte`/`lt`/`lte` also work since datetime is stored as an ISO string.

## Indexing for performance

For filters to be fast, the field must be **indexed**. By default, all fields are indexed. For large collections (10k+ docs), you may need to mark only certain fields as indexed via the `searchable` config.

See `references/graphql/07-performance.md`.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `{ in: 'react' }` (string) | Type error — must be array | Wrap in array: `{ in: ['react'] }` |
| `{ eq: 'draft' }` for boolean field | Doesn't match | Use `{ eq: true }` for booleans |
| Tried to OR with `\|\|` syntax | Not supported | Use `in: [...]` or run multiple queries |
| Filtered by nested object field | Doesn't work | Filter at top level, narrow in JS |
| Used `gt` on a boolean | Type error | Boolean only supports `eq` and `in` |
