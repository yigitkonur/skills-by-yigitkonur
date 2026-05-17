# `TinaMarkdown` Component

Renders rich-text AST content. Import from `tinacms/dist/rich-text`.

## Basic usage

```tsx
import { TinaMarkdown } from 'tinacms/dist/rich-text'

<TinaMarkdown content={data.post.body} />
```

That's it for plain markdown body content. The component walks the AST and renders default HTML elements (`<h1>`, `<p>`, `<a>`, etc.).

## With component overrides

```tsx
const components = {
  h1: (props) => <h1 className="text-4xl font-bold">{props.children}</h1>,
  p: (props) => <p className="mb-4 text-lg leading-relaxed">{props.children}</p>,
  a: (props) => <a className="text-blue-600 underline" {...props} />,
  code_block: (props) => <pre className="rounded bg-zinc-900 p-4 text-zinc-100">{props.children}</pre>,
}

<TinaMarkdown content={data.post.body} components={components} />
```

The `components` prop maps element types to React components. See `references/rendering/06-overriding-builtins.md`.

## With MDX templates

```tsx
const components = {
  // Built-in element overrides
  h1: (props) => <h1 className="..." {...props} />,

  // Custom MDX templates (must match schema template names)
  Cta: (props) => <a className="cta" href={props.href}>{props.heading}</a>,
  Callout: (props) => (
    <CalloutBox tone={props.tone}>
      {props.children && <TinaMarkdown content={props.children} components={components} />}
    </CalloutBox>
  ),
}
```

For nested rich-text (template with a `children: rich-text` field), recursively pass `components` so child content renders the same way.

See `references/rendering/05-mdx-component-mapping.md`.

## Type safety with `Components<T>`

```tsx
import { TinaMarkdown, type Components } from 'tinacms/dist/rich-text'

const components: Components<{
  Cta: { heading?: string; href?: string }
  Callout: { tone?: 'info' | 'warn' | 'success'; children?: any }
}> = {
  Cta: (props) => /* fully typed */,
  Callout: (props) => /* fully typed */,
}
```

The generic parameter is a map of `templateName: PropsType`. Helps catch typos and prop mismatches at compile time.

## Server Component vs Client Component

`TinaMarkdown` itself doesn't require `"use client"` — it's a renderer. **However**, when you use `useTina` (which is required for visual editing), the surrounding component is a Client Component, and `TinaMarkdown` lives there.

For pages that don't need visual editing (e.g. an `<RSSItem>` rendered server-side), `TinaMarkdown` works in Server Components too.

## Default element rendering

Without overrides, `TinaMarkdown` renders:

| AST element | HTML |
|---|---|
| `h1`, `h2`, ..., `h6` | `<h1>`, etc. |
| `p` | `<p>` |
| `a` | `<a>` |
| `img` | `<img>` |
| `ul`, `ol`, `li` | `<ul>`, `<ol>`, `<li>` |
| `code` | `<code>` |
| `code_block` | `<pre>` |
| `block_quote` | `<blockquote>` |
| `hr` | `<hr>` |
| `table`, `tr`, `td`, `th` | `<table>`, etc. |
| `mermaid` | (none — needs override; see `references/rendering/07-mermaid-diagrams.md`) |

## Empty content handling

```tsx
{data.post.body && <TinaMarkdown content={data.post.body} components={components} />}
```

If `body` is null (e.g. document not found), `TinaMarkdown` may throw. Defensive null-check.

## Performance

`TinaMarkdown` is fast for typical body content (under ~50 KB AST). For very long content (50+ KB AST), consider:

- Splitting into multiple rich-text fields (intro / body / conclusion)
- Lazy-loading the rendered output

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `components` prop | MDX templates render as `[object]` | Pass components map |
| Component map keys don't match template names | Component doesn't render | Match exactly (PascalCase for MDX templates) |
| Forgot to recurse for nested children | Nested rich-text shows as raw AST | Recurse: `<TinaMarkdown content={props.children} components={components} />` |
| Imported from `tinacms/dist/react` (wrong path) | Module not found | Import from `tinacms/dist/rich-text` |
| Used `<TinaMarkdown>` without typing component map | Props are `any` | Use `Components<T>` generic |
