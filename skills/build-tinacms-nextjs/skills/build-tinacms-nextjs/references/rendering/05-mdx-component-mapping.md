# MDX Component Mapping

How to map schema-defined MDX templates to React components.

## The mapping rule

Every template `name` in the schema maps to a key in the `components` prop:

```typescript
// Schema:
templates: [
  { name: 'Cta', fields: [...] },        // schema name
  { name: 'YouTubeEmbed', fields: [...] },
]

// Renderer:
const components = {
  Cta: (props) => /* matching key */,
  YouTubeEmbed: (props) => /* matching key */,
}
```

**Names must match exactly.** Mismatched key → component doesn't render.

## Centralizing the components map

```tsx
// components/MdxComponents.tsx
import { TinaMarkdown, type Components, type TinaMarkdownContent } from 'tinacms/dist/rich-text'
import { CalloutBox } from './CalloutBox'

export const mdxComponents: Components<{
  Cta: { heading?: string; href?: string }
  Callout: { tone?: 'info' | 'warn' | 'success'; children?: TinaMarkdownContent }
  YouTubeEmbed: { videoId: string; autoplay?: boolean }
  CodeSnippet: { language?: string; children?: string }
}> = {
  Cta: (props) => (
    <a className="cta-button" href={props.href}>
      {props.heading}
    </a>
  ),

  Callout: (props) => (
    <CalloutBox tone={props.tone || 'info'}>
      {props.children && (
        <TinaMarkdown content={props.children} components={mdxComponents} />
      )}
    </CalloutBox>
  ),

  YouTubeEmbed: (props) => (
    <iframe
      src={`https://www.youtube.com/embed/${props.videoId}${props.autoplay ? '?autoplay=1' : ''}`}
      width={560}
      height={315}
      allow="autoplay; encrypted-media"
      title="YouTube video"
    />
  ),

  CodeSnippet: (props) => (
    <pre className={`language-${props.language || 'text'}`}>
      <code>{props.children}</code>
    </pre>
  ),
}
```

Reusable across pages — every page that renders a body imports `mdxComponents` and passes it.

## Handling nested rich-text (`children`)

When an MDX template has a `children: rich-text` field, recursively render through `TinaMarkdown`:

```tsx
Callout: (props) => (
  <CalloutBox tone={props.tone}>
    {props.children && (
      <TinaMarkdown content={props.children} components={mdxComponents} />
    )}
  </CalloutBox>
),
```

The `children` rich-text content is itself an AST that needs rendering — pass the same `components` map down so nested templates work.

## Fallback for missing template

```tsx
const mdxComponents = {
  Cta: (props) => /* ... */,
  Callout: (props) => /* ... */,

  // Generic fallback:
  __unknownComponent: (props) => {
    if (process.env.NODE_ENV !== 'production') {
      console.warn('Unknown MDX component:', props)
    }
    return null  // or render something visible in dev
  },
}
```

TinaCMS doesn't have a first-class `__unknownComponent` slot — you handle this by always defining a component for every schema template. If a template renders `<Foo>` but the components map has no `Foo`, the renderer logs a warning and renders nothing.

**Best practice:** keep the schema templates and the components map in lockstep. When you add a template, add a component. Type the components map with `Components<...>` so TS catches missing entries.

## Targeting specific fields with `tinaField` inside MDX

```tsx
import { tinaField } from 'tinacms/dist/react'

Cta: (props) => (
  <a
    data-tina-field={tinaField(props, 'heading')}  // target the heading field
    href={props.href}
  >
    {props.heading}
  </a>
),
```

`tinaField(props)` (no second arg) targets the whole template instance.
`tinaField(props, 'fieldName')` targets a specific field within it.

See `references/visual-editing/04-tinamarkdown-tinafield.md`.

## Components that wrap children in DOM elements

If you wrap children in a custom component, propagate `data-tina-field` via prop:

```tsx
function CalloutBox({ tinaFieldRef, tone, children }: any) {
  return (
    <div data-tina-field={tinaFieldRef} className={`callout callout-${tone}`}>
      {children}
    </div>
  )
}

Callout: (props) => (
  <CalloutBox tinaFieldRef={tinaField(props)} tone={props.tone}>
    {/* ... */}
  </CalloutBox>
),
```

React components can't accept `data-tina-field` directly. Pass it as a normal prop and forward to the rendered DOM.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Component map key doesn't match schema name | Component doesn't render | Match exactly (case-sensitive) |
| Forgot to recurse `<TinaMarkdown>` for nested children | Children show as raw AST | Recursively render |
| Mapping the same template to multiple keys | Last wins; confusing | One key per template |
| Component imports from `tina/__generated__/types` directly | Type drift | Import from `tinacms/dist/rich-text` for `Components` and `TinaMarkdownContent` |
| Editing schema without updating components map | Component shows nothing | Update both together (type the map for compile-time check) |
