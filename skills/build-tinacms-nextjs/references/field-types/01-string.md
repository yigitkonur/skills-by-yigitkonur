# `string` field

The most-used field type. Single-line text input by default; can be turned into textarea, select, tag input, or multi-select.

## Basic single-line

```typescript
{
  name: 'title',
  label: 'Title',
  type: 'string',
  isTitle: true,        // shows in document list, used for filename slug
  required: true,
}
```

## Multi-line (textarea)

```typescript
{
  name: 'excerpt',
  label: 'Excerpt',
  type: 'string',
  ui: {
    component: 'textarea',
  },
}
```

## Select dropdown (fixed options)

```typescript
{
  name: 'layout',
  label: 'Layout',
  type: 'string',
  options: [
    { value: 'centered', label: 'Centered' },
    { value: 'left', label: 'Left Aligned' },
    { value: 'split', label: 'Split (Text + Image)' },
  ],
}
```

`options` accepts either:

- Array of strings: `options: ['draft', 'published', 'archived']`
- Array of `{ value, label }`: gives editors a friendly label

## List (tags or multi-select)

```typescript
{
  name: 'tags',
  label: 'Tags',
  type: 'string',
  list: true,
}
```

With `list: true` alone → free-form tag input (editor types each tag).

```typescript
{
  name: 'categories',
  label: 'Categories',
  type: 'string',
  list: true,
  options: ['design', 'engineering', 'product', 'marketing'],
}
```

With `list: true + options` → multi-select dropdown.

## Validation

```typescript
{
  name: 'metaTitle',
  type: 'string',
  ui: {
    validate: (value) => {
      if (!value) return undefined  // empty is fine (use `required: true` to force)
      if (value.length > 60) return `${value.length}/60 chars — too long`
      return undefined
    },
  },
}
```

Return `undefined` for valid, or a string error message for invalid. The error shows beneath the input.

## Common patterns

### Email field with format check

```typescript
{
  name: 'email',
  type: 'string',
  ui: {
    validate: (value) => {
      if (!value) return undefined
      if (!/^[^@]+@[^@]+\.[^@]+$/.test(value)) return 'Invalid email'
      return undefined
    },
  },
}
```

### URL field

```typescript
{
  name: 'url',
  type: 'string',
  ui: {
    validate: (value) => {
      if (!value) return undefined
      try {
        new URL(value.startsWith('/') ? `https://example.com${value}` : value)
        return undefined
      } catch {
        return 'Invalid URL'
      }
    },
  },
}
```

### Hidden field (programmatic only)

```typescript
{
  name: 'modifiedDate',
  type: 'string',
  ui: { component: 'hidden' },
}
```

Combined with a `beforeSubmit` hook, the field is set programmatically without an editor input.

## `isTitle` rules

Exactly one field per collection should have `isTitle: true`. It:

- Shows in the document list view
- Used by `ui.filename.slugify` if no custom slugifier is provided
- Used as the `label` in the admin's breadcrumb

If you don't mark a title field, the admin shows filenames or "Untitled".

## `ui.halfWidth` (TinaCMS 3.2+)

Renders the field at 50% width — useful for pairing two related fields side-by-side:

```typescript
[
  { name: 'firstName', type: 'string', ui: { halfWidth: true } },
  { name: 'lastName', type: 'string', ui: { halfWidth: true } },
]
```

Two adjacent half-width fields appear in one row. Without `halfWidth`, fields stack vertically.

## `ui.format` and `ui.parse`

Transform values between display (in form) and storage (in file):

```typescript
{
  name: 'price',
  type: 'string',
  ui: {
    // Display: format stored cents as dollars in input
    format: (value) => value ? `$${(parseInt(value, 10) / 100).toFixed(2)}` : '',
    // Storage: parse "$10.00" back to cents string
    parse: (value) => {
      const cleaned = String(value).replace(/[^\d.]/g, '')
      return Math.round(parseFloat(cleaned) * 100).toString()
    },
  },
}
```

For most string fields you don't need these.

## TinaMarkdown overrides for string

Strings render as plain text — no special rendering needed. Just use `data.<field>`.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `isTitle` on multiple fields | Confusing list view | Pick one |
| Forgot `required: true` on critical fields | Editors save empty docs | Add `required` |
| `options` with raw CSS values | Editors confused; design changes break content | Use design tokens |
| Validation function returns falsy non-undefined | "false" shows as error | Always return `undefined` for valid |
| Mixed `list: true` and `ui.component: 'textarea'` | Doesn't combine — `list` wins | Pick one shape |
