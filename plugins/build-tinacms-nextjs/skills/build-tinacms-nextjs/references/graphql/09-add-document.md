# Add a Document (Create Mutation)

Programmatic document creation via the `createDocument` mutation. Most projects don't need this — editors create through the admin UI. Useful for content imports.

## TypeScript client

```tsx
const result = await client.queries.createPost({
  relativePath: 'new-post.md',
  params: {
    post: {
      title: 'New Post',
      date: new Date().toISOString(),
      body: { type: 'root', children: [{ type: 'p', children: [{ type: 'text', text: 'Hello' }] }] },
    },
  },
})
```

The `params` object is keyed by collection name and contains the document's fields.

## GraphQL equivalent

```graphql
mutation CreatePost($relativePath: String!, $params: PostMutation!) {
  createPost(relativePath: $relativePath, params: $params) {
    title
    date
  }
}
```

## Field shape

The fields you pass match the schema definitions. Rich-text fields require an AST (not a markdown string) — see below.

## Rich-text AST shape

```typescript
{
  body: {
    type: 'root',
    children: [
      {
        type: 'p',
        children: [
          { type: 'text', text: 'Plain text' },
          { type: 'text', text: 'Bold', bold: true },
        ],
      },
      {
        type: 'h1',
        children: [{ type: 'text', text: 'Heading' }],
      },
    ],
  },
}
```

For complex content, use a markdown-to-AST conversion library or the TinaCMS rich-text utilities.

## Bulk import pattern

```tsx
import { client } from '@/tina/__generated__/client'
import * as fs from 'fs'
import * as path from 'path'

async function importPosts(jsonPath: string) {
  const posts = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'))

  for (const post of posts) {
    try {
      await client.queries.createPost({
        relativePath: `${post.slug}.md`,
        params: {
          post: {
            title: post.title,
            date: post.publishedAt,
            body: convertMarkdownToAst(post.body),
          },
        },
      })
      console.log(`✓ ${post.slug}`)
    } catch (e) {
      console.error(`✗ ${post.slug}: ${(e as Error).message}`)
    }
  }
}
```

## Using the auth token

Mutations require auth. For self-hosted projects, the auth provider gates the request. For TinaCloud, you need a write-capable token (different from the read-only `TINA_TOKEN`):

```env
TINA_WRITE_TOKEN=<from app.tina.io with write scope>
```

Pass via custom client headers:

```tsx
import { Client } from 'tinacms/dist/client'

const writeClient = new Client({
  branch: 'main',
  clientId: process.env.NEXT_PUBLIC_TINA_CLIENT_ID,
  token: process.env.TINA_WRITE_TOKEN,
})

await writeClient.queries.createPost({...})
```

Don't confuse `TINA_TOKEN` (read-only) with a write token.

## Validation

Validation runs on create:

- Required fields must be set
- `ui.validate` functions execute
- Field name format is enforced

If validation fails, the mutation throws. Wrap in try/catch.

## Conflicts

If a document with the same `relativePath` already exists, `createPost` fails. **Neither mutation is a true upsert** — `updatePost` also fails when the document doesn't exist. For upsert behavior implement it yourself: try `updatePost`, narrow ONLY on a "document not found" error, fall through to `createPost`. See `references/graphql/10-update-document.md`.

## When NOT to use

- One-off documents — editors create through admin
- Documents that need media uploads (separate API call)
- Production runtime — mutations write to git, which is slow

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Used `client.queries.createPost(...)` with read-only token | Auth error | Use write-capable token |
| Passed markdown string instead of AST for `rich-text` field | Schema error | Convert to AST first |
| Forgot collection key in `params` | "Field 'post' missing" | Wrap fields under collection name |
| Tried to pass image file blob | Not supported | Upload via media API first, then reference path |
| Used in production runtime | Slow due to git commit | Use mutations only for batch imports / admin tooling |
