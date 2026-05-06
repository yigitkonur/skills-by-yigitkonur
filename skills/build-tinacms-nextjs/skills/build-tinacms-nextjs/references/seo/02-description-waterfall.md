# Description Waterfall

Never leave the meta description empty. Implement a 4-step fallback chain.

## The waterfall

1. `page.seo.metaDescription` — explicit per-page override
2. `page.excerpt` (or `summary`, if your collection has it)
3. Auto-truncated first paragraph of body content (~155 chars)
4. `global.siteDescription` — final fallback

Why each step:

| Step | Reason |
|---|---|
| 1 | Editor wants explicit control — they wrote the description |
| 2 | Excerpt is editor-curated; better than auto-truncation |
| 3 | Body's opening paragraph is usually a good description |
| 4 | Global fallback prevents empty result |

## Implementation

```typescript
function resolveDescription(page: any, global: any): string {
  // 1. Explicit metaDescription
  if (page.seo?.metaDescription) {
    return page.seo.metaDescription
  }

  // 2. Excerpt
  if (page.excerpt) {
    return page.excerpt
  }

  // 3. Auto-truncate body
  const auto = autoTruncateBody(page.body)
  if (auto) return auto

  // 4. Global fallback
  return global.siteDescription || ''
}

function autoTruncateBody(body: any): string {
  if (!body) return ''
  // body is a rich-text AST; flatten the first few paragraphs to plain text
  const text = flattenRichText(body)
  if (!text) return ''
  return text.slice(0, 155).trim() + (text.length > 155 ? '…' : '')
}

function flattenRichText(node: any): string {
  if (typeof node === 'string') return node
  if (Array.isArray(node)) return node.map(flattenRichText).join(' ')
  if (node?.type === 'text') return node.text || ''
  if (node?.children) return flattenRichText(node.children)
  return ''
}
```

## Use in `generateMetadata`

```typescript
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  const [pageResult, globalResult] = await Promise.all([
    client.queries.page({ relativePath: `${slug}.md` }),
    client.queries.global({ relativePath: 'global.json' }),
  ])
  const page = pageResult.data.page
  const global = globalResult.data.global

  return {
    title: page.seo?.metaTitle || page.title,
    description: resolveDescription(page, global),
    // ...
  }
}
```

## Length validation

Aim for 120–160 characters. Too short → bare; too long → Google truncates with ellipsis.

In the TinaCMS schema:

```typescript
{
  name: 'metaDescription',
  type: 'string',
  ui: {
    component: 'textarea',
    validate: (value) => {
      if (!value) return undefined
      if (value.length > 160) return `${value.length}/160 — too long`
      if (value.length < 50) return `${value.length}/50 — too short`
      return undefined
    },
  },
}
```

Editors get live feedback on description length.

## Per-collection waterfall variations

Blog posts may have a different waterfall:

```typescript
function resolvePostDescription(post: any, global: any): string {
  return post.seo?.metaDescription
    || post.excerpt
    || post.summary
    || autoTruncateBody(post.body)
    || `${post.title} — ${global.siteName}`
}
```

Always end with a non-empty fallback.

## Title waterfall

Same idea for titles:

1. `page.seo.metaTitle` (explicit override)
2. `page.title` (the document title)
3. `global.siteName` (final fallback)

Combined with `titleTemplate`:

```typescript
const title = page.seo?.metaTitle || page.title
const fullTitle = global.titleTemplate?.replace('%s', title) || title
// e.g. "My Page | My Site"
```

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Empty description in production | SEO score drops; cards look bare | Always implement waterfall |
| Auto-truncation cuts mid-word | Description looks bad | Truncate at word boundaries |
| Used `???` or "Loading..." as fallback | Bad UX in social shares | Always provide a real string |
| Description over 160 chars | Truncated by Google | Validate with character limit |
| Description identical across pages | Duplicate-content signal | Vary per page (waterfall handles this) |
