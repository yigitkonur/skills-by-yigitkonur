# Repo-Based Media (default)

The default media store. Images and assets upload to a folder in your `public/` directory and are committed to git. Free, simple, but doesn't scale to media-heavy sites.

## Configuration

```typescript
// tina/config.ts
media: {
  tina: {
    mediaRoot: 'uploads',     // subfolder of publicFolder
    publicFolder: 'public',   // your Next.js public dir
  },
}
```

Files uploaded through the admin land at `public/uploads/<filename>` and are served at `/uploads/<filename>` in the browser.

## When to use

- Small sites (< 100 images)
- Simple blogs or marketing pages
- You want everything in git (no external service)
- Cost-sensitive (free)

## When NOT to use

- Media-heavy sites (> 500 images, video)
- Need image optimization (resize, format conversion)
- Need a CDN (repo-based is served from your origin)
- Multiple editors uploading simultaneously (commit conflicts)
- Large file uploads (git history bloats)

For media-heavy production sites, switch to Cloudinary, S3, or Vercel Blob. See `references/media/03-cloudinary.md`.

## File handling

When an editor uploads:

1. Browser sends file to TinaCMS (via TinaCloud or self-hosted backend)
2. Backend writes to `public/<mediaRoot>/<filename>`
3. Backend commits to git via the configured Git Provider

The image's path is stored in the document field as a string:

```yaml
heroImage: '/uploads/hero-2026-05-08.jpg'
```

## Filename conflicts

If two uploads have the same name, TinaCMS appends a suffix or overwrites depending on version. Don't rely on specific names — let the picker generate unique names.

## Renderer side

```tsx
import Image from 'next/image'

<Image
  src={data.heroImage}      // '/uploads/hero.jpg'
  alt={data.alt}
  width={1920}
  height={1080}
/>
```

`next/image` handles optimization, even for repo-based images.

## Optimization caveats

`next/image` provides:

- WebP conversion at request time
- Resize-to-fit
- Lazy loading

But the original full-size file is still committed to git. Heavy use → bloated git history. For media-heavy sites, external providers (Cloudinary, S3) avoid this.

## Filtering accepted types

```typescript
media: {
  tina: {
    mediaRoot: 'uploads',
    publicFolder: 'public',
    accept: 'image/jpeg,image/png,image/webp',  // restrict file types
  },
}
```

See `references/media/02-accepted-types.md`.

## Multiple media folders

Tinacms allows only one `media.tina` config. For separating asset types (images vs PDFs), use one folder + sort by extension.

For project-level multiple media stores (image to Cloudinary, video to S3), you'd need a custom store — non-trivial.

## Migration to external provider

If your repo-based media outgrows the use case:

1. Set up the new provider (e.g. Cloudinary)
2. Bulk upload existing `public/uploads/*` to the new provider
3. Update document fields with new URLs (script over content files)
4. Switch `tina/config.ts` to use `loadCustomStore`

Mass migration is non-trivial; usually you start over rather than migrate.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `mediaRoot: '/uploads'` (leading slash) | Files written to wrong path | No leading slash |
| `publicFolder: 'static'` (wrong dir) | Next.js doesn't serve them | Match Next.js's `public/` |
| Committed > 100MB of images | Git history bloated | Use external provider, or Git LFS |
| Same filename collisions | Overwritten content | Don't reuse names |
| Used `mediaRoot: 'public/uploads'` (duplicated) | Files written to `public/public/uploads/` | `mediaRoot` is relative to `publicFolder` |
