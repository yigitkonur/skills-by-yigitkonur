# Field Types Overview

TinaCMS has **9 built-in field types**. Each has its own widget, validation options, and UI customization paths.

## Type matrix

| Type | Stores | Widget | Common use |
|---|---|---|---|
| `string` | string | text input | Title, slug, label, single-line content |
| `string + list:true` | string[] | tag input or select | Tags, categories, multi-select |
| `string + ui.component:'textarea'` | string | multi-line text | Excerpts, descriptions |
| `string + options` | string | select dropdown | Layout style, theme variant |
| `number` | number | number input | Price, count, rating |
| `boolean` | boolean | toggle switch | Draft, featured, hidden |
| `datetime` | ISO 8601 string | date/time picker | Published date, expiry |
| `image` | string (path) | image picker → media store | Hero image, avatar |
| `reference` | document ID | document picker | Author, category, related post |
| `object` | nested fields | grouped form | SEO group, address |
| `object + list:true` | array of objects | repeatable group | List of features, FAQ items |
| `object + list:true + templates` | array of typed objects | block selector | The blocks pattern |
| `rich-text` | AST | markdown editor | Body content |
| `rich-text + templates` | AST + JSX | MDX editor | Body with embedded React components |

## When to pick each type

```
Need a single string?                                       → string
Need many strings (tags)?                                   → string + list:true
Need a multi-line string (description)?                     → string + textarea
Need to pick from a fixed set?                              → string + options or string + list:true + options
Need a number?                                              → number
Need true/false?                                            → boolean
Need a date?                                                → datetime
Need an image?                                              → image
Need to link to another document?                           → reference
Need a nested struct (e.g. SEO group)?                      → object
Need a repeatable struct (e.g. list of features)?           → object + list:true
Need a content body (formatted text)?                       → rich-text + isBody:true
Need a content body with React components?                  → rich-text + isBody:true + format:'mdx' + templates
Need a page builder (varied sections per page)?             → object + list:true + templates  (the blocks pattern)
```

## Common field-level properties

Available on most types:

| Property | Purpose |
|---|---|
| `name` | Required — field identifier |
| `label` | Display name in admin |
| `type` | Field type (one of above) |
| `required` | Reject save if empty |
| `description` | Editorial guidance shown below the input |
| `isTitle` | This field is the document's title (for list view + filename) |
| `isBody` | This field is the document body (rich-text only) |
| `list` | Make this field a list (string, object) |
| `default` | Default value for new docs / list items |
| `searchable` | Include in TinaCloud search index (default true) |
| `ui` | UI customization sub-object |

## Common `ui.*` properties

| Property | Purpose |
|---|---|
| `ui.label` | Override label without changing field name |
| `ui.description` | Same as field-level `description` |
| `ui.component` | `'textarea'`, `'group'`, `'hidden'`, custom plugin name, or React component |
| `ui.defaultItem` | Default for new list items |
| `ui.itemProps` | Label function for list items |
| `ui.validate` | Function returning error message or undefined |
| `ui.format` | Transform display value |
| `ui.parse` | Transform stored value |
| `ui.halfWidth` | Render at 50% width (TinaCMS 3.2+) |
| `ui.openFormOnCreate` | Auto-navigate into the form after creation (TinaCMS 3.6+) |
| `ui.addItemBehavior` | `'append'` (default) or `'prepend'` for list fields |
| `ui.visualSelector` | Show visual block picker (object + list + templates only) |
| `ui.previewSrc` | Thumbnail for visual selector (block templates only) |

## Reading order

For each field type, there's a dedicated reference:

1. `references/field-types/01-string.md`
2. `references/field-types/02-number.md`
3. `references/field-types/03-boolean.md`
4. `references/field-types/04-datetime.md`
5. `references/field-types/05-image.md`
6. `references/field-types/06-reference.md`
7. `references/field-types/07-object.md`
8. `references/field-types/08-rich-text-markdown.md`
9. `references/field-types/09-rich-text-mdx.md`
10. `references/field-types/10-markdown-shortcodes.md` — for `{{...}}` syntax
11. `references/field-types/11-reserved-names.md`

## TypeScript hints

`defineConfig`'s schema is fully typed. In your IDE, hover over `type:` to see the discriminated union — picking `'string'` constrains the rest of the field to string-specific options. Same for `'number'`, `'rich-text'`, etc.

For shared field group files, use `as const`:

```typescript
{ name: 'foo', type: 'string' as const }
```

Without `as const`, TypeScript widens to `string` and discriminated narrowing fails.

## Common mistakes across types

| Mistake | Fix |
|---|---|
| `name: 'hero-image'` | Alphanumeric + underscores only |
| `name: 'children'` | Reserved — pick another |
| Missing `required: true` on critical fields | Add it |
| No `ui.itemProps` on list fields | Add it |
| Style enum with raw CSS | Map to design tokens |
| `image` field with no media store configured | Configure `media.tina` or external provider |
