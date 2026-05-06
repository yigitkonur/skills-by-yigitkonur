# `rich-text` with MDX templates

When you want editors to embed React components inside the body — e.g. a `<Cta>`, `<Callout>`, or `<YouTubeEmbed>`. This is what makes TinaCMS uniquely powerful for component-driven content.

## Schema

```typescript
{
  name: 'post',
  format: 'mdx',         // ← required for MDX content
  fields: [
    {
      name: 'body',
      type: 'rich-text',
      isBody: true,
      templates: [
        {
          name: 'Cta',                    // becomes <Cta /> in the body
          label: 'Call to Action',
          fields: [
            { name: 'heading', type: 'string' },
            { name: 'href', type: 'string' },
          ],
        },
        {
          name: 'Callout',
          label: 'Callout Box',
          fields: [
            {
              name: 'tone',
              type: 'string',
              options: ['info', 'warn', 'success'],
            },
            { name: 'children', type: 'rich-text' },  // nested rich-text
          ],
        },
        {
          name: 'YouTubeEmbed',
          label: 'YouTube Video',
          fields: [
            { name: 'videoId', type: 'string', required: true },
            { name: 'autoplay', type: 'boolean' },
          ],
        },
      ],
    },
  ],
}
```

## Rules

- **Collection `format` must be `'mdx'`.** Plain `'md'` doesn't support JSX in the body.
- **Template `name` is the JSX tag.** PascalCase per React convention.
- **`children` field is special** inside an MDX template — for nested rich-text content. **Don't use `children` for non-rich-text fields**; it conflicts.
- **Don't use `mark` as a field name** — also reserved.

## What editors see

In the rich-text editor, editors hit `/` to insert a template. They get a picker:

```
/  → Cta — Call to Action
   → Callout — Callout Box
   → YouTubeEmbed — YouTube Video
```

Picking one inserts a JSX-style block:

```mdx
This is some text.

<Cta heading="Get Started" href="/signup" />

More text here.

<Callout tone="info">
  Some helpful note.
</Callout>
```

Editors can edit the props through a form panel, or click into the JSX directly.

## Stored format

`.mdx` file:

```mdx
---
title: My Post
---

This is the intro paragraph.

<Cta heading="Get Started Today" href="/signup" />

More content...

<Callout tone="info">
  This is the callout body — also rich-text content.
</Callout>
```

Markdown text and JSX components interleave naturally.

## Renderer side: `TinaMarkdown` + components map

```tsx
'use client'

import { TinaMarkdown, type Components } from 'tinacms/dist/rich-text'
import { useTina, tinaField } from 'tinacms/dist/react'
import { CalloutBox } from '@/components/CalloutBox'

const components: Components<{
  Cta: { heading?: string; href?: string }
  Callout: { tone?: 'info' | 'warn' | 'success'; children?: any }
  YouTubeEmbed: { videoId: string; autoplay?: boolean }
}> = {
  Cta: (props) => (
    <a className="cta-button" href={props.href}>
      {props.heading}
    </a>
  ),
  Callout: (props) => (
    <CalloutBox tone={props.tone}>
      {props.children && <TinaMarkdown content={props.children} components={components} />}
    </CalloutBox>
  ),
  YouTubeEmbed: (props) => (
    <iframe
      src={`https://www.youtube.com/embed/${props.videoId}${props.autoplay ? '?autoplay=1' : ''}`}
      width={560}
      height={315}
      allow="autoplay; encrypted-media"
    />
  ),
}

export default function PostClient(props: any) {
  const { data } = useTina(props)
  return (
    <article>
      <h1 data-tina-field={tinaField(data.post, 'title')}>{data.post.title}</h1>
      <div data-tina-field={tinaField(data.post, 'body')}>
        <TinaMarkdown content={data.post.body} components={components} />
      </div>
    </article>
  )
}
```

**Key points:**

- The `components` map keys must match the schema template `name` values exactly.
- For nested `children` fields (rich-text inside a template), recursively render via `TinaMarkdown`.
- Pass the same `components` map down to nested `TinaMarkdown` calls.

## Custom components and `tinaField` (the MDX template trick)

React components don't accept arbitrary HTML attributes like `data-tina-field`. To make an MDX-embedded component editable inline, accept the field as a prop and forward to the DOM:

```tsx
function CalloutBox({ tinaField, children, tone }: { tinaField?: string; children?: any; tone?: string }) {
  return (
    <div data-tina-field={tinaField} className={`callout callout-${tone}`}>
      {children}
    </div>
  )
}

// In components map:
Callout: (props) => (
  <CalloutBox tinaField={tinaField(props)} tone={props.tone}>
    {props.children && <TinaMarkdown content={props.children} components={components} />}
  </CalloutBox>
),
```

`tinaField(props)` automatically reads `_content_source` metadata that TinaCMS injects in edit mode.

To target a specific field inside the component:

```tsx
<div data-tina-field={tinaField(props, 'tone')}>
  Tone: {props.tone}
</div>
```

The second argument is the field name within the template.

## Default value (`defaultItem`)

```typescript
templates: [
  {
    name: 'Cta',
    fields: [...],
    defaultItem: {
      heading: 'Get Started',
      href: '#',
    },
  },
]
```

When editors insert a new `<Cta />`, fields prepopulate.

## Toolbar additions

The MDX templates add to the editor's toolbar/palette automatically. Editors discover them via the `/` slash menu.

## Common patterns

### Embedded YouTube/Vimeo

```typescript
{
  name: 'VideoEmbed',
  fields: [
    { name: 'platform', type: 'string', options: ['youtube', 'vimeo'] },
    { name: 'videoId', type: 'string', required: true },
  ],
}
```

### Tabs / accordion

```typescript
{
  name: 'Tabs',
  fields: [
    {
      name: 'tabs',
      type: 'object',
      list: true,
      fields: [
        { name: 'label', type: 'string' },
        { name: 'children', type: 'rich-text' },
      ],
    },
  ],
}
```

### Pull-quote

```typescript
{
  name: 'PullQuote',
  fields: [
    { name: 'children', type: 'rich-text' },     // the quote
    { name: 'attribution', type: 'string' },
  ],
}
```

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Collection `format: 'md'` (not 'mdx') | JSX renders as raw text | Set `format: 'mdx'` |
| Template name `cta` (lowercase) | Editor inserts `<cta />` (invalid JSX) | Use `Cta` (PascalCase) |
| `children` used for non-rich-text field | Schema build fails | Rename to anything else |
| Components map key doesn't match template name | Component doesn't render | Match exactly |
| Forgot to recurse into `<TinaMarkdown>` for nested children | Children render as `[object]` | Recursively render |
| Component doesn't forward `data-tina-field` | Click-to-edit doesn't work for MDX components | Accept `tinaField` prop, forward to DOM |
