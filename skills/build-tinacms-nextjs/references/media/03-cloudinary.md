# Cloudinary Media Store

External media provider. Best for media-heavy production sites — built-in image optimization, CDN, format conversion.

## Why Cloudinary

- Image optimization (resize, format conversion, quality)
- CDN delivery (fast worldwide)
- 25 GB free tier
- Transformations on URL (no pre-processing pipeline needed)

## Install

```bash
pnpm add next-tinacms-cloudinary @tinacms/auth
```

## Cloudinary credentials

Sign up at https://cloudinary.com and get from the Dashboard:

```env
# .env
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

## `tina/config.ts`

```typescript
export default defineConfig({
  // ...
  media: {
    // Replace media.tina with loadCustomStore
    loadCustomStore: async () => {
      const pack = await import('next-tinacms-cloudinary')
      return pack.TinaCloudCloudinaryMediaStore
    },
  },
  // ...
})
```

## API route

You also need a Next.js API route to handle Cloudinary signing/auth:

```typescript
// app/api/cloudinary/[...path]/route.ts
import { mediaHandlerConfig, createMediaHandler } from 'next-tinacms-cloudinary/dist/handlers'
import { isAuthorized } from '@tinacms/auth'

const handler = createMediaHandler({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME!,
  api_key: process.env.CLOUDINARY_API_KEY!,
  api_secret: process.env.CLOUDINARY_API_SECRET!,
  authorized: async (req: any) => {
    if (process.env.NODE_ENV === 'development') return true
    try {
      const user = await isAuthorized(req)
      return user && user.verified
    } catch {
      return false
    }
  },
})

export { handler as GET, handler as POST, handler as DELETE }
```

## Stored format

Image fields store the full Cloudinary URL:

```yaml
heroImage: 'https://res.cloudinary.com/your-cloud/image/upload/v1234567890/hero.jpg'
```

## Transformations on URL

Cloudinary transformations modify the URL:

```
https://res.cloudinary.com/your-cloud/image/upload/w_1200,h_630,c_fill/hero.jpg
                                              ↑ width 1200, height 630, crop fill
```

For OG images, append transformations:

```typescript
function ogImageUrl(rawUrl: string): string {
  return rawUrl.replace('/upload/', '/upload/w_1200,h_630,c_fill,q_auto,f_auto/')
}
```

## next/image config

```typescript
// next.config.ts
const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'res.cloudinary.com' },
    ],
  },
}
```

Without this, `next/image` blocks Cloudinary URLs.

## Renderer

```tsx
import Image from 'next/image'

<Image
  src={data.heroImage}
  alt={data.alt}
  width={1200}
  height={630}
/>
```

`next/image` adds its own optimization layer. With Cloudinary, you double-optimize — usually fine, but be aware.

## Free tier limits

| Resource | Free |
|---|---|
| Storage | 25 GB |
| Bandwidth | 25 GB/month |
| Transformations | 25,000/month |

Most marketing sites stay free. High-traffic sites need a paid plan.

## "Ghost upload" issue

A known TinaCMS UX bug: the upload toast shows an error, but the file actually succeeds. **Refresh the media browser before retrying** — duplicates a file that's already there.

## Verifying

After config:

1. Open admin → media library — should show Cloudinary assets
2. Upload an image — should appear in your Cloudinary dashboard
3. The URL should be `https://res.cloudinary.com/...`

If the upload fails:

- Check `.env` credentials
- Check the API route at `/api/cloudinary/...` is accessible
- Check `loadCustomStore` runs (not just `media.tina`)

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `next.config.ts` `remotePatterns` | next/image fails | Add hostname |
| `media.tina` AND `loadCustomStore` both set | Conflict | Use one or the other |
| `CLOUDINARY_API_SECRET` exposed in client | Security issue | Always server-side only |
| API route at wrong path | Uploads fail with 404 | Match the path next-tinacms-cloudinary expects |
| Forgot auth check in API route | Public uploads | Use `isAuthorized` from `@tinacms/auth` |
