# Collection Templates (multi-shape collections)

Use `templates` instead of `fields` when documents in the same collection have **structurally different shapes**. This is rare. The default is `fields`.

## When to use `templates`

Use it when:

- A `pages` collection holds both landing pages (with `hero`, `cta`, `features` fields) and legal pages (with `lastUpdated`, `body` only)
- A `posts` collection holds both `article` and `link` post types with very different fields
- A `cards` collection holds different card types each requiring different fields

Don't use it for:

- Pages that share most fields and differ in one toggle (use a discriminator field instead)
- Pages that share fields but differ in rendering (handle in the renderer, not the schema)

The blocks pattern (`object + list + templates`) is different — that's the right way to compose pages out of varied sections. Templates at the collection level are for documents where *the entire shape* differs.

## Schema example

```typescript
{
  name: 'page',
  label: 'Pages',
  path: 'content/pages',
  format: 'mdx',
  templates: [
    {
      name: 'landing',
      label: 'Landing Page',
      fields: [
        { name: 'title', type: 'string', isTitle: true, required: true },
        { name: 'hero', type: 'object', fields: [/* hero fields */] },
        { name: 'cta', type: 'object', fields: [/* cta fields */] },
        { name: 'body', type: 'rich-text', isBody: true },
      ],
    },
    {
      name: 'legal',
      label: 'Legal Page',
      fields: [
        { name: 'title', type: 'string', isTitle: true, required: true },
        { name: 'lastUpdated', type: 'datetime', required: true },
        { name: 'body', type: 'rich-text', isBody: true },
      ],
    },
  ],
}
```

## Documents must declare their template

Each document in a multi-shape collection needs `_template` in frontmatter:

```yaml
---
_template: landing
title: Welcome
hero:
  heading: ...
---

# Body content
```

Without `_template`, queries fail with:

```
GetCollection failed: Unable to fetch
template name was not provided
```

## When a single discriminator is enough — prefer that

If the difference is small (e.g. "this is a featured post"), a discriminator field is simpler:

```typescript
{
  name: 'post',
  fields: [
    { name: 'title', type: 'string' },
    {
      name: 'kind',
      type: 'string',
      options: ['standard', 'featured'],
    },
    { name: 'featuredImage', type: 'image' },  // optional, used when kind === 'featured'
    { name: 'body', type: 'rich-text', isBody: true },
  ],
}
```

Renderers branch on `post.kind`. No `_template` required, no multi-shape collection.

## Migrating from `templates` to `fields`

If you started with `templates` and realized you only have one shape, migrate:

1. Move `templates[0].fields` to `collection.fields`
2. Remove `_template:` lines from all documents:
   ```bash
   find content/posts -name '*.md' -exec sed -i '' '/^_template:/d' {} \;
   ```
3. Run `pnpm tinacms build` and verify content still loads

## Migrating from `fields` to `templates`

If you started with `fields` and now need `templates`:

1. Move `collection.fields` into `templates[0].fields` with a `name`/`label`
2. Add `_template: <name>` to existing documents:
   ```bash
   find content/pages -name '*.md' -exec sed -i '' '1a\
   _template: landing\
   ' {} \;
   ```
3. Add the second template alongside

## Querying multi-shape collections

The auto-generated GraphQL client returns a discriminated union:

```typescript
const result = await client.queries.page({ relativePath: 'home.mdx' })

// result.data.page is a union — narrow with __typename:
if (result.data.page.__typename === 'PageLanding') {
  // landing-page fields available
} else if (result.data.page.__typename === 'PageLegal') {
  // legal-page fields available
}
```

Renderers must handle each shape explicitly. There's no implicit fallback.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `_template` in a doc | "Template name was not provided" | Add `_template: <name>` to frontmatter |
| Used `templates` for a single shape | Editor sees a confusing template picker | Use `fields` instead |
| Mismatched template names between schema and frontmatter | Doc fails to load | Use the exact `name` value from schema |
| Querying without narrowing on `__typename` | TS errors / runtime nulls | Branch on `__typename` |

## Default stance

**Default to `fields`.** Use `templates` only when documents genuinely have different shapes that don't share most fields. The blocks pattern handles "different sections within one document" — that's a different mechanism.
