# `ui.router` Configuration

Per-collection function that maps a document to its live URL. Required for visual editing.

## Basic

```typescript
{
  name: 'page',
  ui: {
    router: ({ document }) => {
      if (document._sys.filename === 'home') return '/'
      return `/${document._sys.filename}`
    },
  },
  // ...
}
```

The function receives the document and returns a URL string. Returning `undefined` means "no live URL" — falls back to form-only editing for that document.

## Function signature

```typescript
ui: {
  router: ({
    collection,    // the collection definition
    document,      // the document being routed
  }) => string | undefined,
}
```

## Common patterns

### Homepage special-case

```typescript
router: ({ document }) => {
  if (document._sys.filename === 'home' || document._sys.filename === 'index') {
    return '/'
  }
  return `/${document._sys.filename}`
},
```

### Date-prefixed posts

```typescript
router: ({ document }) => {
  // filename like '2026-05-08-my-post' → URL '/blog/my-post'
  const filename = document._sys.filename
  const slug = filename.replace(/^\d{4}-\d{2}-\d{2}-/, '')
  return `/blog/${slug}`
},
```

### Nested paths via breadcrumbs

```typescript
router: ({ document }) => {
  // content/docs/guide/installation.md → /docs/guide/installation
  return `/docs/${document._sys.breadcrumbs.join('/')}`
},
```

### Per-collection prefixes

```typescript
// posts collection
router: ({ document }) => `/blog/${document._sys.filename}`

// docs collection
router: ({ document }) => `/docs/${document._sys.breadcrumbs.join('/')}`

// authors collection — no live page (no router returns undefined)
router: () => undefined
```

### Skip drafts

```typescript
router: ({ document }) => {
  if (document.draft) return undefined  // no preview for drafts
  return `/${document._sys.filename}`
},
```

## What `_sys` provides

```typescript
document._sys = {
  filename: 'my-post',                              // basename without extension
  breadcrumbs: ['guide', 'installation'],           // nested path components
  basename: 'my-post.md',                           // full filename
  path: 'content/docs/guide/installation.md',       // full file path
  relativePath: 'guide/installation.md',            // relative to collection path
  extension: 'md',                                   // file extension
}
```

## Editorial Workflow `previewUrl` (the other half)

`ui.router` returns the path; `ui.previewUrl` (collection-level config) returns the full URL with branch prefix:

```typescript
// tina/config.ts
ui: {
  previewUrl: (context) => ({
    url: `https://my-app-git-${context.branch}.vercel.app`,
  }),
}
```

Combined: editor on a draft branch clicks a page → preview opens at `https://my-app-git-feature.vercel.app/<router-path>`.

See `references/config/03-admin-and-ui.md`.

## Per-document override

There's no per-document `router` — only per-collection. If a document needs a unique URL pattern, branch in the collection-level function:

```typescript
router: ({ document }) => {
  if (document.kind === 'special') return `/special/${document._sys.filename}`
  return `/${document._sys.filename}`
},
```

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Returning a URL with leading `https://` | Tina treats as external; iframe breaks | Return relative path only |
| Forgot to add router | Click-to-edit in admin opens form-only | Add `router` |
| Returning `''` (empty string) | Preview opens at root by accident | Return `undefined` for "no preview" |
| Hardcoded `/blog/${filename}` for all posts | Breaks if blog moves | Use a layout constant or env var |
| Different base URLs in dev vs prod | Confusing | Use relative paths; let `previewUrl` handle host |
