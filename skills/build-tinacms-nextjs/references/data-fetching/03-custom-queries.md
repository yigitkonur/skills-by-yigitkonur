# Custom Queries

The auto-generated client covers 95% of needs. For custom GraphQL — selecting fewer fields, complex filtering, or ad-hoc queries — drop a `.gql` file in `tina/queries/`.

## When to use

- Performance: select fewer fields than auto-generated (smaller responses)
- Reusability: a named query used across multiple pages
- Custom shapes: union queries, fragments, custom argument signatures

## The pattern

```graphql
# tina/queries/postsForListing.gql
query PostsForListing($first: Int!, $sort: String) {
  postConnection(first: $first, sort: $sort) {
    edges {
      node {
        id
        title
        date
        excerpt
        coverImage
        _sys {
          filename
        }
      }
    }
  }
}
```

After `tinacms build`, this query attaches to the same client:

```tsx
const result = await client.queries.PostsForListing({
  first: 10,
  sort: 'date',
})
```

## Multi-query files

You can define multiple queries in one file, or one per file:

```graphql
# tina/queries/post-queries.gql
query GetPostBySlug($slug: String!) {
  post(relativePath: $slug) {
    title
    body
  }
}

query GetPostList($first: Int!) {
  postConnection(first: $first) {
    edges {
      node {
        title
      }
    }
  }
}
```

Each named query becomes a method on `client.queries`.

## Fragments

```graphql
# tina/queries/fragments.gql
fragment PostMeta on Post {
  title
  date
  excerpt
}
```

Then use:

```graphql
# tina/queries/list.gql
query ListPosts {
  postConnection {
    edges {
      node {
        ...PostMeta
      }
    }
  }
}
```

## Inline queries via `client.request`

For one-off queries without creating a `.gql` file:

```tsx
const result = await client.request({
  query: `
    query GetTwoPosts {
      first: post(relativePath: "post-1.md") { title }
      second: post(relativePath: "post-2.md") { title }
    }
  `,
  variables: {},
})

console.log(result.first.title, result.second.title)
```

Useful for pages that need data from multiple documents in one round-trip.

## When to break out into custom queries

| Use case | Auto-generated suffices? |
|---|---|
| Single-doc fetch | Yes — `client.queries.<collection>(...)` |
| List with simple filter | Yes — `<collection>Connection({ filter, sort })` |
| Select fewer fields for perf | No — write custom query |
| Multiple docs in one round-trip | No — write custom query |
| Fragment reuse | No — define fragment in `.gql` |
| Custom argument names | No — define query with your names |

## Custom query types vs auto-generated

Generated types are for the auto-generated queries. For custom queries, the types are also auto-generated when you save the `.gql` file:

```tsx
import type { PostsForListingQuery } from '@/tina/__generated__/types'

const result: { data: PostsForListingQuery } = await client.queries.PostsForListing({...})
```

## Performance: don't over-select

The auto-generated client selects every field on the document. For a list view that only needs `title` and `excerpt`, that's wasteful:

```graphql
# Custom — only what you need
query PostsForCard {
  postConnection(first: 20) {
    edges {
      node {
        title
        excerpt
        coverImage
      }
    }
  }
}
```

Smaller payloads, faster pages.

## Verifying

After saving a `.gql` file:

```bash
pnpm tinacms build
# Should regenerate `tina/__generated__/queries.gql` and `client.ts`

# Then in your code:
const result = await client.queries.PostsForListing({...})
// TypeScript should autocomplete the method
```

If the new method isn't on `client.queries`, the build didn't pick up your file. Check it's in `tina/queries/` (not nested), has a valid `query` declaration, and re-run the build.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| File outside `tina/queries/` | Not picked up | Move into `tina/queries/` |
| Anonymous query (no name) | Method not generated | Add a name: `query MyName { ... }` |
| Syntax error in `.gql` | Build fails silently | Check `tinacms build` output |
| Used a fragment without defining it | Build fails | Either define fragment or inline |
| Custom query selects fields not in schema | Schema mismatch | Match field names exactly |
