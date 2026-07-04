# Tags and List Plugins

For string lists with tag-style input.

## `tags` (free-form)

```typescript
{
  name: 'keywords',
  type: 'string',
  list: true,
  ui: { component: 'tags' },
}
```

Behavior:

- Editor types each tag, presses Enter or comma
- Each tag becomes a chip
- Click X on a chip to remove

## Default list (no `tags` component)

```typescript
{
  name: 'tags',
  type: 'string',
  list: true,
}
```

Renders as a list with "Add Item" button — editor adds each value through a small text input. More verbose than `tags` plugin; stick with `tags` for free-form input.

## `tags` with options (curated)

```typescript
{
  name: 'categories',
  type: 'string',
  list: true,
  options: ['design', 'engineering', 'product'],
}
```

When `options` is present, multi-select dropdown is the natural widget — `tags` widget falls back to it.

## When to use tags vs reference

| Scenario | Use |
|---|---|
| < 50 tag values, free-form | `string + list + tags` |
| < 50 curated values | `string + list + options` |
| > 50 values, structured (each tag has its own page) | `reference + collections: ['tag']` |

## Stored format

```yaml
---
keywords: ['react', 'typescript', 'tinacms', 'nextjs']
---
```

YAML array. Renderer accesses as `data.keywords` (`string[]`).

## Querying lists

GraphQL filter `in` operator:

```typescript
const result = await client.queries.postConnection({
  filter: { tags: { in: ['react'] } },  // posts where tags includes 'react'
})
```

The exact syntax depends on TinaCMS version — see `references/graphql/04-filter-documents.md`.

## Common mistakes

| Mistake | Fix |
|---|---|
| `list: true` without `ui.component: 'tags'` for free-form | Editor sees verbose "Add Item" UI | Add `'tags'` component |
| Storing tags as comma-separated string | Use `string + list:true` instead |
| > 100 free-form tags | Switch to a `tag` collection + `reference` |
