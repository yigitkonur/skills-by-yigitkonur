# Reserved Names

Names that TinaCMS reserves for internal use. Don't use them as field, collection, or template names.

## The list

| Name | Reserved for | Where |
|---|---|---|
| `children` | Rich-text AST children | Inside `rich-text` templates only |
| `mark` | Rich-text markup nodes | Globally |
| `_template` | Multi-shape collection discriminator | Globally |
| `_sys` | Document metadata (filename, breadcrumbs, lastModified) | Globally |
| `id` | Document ID | Globally |
| `__typename` | GraphQL type discriminator | Globally |

## Why each is reserved

### `children` — rich-text only

```typescript
// ✅ OK: regular field
{ name: 'children', type: 'object', list: true, fields: [...] }

// ❌ Inside rich-text template — conflicts with the AST's `children`
{
  type: 'rich-text',
  templates: [
    {
      name: 'Callout',
      fields: [
        { name: 'children', type: 'string' },  // ❌ not allowed
      ],
    },
  ],
}
```

**Exception:** `children` IS used as a field name when you want **nested rich-text inside an MDX template**:

```typescript
{
  name: 'Callout',
  fields: [
    { name: 'children', type: 'rich-text' },  // ✅ this works (rich-text type only)
  ],
}
```

The reserved-ness applies to non-rich-text fields named `children` *inside* rich-text templates. For regular collections (not in a rich-text template), `children` is fine — but consider using `submenu` or `items` for clarity.

### `mark` — globally reserved

Conflicts with rich-text marks (bold, italic, code spans). If you need a "mark" field, name it `marker`, `bookmark`, or `highlight`.

### `_template` — discriminator

Used by multi-shape collections (`templates: [...]`) to tell the parser which template to apply to a document:

```yaml
---
_template: landing
---
```

If you create a field named `_template`, it collides with this internal use. Rename to `pageType` or `kind`.

### `_sys` — document metadata

The auto-generated GraphQL response includes a `_sys` object on every document:

```typescript
result.data.page._sys.filename       // 'home'
result.data.page._sys.breadcrumbs    // ['blog', 'my-post']
result.data.page._sys.lastModified   // ISO date
result.data.page._sys.path           // 'content/pages/home.md'
```

Don't use `_sys` as a field name — you'd shadow these.

### `id` — internal document ID

Tina assigns each document an internal ID. Don't define your own `id` field; if you need a custom ID use `slug`, `uid`, or `documentId`.

### `__typename` — GraphQL discriminator

GraphQL uses `__typename` to discriminate union types in responses. Don't define a field with this name — Tina relies on it for the blocks pattern.

## What about `slug`?

`slug` is **not reserved** but is conventionally used for URL slugs. If you define a `slug` field:

- Fine, no conflict
- Use it in your renderer as the URL identifier
- Don't expect TinaCMS to auto-populate it — write a `beforeSubmit` hook for that

## What about `seo`?

Not reserved. Convention only. Standard practice is to use a field named `seo` for the SEO field group.

## What about `image`?

Not reserved. Despite being the field type name, it's also valid as a field name (`{ name: 'image', type: 'image' }` works).

But for clarity, prefer descriptive names: `heroImage`, `coverImage`, `avatar`.

## Adjacent gotchas

These aren't reserved but cause confusion:

| Name | Why be careful |
|---|---|
| `body` | Convention — usually `isBody: true`. Don't use elsewhere. |
| `title` | Convention — usually `isTitle: true`. Use `name` or `label` if you mean something else. |
| `date` | GraphQL has no Date type — TinaCMS uses string. Make sure you mean ISO datetime. |
| `tags` | Convention — usually `string + list`. Use `categories`, `topics`, or `subjects` for distinct meanings. |

## Validation

The CLI catches reserved-name violations at schema build time:

```bash
pnpm tinacms build
# ERROR: Field name 'children' is reserved in rich-text template 'Callout'
```

Run `pnpm tinacms build` after every schema change to catch these early.

## Common mistakes

| Mistake | Fix |
|---|---|
| `name: 'children'` for non-rich-text field inside MDX template | Rename to `items`, `submenu`, `subFields` |
| `name: 'mark'` for highlight field | Rename to `highlight` or `marker` |
| `name: '_template'` to override the discriminator | Use a non-reserved name like `pageKind` |
| `name: '_sys'` for "system" fields | Use `meta`, `system`, or specific names |
| `name: 'id'` for custom IDs | Use `slug`, `uid`, `documentId` |
