# Collections

A collection defines a content type — a directory of documents with a shared schema.

## Folder collection (multiple documents)

```typescript
{
  name: 'page',                  // internal identifier
  label: 'Pages',                // shown in admin
  path: 'content/pages',         // filesystem location, no trailing slash
  format: 'mdx',                 // md, mdx, markdown, json, yaml, toml
  ui: {
    router: ({ document }) => `/${document._sys.filename}`,
  },
  fields: [/* ... */],
}
```

Files at `content/pages/*.{md,mdx}` — one file = one document.

## Singleton collection (one document)

```typescript
{
  name: 'settings',
  label: 'Site Settings',
  path: 'content/settings',
  format: 'json',
  ui: {
    global: true,                          // appears in admin "global" section
    allowedActions: {
      create: false,                       // editor can't make new ones
      delete: false,                       // can't be deleted
    },
  },
  fields: [/* ... */],
}
```

Used for site-wide settings, navigation, footer config.

## All collection properties

| Property | Required | Purpose |
|---|---|---|
| `name` | yes | Internal identifier (alphanumeric + underscores) |
| `label` | yes | Display name in admin |
| `path` | yes | Filesystem directory relative to project root |
| `format` | no | File format (default `md`) |
| `fields` | one of | Single shape — every doc identical |
| `templates` | one of | Multiple shapes — docs need `_template` in frontmatter |
| `ui.router` | recommended | Function returning the live URL for a doc |
| `ui.global` | no | Show this collection in the admin's "global" section |
| `ui.filename` | no | Customize filename generation for new docs |
| `ui.allowedActions` | no | Lock create/delete for singletons |
| `ui.beforeSubmit` | no | Hook to mutate values on save |
| `ui.defaultItem` | no | Default values for new docs |
| `match` | no | Glob filter — restrict which files in `path` are part of the collection |
| `defaultItem` | no | Default content for new docs |

## `format` options

| Format | File ext | Frontmatter | Body |
|---|---|---|---|
| `md` | `.md` | YAML frontmatter | Plain markdown body |
| `mdx` | `.mdx` | YAML frontmatter | MDX body (markdown + JSX) |
| `markdown` | `.markdown` | YAML | Same as `md` |
| `json` | `.json` | n/a | All fields are JSON |
| `yaml` | `.yaml` / `.yml` | n/a | All fields are YAML |
| `toml` | `.toml` | n/a | All fields are TOML |

**For body content use `md` or `mdx`.** Use `mdx` if you need to embed React components in the body via the `templates` rich-text field. **For structured data without a body use `json`.**

## `ui.router`

Tells TinaCMS what URL the document maps to in your live site. Used for:

1. Click-to-edit jumps from admin to the live page
2. Editorial workflow preview links
3. The visual editing iframe

```typescript
ui: {
  router: ({ document }) => {
    if (document._sys.filename === 'home') return '/'
    return `/${document._sys.filename}`
  },
}
```

For nested paths (e.g. `/docs/setup/installation`), use `_sys.breadcrumbs`:

```typescript
ui: {
  router: ({ document }) => {
    return `/docs/${document._sys.breadcrumbs.join('/')}`
  },
}
```

Returning `undefined` means "no live URL" — falls back to form-only editing.

## `ui.filename` (customizing new-doc filenames)

By default, TinaCMS uses the title to slugify a filename. To override:

```typescript
ui: {
  filename: {
    readonly: false,
    slugify: (values) => {
      return `${new Date().toISOString().split('T')[0]}-${values.title?.toLowerCase().replace(/\s+/g, '-')}`
    },
  },
}
```

Useful for date-prefixed blog posts (`2026-05-08-my-post.md`).

## `match` (glob filter)

If multiple collections live in overlapping directories:

```typescript
{
  name: 'post',
  path: 'content/posts',
  match: {
    include: '**/*',
    exclude: '_drafts/**',  // exclude draft folder from this collection
  },
  // ...
}
```

Most projects don't need this.

## `defaultItem` (default values for new docs)

```typescript
defaultItem: () => ({
  title: 'New Page',
  date: new Date().toISOString(),
  draft: true,
}),
```

Editors get sensible defaults instead of an empty form.

## Collection-level vs field-level `defaultItem`

- **Collection-level** `defaultItem`: applied when a new document is created in this collection
- **Field-level** `ui.defaultItem` (on a block template): applied when a new instance of that block is added

Both work; pick the right level for the use case.

## File location patterns

| Use | `path` |
|---|---|
| Pages | `content/pages` |
| Blog posts | `content/posts` |
| Docs | `content/docs` |
| Authors | `content/authors` |
| Site settings (singleton) | `content/settings` |
| Navigation (singleton) | `content/navigation` |

The `content/` prefix is convention; you can use `data/`, `cms/`, or anything. Stay consistent within a project.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `path: 'content/posts/'` (trailing slash) | Files not found, queries empty | Remove trailing slash |
| `path: 'posts'` (missing parent) | Files not found | Match actual directory |
| `path: '/Users/me/.../posts'` (absolute) | Schema fails | Use relative-to-project paths |
| Forgot `format: 'mdx'` for MDX content | Body parsed as plain markdown | Set `format: 'mdx'` |
| Singleton without `allowedActions` | Editors create duplicates | Add `allowedActions: { create: false, delete: false }` |
| Missing `ui.router` | Click-to-edit defaults to form-only | Add `router` returning live URL |

## Verification

```bash
pnpm dlx @tinacms/cli@latest audit
```

Reports any path mismatches between schema and disk.
