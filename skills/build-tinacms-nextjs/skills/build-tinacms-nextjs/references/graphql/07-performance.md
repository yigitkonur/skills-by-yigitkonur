# Performance

Query cost considerations and indexing tuning for TinaCMS GraphQL.

## What's cheap

- Single-doc fetch by `relativePath`
- Connection with `first: 50` and a filter on indexed fields
- Sorting by indexed numeric/datetime fields

## What's expensive

- Connection with `first: 1000` (massive payload)
- Walking all pages of a 10k+ collection (sequential cursor traversal)
- Filtering by string `startsWith` on millions of records
- Cross-collection joins (no native support — done in JS, slow)

## Query response size

Auto-generated queries select **every field** on the document by default. For list views, select only what you render:

```tsx
// Use a custom query that selects only `title`, `excerpt`, `coverImage`
// See references/data-fetching/03-custom-queries.md
const result = await client.queries.PostsForListing({ first: 10 })
```

## Indexing

TinaCMS indexes documents into the database (Vercel KV or MongoDB for self-hosted; managed for TinaCloud). Indexed fields are fast for filtering and sorting.

By default **all fields are indexed**. For very large collections, you can opt out per-field via `searchable: false`:

```typescript
{
  name: 'verboseInternalNotes',
  type: 'string',
  searchable: false,  // skip indexing — saves space, can't filter/sort by this
}
```

For most projects, leave the default. Only tune indexing for collections with > 10k docs.

## Filter pushdown

Filters are evaluated in the database, not in JS. So:

```tsx
// ✅ Cheap — filter pushed down
client.queries.postConnection({ filter: { draft: { eq: false } }, first: 10 })

// ❌ Expensive — fetches all, filters in JS
const all = await client.queries.postConnection({ first: 1000 })
const filtered = all.data.postConnection.edges?.filter((e) => !e?.node?.draft)
```

Always push filters down.

## Caching layers

Three layers stack:

1. **TinaCloud / self-hosted DB cache** — content cached at the GraphQL endpoint
2. **Vercel data cache** — Vercel caches `fetch()` responses (default up to 1 year)
3. **Next.js framework cache** — `"use cache"` adds another layer

For TinaCMS sites, layer 2 is the most impactful. Use `revalidate: 60–300` to balance freshness and TinaCloud quota.

## TinaCloud quota

Free tier: 10k requests/month. Each `client.queries.X(...)` call counts as one request (regardless of size).

Tips for staying under quota:

- Use Next.js fetch cache (`revalidate: 60+`) so requests dedupe
- Use `"use cache"` for in-process caching
- Use ISR/SSG instead of SSR where possible
- Pre-render via `generateStaticParams` so requests happen at build time

## Avoiding the 503 dropdown

Reference fields with > 500 docs in the referenced collection cause 503 timeouts (see `references/field-types/06-reference.md`). Mitigate by splitting collections or using string + options.

## CI build time

For sites with 1000+ pages:

```tsx
export async function generateStaticParams() {
  // Paginate to fetch all
  const all = await fetchAllPosts()
  return all.map((p) => ({ slug: p._sys.filename }))
}
```

Build time scales linearly with page count (each page renders once). For 10k+ pages, consider switching to ISR (`dynamicParams: true`) so most pages render on-demand.

## Mutations

Editor saves are mutations. Each save:

- Updates DB index
- Commits to git
- Optionally triggers webhooks

These are slower than reads (writes go through the full git push). Batch saves when possible — most editor flows naturally batch (one save per document).

## Common bottlenecks

| Symptom | Fix |
|---|---|
| Slow listing pages | Use custom query selecting fewer fields |
| Slow build | Switch to ISR; reduce `generateStaticParams` page count |
| Hit TinaCloud rate limits | Add `revalidate`; cache aggressively |
| Vercel function timeouts on connection queries | Paginate; reduce `first` |
| Drafts contaminate indexed search | Filter `draft: { eq: false }` at fetch |

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Filtering in JS instead of GraphQL | Wasted bandwidth and time | Push filter down to query |
| `first: 1000` to "fetch all" | Slow / 503 | Paginate with `first: 50` |
| No `revalidate` | Every request hits TinaCloud | Add `next: { revalidate: 60 }` |
| Custom query selects every field | Same payload as auto-generated | Select only what's needed |
| Indexed every field on a 100k-doc collection | Slow writes | Opt out via `searchable: false` for non-filterable fields |
