# Group and Group-list Plugins

`group` and `group-list` are toolkit plugins for nested object editing — usually applied automatically when you use `type: 'object'`.

## `group` (default for nested object)

```typescript
{
  name: 'seo',
  type: 'object',
  fields: [/* ... */],
}
// Implicit: ui.component: 'group'
```

Behavior:

- Renders fields in an expandable section
- Default: expanded
- Click header to collapse

## `group` collapsible (default-collapsed)

```typescript
{
  name: 'seo',
  label: 'SEO & Social',
  type: 'object',
  ui: { component: 'group' },   // explicit; default-collapsed in some Tina versions
  fields: [/* ... */],
}
```

Useful for secondary fields (SEO, advanced settings) that shouldn't dominate the main form.

## `group-list` (default for object + list)

```typescript
{
  name: 'features',
  type: 'object',
  list: true,
  fields: [/* ... */],
}
// Implicit: ui.component: 'group-list'
```

Behavior:

- Renders an accordion of items
- Add/remove/reorder controls per item
- Click header to expand each

## `ui.itemProps` for accordion labels

```typescript
{
  name: 'features',
  type: 'object',
  list: true,
  ui: {
    itemProps: (item) => ({
      label: item?.title || 'Feature',
    }),
  },
  fields: [/* ... */],
}
```

Without it: items show as "Item 0", "Item 1". Always provide `itemProps`. See `references/schema/07-list-ui-customization.md`.

## `ui.defaultItem`

```typescript
{
  name: 'features',
  type: 'object',
  list: true,
  ui: {
    defaultItem: { title: 'New feature', description: '' },
    itemProps: (item) => ({ label: item?.title }),
  },
  fields: [/* ... */],
}
```

When editor adds a new item, fields prepopulate.

## `ui.addItemBehavior` (TinaCMS 3.x)

```typescript
ui: {
  addItemBehavior: 'prepend',   // default 'append'
}
```

`'prepend'` puts new items at the top — useful for blogs/feeds.

## `ui.openFormOnCreate` (TinaCMS 3.6+)

```typescript
ui: {
  openFormOnCreate: true,
}
```

Auto-navigate into the new item's form so editors don't miss empty fields.

## `ui.visualSelector` (block templates only)

For `object + list + templates`:

```typescript
{
  name: 'blocks',
  type: 'object',
  list: true,
  ui: { visualSelector: true },
  templates: [hero, content, cta],
}
```

Adds a visual block picker. See `references/schema/04-blocks-pattern.md`.

## When to use group-list vs blocks

| Use | Pattern |
|---|---|
| Repeatable items of one shape | `object + list` (group-list) |
| Repeatable items of multiple shapes | `object + list + templates` (blocks pattern) |

Don't reach for `templates` if items always have the same shape — that's `fields` territory.

## Common mistakes

| Mistake | Fix |
|---|---|
| Forgot `itemProps` | "Item 0" labels | Add the function |
| Used `templates` for single-shape list | Confusing template picker | Use `fields` |
| Missing `defaultItem` | Empty form when adding | Provide defaults |
| Custom group component breaks list reordering | Use the built-in `group-list` |
