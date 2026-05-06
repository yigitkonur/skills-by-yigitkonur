# Text, Textarea, Number Plugins

The most common toolkit overrides. `text` is the default for `string`; `textarea` and `number` are common variants.

## `text` (default)

```typescript
{ name: 'title', type: 'string' }
// Implicit: ui.component: 'text'
```

Behavior:

- Single-line `<input type="text">`
- Renders the field's `label` and `description`
- Shows validation errors below

## `textarea`

```typescript
{
  name: 'excerpt',
  type: 'string',
  ui: { component: 'textarea' },
}
```

Behavior:

- Multi-line `<textarea>`
- Auto-resizes (within reasonable bounds)
- Same validation/description rendering as text

For long-form content (article body, marketing copy), prefer `rich-text + isBody` instead — editors get formatting tools.

## `number` (default for type: 'number')

```typescript
{ name: 'price', type: 'number' }
// Implicit: ui.component: 'number'
```

Behavior:

- `<input type="number">`
- Browser validation (min/max via `min`/`max` HTML attrs not currently supported via TinaCMS' simple API — use `ui.validate` instead)

## Validation rendering

All three render `ui.validate` errors the same way:

```typescript
{
  name: 'metaDescription',
  type: 'string',
  ui: {
    component: 'textarea',
    validate: (value) => {
      if (value && value.length > 160) return `${value.length}/160 chars — too long`
      return undefined
    },
  },
}
```

Error appears in red below the input. Editor can still save unless `required: true` is set and value is empty.

## `ui.format` and `ui.parse`

Transform between display and storage:

```typescript
{
  name: 'price',
  type: 'string',
  ui: {
    component: 'text',
    format: (value) => value ? `$${(parseInt(value, 10) / 100).toFixed(2)}` : '',
    parse: (value) => {
      const cleaned = String(value).replace(/[^\d.]/g, '')
      return Math.round(parseFloat(cleaned) * 100).toString()
    },
  },
}
```

- `format` runs when reading the stored value into the input
- `parse` runs when reading the input value back to storage

Useful for currency, percentages, slug normalization.

## `ui.placeholder`

```typescript
{
  name: 'title',
  type: 'string',
  ui: {
    component: 'text',
    placeholder: 'Enter the page title…',
  },
}
```

Browser placeholder text (gray text shown in empty input).

## Auto-format integrations

Hook auto-formatting on the way in:

```typescript
{
  name: 'slug',
  type: 'string',
  ui: {
    parse: (value) =>
      String(value).toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''),
  },
}
```

Editor types `My Page Title`, gets stored as `my-page-title` automatically.

## When to use `text` vs `textarea` vs `rich-text`

| Use | Field |
|---|---|
| ≤ 100 chars, single-line | `text` |
| > 100 chars, plain text | `textarea` |
| Formatted body content | `rich-text + isBody` |
| Copy with embedded React components | `rich-text + isBody + templates` (MDX) |

## Common mistakes

| Mistake | Fix |
|---|---|
| `<textArea>` syntax (CamelCase) | Lowercase: `'textarea'` |
| Long body content as `textarea` | Switch to `rich-text` |
| `ui.parse` returning wrong type | Match the field type (string for `string` fields, number for `number`) |
| Forgot `required: true` after switching to textarea | Editors save empty | Re-add `required` |
