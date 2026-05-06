# Schema Overview

The schema is the heart of TinaCMS. It defines:

- **Collections** — content types (think tables in a database)
- **Fields** — the data shape and editing UI for each document
- **Templates** — alternate document shapes within a single collection
- **Blocks** — repeatable content sections (templates inside an `object + list` field)

## The trinity: Collections, Fields, Templates

```
Collection            ← `Pages`, `Posts`, `Authors` (one per content type)
└── Document          ← One file in the collection (e.g. `home.md`)
    └── Fields        ← Title, body, blocks, SEO
        └── Templates ← Hero block, content block, CTA block (multiple shapes)
```

## Collection types

| Kind | When to use | Config |
|---|---|---|
| **Folder** | Many documents (pages, posts, authors) | `path: 'content/pages'` — files at `content/pages/*.md` |
| **Singleton** | One document (site settings, navigation) | `ui.global: true`, `allowedActions: { create: false, delete: false }` |

See `references/schema/01-collections.md` for full collection properties.

## Single-shape vs multi-shape collections

A collection can have either:

- **`fields`** — every document has the same shape. Editor doesn't pick a template.
- **`templates`** — multiple shapes; editor picks one when creating a doc. Documents must have `_template: <name>` in frontmatter.

```typescript
// Single shape
{
  name: 'post',
  fields: [
    { name: 'title', type: 'string' },
    { name: 'body', type: 'rich-text' },
  ],
}

// Multi shape (rare; useful when a "page" can be either a landing or a legal page)
{
  name: 'page',
  templates: [
    {
      name: 'landing',
      fields: [/* landing-specific */],
    },
    {
      name: 'legal',
      fields: [/* legal-specific */],
    },
  ],
}
```

**Rule of thumb:** prefer `fields`. Use `templates` only when document shapes genuinely differ. See `references/schema/02-collection-templates.md`.

## The blocks pattern

For page builders, use a **single field** of type `object + list + templates`:

```typescript
{
  name: 'page',
  fields: [
    { name: 'title', type: 'string', isTitle: true },
    {
      name: 'blocks',
      type: 'object',
      list: true,
      ui: { visualSelector: true },
      templates: [heroBlock, contentBlock, ctaBlock],
    },
  ],
}
```

Editors add/reorder/remove blocks of different types within one document. This is the most common pattern for marketing sites. See `references/schema/04-blocks-pattern.md`.

## Field types matrix

| Type | Stores | Widget | See |
|---|---|---|---|
| `string` | string | text input (or list/select) | `references/field-types/01-string.md` |
| `number` | number | number input | `references/field-types/02-number.md` |
| `boolean` | boolean | toggle | `references/field-types/03-boolean.md` |
| `datetime` | ISO 8601 string | date picker | `references/field-types/04-datetime.md` |
| `image` | string (path) | image picker | `references/field-types/05-image.md` |
| `reference` | document ID | document picker | `references/field-types/06-reference.md` |
| `object` | nested fields | grouped form | `references/field-types/07-object.md` |
| `rich-text` | AST (markdown/MDX) | markdown editor | `references/field-types/08-rich-text-markdown.md` |
| `rich-text + templates` | AST with embedded JSX | MDX editor | `references/field-types/09-rich-text-mdx.md` |

## Naming rules (must follow)

Field and collection `name` values must be **alphanumeric + underscores only**. No hyphens, spaces, or special chars. Reserved names: `children` (inside rich-text templates only), `mark`, `_template`, `_sys`, `id`, `__typename`. See `references/schema/03-naming-rules.md`.

## Default-shape collections to start with

For most projects, four collections cover 90% of needs:

| Collection | Type | Purpose |
|---|---|---|
| `pages` | Folder, blocks pattern | Marketing pages, landing pages |
| `posts` | Folder, MDX body | Blog posts |
| `global` | Singleton | siteName, defaults |
| `navigation` | Singleton | Main nav + footer links |

See `references/schema/08-default-collection-set.md` for the full starter schema.

## Reading order

1. `references/schema/01-collections.md` — folder vs singleton, all properties
2. `references/schema/03-naming-rules.md` — what's allowed in names
3. `references/field-types/00-overview.md` — pick field types
4. `references/schema/04-blocks-pattern.md` — for page builders
5. `references/schema/05-reusable-field-groups.md` — DRY field groups (CTA, SEO)
6. `references/schema/02-collection-templates.md` — multi-shape collections (only if needed)
7. `references/schema/06-content-hooks.md` — `beforeSubmit` for slug auto-generation
8. `references/schema/07-list-ui-customization.md` — `ui.itemProps` to never see "Item 0"
9. `references/schema/08-default-collection-set.md` — the starter set

## Validation tools

```bash
pnpm dlx @tinacms/cli@latest audit
```

Catches:

- Field-name conflicts (hyphens, reserved names)
- Path mismatches (collection `path` doesn't match disk)
- Missing `_template` in documents from `templates` collections
- Schema vs content drift

Run after every schema change.
