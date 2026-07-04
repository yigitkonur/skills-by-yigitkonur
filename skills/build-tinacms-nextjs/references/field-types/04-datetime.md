# `datetime` field

Stores ISO 8601 date/time strings. Renders as a date/time picker.

## Basic

```typescript
{
  name: 'date',
  label: 'Published Date',
  type: 'datetime',
  required: true,
}
```

## Stored format

```yaml
---
date: '2026-05-08T14:30:00.000Z'
---
```

ISO 8601 with timezone. The picker handles timezones — stored values are always UTC.

## With `default`

```typescript
{
  name: 'date',
  type: 'datetime',
  default: () => new Date().toISOString(),
}
```

`default` can be a function for dynamic defaults (current time per new doc).

## Date-only (no time)

```typescript
{
  name: 'date',
  type: 'datetime',
  ui: {
    dateFormat: 'YYYY-MM-DD',
    timeFormat: false,
  },
}
```

The picker hides the time portion. Stored value is still ISO 8601 (with time set to `00:00:00.000Z`).

## Format strings (Moment.js syntax)

| Token | Meaning | Example |
|---|---|---|
| `YYYY` | 4-digit year | 2026 |
| `MM` | 2-digit month | 05 |
| `DD` | 2-digit day | 08 |
| `MMM` | Short month | May |
| `MMMM` | Full month | May |
| `dddd` | Weekday | Friday |
| `HH` | Hour (24h) | 14 |
| `mm` | Minute | 30 |

## Validation

```typescript
{
  name: 'expiry',
  type: 'datetime',
  ui: {
    validate: (value) => {
      if (!value) return undefined
      if (new Date(value) < new Date()) return 'Expiry must be in the future'
      return undefined
    },
  },
}
```

## Common patterns

### Published-date filter

```typescript
const result = await client.queries.postConnection({
  filter: { date: { before: new Date().toISOString() } },
})
```

Filter operators on datetime: `eq`, `in`, `before`, `after`. See `references/graphql/04-filter-documents.md`.

### Auto-update modified date

```typescript
{
  name: 'modifiedDate',
  type: 'datetime',
  ui: { component: 'hidden' },
}
```

Combined with `beforeSubmit`:

```typescript
beforeSubmit: async ({ values }) => ({
  ...values,
  modifiedDate: new Date().toISOString(),
}),
```

### Date-prefixed filename

```typescript
ui: {
  filename: {
    slugify: (values) => {
      const date = (values.date || new Date().toISOString()).split('T')[0]
      const title = (values.title ?? 'untitled').toLowerCase().replace(/\s+/g, '-')
      return `${date}-${title}`
    },
  },
}
```

Produces `2026-05-08-my-post.md`. Default the title (and any other optional input) before calling `.replace()` — `slugify` runs while editors are still typing, so values can be `undefined`.

## Querying / sorting

```typescript
const result = await client.queries.postConnection({
  sort: 'date',         // sort by date field
  first: 10,            // most recent 10
})
```

Sortable fields must be indexed — see `references/graphql/05-sorting.md`.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Storing dates as `string` | Lose type, can't sort by date | Use `datetime` |
| Default value `new Date()` (Date object, not string) | Storage error | Use `() => new Date().toISOString()` |
| Comparing strings instead of `new Date(x)` in filters | Wrong order | Pass ISO strings; Tina compares correctly |
| Forgot timezone handling in display | Show "GMT-0700" to user | Format with `toLocaleDateString()` in renderer |
| `dateFormat: 'YY-MM-DD'` (2-digit year) | Y2K-style ambiguity | Always use 4-digit year |
