# `boolean` field

Toggle switch. Stores `true` or `false`.

## Basic

```typescript
{
  name: 'draft',
  label: 'Draft',
  type: 'boolean',
  description: 'If checked, document is hidden from production',
}
```

## With default

```typescript
{
  name: 'featured',
  type: 'boolean',
  default: false,
}
```

## Use cases

| Field | Purpose |
|---|---|
| `draft` | Hide doc from production renders |
| `featured` | Promote in lists |
| `noIndex` | SEO — exclude from sitemap and add `<meta name="robots" noindex>` |
| `noFollow` | SEO — `<meta name="robots" nofollow>` |
| `published` | Inverse of draft |
| `pinned` | Pin to top of listing |
| `openInNewTab` | For link fields |
| `disabled` | Soft-delete flag |

## Don't use boolean for…

- **3+ states.** Use `string + options: ['draft', 'review', 'published']`.
- **Nullable boolean.** TinaCMS booleans default to `false` if absent. If you need true tri-state, use a string enum.

## `noIndex` + `noFollow` pattern

These are **independent**:

```typescript
{ name: 'noIndex', label: 'Hide from Search', type: 'boolean' }
{ name: 'noFollow', label: 'No Follow Links', type: 'boolean',
  description: 'Independent of noIndex' }
```

A page can be `noIndex: true, noFollow: false` (don't list me but follow my links) or vice versa. Don't combine them into one toggle.

## `draft` rendering pattern

Schema:

```typescript
{ name: 'draft', label: 'Draft', type: 'boolean', default: false }
```

Renderer (filter at query time):

```typescript
const result = await client.queries.postConnection({
  filter: process.env.NODE_ENV === 'production' ? { draft: { eq: false } } : undefined,
})
```

In production, drafts disappear. In dev, drafts appear so editors see what they're working on.

## `featured` pattern

Sort featured items first, then by date:

```typescript
const result = await client.queries.postConnection({
  sort: 'date',
})
const sorted = (result.data.postConnection.edges ?? []).sort((a, b) => {
  const aFeatured = a?.node?.featured ? 1 : 0
  const bFeatured = b?.node?.featured ? 1 : 0
  if (aFeatured !== bFeatured) return bFeatured - aFeatured
  return new Date(b!.node!.date!).getTime() - new Date(a!.node!.date!).getTime()
})
```

GraphQL doesn't support secondary sort, so do it in JS after fetch.

## Stored format

YAML/Markdown frontmatter:

```yaml
---
draft: true
noIndex: false
---
```

JSON:

```json
{ "draft": true, "noIndex": false }
```

## GraphQL filter

```typescript
const result = await client.queries.postConnection({
  filter: { draft: { eq: false } },
})
```

`eq` and `in` work on booleans.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `default: 'false'` (string) | Type mismatch | Use `default: false` |
| One boolean for `published` AND `notArchived` | Confusing — fix scope | Use clear booleans + a status enum |
| Forgot to filter drafts in production | Drafts leak | Add `filter: { draft: { eq: false } }` to production queries |
| Forgot to update sitemap to respect `noIndex` | SEO leak | Filter sitemap by `noIndex !== true` — see `references/seo/06-sitemap-and-robots.md` |
