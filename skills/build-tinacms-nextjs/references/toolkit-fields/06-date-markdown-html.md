# Date, Markdown, and HTML Plugins

Less-common toolkit plugins for specific use cases.

## `date` (default for datetime)

```typescript
{ name: 'publishDate', type: 'datetime' }
// Implicit: ui.component: 'date'
```

Behavior:

- Date picker
- Optional time picker
- Stores ISO 8601 string

See `references/field-types/04-datetime.md` for full datetime patterns.

### Date-only (no time)

```typescript
{
  name: 'date',
  type: 'datetime',
  ui: {
    dateFormat: 'YYYY-MM-DD',
    timeFormat: false,
  },
}
```

## `markdown`

```typescript
{
  name: 'shortBody',
  type: 'string',
  ui: { component: 'markdown' },
}
```

Behavior:

- Markdown editor (subset of full rich-text)
- Plain markdown stored as a string (not AST)
- Lighter than `rich-text` for simple use cases

When to use:

- Comments, descriptions, simple snippets where rich-text is overkill
- Migrating from a system that stored raw markdown strings

When NOT to use:

- Document body (use `rich-text + isBody` instead)
- Anything needing MDX templates (use `rich-text + templates`)
- Complex formatting needs (rich-text gives a fuller editing UX)

## `html`

```typescript
{
  name: 'embedCode',
  type: 'string',
  ui: { component: 'html' },
}
```

Behavior:

- Plain HTML editor
- No syntax highlighting (use a custom field component for that)
- Stored as raw HTML string

When to use:

- Embedding third-party widget HTML (analytics scripts, embedded forms)
- Migrating legacy HTML content

When NOT to use:

- Body content (use `rich-text` instead)
- Anything where editors should not write raw HTML

⚠️ **XSS warning:** content from this field is dangerously trusted. If you render with `dangerouslySetInnerHTML`, sanitize it server-side first.

## Renderer side for markdown / HTML strings

```tsx
// markdown stored as string — render with a markdown library:
import { compileMDX } from 'next-mdx-remote/rsc'
const compiled = await compileMDX({ source: data.shortBody })

// HTML — render with sanitization:
import DOMPurify from 'isomorphic-dompurify'
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(data.embedCode) }} />
```

## When to skip these and use rich-text

For anything that becomes part of the document body, prefer `rich-text + isBody:true`:

- Editor gets toolbar
- Stored as AST (round-trips cleanly)
- Renders with `<TinaMarkdown>` (no sanitization needed since AST is structured)

`markdown` and `html` plugins are fallbacks when rich-text doesn't fit.

## Common mistakes

| Mistake | Fix |
|---|---|
| `markdown` plugin for body content | Use `rich-text + isBody` |
| `html` field rendered without sanitization | Sanitize with DOMPurify or similar |
| `date` widget with `timeFormat: false` but storage is full ISO | Storage is correct (T00:00:00); display only changes |
| Using `markdown` for MDX content | Use `rich-text + templates` instead |
