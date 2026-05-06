# GraphQL Limitations

Known things TinaCMS' GraphQL layer doesn't support, and the workarounds.

## No cross-collection joins

GraphQL has no `JOIN` semantics. Reference fields auto-resolve when traversed in the query, but you can't filter posts by author traits in one query:

```graphql
# Doesn't work: filter posts by author.country
query {
  postConnection(filter: { author: { country: { eq: 'US' } } }) {
    # ...
  }
}
```

**Workaround:** fetch separately and combine in JS.

```tsx
const [posts, authors] = await Promise.all([
  client.queries.postConnection(),
  client.queries.authorConnection({ filter: { country: { eq: 'US' } } }),
])
const usAuthorPaths = new Set(
  authors.data.authorConnection.edges?.map((e) => `content/authors/${e?.node?._sys.filename}.json`),
)
const usPosts = posts.data.postConnection.edges?.filter((e) =>
  usAuthorPaths.has(e?.node?.author?._sys.path)
)
```

## No OR filters

Filters are AND-only. For OR semantics:

- Use `in: [...]` for "match any of these values" (built-in OR over a single field)
- Run multiple queries in parallel and merge

## No nested-field filtering

```graphql
# Doesn't work
query {
  postConnection(filter: { seo: { metaTitle: { startsWith: 'Hello' } } }) {
    # ...
  }
}
```

Filters apply only to top-level fields. **Workaround:** fetch + filter in JS.

## No aggregations

No `count`, `sum`, `avg`. To count results:

```tsx
const result = await client.queries.postConnection({ first: 0 })
console.log(result.data.postConnection.totalCount)
```

`totalCount` is the only aggregation supported.

## No subscriptions

GraphQL subscriptions (real-time push) aren't supported. The `useTina` hook uses a different mechanism (websocket directly to TinaCloud's edit-mode protocol).

## No mutations from app code (effectively)

Mutations exist in the GraphQL schema (`createDocument`, `updateDocument`) but you don't call them from your app code — editors save through the admin UI. For programmatic content creation (e.g. import scripts), mutations work but are uncommon.

## Reference field 503 with > 500 docs

Reference field dropdowns load all referenced docs at once. > 500 docs → 503.

**Workaround:** split collections or replace with `string + options`. See `references/field-types/06-reference.md`.

## No full-text search (in self-hosted)

TinaCloud has built-in fuzzy search (`search.tina.indexerToken`). Self-hosted projects don't have search. Use a separate service (Algolia, Meilisearch) for self-hosted full-text needs.

## No GraphQL introspection in production

By default, the GraphQL endpoint doesn't expose introspection metadata in production (only in dev). For tooling that needs introspection (codegen, GraphiQL), point at the local dev endpoint.

## Reference fields cannot be `list: true` directly

```typescript
// ❌ Schema fails
{ name: 'authors', type: 'reference', list: true, collections: ['author'] }

// ✅ Wrap in object + list
{
  name: 'authors',
  type: 'object',
  list: true,
  fields: [{ name: 'author', type: 'reference', collections: ['author'] }],
}
```

## No file uploads via GraphQL

Image fields are populated via the media picker (separate upload API), not by GraphQL mutations. You can't programmatically upload a file then reference it in a mutation in one step.

## Sub-path deployment broken

Even with `basePath` set in `tina/config.ts`, the admin SPA tries to load assets from the domain root. **Deploy at root.** See `references/deployment/05-edge-runtime-not-supported.md`.

## Edge runtime not supported

The TinaCMS backend (self-hosted) is Node.js only. Cloudflare Workers, Vercel Edge Functions, and other V8-isolate runtimes are unsupported. See `references/deployment/05-edge-runtime-not-supported.md`.

## What you CAN do

- Single-doc fetch by relativePath
- Connection list with filter/sort/cursor pagination
- Filter by top-level field with one of: eq, in, gt, gte, lt, lte, startsWith, after, before
- Sort by a single indexed field
- Reference traversal (auto-resolves when selected in query)
- `__typename` discrimination on multi-shape collections
- `_sys` metadata access
- Custom queries via `tina/queries/*.gql`

For everything else, fetch and combine in JS.
