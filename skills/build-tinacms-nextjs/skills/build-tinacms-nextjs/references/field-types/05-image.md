# `image` field

Image picker that hooks into the configured media store (repo-based or external).

## Basic

```typescript
{
  name: 'heroImage',
  label: 'Hero Image',
  type: 'image',
  description: '1920x1080 recommended',
}
```

## Stored format

The path to the image relative to the public folder:

```yaml
---
heroImage: '/uploads/hero-2026-05-08.jpg'
---
```

For Cloudinary or external media, the value is the URL:

```yaml
---
heroImage: 'https://res.cloudinary.com/demo/image/upload/v123/sample.jpg'
---
```

## Required + alt text companion

Images often need an alt text companion field. Wrap them in an object:

```typescript
{
  name: 'heroImage',
  label: 'Hero Image',
  type: 'object',
  fields: [
    { name: 'src', type: 'image', required: true },
    {
      name: 'alt',
      type: 'string',
      required: true,
      description: 'Required for accessibility',
      ui: {
        validate: (value) => !value || value.length < 4 ? 'Alt text required (≥4 chars)' : undefined,
      },
    },
    { name: 'caption', type: 'string' },
  ],
}
```

See `references/schema/05-reusable-field-groups.md` for the reusable image field group.

## List of images

```typescript
{
  name: 'gallery',
  type: 'image',
  list: true,
}
```

A simple list of image paths. For images-with-alt-text use `object + list`:

```typescript
{
  name: 'gallery',
  type: 'object',
  list: true,
  ui: {
    itemProps: (item) => ({ label: item?.alt || 'Image' }),
  },
  fields: [
    { name: 'src', type: 'image', required: true },
    { name: 'alt', type: 'string', required: true },
    { name: 'caption', type: 'string' },
  ],
}
```

## Media store options

| Provider | When | Reference |
|---|---|---|
| Repo-based (default) | Small sites | `references/media/01-repo-based-default.md` |
| Cloudinary | Media-heavy production | `references/media/03-cloudinary.md` |
| S3 / DO Spaces | AWS infra | `references/media/04-s3.md`, `05-do-spaces.md` |
| Vercel Blob | Vercel-native | `references/media/06-vercel-blob.md` |

The image field's storage format depends on the configured provider. With external providers, the picker uploads to the provider and stores the resulting URL.

## Renderer side

```tsx
import Image from 'next/image'

export default function Hero({ data }: { data: { heroImage: string; title: string } }) {
  return (
    <section>
      <Image
        src={data.heroImage}
        alt={data.title}
        width={1920}
        height={1080}
        priority
      />
    </section>
  )
}
```

For repo-based images at `/uploads/...`, configure `next/image` to serve them:

```typescript
// next.config.ts
const nextConfig = {
  images: {
    remotePatterns: [
      // For external media providers:
      { protocol: 'https', hostname: 'res.cloudinary.com' },
    ],
  },
}
```

## Image validation

```typescript
{
  name: 'heroImage',
  type: 'image',
  ui: {
    validate: (value) => {
      if (!value) return undefined
      if (!/\.(jpg|jpeg|png|webp|avif)$/i.test(value)) return 'Use JPG/PNG/WEBP/AVIF'
      return undefined
    },
  },
}
```

## Accepted MIME types (override)

By default the picker accepts standard web image types. To override:

```typescript
// tina/config.ts
media: {
  tina: {
    mediaRoot: 'uploads',
    publicFolder: 'public',
    accept: 'image/jpeg,image/png,image/webp',
  },
}
```

See `references/media/02-accepted-types.md`.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Image field without alt-text companion | Accessibility issue | Wrap in object with required alt |
| External media provider configured but `next/image` not allowed | Image fails to load | Add to `remotePatterns` |
| Stored path `uploads/hero.jpg` (no leading slash) | Path doesn't resolve in renderer | Should be `/uploads/hero.jpg` |
| Big images committed to repo | Bloat git history | Use external media provider for production |
| Missing `width`/`height` on `next/image` | LCP/CLS issues | Always set explicit dimensions |
