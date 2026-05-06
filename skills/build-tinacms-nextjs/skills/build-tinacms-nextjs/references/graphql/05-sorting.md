# Sorting

Sort connection results by a field.

## Basic

```tsx
const result = await client.queries.postConnection({
  sort: 'date',
})
```

Default direction depends on the field type:

- Numeric/datetime fields: descending (newest first)
- String fields: ascending (alphabetical)

## Reverse direction

```tsx
const result = await client.queries.postConnection({
  sort: 'date',
  last: 50,         // last 50 (in ascending order = oldest first when sorted descending)
})
```

`last: N` reverses the iteration order. For most blog/post listings you want newest-first, which is the default behavior with `first: N`.

## Multiple-field sort (not supported natively)

GraphQL sort accepts a single field. For secondary sorts (e.g. featured first, then by date), do it in JS:

```tsx
const result = await client.queries.postConnection({ sort: 'date', first: 50 })
const sorted = (result.data.postConnection.edges ?? []).sort((a, b) => {
  // Primary: featured
  const af = a?.node?.featured ? 1 : 0
  const bf = b?.node?.featured ? 1 : 0
  if (af !== bf) return bf - af
  // Secondary: date (already in result, but tie-break here)
  return new Date(b!.node!.date!).getTime() - new Date(a!.node!.date!).getTime()
})
```

## Sortable fields must be indexed

By default all fields are indexed. For very large collections you may turn off indexing on irrelevant fields to speed up writes — but then those fields can't be sorted on. See `references/graphql/07-performance.md`.

## Sort by `_sys` fields

Auto-fields are sortable too:

```tsx
// Sort by file modified time
const result = await client.queries.postConnection({ sort: 'lastModified' })

// Sort by filename
const result = await client.queries.postConnection({ sort: 'filename' })
```

These come from `_sys` metadata.

## Common patterns

### Newest first (default for date)

```tsx
const result = await client.queries.postConnection({ sort: 'date', first: 10 })
```

### Alphabetical

```tsx
const result = await client.queries.docConnection({ sort: 'title', first: 100 })
```

### Custom order field

```typescript
// Schema:
{ name: 'order', type: 'number' }

// Query:
const result = await client.queries.menuItemConnection({ sort: 'order' })
```

For navigation/menu items, use a numeric `order` field rather than alphabetical.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `sort: { date: 'desc' }` (object syntax) | Type error | Sort accepts only a field name string |
| Sorted by a non-indexed field | Returns unsorted | Field must be indexed |
| Trying to sort with multiple fields | No native syntax | Sort by primary, tie-break in JS |
| Forgot `sort` argument entirely | Default may not be deterministic | Always specify when order matters |
