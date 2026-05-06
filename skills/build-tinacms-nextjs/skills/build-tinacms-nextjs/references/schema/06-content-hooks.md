# Content Hooks (`beforeSubmit` and friends)

Hooks let you mutate or augment document values when editors save. Use them for slug auto-generation, computed fields, audit timestamps, and validation.

## `beforeSubmit` — most common hook

```typescript
{
  name: 'post',
  ui: {
    beforeSubmit: async ({ values }) => {
      return {
        ...values,
        slug: values.title
          .toLowerCase()
          .replace(/\s+/g, '-')
          .replace(/[^a-z0-9-]/g, ''),
        modifiedDate: new Date().toISOString(),
      }
    },
  },
  fields: [/* ... */],
}
```

Runs before the document is saved. Whatever you return becomes the saved values.

## Use cases

| Hook | Purpose |
|---|---|
| Slug from title | Auto-generate URL slug from the title field |
| `modifiedDate: new Date().toISOString()` | Stamp every save with timestamp |
| Editor identity | If your auth provides user info, stamp `lastEditor: userEmail` |
| Computed fields | Derive `wordCount`, `readingTimeMinutes` from body |
| Cross-field validation | Reject save if combination of fields is invalid |

## Function signature

```typescript
beforeSubmit: async ({ values, cms, form }) => {
  // values — the object about to be saved
  // cms    — the TinaCMS instance (rarely needed)
  // form   — the form state (rarely needed)

  // Return the modified values, or throw to abort the save
  return { ...values, /* additions */ }
}
```

The function can be `async`. For computed values that need to fetch external data, that's where you do it.

## Slug auto-generation patterns

Simple slug from title:

```typescript
beforeSubmit: async ({ values }) => ({
  ...values,
  slug: values.title?.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''),
}),
```

Date-prefixed slug for blog posts:

```typescript
beforeSubmit: async ({ values }) => {
  const date = values.date || new Date().toISOString()
  const datePrefix = date.split('T')[0]  // '2026-05-08'
  const slugTitle = values.title?.toLowerCase().replace(/\s+/g, '-')
  return {
    ...values,
    slug: `${datePrefix}-${slugTitle}`,
  }
},
```

## Audit timestamps

```typescript
beforeSubmit: async ({ values }) => ({
  ...values,
  createdDate: values.createdDate || new Date().toISOString(),  // first save only
  modifiedDate: new Date().toISOString(),                       // every save
}),
```

The schema needs to include both fields, hidden from the editor:

```typescript
{
  name: 'createdDate',
  type: 'datetime',
  ui: { component: 'hidden' },
},
{
  name: 'modifiedDate',
  type: 'datetime',
  ui: { component: 'hidden' },
},
```

## Computed `wordCount` and reading time

```typescript
beforeSubmit: async ({ values }) => {
  // body is rich-text AST; flatten to text
  const text = JSON.stringify(values.body || '')
  const words = text.split(/\s+/).filter(Boolean).length
  const readingMinutes = Math.max(1, Math.round(words / 200))

  return {
    ...values,
    wordCount: words,
    readingTimeMinutes: readingMinutes,
  }
},
```

## Cross-field validation (abort save)

```typescript
beforeSubmit: async ({ values }) => {
  if (values.publishDate && new Date(values.publishDate) > new Date(values.expiryDate)) {
    throw new Error('Publish date cannot be after expiry date')
  }
  return values
},
```

The thrown error shows in the admin and prevents save.

## Field-level vs collection-level

Hooks live at the **collection** `ui.beforeSubmit`. There's no field-level equivalent — for field-level computation, use the collection hook and only mutate that field.

## Block-level hooks

Blocks (templates inside a list field) can have their own `ui.defaultItem` for **creation** but no `beforeSubmit` for save mutations. Save-time hooks are collection-level only.

## When NOT to use `beforeSubmit`

- Don't use it for **expensive operations** that block save UX (large API calls, image processing). Editors notice.
- Don't use it for **side effects** (sending emails, kicking off webhooks). Use Vercel deploy hooks or TinaCloud webhooks for those — they fire on commit, not save.
- Don't use it to **enforce auth/role rules**. Auth happens at the auth provider, not here.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Mutating `values` in place instead of returning a new object | Some fields don't update | Return `{ ...values, ... }` |
| Using `cms.api.tina` for external calls | Save hangs | Use plain `fetch` or external clients |
| Throwing without a useful message | Editors confused | Always `throw new Error('...descriptive...')` |
| Forgot `async` keyword | Promise<...> coerced to value | Mark function `async` |

## Verification

Add a temporary log:

```typescript
beforeSubmit: async ({ values }) => {
  console.log('[Tina] beforeSubmit:', values)
  return { ...values, modifiedDate: new Date().toISOString() }
},
```

Save a document; check the dev-server output. You should see the original values, then verify the new fields appear in the saved file.
