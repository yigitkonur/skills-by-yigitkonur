# Image and Color Plugins

## `image` (default for type: 'image')

```typescript
{ name: 'heroImage', type: 'image' }
// Implicit: ui.component: 'image'
```

Behavior:

- Renders an image picker that opens the configured media store
- Shows preview thumbnail of the picked image
- Drag-and-drop upload support

For external media providers (Cloudinary, S3) the picker uploads to the provider and stores the URL. See `references/media/03-cloudinary.md`.

## `color`

```typescript
{
  name: 'themeColor',
  type: 'string',
  ui: {
    component: 'color',
  },
}
```

Behavior:

- Color swatch picker
- Stores the picked value as a hex string (e.g. `#0a0a0a`) in the underlying string field
- Allows custom hex input alongside the swatch picker

## `color` with brand palette

```typescript
{
  name: 'background',
  type: 'string',
  ui: {
    component: 'color',
    colorFormat: 'hex',
    colors: [
      '#0a0a0a',
      '#ffffff',
      '#3b82f6',  // brand blue
      '#10b981',  // brand green
      '#ef4444',  // brand red
    ],
    widget: 'block',  // or 'sketch' for full color wheel
  },
}
```

Restrict editors to brand colors. Without `colors`, editors get the full color wheel.

| `widget` value | Behavior |
|---|---|
| `'block'` | Swatch grid only |
| `'sketch'` | Full color wheel + alpha + custom hex |

## When to use color vs string-with-options

```typescript
// Use color if you really mean "any color":
{ type: 'string', ui: { component: 'color', widget: 'sketch' } }

// Use string + options for design-token enforcement:
{
  type: 'string',
  options: [
    { value: 'bg-white', label: 'White' },
    { value: 'bg-gray-50', label: 'Light Gray' },
    { value: 'bg-gray-900', label: 'Dark' },
  ],
}
```

The string-options approach maps to design tokens / Tailwind classes, which is usually what marketing teams want. The color picker is for "let editors pick anything" scenarios (rare; usually a smell).

## Image alt-text companion

```typescript
{
  name: 'hero',
  type: 'object',
  fields: [
    { name: 'src', type: 'image', required: true },
    {
      name: 'alt',
      type: 'string',
      required: true,
      description: 'Required for accessibility',
    },
    { name: 'caption', type: 'string' },
  ],
}
```

See `references/schema/05-reusable-field-groups.md` for the reusable image group.

## Image accept-types

Override the default accepted MIME types:

```typescript
// In tina/config.ts:
media: {
  tina: {
    mediaRoot: 'uploads',
    publicFolder: 'public',
    accept: 'image/jpeg,image/png,image/webp',  // limit to these
  },
}
```

See `references/media/02-accepted-types.md`.

## Image renderer-side optimization

Use `next/image` for optimization:

```tsx
import Image from 'next/image'

<Image src={data.heroImage} alt={data.alt} width={1920} height={1080} priority />
```

For external media (Cloudinary), allowlist the domain in `next.config.ts`:

```typescript
images: {
  remotePatterns: [
    { protocol: 'https', hostname: 'res.cloudinary.com' },
  ],
}
```

## Color renderer-side rendering

```tsx
<section style={{ backgroundColor: data.themeColor }}>...</section>
```

Or, if you stored a Tailwind class via string-options:

```tsx
<section className={data.background}>...</section>
```

Mind the Tailwind dynamic-class issue (see `references/schema/04-blocks-pattern.md`).

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `image` field with no media store configured | Picker fails | Configure `media.tina` or external provider |
| Color stored as RGB but rendered as hex | Mismatch | Pick one format and stick |
| Color picker for design choices that should be tokens | Drift from design system | Use `string + options` instead |
| Image without alt-text companion | A11y violation | Wrap in object with required alt |
| Forgot Cloudinary domain in `remotePatterns` | next/image fails | Add hostname |
