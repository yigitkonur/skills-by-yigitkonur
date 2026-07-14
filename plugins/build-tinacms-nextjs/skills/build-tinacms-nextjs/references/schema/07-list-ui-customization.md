# Customizing List UI (`ui.itemProps`)

Without customization, list items in the admin show as "Item 0", "Item 1", "Item 2"… This is unusable for editors. Always add `ui.itemProps` to give items meaningful labels.

## The pattern

```typescript
{
  name: 'blocks',
  type: 'object',
  list: true,
  ui: {
    itemProps: (item) => ({
      label: item?.heading || item?.title || 'Untitled section',
    }),
  },
  templates: [/* block templates */],
}
```

## Why it's mandatory

The TinaCMS admin renders list fields as a collapsible accordion. Each closed item needs a label. Without `itemProps`, you get:

```
Item 0
Item 1
Item 2
```

With it:

```
Hero — "Welcome to our platform"
Content — "Why we built this"
CTA — "Get started today"
```

## The `itemProps` function

```typescript
itemProps: (item) => ({
  label: string,
  // optionally:
  description?: string,
}),
```

| Property | Purpose |
|---|---|
| `label` | The text shown as the item's title in the accordion |
| `description` | Optional secondary text |

## Multi-template lists (blocks)

When a list has multiple template types, branch on `__typename`:

```typescript
ui: {
  itemProps: (item) => {
    const templateLabel = (() => {
      switch (item?._template) {
        case 'hero': return 'Hero'
        case 'content': return 'Content'
        case 'ctaBanner': return 'CTA'
        case 'features': return 'Features'
        default: return 'Section'
      }
    })()
    const detail = item?.heading || item?.title || 'Untitled'
    return { label: `${templateLabel} — ${detail}` }
  },
},
```

The result: `Hero — Welcome to our platform`.

## Common label resolution patterns

```typescript
// Try several fields in order
itemProps: (item) => ({
  label: item?.heading || item?.title || item?.name || item?.label || 'Untitled',
}),

// Truncate long values
itemProps: (item) => ({
  label: (item?.title || 'Untitled').slice(0, 50) + ((item?.title?.length ?? 0) > 50 ? '…' : ''),
}),

// Show metadata
itemProps: (item) => ({
  label: item?.title || 'Untitled',
  description: item?.date ? new Date(item.date).toLocaleDateString() : undefined,
}),
```

## For `reference` list fields

```typescript
{
  name: 'authors',
  type: 'object',
  list: true,
  ui: {
    itemProps: (item) => ({
      label: item?.name || 'Author',
    }),
  },
  fields: [
    { name: 'author', type: 'reference', collections: ['author'] },
  ],
}
```

When the list contains references, `item` includes the resolved reference data.

## For nested objects

```typescript
{
  name: 'team',
  type: 'object',
  list: true,
  ui: {
    itemProps: (item) => ({
      label: item?.member?.name || item?.name || 'Team member',
    }),
  },
  fields: [
    { name: 'name', type: 'string' },
    { name: 'role', type: 'string' },
    { name: 'bio', type: 'rich-text' },
  ],
}
```

## Lists of strings

For simple `string` lists, the value itself is the item:

```typescript
{
  name: 'tags',
  type: 'string',
  list: true,
  ui: {
    itemProps: (item) => ({
      label: item || 'Untag',
    }),
  },
}
```

Strings often work without `itemProps` since the admin renders the value inline. But it's safer to include the function explicitly.

## Default `itemProps` heuristic

If you don't define `itemProps`, TinaCMS guesses:

1. Looks for a field marked `isTitle: true` and uses its value
2. Otherwise looks for a field named `title`, `label`, or `name`
3. Falls back to "Item N"

You can rely on this for simple cases (a list of `{ name, role }` objects shows the `name`), but explicit `itemProps` is more reliable.

## Combining with `defaultItem`

`defaultItem` provides initial values for new items; `itemProps` labels them after creation. They're complementary:

```typescript
ui: {
  defaultItem: { heading: 'New section', body: '' },
  itemProps: (item) => ({ label: item?.heading || 'New section' }),
},
```

When an editor adds a new item, it appears as "New section" until they fill it in.

## Verification

In the admin, expand a list field with multiple items. Closed items should show meaningful labels — your title, heading, or name field. If you see "Item 0", `itemProps` is missing or the function returned undefined.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `ui.itemProps` | Editors see "Item 0", "Item 1" | Add the function |
| `label: undefined` returned | Falls back to "Item N" | Always return a string |
| Used `||` with empty string | Empty fallback never triggers (empty string is falsy) | Works as expected; verify the chain |
| Used `??` instead of `||` | `??` only catches null/undefined, not empty string | Use `||` for label fallback chains |
| Forgot to handle missing `_template` | Multi-template list shows raw type | Add a default case in the switch |
