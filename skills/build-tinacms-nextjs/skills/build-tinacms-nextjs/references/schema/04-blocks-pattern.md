# Blocks Pattern (page builder)

The most common content-modeling pattern for TinaCMS. A "blocks" field is a list of objects, each with its own template. Editors compose pages by adding/reordering/removing blocks of different types.

## The shape

```typescript
{
  name: 'page',
  fields: [
    { name: 'title', type: 'string', isTitle: true, required: true },
    {
      name: 'blocks',                    // the list field
      label: 'Page Sections',
      type: 'object',
      list: true,
      ui: {
        visualSelector: true,            // shows visual block picker
      },
      templates: [                       // available block types
        heroBlock,
        contentBlock,
        ctaBlock,
        featuresBlock,
        faqBlock,
      ],
    },
  ],
}
```

In the admin, editors see:

- A "+" button to add a new block
- The visual selector lets them pick from `templates`
- Each block expands to show its fields
- Blocks reorder via drag

## Block template structure

A single block template:

```typescript
const heroBlock = {
  name: 'hero',                              // becomes __typename: PageBlocksHero
  label: 'Hero Section',                     // shown in visual selector
  ui: {
    previewSrc: '/admin/blocks/hero.png',    // optional thumbnail (192x108 recommended)
    defaultItem: {                           // values for new instances
      heading: 'Your Heading Here',
      subheading: 'A compelling subheading.',
      ctaText: 'Get Started',
      ctaUrl: '#',
      style: 'centered',
    },
  },
  fields: [
    { name: 'heading', label: 'Heading', type: 'string', required: true },
    { name: 'subheading', label: 'Subheading', type: 'string' },
    { name: 'backgroundImage', label: 'Background', type: 'image' },
    {
      name: 'style',
      label: 'Layout',
      type: 'string',
      options: [
        { value: 'centered', label: 'Centered' },
        { value: 'left', label: 'Left Aligned' },
        { value: 'split', label: 'Split (Text + Image)' },
      ],
    },
    { name: 'ctaText', label: 'Button Text', type: 'string' },
    { name: 'ctaUrl', label: 'Button URL', type: 'string' },
  ],
}
```

## Always include `ui.defaultItem`

Without `defaultItem`, editors get an empty block with no defaults. They have to fill every field before they can save. This is bad UX. Always provide sensible defaults.

For required fields, `defaultItem` is doubly important — without a default, the document fails validation immediately.

## `ui.previewSrc` thumbnails

The visual selector becomes a grid of card-style previews. Without thumbnails, editors see text labels only. With thumbnails:

- Place images at `public/admin/blocks/<name>.png`
- Recommended size: 192x108 (16:9)
- Use mockups, not actual screenshots — screenshots get stale

## What blocks to include

A typical production site has 5–13 blocks. Here's a starter set:

| Block | Fields |
|---|---|
| **Hero** | heading, subheading, CTA text/url, background image, layout style |
| **Content** | heading, rich-text body, optional image, image position |
| **CTA Banner** | heading, subheading, button text/url, style |
| **Features** | heading, items list (icon, title, description), columns enum |
| **FAQ** | heading, items list (question, answer) |
| **Testimonials** | items list (quote, author, role, avatar) |
| **Gallery** | images list |
| **Stats** | number highlights (value, label) |
| **Team** | people list (name, role, photo, bio) |
| **Pricing** | plans list (name, price, features list, CTA) |
| **Logos** | images list (partner/client logos) |
| **Video** | embed URL, poster image |
| **Contact** | form embed or contact info |

Define each in `tina/blocks/<name>.ts`, import into the page collection.

## `__typename` resolution

Each block template gets a unique `__typename` derived from collection + field + template name:

```
{CollectionName}Blocks{TemplateName}    // PascalCase

PageBlocksHero
PageBlocksContent
PageBlocksCtaBanner
PostBlocksGallery
```

Renderers map `__typename` to React components — see `references/rendering/08-block-renderer.md`.

## Style enums must map to design tokens

```typescript
// ❌ Don't expose raw CSS
{
  name: 'background',
  type: 'string',
  options: ['#ffffff', '#f3f4f6', '#000000'],
}

// ✅ Expose design tokens / Tailwind classes
{
  name: 'background',
  type: 'string',
  options: [
    { value: 'bg-white', label: 'White' },
    { value: 'bg-gray-50', label: 'Light Gray' },
    { value: 'bg-gray-900', label: 'Dark' },
  ],
}
```

Editors pick from semantic options; devs control the actual styling.

**Tailwind v4 caveat:** dynamic class names like `bg-blue-500` aren't found by Tailwind's source scanner if they appear only in content. Fix with `@source inline()`:

```css
/* In your global CSS */
@source inline("{hover:,}bg-{red,green,blue,gray}-{50,100,500,900}");
```

Or use a class mapping object so Tailwind sees full strings at build time.

## Reusable field groups across blocks

Many blocks share fields like CTA, image-with-alt, or section style. Extract:

```typescript
// tina/shared/cta-fields.ts
export const ctaFields = [
  { name: 'text', label: 'Button Text', type: 'string' as const },
  { name: 'url', label: 'Button URL', type: 'string' as const },
  {
    name: 'style',
    label: 'Style',
    type: 'string' as const,
    options: ['primary', 'secondary', 'ghost'],
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
    { name: 'cta', type: 'object', fields: ctaFields },  // reused
  ],
}
```

See `references/schema/05-reusable-field-groups.md`.

## `ui.itemProps` — never see "Item 0"

Without it, blocks in the editor list show as "Item 0", "Item 1". Add labels:

```typescript
{
  name: 'blocks',
  type: 'object',
  list: true,
  ui: {
    visualSelector: true,
    itemProps: (item) => ({
      label:
        item?.heading ||
        item?.title ||
        (item?.__typename === 'PageBlocksHero' && 'Hero') ||
        'Untitled section',
    }),
  },
  templates: [...],
}
```

See `references/schema/07-list-ui-customization.md`.

## Anti-patterns

| Don't | Do |
|---|---|
| Single rich-text body for landing pages | Blocks list with templates |
| Block templates without `defaultItem` | Always include defaults |
| Style enums with raw CSS values | Enums mapped to design tokens |
| Block templates that overlap heavily | Extract shared fields, parameterize |
| One mega-block "section" with 30 fields | Split into focused blocks |

## Renderer side

See `references/rendering/08-block-renderer.md` for the React side — `__typename` mapping, fallback for unknown types, `data-tina-field` placement.
