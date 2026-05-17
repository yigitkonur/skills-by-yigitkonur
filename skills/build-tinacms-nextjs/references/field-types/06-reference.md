# `reference` field

Cross-collection link — pick a document from another collection. Useful for `author` on a post, `category` on a doc, `relatedPost` linking blog posts.

## Basic

```typescript
{
  name: 'author',
  label: 'Author',
  type: 'reference',
  collections: ['author'],
}
```

`collections` is an array — you can reference multiple collections from one field:

```typescript
{
  name: 'pinned',
  type: 'reference',
  collections: ['post', 'page'],  // editor picks any post or page
}
```

When referencing multiple collections, query results return a discriminated union — narrow on `__typename`.

## List of references

```typescript
// Direct list — DOES NOT WORK
{
  name: 'authors',
  type: 'reference',
  list: true,            // ❌ reference fields cannot be list:true
  collections: ['author'],
}

// Workaround: wrap in object + list
{
  name: 'authors',
  type: 'object',
  list: true,
  ui: { itemProps: (item) => ({ label: item?.author?.name || 'Author' }) },
  fields: [
    { name: 'author', type: 'reference', collections: ['author'] },
  ],
}
```

The current TinaCMS schema doesn't allow `reference + list:true`. Wrap each reference in a single-field object inside an `object + list`.

## Referenced document fields in queries

When you query a document with a reference, the GraphQL response inlines the referenced document's fields:

```typescript
const result = await client.queries.post({ relativePath: 'my-post.md' })
// result.data.post.author  // the resolved author document, not just the ID
console.log(result.data.post.author.name)
console.log(result.data.post.author.bio)
```

## Stored format

The reference is stored as a relative path:

```yaml
---
author: 'content/authors/jane-doe.json'
---
```

The path is relative to the project root.

## 503 / dropdown timeouts (the big gotcha)

Reference fields **load all documents** in the referenced collection at once. There's **no pagination**. Above ~500 documents, the dropdown 503s.

Symptoms:

- Dropdown spins forever
- 503 Service Unavailable in the network tab
- Admin becomes unresponsive when opening this field

### Fixes

**Option 1: Split the collection.**

```typescript
// Instead of one big "author" collection
{ name: 'author', path: 'content/authors', /* 1000 authors */ }

// Split:
{ name: 'active_author', path: 'content/authors/active' }
{ name: 'archived_author', path: 'content/authors/archived' }
```

**Option 2: Replace with a `string` + `options`.**

```typescript
// Trade dynamic dropdown for a curated list
{
  type: 'string',
  name: 'authorId',
  label: 'Author',
  options: [
    { value: 'jane-doe', label: 'Jane Doe' },
    { value: 'john-smith', label: 'John Smith' },
    // ... up to ~50 entries
  ],
}
```

Pair with a custom resolver in your renderer to fetch the author by ID.

**Option 3: Custom field component with pagination.**

Implement a custom React component that paginates the dropdown. Advanced — see `references/toolkit-fields/07-custom-field-component.md` and TinaCMS' "extending-tina/custom-field-components" docs.

## Schema-conflict warning

If you reference multiple collections, the **fields you query must exist on all of them** — otherwise GraphQL fails with a schema conflict:

```typescript
// post collection has `title`
// page collection has `pageTitle` (different name)

{
  type: 'reference',
  collections: ['post', 'page'],  // ⚠️
}

// Query: select `title`
// Fails on `page` documents — `title` doesn't exist
```

Either:

- Standardize field names across referenced collections (`title` everywhere)
- Use inline fragments in the query (`__typename`-aware fields)

## Validation

`reference` fields auto-validate that the picked path resolves to an existing document. If a referenced document is deleted, queries return null for the reference.

Defensive rendering:

```tsx
{post.author && <AuthorCard author={post.author} />}
```

## When NOT to use `reference`

- **Tags / categories with < 50 values:** use `string + list + options` instead.
- **One-off relationships:** if the data is needed only on one document, embed it inline as an `object`.
- **Large referenced collections (>500 docs):** the 503 limitation makes this unworkable.

## Renderer

The auto-generated client resolves references to full document objects:

```tsx
type PostProps = {
  data: {
    post: {
      title: string
      author: {
        name: string
        avatar: string
        bio: string
      }
    }
  }
}

export default function Post({ data }: PostProps) {
  return (
    <article>
      <h1>{data.post.title}</h1>
      <div>By {data.post.author.name}</div>
    </article>
  )
}
```

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `type: 'reference', list: true` | Schema build fails | Wrap in `object + list` |
| Multi-collection reference with mismatched fields | Schema conflict | Standardize field names or use inline fragments |
| Large referenced collection (>500) | 503 dropdown | Split collection or switch to `string + options` |
| Forgot null check in renderer | Crash when referenced doc deleted | Defensive rendering with `&&` |
| Querying without selecting referenced fields | `null` instead of resolved object | Make sure your query selects referenced fields |
