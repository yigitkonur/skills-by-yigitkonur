# Update a Document (Update Mutation)

Programmatic document update via `updateDocument`. Most updates happen through the admin UI; mutations are for tooling.

## TypeScript client

```tsx
const result = await client.queries.updatePost({
  relativePath: 'launch.md',
  params: {
    post: {
      title: 'Updated Title',
      date: new Date().toISOString(),
    },
  },
})
```

Same shape as create (see `references/graphql/09-add-document.md`), but the document must already exist.

## GraphQL equivalent

```graphql
mutation UpdatePost($relativePath: String!, $params: PostMutation!) {
  updatePost(relativePath: $relativePath, params: $params) {
    title
    date
  }
}
```

## Partial updates

Pass only the fields you want to change:

```tsx
await client.queries.updatePost({
  relativePath: 'launch.md',
  params: {
    post: {
      modifiedDate: new Date().toISOString(),
      // Other fields unchanged
    },
  },
})
```

Fields not in `params` keep their current values.

## Common patterns

### Bulk migration

```tsx
async function migratePosts() {
  const all = await client.queries.postConnection()
  const posts = all.data.postConnection.edges?.map((e) => e?.node).filter(Boolean) ?? []

  for (const post of posts) {
    await client.queries.updatePost({
      relativePath: `${post._sys.filename}.md`,
      params: {
        post: {
          modifiedDate: new Date().toISOString(),
          // ... migration logic
        },
      },
    })
  }
}
```

### Toggle published state

```tsx
async function togglePublished(slug: string, draft: boolean) {
  await client.queries.updatePost({
    relativePath: `${slug}.md`,
    params: { post: { draft } },
  })
}
```

### Augment with computed fields (one-time)

```tsx
async function addReadingTimes() {
  const all = await client.queries.postConnection()
  for (const edge of all.data.postConnection.edges ?? []) {
    const post = edge?.node
    if (!post) continue
    const minutes = Math.ceil(estimateWordCount(post.body) / 200)
    await client.queries.updatePost({
      relativePath: `${post._sys.filename}.md`,
      params: { post: { readingTimeMinutes: minutes } },
    })
  }
}
```

## Auth requirements

Same as create — needs a write-capable token (TinaCloud) or pass through the self-hosted auth provider.

## What if the doc doesn't exist?

`updatePost` errors with "Document not found." Don't catch every error and fall through to `createPost` — that masks auth, validation, and network failures. Narrow on the not-found error only:

```tsx
async function upsertPost(relativePath: string, params: any) {
  try {
    await client.queries.updatePost({ relativePath, params })
  } catch (e: any) {
    const msg = String(e?.message || e)
    // Only fall through for "document not found" — re-throw everything else
    if (!/document not found|cannot be found|no such document/i.test(msg)) throw e
    await client.queries.createPost({ relativePath, params })
  }
}
```

## What changes commit to git

Each mutation commits a single file change to the configured branch. Bulk migrations create many commits — squash later with `git rebase -i` if commit history matters.

For batch updates without per-update commits, you'd need to write directly to the filesystem and reindex (advanced; skips TinaCMS validation).

## Validation runs on update

```tsx
try {
  await client.queries.updatePost({
    relativePath: 'launch.md',
    params: { post: { title: '' } },  // empty, but title is required
  })
} catch (e) {
  console.error('Validation:', (e as Error).message)
}
```

Required-field violations and `ui.validate` errors throw at the mutation level.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Used `updatePost` for non-existent doc | "Document not found" | Use `createPost` or upsert pattern |
| Forgot the collection key in `params` | Schema error | Wrap fields under collection name |
| Read-only token | Auth error | Use write-capable token |
| Passed a Date object instead of ISO string for `datetime` | Schema error | `new Date().toISOString()` |
| Tried to update `_sys` fields | Schema error — these are auto-managed | Skip them; only update content fields |
