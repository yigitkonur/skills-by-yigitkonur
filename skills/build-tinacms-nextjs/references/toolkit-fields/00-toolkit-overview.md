# Toolkit Fields Overview

The "toolkit" is TinaCMS's lower-level field component library — the **plugin system** that powers the built-in fields. Most projects don't touch the toolkit directly. You reach for it when:

- You need a field widget that the schema's high-level types don't provide
- You want to build a custom field (markdown editor variant, color picker with brand swatches, etc.)
- You're customizing an existing field's UI without changing its data shape

## High-level fields vs toolkit fields

| Layer | What | Used in |
|---|---|---|
| **High-level fields** | `string`, `number`, `image`, etc. | `tina/config.ts` `fields` array |
| **Toolkit fields** | `text`, `textarea`, `select`, `color`, `toggle` plug-ins | `ui.component: 'name'` overrides |

A high-level `string` field with `ui.component: 'textarea'` is wired through the toolkit's `textarea` plugin under the hood.

## When to swap a toolkit component

```typescript
// Default: string field renders as <input type="text">
{ name: 'description', type: 'string' }

// Override to textarea via the toolkit's 'textarea' plugin
{
  name: 'description',
  type: 'string',
  ui: { component: 'textarea' },
}

// Override to a custom React component
{
  name: 'description',
  type: 'string',
  ui: { component: MyCustomEditor },
}
```

## Available built-in toolkit plugins

| Plugin name (`ui.component`) | Underlying type | Purpose |
|---|---|---|
| `'text'` | string | Single-line text input (default for string) |
| `'textarea'` | string | Multi-line text |
| `'number'` | number | Number input (default for number) |
| `'image'` | string (path) | Image picker (default for image) |
| `'color'` | string | Color picker — see `references/toolkit-fields/02-image-color.md` |
| `'toggle'` | boolean | Toggle switch (default for boolean) |
| `'radio-group'` | string | Radio buttons (alternative to dropdown) |
| `'select'` | string | Dropdown (default when `options` present) |
| `'tags'` | string[] | Free-form tag input |
| `'list'` | array | List management UI |
| `'group'` | object | Collapsible group (object fields default to this when nested) |
| `'group-list'` | object[] | Repeatable group |
| `'date'` | datetime | Date picker (default for datetime) |
| `'markdown'` | string | Markdown editor (alternative to rich-text for simpler cases) |
| `'html'` | string | HTML editor |
| `'hidden'` | any | Don't render in the form (programmatic-only) |

## When to use which

```typescript
// Text input (default)
{ name: 'title', type: 'string' }

// Multi-line
{ name: 'description', type: 'string', ui: { component: 'textarea' } }

// Color
{ name: 'themeColor', type: 'string', ui: { component: 'color' } }

// Radio (instead of dropdown for short option lists)
{
  name: 'layout',
  type: 'string',
  options: ['left', 'center', 'right'],
  ui: { component: 'radio-group' },
}

// Tags
{ name: 'keywords', type: 'string', list: true, ui: { component: 'tags' } }

// Hidden
{ name: 'modifiedDate', type: 'datetime', ui: { component: 'hidden' } }

// Custom React component (advanced)
{ name: 'rating', type: 'number', ui: { component: MyStarRating } }
```

## Custom field component pattern

```typescript
import { wrapFieldsWithMeta } from 'tinacms'

const MyStarRating = wrapFieldsWithMeta(({ input }) => (
  <div>
    {[1, 2, 3, 4, 5].map((n) => (
      <button key={n} onClick={() => input.onChange(n)}>
        {n <= input.value ? '★' : '☆'}
      </button>
    ))}
  </div>
))
```

The component receives `input` (with `value` and `onChange`), `field` (definition), `meta` (form state), and `form` (CMS form for cross-field updates). Use `wrapFieldsWithMeta` to inherit standard label, description, and validation rendering.

See `references/toolkit-fields/07-custom-field-component.md`.

## When NOT to swap

- **For a different field type:** use the right `type` instead of overriding `component` on a wrong type.
- **For visual tweaks only:** style with CSS rather than swapping components.
- **To "fix" missing features:** check if the high-level field already supports it via `ui.*` properties.

## Reading order

| File | When |
|---|---|
| `references/toolkit-fields/01-text-textarea-number.md` | Common text/number plugin overrides |
| `references/toolkit-fields/02-image-color.md` | Image and color pickers |
| `references/toolkit-fields/03-toggle-radio-select.md` | Boolean and choice widgets |
| `references/toolkit-fields/04-tags-list.md` | List variants |
| `references/toolkit-fields/05-group-and-group-list.md` | Grouped/repeatable fields |
| `references/toolkit-fields/06-date-markdown-html.md` | Date, markdown, HTML inputs |
| `references/toolkit-fields/07-custom-field-component.md` | Building your own |

## Common mistakes

| Mistake | Fix |
|---|---|
| `ui.component: 'textArea'` (wrong case) | `'textarea'` (lowercase) |
| Custom component without `wrapFieldsWithMeta` | Wrap it for standard label/description rendering |
| Swap component on wrong type (`'select'` on number) | Pick a component compatible with the type |
| `ui.component: 'hidden'` on required field | Editor can't fill required value | Remove `required` or set value programmatically |
