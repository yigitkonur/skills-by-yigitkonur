# Custom Field Component

When the built-in field widgets don't meet your needs, write a custom React component and pass it as `ui.component`.

## The pattern

```typescript
import { wrapFieldsWithMeta } from 'tinacms'

const StarRating = wrapFieldsWithMeta(({ input }) => {
  const value = parseInt(input.value, 10) || 0
  return (
    <div className="star-rating">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          onClick={() => input.onChange(String(n))}
          aria-label={`Set rating to ${n}`}
        >
          {n <= value ? '★' : '☆'}
        </button>
      ))}
    </div>
  )
})

// Use in schema:
{
  name: 'rating',
  type: 'number',
  ui: { component: StarRating },
}
```

`wrapFieldsWithMeta` adds the standard label, description, and validation rendering — your component focuses on the input UI.

## What your component receives

```typescript
type FieldProps = {
  field: TinaField,                  // the field definition
  input: {
    value: any,                      // current value
    onChange: (value: any) => void,  // mutate value
    onBlur: () => void,
    onFocus: () => void,
  },
  meta: {
    dirty: boolean,                  // changed since load
    valid: boolean,
    error: string,                   // validation error
    submitFailed: boolean,
    touched: boolean,
  },
  form: TinaForm,                    // for cross-field operations
}
```

For type narrowing, import from `tinacms`:

```typescript
import type { Wrapped, FieldProps } from 'tinacms'
```

## Cross-field updates with `form.change`

```typescript
const SlugFromTitle = wrapFieldsWithMeta(({ input, form }) => {
  return (
    <div>
      <input
        value={input.value}
        onChange={(e) => input.onChange(e.target.value)}
      />
      <button
        onClick={() => {
          // Read the title field, slug-ify, write back to this field
          const title = form.getState().values.title
          if (title) {
            const slug = title.toLowerCase().replace(/\s+/g, '-')
            input.onChange(slug)
          }
        }}
      >
        Generate from title
      </button>
    </div>
  )
})
```

## Hide a field programmatically

```typescript
{
  name: 'modifiedDate',
  type: 'datetime',
  ui: { component: 'hidden' },  // built-in 'hidden' plugin
}
```

`'hidden'` is a built-in component that renders nothing. Combined with `beforeSubmit`, the field is set programmatically.

## Render nothing

```typescript
ui: {
  component: () => null,   // not rendered, but value still part of saved data
}
```

Use when you need a field to exist in the data but never appear in the form.

## Reusable example: char-count textarea

```typescript
const CharCountTextarea = wrapFieldsWithMeta(({ input, field }) => {
  const max = (field.max as number) ?? 160
  return (
    <div>
      <textarea
        value={input.value}
        onChange={(e) => input.onChange(e.target.value)}
        rows={4}
      />
      <small>
        {input.value?.length ?? 0} / {max}
      </small>
    </div>
  )
})

{
  name: 'metaDescription',
  type: 'string',
  ui: { component: CharCountTextarea },
  // Custom property — your component reads it via `field`
}
```

## Custom validation in the component

```typescript
const HexColor = wrapFieldsWithMeta(({ input, meta }) => {
  const error = !/^#[0-9a-fA-F]{6}$/.test(input.value || '') && input.value
    ? 'Must be a hex color (#rrggbb)'
    : undefined
  return (
    <div>
      <input
        type="text"
        value={input.value || ''}
        onChange={(e) => input.onChange(e.target.value)}
        placeholder="#0a0a0a"
      />
      {error && <span style={{ color: 'red' }}>{error}</span>}
    </div>
  )
})
```

For most validation, prefer `ui.validate` on the field (it integrates with the standard error rendering).

## Custom field plugin via `cmsCallback`

For advanced cases (registering a plugin for use across many fields):

```typescript
import type { TinaCMS } from 'tinacms'

export default defineConfig({
  // ...
  cmsCallback: (cms: TinaCMS) => {
    cms.fields.add({
      name: 'color',
      Component: MyColorPicker,
    })
    return cms
  },
})
```

After registering, refer by name:

```typescript
{ name: 'brand', type: 'string', ui: { component: 'color' } }
```

## When NOT to write a custom component

- The built-in widget already covers it (you just didn't know about `ui.*` options)
- For visual-only tweaks — use CSS instead
- For "fixing" the underlying field type — use the right `type:` instead

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Custom component without `wrapFieldsWithMeta` | No label/description rendered | Wrap it |
| Component that mutates `input.value` directly | Doesn't update form state | Use `input.onChange` |
| Forgot to handle empty value | Crash on first render | Default with `?? ''` or `?? 0` |
| Component depends on browser APIs at module level | SSR fails | Use `useEffect` for browser-only code |
| Importing into `tina/config.ts` directly | Schema build fails (Node-side) | Register via `cmsCallback` instead |
