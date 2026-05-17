# `number` field

Stores a number (int or float). Renders as a number input.

## Basic

```typescript
{
  name: 'order',
  label: 'Sort Order',
  type: 'number',
  description: 'Lower numbers sort first',
}
```

## Required + default

```typescript
{
  name: 'price',
  type: 'number',
  required: true,
  default: 0,
}
```

## Validation

```typescript
{
  name: 'rating',
  type: 'number',
  ui: {
    validate: (value) => {
      if (value === undefined || value === null) return undefined  // empty OK unless required
      if (value < 1 || value > 5) return 'Rating must be between 1 and 5'
      if (!Number.isInteger(value)) return 'Rating must be a whole number'
      return undefined
    },
  },
}
```

## Step / min / max via custom component

The default number widget accepts plain numeric input. For range sliders, increment/decrement buttons, or strict step constraints, use a custom component:

```typescript
import { wrapFieldsWithMeta } from 'tinacms'

{
  name: 'rating',
  type: 'number',
  ui: {
    component: wrapFieldsWithMeta(({ input }) => (
      <input type="range" min={1} max={10} step={1} {...input} />
    )),
  },
}
```

See `references/toolkit-fields/07-custom-field-component.md`.

## `ui.halfWidth`

```typescript
[
  { name: 'width', type: 'number', ui: { halfWidth: true } },
  { name: 'height', type: 'number', ui: { halfWidth: true } },
]
```

Two halfwidth numbers (width / height) sit side by side.

## Common patterns

### Sort order

```typescript
{ name: 'order', type: 'number', description: 'Sort order in list' }
```

Used for ordering items where alphabetical sort isn't right.

### Reading time

```typescript
{ name: 'readingTimeMinutes', type: 'number', ui: { component: 'hidden' } }
```

Combined with `beforeSubmit` to compute from body word count.

### Word count

```typescript
{ name: 'wordCount', type: 'number', ui: { component: 'hidden' } }
```

Same — programmatically populated.

## Stored format

`number` is stored as a number in JSON, or as a YAML number in frontmatter:

```yaml
---
order: 3
rating: 4.5
---
```

Don't use `string` for numeric values — you lose type safety in queries and pay no benefit.

## Querying numbers

GraphQL filter operators that work on numbers: `eq`, `in`, `gt`, `gte`, `lt`, `lte`. See `references/graphql/04-filter-documents.md`.

```typescript
const result = await client.queries.postConnection({
  filter: { rating: { gte: 4 } },
})
```

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Storing IDs/codes as numbers | Lose leading zeros (e.g. ZIP codes) | Use `string` for codes |
| `default: '0'` (string) | Type mismatch | Use `default: 0` |
| Validation accepts negative numbers when not desired | Bad data sneaks through | Add range check |
| `required` + numeric default of 0 | "Required" check passes even if intent was "must be set" | Use `validate` instead |
