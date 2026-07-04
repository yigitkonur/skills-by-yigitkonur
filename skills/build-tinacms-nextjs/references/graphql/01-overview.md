# GraphQL Overview

TinaCMS auto-generates a GraphQL schema from your `tina/config.ts`. The schema includes typed query types per collection, connection types for lists, and mutation types for content edits.

## What's generated

For each collection `name: 'X'` in your schema:

| Generated | Purpose |
|---|---|
| `Query.X(relativePath: String!)` | Single document fetch |
| `Query.XConnection(filter, sort, first, after, last, before)` | List documents |
| `Mutation.createX(relativePath, params)` | Create new document |
| `Mutation.updateX(relativePath, params)` | Update existing document |
| Type `X` | Document shape |
| Type `XConnection` | Page of documents |

For multi-shape collections (using `templates`), `X` is a union of all template types.

## Inspecting the schema

```bash
cat tina/__generated__/schema.gql
```

Shows the full GraphQL schema in standard syntax. Useful for IDE plugins, GraphQL clients, or just understanding what's available.

## Reading order

| File | Topic |
|---|---|
| `references/graphql/02-get-document.md` | Single-document fetches |
| `references/graphql/03-query-documents.md` | List fetches via Connection |
| `references/graphql/04-filter-documents.md` | Filter operators |
| `references/graphql/05-sorting.md` | Sort by indexed fields |
| `references/graphql/06-pagination.md` | Cursor pagination |
| `references/graphql/07-performance.md` | Performance considerations |
| `references/graphql/08-limitations.md` | Known limits |
| `references/graphql/09-add-document.md` | createDocument mutation |
| `references/graphql/10-update-document.md` | updateDocument mutation |

## Auto-generated client wraps GraphQL

`tina/__generated__/client.ts` exposes:

```tsx
client.queries.<collection>(...)        // single doc
client.queries.<collection>Connection(...) // list
```

These are typed wrappers around the GraphQL endpoint. For the GraphQL itself, look at `tina/__generated__/queries.gql`.

## Inline custom queries

```tsx
const result = await client.request({
  query: `query { ... }`,
  variables: {},
})
```

For any GraphQL not auto-generated. See `references/data-fetching/03-custom-queries.md`.

## Mutations (writes)

For most app code, you don't write mutations directly — editors save through the admin UI, which calls the auto-generated mutations under the hood. For programmatic content creation (e.g. importing content), see `references/graphql/09-add-document.md`.

## Common patterns

```tsx
// Single doc
const result = await client.queries.page({ relativePath: 'home.md' })

// List with filter + sort
const list = await client.queries.postConnection({
  filter: { draft: { eq: false } },
  sort: 'date',
  first: 10,
})

// Pagination
const more = await client.queries.postConnection({
  first: 10,
  after: list.data.postConnection.pageInfo.endCursor,
})
```

## Limitations

GraphQL queries TinaCMS supports:

- Single-doc by `relativePath`
- Connection lists with `filter`, `sort`, `first`/`last`, `after`/`before`
- Mutations for create/update

GraphQL queries TinaCMS does NOT support:

- Arbitrary cross-collection joins
- Aggregate queries (count, sum)
- Subscriptions (websocket-based real-time queries)
- Complex nested filters across multiple objects

For cross-collection logic, fetch separately and combine in JS. See `references/graphql/08-limitations.md`.
