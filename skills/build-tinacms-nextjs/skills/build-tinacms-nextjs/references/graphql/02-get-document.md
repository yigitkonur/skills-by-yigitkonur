# Get a Single Document

Fetch one document by its relative path within a collection.

## TypeScript client

```tsx
const result = await client.queries.page({ relativePath: 'home.md' })
console.log(result.data.page.title)
```

## GraphQL equivalent

```graphql
query GetPage($relativePath: String!) {
  page(relativePath: $relativePath) {
    title
    blocks {
      __typename
      ... on PageBlocksHero {
        heading
        subheading
      }
    }
    seo {
      metaTitle
      metaDescription
    }
  }
}
```

Variables:

```json
{ "relativePath": "home.md" }
```

## `relativePath` rules

| Collection path | File on disk | `relativePath` |
|---|---|---|
| `content/pages` | `content/pages/home.md` | `'home.md'` |
| `content/posts` | `content/posts/launch.md` | `'launch.md'` |
| `content/docs` | `content/docs/guide/install.md` | `'guide/install.md'` |
| `content/posts` (date-prefixed) | `content/posts/2026-05-08-launch.md` | `'2026-05-08-launch.md'` |

Always include the file extension. The path is relative to the collection's `path` config, not the project root.

## Result shape

```typescript
{
  data: {
    page: {                    // matches collection name
      title: string,
      blocks: Array<...>,
      seo: { ... },
      _sys: {
        filename: 'home',
        breadcrumbs: [],
        lastModified: '2026-05-08T...',
      },
      // ... all schema fields
    },
  },
  query: string,               // the GraphQL query string
  variables: { relativePath: 'home.md' },
}
```

`_sys` is a Tina-injected metadata object — file info that doesn't come from the document itself.

## Document not found

If the relativePath doesn't match any document:

```tsx
try {
  const result = await client.queries.page({ relativePath: 'missing.md' })
} catch (e) {
  console.error('Document not found:', e)
}
```

The query throws. Wrap in try/catch or use `notFound()` in App Router:

```tsx
import { notFound } from 'next/navigation'

try {
  const result = await client.queries.page({ relativePath: `${slug}.md` })
  return <PageClient {...result} />
} catch {
  notFound()
}
```

## Multi-shape collections

For collections with `templates: [...]`, the result is a union — narrow on `__typename`:

```graphql
query GetPage($relativePath: String!) {
  page(relativePath: $relativePath) {
    __typename
    ... on PageLanding {
      title
      hero { heading }
    }
    ... on PageLegal {
      title
      lastUpdated
    }
  }
}
```

In the auto-generated client, this is handled automatically — narrow on `result.data.page.__typename`.

## Singletons

```tsx
const result = await client.queries.global({ relativePath: 'global.json' })
console.log(result.data.global.siteName)
```

Singletons follow the same API as folder collections — pass the file's relativePath.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `.md` extension | "Document not found" | Include extension |
| Used `posts/launch.md` (with collection prefix) | "Document not found" | Use just `launch.md` |
| Used absolute path | Error | Use relative to collection `path` |
| `client.queries.posts(...)` (plural) | No method | Use the collection name singular |
| Didn't run `tinacms build` after schema change | Wrong type signature | Rebuild |
