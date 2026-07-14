# Toggle, Radio, Select Plugins

Boolean and choice widgets.

## `toggle` (default for boolean)

```typescript
{ name: 'draft', type: 'boolean' }
// Implicit: ui.component: 'toggle'
```

Behavior:

- iOS-style toggle switch
- Stores `true` or `false`
- Defaults to `false` if not specified

For checkbox style:

```typescript
{
  name: 'draft',
  type: 'boolean',
  ui: { component: 'checkbox' },  // alternative widget
}
```

## `radio-group`

```typescript
{
  name: 'layout',
  type: 'string',
  options: [
    { value: 'left', label: 'Left' },
    { value: 'center', label: 'Center' },
    { value: 'right', label: 'Right' },
  ],
  ui: { component: 'radio-group' },
}
```

Behavior:

- Renders horizontal radio buttons
- One option always selected
- Better than dropdown for ≤ 5 options

## `select` (default when options present)

```typescript
{
  name: 'category',
  type: 'string',
  options: ['design', 'engineering', 'product'],
}
// Implicit: ui.component: 'select'
```

Behavior:

- Dropdown
- Optional searchable
- Better than radio for > 5 options

## When to use which

| Options | Best widget |
|---|---|
| Boolean (yes/no) | `toggle` |
| 2-3 options | `radio-group` |
| 4-7 options | `radio-group` or `select` |
| 8-20 options | `select` |
| 20+ options | `select` (with search), or rethink (use `reference` to a collection) |

## Multi-select (`list: true`)

```typescript
{
  name: 'tags',
  type: 'string',
  list: true,
  options: ['react', 'typescript', 'nextjs', 'tailwind'],
}
```

Multi-select dropdown — editors pick multiple values from the option list.

For free-form tagging (no fixed options):

```typescript
{
  name: 'tags',
  type: 'string',
  list: true,
  ui: { component: 'tags' },
}
```

See `references/toolkit-fields/04-tags-list.md`.

## Conditional fields based on a select

To show fields based on a select value, branch in the renderer (not the schema):

```tsx
{data.layout === 'split' && data.image && (
  <Image src={data.image} alt="" />
)}
```

TinaCMS schema doesn't support conditional field visibility natively. For the editor experience, all fields show; you handle conditional rendering in code.

## Validation

```typescript
{
  name: 'category',
  type: 'string',
  options: ['design', 'engineering', 'product'],
  required: true,
  ui: {
    validate: (value) => {
      if (!value) return 'Pick a category'
      return undefined
    },
  },
}
```

For `select` with `required: true`, the picker pre-selects the first option (so it's never empty unless the editor cleared it).

## Stored format

```yaml
---
draft: true
layout: 'centered'
tags: ['react', 'typescript']
---
```

## Common mistakes

| Mistake | Fix |
|---|---|
| `radio-group` for 20 options | Switch to `select` |
| `select` for 2 options | Use `radio-group` for visibility |
| Forgot `options` on a `radio-group` | Field renders as text input | Add options array |
| Toggle for tri-state (`null` / `true` / `false`) | Use a string enum instead |
| Multi-select stored as comma-separated string | Should be string list — `type: 'string', list: true` |
