# `rich-text` field (markdown body)

Rich-text is TinaCMS's most-used field for body content. Stores an AST that can be rendered with `<TinaMarkdown>`.

## Basic body field

```typescript
{
  name: 'body',
  label: 'Body',
  type: 'rich-text',
  isBody: true,        // marks this as the document body
}
```

`isBody: true` tells TinaCMS:

- This field's content goes in the body of the markdown file (after frontmatter)
- The admin shows this as the main editor area, not a sidebar form

## Stored format

For `format: 'md'`:

```markdown
---
title: My page
---

# Hello

This is **bold** content.

- list item
- another
```

The AST roundtrips to standard markdown. Edit-then-save produces clean markdown unchanged from human-readable form.

## Toolbar customization

```typescript
{
  name: 'body',
  type: 'rich-text',
  isBody: true,
  toolbarOverride: ['heading', 'bold', 'italic', 'link', 'ul', 'ol'],
  // OR omit entirely to use the default toolbar
}
```

Available toolbar items:

| Item | Behavior |
|---|---|
| `heading` | H1-H6 picker |
| `link` | Inline link |
| `image` | Inline image |
| `quote` | Block quote |
| `ul` | Unordered list |
| `ol` | Ordered list |
| `bold` | Bold |
| `italic` | Italic |
| `code` | Inline code |
| `codeBlock` | Fenced code block |
| `mermaid` | Mermaid diagram block |
| `table` | Markdown table |
| `raw` | Raw HTML/MDX block |
| `embed` | Embed (YouTube, Twitter, etc.) |

Per-collection customization: trim the toolbar for blog posts, expand for landing pages.

## Floating toolbar

```typescript
{
  type: 'rich-text',
  isBody: true,
  showFloatingToolbar: false,    // disable the floating toolbar
}
```

Default is `true` — a floating toolbar appears on text selection.

## Rendering

```tsx
import { TinaMarkdown } from 'tinacms/dist/rich-text'

<TinaMarkdown content={data.post.body} />
```

For the components prop (overriding default elements + custom MDX templates), see `references/rendering/04-tinamarkdown.md` and `references/rendering/06-overriding-builtins.md`.

## Default toolbar items render to

| Markdown | Rendered HTML |
|---|---|
| `# Heading` | `<h1>` (also h2-h6) |
| `**bold**` | `<strong>` |
| `*italic*` | `<em>` |
| `[text](url)` | `<a>` |
| `![alt](url)` | `<img>` |
| `> quote` | `<blockquote>` |
| `- item` | `<ul><li>` |
| `1. item` | `<ol><li>` |
| `` `code` `` | `<code>` |
| Triple-backtick block | `<pre>` (default) or `code_block` component override |
| `\| col \| col \|` | `<table>` |

## Image handling in body

When editor inserts an image:

- File uploads to the configured media store
- The path is inserted as `![alt](path)` in markdown

Renderers can map `img` elements to `next/image` for optimization (see `references/rendering/06-overriding-builtins.md`).

## Body vs frontmatter

```typescript
{
  name: 'body',
  type: 'rich-text',
  isBody: true,
}

// vs

{
  name: 'description',
  type: 'rich-text',
  // no isBody — stored in frontmatter as a serialized AST
}
```

`isBody: true` puts the content in the markdown body. Without it, the rich-text AST is stored in YAML/JSON frontmatter — works but less readable in the source file.

**Convention:** one `isBody` field per collection (the main content). Other rich-text fields (sidebar, callout text) without `isBody`.

## Performance

Rich-text bodies up to ~100KB render fine. Beyond that:

- Editor lag (parsing the AST on every keystroke)
- Slow query parsing

For very long content, consider splitting into multiple rich-text fields or sections.

## When NOT to use rich-text

- **Single-line content:** use `string` instead.
- **Plain text without formatting:** use `string + textarea`.
- **Page-builder sections:** use the blocks pattern (`object + list + templates`).
- **Body with React components:** use `rich-text + templates` (see `references/field-types/09-rich-text-mdx.md`).

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Multiple `isBody: true` fields | Schema build fails | Pick one |
| `isBody: true` on a non-rich-text field | Schema fails | Only rich-text supports isBody |
| `format: 'mdx'` collection but rich-text has no `templates` | Body parses as plain markdown | Add templates if you want JSX |
| Rich-text body but `format: 'json'` | Body stored as serialized AST in JSON (ugly) | Use `format: 'md'` or `'mdx'` |
| Rendered without `<TinaMarkdown>` | Shows AST as `[object Object]` | Use `<TinaMarkdown content={...} />` |
