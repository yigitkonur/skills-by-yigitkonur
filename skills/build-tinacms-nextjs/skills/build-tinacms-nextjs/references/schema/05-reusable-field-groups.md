# Reusable Field Groups (DRY schemas)

Extract shared field definitions into pure-data modules. Import them where needed. This keeps `tina/config.ts` thin and prevents schema drift.

## The pattern

```
tina/
├── config.ts                  ← imports the shared groups
├── blocks/
│   ├── hero.ts
│   └── cta.ts
└── shared/
    ├── cta-fields.ts          ← reusable CTA field group
    ├── seo-fields.ts          ← SEO field group attached to all content collections
    ├── image-fields.ts        ← image + alt + caption
    ├── section-style.ts       ← layout/background style fields
    └── link-fields.ts         ← internal/external link
```

## CTA field group

```typescript
// tina/shared/cta-fields.ts
export const ctaFields = [
  { name: 'text', label: 'Button Text', type: 'string' as const },
  { name: 'url', label: 'Button URL', type: 'string' as const },
  {
    name: 'style',
    label: 'Style',
    type: 'string' as const,
    options: [
      { value: 'primary', label: 'Primary' },
      { value: 'secondary', label: 'Secondary' },
      { value: 'ghost', label: 'Ghost' },
    ],
  },
  { name: 'openInNewTab', label: 'Open in New Tab', type: 'boolean' as const },
]
```

Use across blocks:

```typescript
// tina/blocks/hero.ts
import { ctaFields } from '@/tina/shared/cta-fields'

export const heroBlock = {
  name: 'hero',
  fields: [
    { name: 'heading', type: 'string' },
    { name: 'cta', type: 'object', fields: ctaFields },
  ],
}
```

## SEO field group (attach to every content collection)

```typescript
// tina/shared/seo-fields.ts
export const seoFields = [
  {
    name: 'metaTitle',
    label: 'Meta Title',
    type: 'string' as const,
    description: 'Override page title for search. Keep under 60 chars.',
    ui: {
      validate: (val: string) =>
        val && val.length > 60 ? `${val.length}/60 chars — too long` : undefined,
    },
  },
  {
    name: 'metaDescription',
    label: 'Meta Description',
    type: 'string' as const,
    description: '120–160 characters.',
    ui: {
      component: 'textarea',
      validate: (val: string) =>
        val && val.length > 160 ? `${val.length}/160 chars — too long` : undefined,
    },
  },
  {
    name: 'ogImage',
    label: 'Social Share Image',
    type: 'image' as const,
    description: '1200x630px recommended.',
  },
  { name: 'noIndex', label: 'Hide from Search', type: 'boolean' as const },
  { name: 'noFollow', label: 'No Follow Links', type: 'boolean' as const },
  { name: 'canonicalUrl', label: 'Canonical URL', type: 'string' as const },
]
```

Attach to collections:

```typescript
// tina/collections/page.ts
import { seoFields } from '@/tina/shared/seo-fields'

export const pageCollection = {
  // ...
  fields: [
    { name: 'title', type: 'string' },
    { name: 'blocks', type: 'object', list: true, templates: [...] },
    {
      name: 'seo',
      label: 'SEO & Social',
      type: 'object',
      ui: { component: 'group' },  // collapsible
      fields: seoFields,
    },
  ],
}
```

## Image field group (image + alt + caption)

```typescript
// tina/shared/image-fields.ts
export const imageFields = [
  { name: 'src', label: 'Image', type: 'image' as const, required: true },
  { name: 'alt', label: 'Alt Text', type: 'string' as const, required: true,
    description: 'Required for accessibility',
    ui: {
      validate: (val: string) =>
        !val || val.length < 4 ? 'Alt text required (≥4 chars)' : undefined,
    },
  },
  { name: 'caption', label: 'Caption', type: 'string' as const },
]
```

Use as `type: 'object'`:

```typescript
{
  name: 'heroImage',
  label: 'Hero Image',
  type: 'object',
  fields: imageFields,
}
```

## Section style group (shared across blocks)

```typescript
// tina/shared/section-style.ts
export const sectionStyleFields = [
  {
    name: 'background',
    label: 'Background',
    type: 'string' as const,
    options: [
      { value: 'bg-white', label: 'White' },
      { value: 'bg-gray-50', label: 'Light Gray' },
      { value: 'bg-gray-900', label: 'Dark' },
    ],
  },
  {
    name: 'spacing',
    label: 'Spacing',
    type: 'string' as const,
    options: [
      { value: 'compact', label: 'Compact' },
      { value: 'default', label: 'Default' },
      { value: 'spacious', label: 'Spacious' },
    ],
  },
  {
    name: 'layout',
    label: 'Width',
    type: 'string' as const,
    options: [
      { value: 'full', label: 'Full Width' },
      { value: 'container', label: 'Container' },
      { value: 'narrow', label: 'Narrow' },
    ],
  },
]
```

## Link field group (internal/external)

```typescript
// tina/shared/link-fields.ts
export const linkFields = [
  { name: 'label', label: 'Label', type: 'string' as const, required: true },
  { name: 'url', label: 'URL', type: 'string' as const, required: true },
  { name: 'openInNewTab', label: 'Open in New Tab', type: 'boolean' as const },
]
```

Used in navigation, footer, CTAs.

## Why pure-data exports

These files run inside `tina/config.ts` (esbuild-bundled, Node.js). They MUST be:

- Pure data exports (`as const` for type narrowing)
- No React imports
- No browser API access

Type-only imports from React are fine but rarely needed.

## TypeScript narrowing with `as const`

Without `as const`, TypeScript widens `type: 'string'` to `string`, which doesn't satisfy the discriminated union. Use `as const` (or wrap each field in a typed factory).

```typescript
// Without as const — type is string, not 'string' literal
{ name: 'foo', type: 'string' }       // ❌ may fail TS check

// With as const
{ name: 'foo', type: 'string' as const }  // ✅
```

Alternatively, type the entire array:

```typescript
import type { TinaField } from 'tinacms'

export const ctaFields: TinaField[] = [...]
```

## Composing groups

Field groups can nest:

```typescript
// tina/blocks/cta-banner.ts
import { ctaFields } from '@/tina/shared/cta-fields'
import { sectionStyleFields } from '@/tina/shared/section-style'

export const ctaBannerBlock = {
  name: 'ctaBanner',
  fields: [
    { name: 'heading', type: 'string' },
    { name: 'subheading', type: 'string' },
    { name: 'cta', type: 'object', fields: ctaFields },
    { name: 'style', type: 'object', fields: sectionStyleFields },
  ],
}
```

## When NOT to extract

- Only used in one place — keep inline
- Two fields that "happen to look similar" but represent different concepts — don't force them into a group
- Group has < 3 fields and is unlikely to grow — inline is fine

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `as const` | TS error: `string` not assignable to `'string'` | Add `as const` |
| Imported a React component into a shared file | Schema build fails | Use type-only import |
| Reused the same field name in different groups (collision) | Confusing TS errors | Rename fields or namespace them |
| Didn't update editorial guidance when adding a field | Editors confused | Update `description` strings on fields |
