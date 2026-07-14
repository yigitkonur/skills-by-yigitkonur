# TinaCloud Search

Built-in fuzzy search across your content. Available on all TinaCloud tiers (not self-hosted).

## Enable

1. Project Settings → Configuration → Search
2. Generate Search Indexer Token
3. Add to your `tina/config.ts`:

```typescript
export default defineConfig({
  // ...
  search: {
    tina: {
      indexerToken: process.env.TINA_SEARCH_INDEXER_TOKEN!,
      stopwordLanguages: ['eng'],
    },
  },
})
```

4. Add the env var:

```env
TINA_SEARCH_INDEXER_TOKEN=<from configuration tab>
```

5. Run `pnpm tinacms build` to index existing content.

## How it works

TinaCloud builds a fuzzy-search index from your indexed fields. The admin's search bar uses this index to find documents by:

- Title
- Body (excerpts shown in results)
- Any string field marked as searchable

Fuzzy match handles typos and partial words.

## Field-level search opt-out

```typescript
{
  name: 'internalNotes',
  type: 'string',
  searchable: false,   // exclude from search index
}
```

Exclude internal-only fields, audit logs, etc.

## Search algorithm

TinaCloud uses Damerau-Levenshtein distance with stopword filtering. Languages currently supported via `stopwordLanguages`:

- `eng` — English

For other languages, omit `stopwordLanguages` to disable stopword filtering (or contribute to TinaCMS).

## Editor experience

In the admin, the search bar at the top:

- Searches across all indexed collections
- Shows results grouped by collection
- Click a result to open the document

## Public-facing search

The TinaCloud search index is admin-only. To expose search to your public site:

1. Use a different service (Algolia, Meilisearch, Typesense)
2. Index content from your repo (run a script periodically or via webhook)
3. Build a search UI in your app

TinaCloud's search isn't designed for public-facing search.

## Quota

Free tier: limited search indexer ops/month.
Paid tiers: more.

For most projects you won't hit the cap — only re-indexing happens on save.

## Self-hosted alternative

Self-hosted TinaCMS doesn't have built-in search. Options:

- Algolia (paid SaaS)
- Meilisearch (open source, self-host)
- Pagefind (static, build-time index)

Index from `content/**/*.{md,mdx,json}` directly.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot to generate indexer token | Search doesn't work | Generate in Configuration tab |
| Token in client-side code | Token leak | Server-side only (use `TINA_SEARCH_INDEXER_TOKEN`) |
| Tried to use TinaCloud search publicly | Admin-only API | Use Algolia / Meilisearch for public search |
| All fields indexed even when secret | Sensitive data searchable | Mark with `searchable: false` |
| Self-hosted project assumed search works | Not available | Use external service |
