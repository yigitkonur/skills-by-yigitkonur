# `object` field

Nested fields grouped into one struct. Used for SEO groups, address fields, image+alt+caption, and the blocks pattern.

## Basic (single object)

```typescript
{
  name: 'address',
  label: 'Address',
  type: 'object',
  fields: [
    { name: 'street', type: 'string' },
    { name: 'city', type: 'string' },
    { name: 'postalCode', type: 'string' },
  ],
}
```

The admin renders this as a grouped form section.

## Collapsible group (`ui.component: 'group'`)

```typescript
{
  name: 'seo',
  label: 'SEO & Social',
  type: 'object',
  ui: { component: 'group' },     // collapsible
  fields: seoFields,
}
```

Collapsed by default — secondary fields don't clutter the main form.

## List of objects (`list: true`)

```typescript
{
  name: 'features',
  label: 'Features',
  type: 'object',
  list: true,
  ui: {
    itemProps: (item) => ({ label: item?.title || 'Feature' }),
  },
  fields: [
    { name: 'icon', type: 'image' },
    { name: 'title', type: 'string', required: true },
    { name: 'description', type: 'string', ui: { component: 'textarea' } },
  ],
}
```

The repeatable group pattern. Always include `ui.itemProps` (see `references/schema/07-list-ui-customization.md`).

## List with multiple shapes (`templates`) — the blocks pattern

```typescript
{
  name: 'blocks',
  type: 'object',
  list: true,
  ui: { visualSelector: true },
  templates: [heroBlock, contentBlock, ctaBlock],
}
```

Each item can be one of the registered templates. See `references/schema/04-blocks-pattern.md`.

## Nested objects

```typescript
{
  name: 'cta',
  type: 'object',
  fields: [
    { name: 'text', type: 'string' },
    { name: 'url', type: 'string' },
    {
      name: 'style',
      type: 'object',
      fields: [
        { name: 'variant', type: 'string', options: ['primary', 'secondary'] },
        { name: 'size', type: 'string', options: ['sm', 'md', 'lg'] },
      ],
    },
  ],
}
```

Nest as deep as needed. Performance only suffers at extreme depth (10+ levels) which you'd never reach in practice.

## `defaultItem` (default list item shape)

```typescript
{
  name: 'features',
  type: 'object',
  list: true,
  ui: {
    defaultItem: { title: 'New feature', description: '' },
    itemProps: (item) => ({ label: item?.title }),
  },
  fields: [/* ... */],
}
```

When editor adds a new item, fields pre-populate.

## `addItemBehavior` (TinaCMS 3.x)

```typescript
ui: {
  addItemBehavior: 'prepend',   // 'append' default — prepend adds to top
}
```

Useful for blogs/feeds where new items belong at the top.

## `openFormOnCreate` (TinaCMS 3.6+)

```typescript
ui: {
  openFormOnCreate: true,
}
```

When a new list item is added, auto-navigate into the form so editors don't miss the empty fields.

## `visualSelector` (block templates only)

```typescript
{
  name: 'blocks',
  type: 'object',
  list: true,
  ui: { visualSelector: true },
  templates: [hero, content, cta, features],
}
```

Adds a visual block picker (with `previewSrc` thumbnails) when editor adds a new block. Without it, editors get a plain dropdown.

## Stored format

YAML/Markdown frontmatter:

```yaml
---
seo:
  metaTitle: 'My page'
  metaDescription: 'A description'
features:
  - title: 'Fast'
    description: 'Very fast'
  - title: 'Cheap'
    description: 'Free tier'
---
```

JSON:

```json
{
  "seo": { "metaTitle": "...", "metaDescription": "..." },
  "features": [{ "title": "...", "description": "..." }]
}
```

## Querying objects

```typescript
const result = await client.queries.page({ relativePath: 'home.md' })
// result.data.page.seo            // the SEO object
// result.data.page.seo.metaTitle  // string
// result.data.page.features       // array of feature objects
```

GraphQL doesn't support filtering by nested object fields directly — query and filter in JS.

## Common patterns

### SEO group on every collection

See `references/schema/05-reusable-field-groups.md`.

### Image + alt + caption

```typescript
{
  name: 'hero',
  type: 'object',
  fields: [
    { name: 'src', type: 'image', required: true },
    { name: 'alt', type: 'string', required: true },
    { name: 'caption', type: 'string' },
  ],
}
```

### CTA group

```typescript
{
  name: 'cta',
  type: 'object',
  fields: [
    { name: 'text', type: 'string' },
    { name: 'url', type: 'string' },
    { name: 'openInNewTab', type: 'boolean' },
  ],
}
```

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| List without `ui.itemProps` | "Item 0" labels | Add the function |
| Forgot `defaultItem` for blocks | Empty form when adding new block | Add sensible defaults |
| Used `templates` array but only one shape | Editor sees redundant template picker | Use `fields` directly |
| Used `fields` when shapes truly differ | Schema bloat | Use `templates` |
| Reused field name across multiple objects in same collection | Confusing, but works | Use unique names per object |
