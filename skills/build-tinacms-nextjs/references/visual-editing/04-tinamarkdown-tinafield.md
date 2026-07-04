# `tinaField` inside `TinaMarkdown`

Click-to-edit support for content rendered through `TinaMarkdown` — both built-in markdown elements and custom MDX templates.

## How it works

When `TinaMarkdown` renders a node, it injects `_content_source` metadata into the props passed to each component. `tinaField(props)` reads this metadata and produces the right target string.

## Inside MDX templates

```tsx
const components = {
  Cta: (props) => (
    <a
      data-tina-field={tinaField(props)}  // targets the whole Cta block
      href={props.href}
    >
      {props.heading}
    </a>
  ),
}
```

`tinaField(props)` (no second arg) targets the entire MDX template instance. Click → form opens to that Cta's fields.

## Targeting a specific field

```tsx
Cta: (props) => (
  <a
    data-tina-field={tinaField(props, 'heading')}  // target the `heading` field only
    href={props.href}
  >
    {props.heading}
  </a>
),
```

The second argument is the field name within the template.

## Built-in element targeting

For default elements (h1, p, code_block), the AST already includes the source metadata:

```tsx
const components = {
  h1: (props) => (
    <h1 data-tina-field={tinaField(props)}>{props.children}</h1>
  ),
}
```

This makes the heading clickable — the form opens to wherever in the rich-text body that heading lives.

## Wrapping children with `data-tina-field`

If you want a wrapper around the entire body for click-to-edit:

```tsx
<div data-tina-field={tinaField(data.post, 'body')}>
  <TinaMarkdown content={data.post.body} components={components} />
</div>
```

Clicking anywhere in the body that doesn't hit a more-specific `data-tina-field` opens the whole body field.

## Custom components and the prop pass-through

For MDX templates that render through a custom React component:

```tsx
function CalloutBox({ tinaFieldRef, tone, children }: any) {
  return (
    <div data-tina-field={tinaFieldRef} className={`callout callout-${tone}`}>
      {children}
    </div>
  )
}

const components = {
  Callout: (props) => (
    <CalloutBox tinaFieldRef={tinaField(props)} tone={props.tone}>
      {props.children && <TinaMarkdown content={props.children} components={components} />}
    </CalloutBox>
  ),
}
```

React components can't accept `data-tina-field` — pass as a normal prop and forward to the rendered DOM.

## Nested rich-text

For an MDX template with a `children: rich-text` field, recursively render and the metadata propagates:

```tsx
Callout: (props) => (
  <CalloutBox tone={props.tone}>
    {props.children && (
      <TinaMarkdown content={props.children} components={components} />
    )}
  </CalloutBox>
),
```

Editors can click headings, paragraphs, or templates *inside* the callout body — `tinaField` targets the right nested field.

## Verifying click-to-edit inside MDX

After wiring up:

1. Visit `/api/preview` to enable Draft Mode
2. Open a page with rich-text content
3. Click an MDX template (e.g. a Cta) → form should open to the right fields
4. Click a heading inside the body → form should open to the body field's heading position

If click-to-edit doesn't work:

- Check `props` is passed through (not destructured into specific fields you forgot to forward)
- Check `data-tina-field` is on a DOM element, not a React component
- Check the surrounding component is `"use client"` and uses `useTina`

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Destructured `{ heading }` from `props` and lost `_content_source` | Click-to-edit dead | Use `tinaField(props, 'heading')` — pass the whole props |
| `data-tina-field` on `<CalloutBox>` not the inner `<div>` | Doesn't propagate | Forward as a prop to the DOM |
| Missing `<TinaMarkdown>` recursion for nested children | Children render but click-to-edit dead | Recursively render children |
| Targeting an MDX template field that doesn't exist in schema | Click does nothing | Make sure field name matches schema |
