# Overriding Built-in Markdown Elements

Override how `TinaMarkdown` renders headings, code blocks, images, tables, etc.

## What you can override

| Key | Default | Override use cases |
|---|---|---|
| `h1`, `h2`, ..., `h6` | `<h1>` etc. | Custom typography classes |
| `p` | `<p>` | Spacing, font size |
| `a` | `<a>` | External-link icon, target=_blank logic |
| `img` | `<img>` | Replace with `next/image` |
| `ul`, `ol`, `li` | `<ul>`, etc. | Custom bullets, spacing |
| `code` | `<code>` | Inline code styling |
| `code_block` | `<pre>` | Syntax highlighting (Shiki, Prism), copy button |
| `block_quote` | `<blockquote>` | Custom blockquote styling |
| `hr` | `<hr>` | Custom dividers |
| `table`, `tr`, `td`, `th` | `<table>`, etc. | Responsive table wrappers |
| `mermaid` | (no default) | Render Mermaid diagrams (see `references/rendering/07-mermaid-diagrams.md`) |

## Heading customization

```tsx
const components = {
  h1: (props) => <h1 className="text-4xl font-bold mb-6 leading-tight">{props.children}</h1>,
  h2: (props) => <h2 className="text-3xl font-semibold mt-8 mb-4">{props.children}</h2>,
  h3: (props) => <h3 className="text-2xl font-semibold mt-6 mb-3">{props.children}</h3>,
}
```

## Anchored headings (auto-generate IDs)

```tsx
import { slugify } from '@/lib/slugify'

const components = {
  h2: (props) => {
    const id = slugify(extractText(props.children))
    return (
      <h2 id={id} className="group">
        <a href={`#${id}`} className="opacity-0 group-hover:opacity-100">#</a>
        {props.children}
      </h2>
    )
  },
}

function extractText(node: any): string {
  if (typeof node === 'string') return node
  if (Array.isArray(node)) return node.map(extractText).join('')
  if (node?.props?.children) return extractText(node.props.children)
  return ''
}
```

## `a` (links) with external indicator

```tsx
const components = {
  a: (props) => {
    const isExternal = props.url?.startsWith('http')
    return (
      <a
        href={props.url}
        target={isExternal ? '_blank' : undefined}
        rel={isExternal ? 'noopener noreferrer' : undefined}
        className="text-blue-600 underline hover:text-blue-700"
      >
        {props.children}
        {isExternal && <span aria-hidden> ↗</span>}
      </a>
    )
  },
}
```

## `img` → next/image

```tsx
import Image from 'next/image'

const components = {
  img: (props) => (
    <Image
      src={props.url}
      alt={props.alt || ''}
      width={1200}
      height={630}
      className="rounded my-6"
    />
  ),
}
```

⚠️ Image dimensions need to be known. For markdown images, `next/image`'s `fill` mode + a sized parent is more flexible:

```tsx
img: (props) => (
  <span className="relative block aspect-video">
    <Image src={props.url} alt={props.alt || ''} fill />
  </span>
),
```

## `code_block` with Shiki + copy button

```tsx
import { codeToHtml } from 'shiki'

const components = {
  code_block: async (props) => {
    const html = await codeToHtml(props.value || '', {
      lang: props.lang || 'text',
      theme: 'vitesse-dark',
    })

    return (
      <div className="relative my-4">
        <button className="absolute top-2 right-2 text-xs">Copy</button>
        <div dangerouslySetInnerHTML={{ __html: html }} />
      </div>
    )
  },
}
```

For client-side syntax highlighting (no async), use Prism:

```tsx
import Prism from 'prismjs'
import 'prismjs/themes/prism.css'

const components = {
  code_block: (props) => {
    useEffect(() => Prism.highlightAll(), [])
    return (
      <pre className={`language-${props.lang || 'text'}`}>
        <code>{props.value}</code>
      </pre>
    )
  },
}
```

## `table` responsive wrapper

```tsx
const components = {
  table: (props) => (
    <div className="overflow-x-auto my-6">
      <table className="min-w-full border-collapse">{props.children}</table>
    </div>
  ),
  th: (props) => <th className="border-b px-4 py-2 text-left font-semibold">{props.children}</th>,
  td: (props) => <td className="border-b px-4 py-2">{props.children}</td>,
}
```

Wrap tables in a horizontally-scrolling container to handle mobile narrow viewports.

## Combining built-in overrides with MDX templates

Both go in the same `components` map:

```tsx
const components = {
  // Built-in overrides
  h1: (props) => <h1 className="..." {...props} />,
  code_block: (props) => <CodeBlock {...props} />,

  // Custom MDX templates
  Cta: (props) => <CTA {...props} />,
  Callout: (props) => <Callout {...props} />,
}

<TinaMarkdown content={data.body} components={components} />
```

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Used `<a href>` (HTML attr) instead of `props.url` | Link doesn't render | TinaCMS passes `url`, not `href` — destructure correctly |
| Forgot `props.children` | Empty rendering | Pass through children |
| `next/image` without dimensions | Build error | Use `width`/`height` or `fill` mode |
| Async component for `code_block` in Server Component | Type mismatch | Use server-rendered Shiki at fetch time, or client-side highlighter |
| Missing key prop on list items | React key warning | If you wrap, ensure stable keys |
