# `tinaField` Helper

Generates the `data-tina-field` attribute that targets a specific field for click-to-edit.

## Basic

```tsx
import { tinaField } from 'tinacms/dist/react'

<h1 data-tina-field={tinaField(data.page, 'title')}>{data.page.title}</h1>
```

When an editor clicks the `<h1>`, the form opens to the `title` field of `data.page`.

## Function signature

```typescript
tinaField(object, fieldName?)
// → returns a string identifier
```

| Argument | Purpose |
|---|---|
| `object` | The data object (e.g. `data.page`, `block`) |
| `fieldName` | Optional — specific field within the object |

Without `fieldName`, targets the whole object's containing field.

## Where to attach

**Always on a DOM element**, not a React component wrapper:

```tsx
// ✅ DOM element
<h1 data-tina-field={tinaField(data.page, 'title')}>{data.page.title}</h1>

// ❌ React component — doesn't propagate
<MyHeading data-tina-field={tinaField(data.page, 'title')}>{data.page.title}</MyHeading>
```

## Workaround for components that wrap children

Pass `tinaField` as a prop to the component, which forwards it to a DOM element:

```tsx
function Section({ children, tinaFieldRef }: { children: React.ReactNode; tinaFieldRef?: string }) {
  return <section data-tina-field={tinaFieldRef}>{children}</section>
}

<Section tinaFieldRef={tinaField(data.page, 'body')}>
  <TinaMarkdown content={data.page.body} />
</Section>
```

Common naming convention: `tinaField`, `tinaFieldRef`, or `editField`.

## Block-level

Wrap each block in a `<section>` with `data-tina-field={tinaField(block)}` (no second argument):

```tsx
{blocks.map((block) => (
  <section key={block.id} data-tina-field={tinaField(block)}>
    <BlockComponent {...block} />
  </section>
))}
```

Clicking the section opens the entire block's form. Per-field clicks within the block (e.g. heading) target specific fields:

```tsx
<h2 data-tina-field={tinaField(block, 'heading')}>{block.heading}</h2>
```

## Nested objects

```tsx
// Schema:
{
  cta: {
    text: '...',
    url: '...',
  }
}

// Renderer:
<a
  href={data.page.cta.url}
  data-tina-field={tinaField(data.page.cta, 'text')}  // target cta.text
>
  {data.page.cta.text}
</a>
```

For the whole CTA group:

```tsx
<a data-tina-field={tinaField(data.page, 'cta')}>...</a>  // target the cta object
```

## Inside MDX templates

`tinaField(props)` automatically picks up the metadata from the MDX rendering context:

```tsx
const components = {
  Cta: (props) => (
    <a
      data-tina-field={tinaField(props, 'heading')}  // target heading field
      href={props.href}
    >
      {props.heading}
    </a>
  ),
}
```

See `references/visual-editing/04-tinamarkdown-tinafield.md`.

## Production behavior

In production (no Draft Mode), `tinaField()` returns the same string but it's a no-op — the admin doesn't read it. Zero performance impact in production.

## When `tinaField` returns the wrong target

Symptoms:

- Clicking opens the wrong field
- Clicking does nothing

Causes:

- `tinaField(wrongObject, ...)` — passing the wrong object reference
- Nested object pointing — confusing `tinaField(data.page, 'cta')` (the cta object) vs `tinaField(data.page.cta, 'text')` (a field within cta)

Rule: pass the object that **contains** the field as the first arg, then the field name as the second.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `data-tina-field` on `<MyComponent>` | Doesn't propagate | Move to DOM element |
| `tinaField(data.page.title)` (single arg, primitive) | Wrong — strings don't have field metadata | Use `tinaField(data.page, 'title')` |
| `tinaField()` with no args | Build error | Always pass at least one arg |
| Using `tinaField` in Server Component | Likely fine but useTina is in Client only | Place per-field tinaField inside the same Client Component as useTina |
| Mismatch between `block` reference and `tinaField(block)` | Wrong field opens | Same `block` reference inside `.map((block) => ...)` |
