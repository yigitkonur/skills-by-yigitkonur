# OG Image Waterfall

Open Graph (`og:image`) and Twitter card (`twitter:image`) need an image, or social shares look broken. Use a waterfall.

## The waterfall

1. `page.seo.ogImage` — explicit per-page override
2. `page.heroImage` (or collection-default image) — first image on the page
3. `global.defaultOgImage` — site-wide fallback
4. Generated OG image (`opengraph-image.tsx`) — see `references/seo/05-dynamic-og-images.md`

## Implementation

```typescript
type OGImage = { url: string; width: number; height: number; alt: string }

function resolveOgImage(page: any, global: any): OGImage[] {
  const url =
    page.seo?.ogImage ||
    page.heroImage?.src ||
    page.heroImage ||
    global.defaultOgImage

  if (!url) return []

  return [
    {
      url,
      width: 1200,
      height: 630,
      alt: page.title || global.siteName,
    },
  ]
}
```

`page.heroImage?.src` first (in case it's an object with alt), then bare string.

## Use in `generateMetadata`

```typescript
return {
  title,
  description,
  openGraph: {
    title,
    description,
    url,
    siteName: global.siteName,
    type: 'website',
    locale: global.locale || 'en_US',
    images: resolveOgImage(page, global),
  },
  twitter: {
    card: 'summary_large_image',
    title,
    description,
    images: resolveOgImage(page, global).map((i) => i.url),
    site: global.twitterHandle,
  },
}
```

## Required dimensions

| Tag | Recommended | Notes |
|---|---|---|
| `og:image` | 1200×630 | Facebook, LinkedIn, Slack, Discord |
| `twitter:image` | 1200×630 | "summary_large_image" card |
| `og:image:alt` | text | Required when image is set |

For images smaller than 1200×630, social platforms may downscale poorly. Validate at upload via `ui.validate` on the image field.

## Absolute URLs required

OG image URLs must be **absolute**, not relative:

```typescript
// ❌ Relative — social platforms can't fetch
url: '/uploads/hero.jpg'

// ✅ Absolute
url: `${global.siteUrl}/uploads/hero.jpg`
```

If your image field stores `/uploads/hero.jpg`, prepend the siteUrl in the metadata layer:

```typescript
function absolute(url: string | undefined, baseUrl: string): string | undefined {
  if (!url) return undefined
  if (url.startsWith('http')) return url
  return `${baseUrl}${url.startsWith('/') ? '' : '/'}${url}`
}

// In waterfall:
const ogImageUrl = absolute(page.seo?.ogImage || page.heroImage, global.siteUrl)
```

## Per-collection variation

Blog posts often use the cover image:

```typescript
function resolvePostOgImage(post: any, global: any): OGImage[] {
  const url =
    post.seo?.ogImage ||
    post.coverImage ||
    global.defaultOgImage

  return url ? [{ url, width: 1200, height: 630, alt: post.title }] : []
}
```

For docs sites without per-page images, fall back to a generated OG image (next-step waterfall).

## Validation

```typescript
{
  name: 'ogImage',
  type: 'image',
  description: '1200×630 recommended (16:1.9 aspect ratio)',
  ui: {
    validate: (value) => {
      if (!value) return undefined
      if (!/\.(jpg|jpeg|png|webp)$/i.test(value)) return 'Use JPG, PNG, or WEBP'
      return undefined
    },
  },
}
```

For animated GIFs, social platforms typically use the first frame — usually fine, but test before relying.

## Verifying

After deploy:

1. Open https://opengraph.xyz/ and paste your URL
2. Check Facebook Sharing Debugger
3. Check Twitter Card Validator
4. Verify the image renders correctly in iOS iMessage, Slack, Discord

If the image doesn't appear:

- URL is relative (must be absolute)
- Image is too large (Facebook caps at 5MB)
- Image is behind auth or CORS-restricted
- Image hasn't been crawled (use the debugger to force re-fetch)

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Relative URL | Image doesn't load on social platforms | Make absolute |
| Missing `og:image:alt` | A11y warning | Always set |
| Wrong dimensions | Image cropped/stretched | Use 1200×630 |
| Using cropped images smaller than 1200×630 | Looks fine in dev, bad on social | Resize at media-store level |
| Different image in `og:image` vs `twitter:image` | Inconsistent social shares | Use same image for both |
