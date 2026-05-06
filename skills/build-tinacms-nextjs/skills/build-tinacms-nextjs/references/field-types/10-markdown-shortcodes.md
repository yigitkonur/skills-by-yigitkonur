# Markdown Shortcodes (custom syntax)

If your existing markdown files use shortcode syntax like `{{ Callout }}` (Hugo, Jekyll-style) or `[shortcode]` (WordPress-style), TinaCMS can parse them as MDX templates.

## When to use

You inherited content with shortcodes:

```mdx
{{ WarningCallout content="This is experimental" }}

[youtube id="abc123"]

[[note]]
This is a note.
[[/note]]
```

By default, TinaCMS parsing **fails on these** because it doesn't know what `{{ ... }}` or `[shortcode]` mean. Define a template with a `match` rule and TinaCMS treats it as if it were JSX.

## The `match` rule

```typescript
{
  name: 'body',
  type: 'rich-text',
  templates: [
    {
      name: 'WarningCallout',
      label: 'WarningCallout',
      match: {
        start: '{{',
        end: '}}',
      },
      fields: [
        {
          name: 'content',
          label: 'Content',
          type: 'string',
          required: true,
          ui: {
            component: 'textarea',
          },
        },
      ],
    },
  ],
}
```

When TinaCMS encounters `{{ WarningCallout content="..." }}` it parses the content into the `WarningCallout` template's fields. The editor sees a regular form for the props, not raw shortcode syntax.

## Multiple shortcode styles in one schema

```typescript
templates: [
  {
    name: 'WarningCallout',
    match: { start: '{{', end: '}}' },
    fields: [{ name: 'content', type: 'string' }],
  },
  {
    name: 'NoteBlock',
    match: { start: '[[note]]', end: '[[/note]]' },
    fields: [{ name: 'children', type: 'rich-text' }],
  },
]
```

Different shortcodes can use different `match` rules.

## Storage format

The shortcode round-trips to/from disk in its original form:

```mdx
{{ WarningCallout content="Migration notice" }}
```

Editors edit through the form; the file stays in shortcode syntax. This is great for migrations — you keep your existing content format while gaining the editor UI.

## Renderer

In the renderer, shortcodes appear under the same `components` map as MDX templates (key matches `name`):

```tsx
const components = {
  WarningCallout: (props: { content?: string }) => (
    <div className="warning-callout">{props.content}</div>
  ),
}

<TinaMarkdown content={data.body} components={components} />
```

## Modern projects: prefer MDX over shortcodes

For new projects, prefer plain MDX templates (no `match` rule). Shortcodes are useful for:

- Migrating from Hugo/Jekyll/WordPress without rewriting all content
- Inheriting content from a parent project that uses shortcodes
- Maintaining compatibility with non-React renderers

For green-field, MDX templates are simpler — editors hit `/`, pick the component, fill the form.

## Common shortcode patterns

### Hugo `{{< ... >}}`

```typescript
match: { start: '{{<', end: '>}}' }
```

### Jekyll `{% ... %}`

```typescript
match: { start: '{%', end: '%}' }
```

### Custom `[[...]]`

```typescript
match: { start: '[[', end: ']]' }
```

### Hashicorp `<% ... %>`

```typescript
match: { start: '<%', end: '%>' }
```

## Validation

Shortcode templates support all the standard field validation. Fields work the same as MDX template fields — string, number, list, even nested objects and rich-text.

## Limitations

- **Self-closing only** for templates without `children`. With `children: rich-text`, the shortcode must have an end tag.
- **No nested same-name shortcodes.** `{{ Foo }}{{ Foo }}` works; `{{ Foo {{ Foo }} }}` doesn't parse.
- **`match` is per-template.** You can't have one global "all `{{ }}` is dynamic" — each template needs its own definition.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `match` rule, content has shortcodes | Parser fails on shortcode syntax | Add `match` to the template |
| `match.start: '{{'` (extra space) | Doesn't match `{{...}}` | Match exact characters |
| Two templates with overlapping `match` rules | Ambiguous parsing | Make patterns distinct |
| Migrated from Hugo without renaming hyphenated fields | Field names invalid | Migrate via `sed` (see `references/schema/03-naming-rules.md`) |
