# Dynamic OG Images

Generate per-page OG cards via `next/og`. Useful when you don't want to design each card by hand.

## The pattern

```tsx
// app/[slug]/opengraph-image.tsx
import { ImageResponse } from 'next/og'
import { client } from '@/tina/__generated__/client'

export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default async function OGImage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const result = await client.queries.page({ relativePath: `${slug}.md` })
  const page = result.data.page

  return new ImageResponse(
    (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          width: '100%',
          height: '100%',
          backgroundColor: '#0a0a0a',
          color: '#fff',
          padding: '60px',
        }}
      >
        <div style={{ fontSize: 64, fontWeight: 700, textAlign: 'center' }}>
          {page.title}
        </div>
        {page.seo?.metaDescription && (
          <div style={{ fontSize: 32, marginTop: 20, color: '#a0a0a0', textAlign: 'center' }}>
            {page.seo.metaDescription.slice(0, 80)}
          </div>
        )}
      </div>
    ),
    { ...size },
  )
}
```

Visit `https://your-site.com/<slug>/opengraph-image` to see the generated image.

## Use `next/og`, not `@vercel/og`

`@vercel/og` is deprecated. `next/og` is the current package — comes with Next.js, no install needed.

```tsx
import { ImageResponse } from 'next/og'  // ✅ correct
// import { ImageResponse } from '@vercel/og'  // ❌ deprecated
```

## Layout constraints

| Constraint | Value |
|---|---|
| Bundle limit | 500 KB (includes fonts and images) |
| Layout | **Flexbox only** (no grid, no positioning) |
| Fonts | TTF, OTF, WOFF (no WOFF2) |
| Images | Inline base64 or remote URL |

## Custom font

```tsx
const interBold = await fetch(
  new URL('./Inter-Bold.ttf', import.meta.url),
).then((res) => res.arrayBuffer())

return new ImageResponse(
  (/* JSX */),
  {
    ...size,
    fonts: [
      { name: 'Inter', data: interBold, weight: 700, style: 'normal' },
    ],
  },
)
```

Place the `.ttf` file next to the route file or in `public/fonts/`.

## With brand identity

```tsx
return new ImageResponse(
  (
    <div style={{ display: 'flex', /* ... */ }}>
      <img src={`${process.env.NEXT_PUBLIC_SITE_URL}/logo.png`} alt="" width={120} height={40} />
      <div style={{ fontSize: 64, fontWeight: 700 }}>{page.title}</div>
      <div style={{ fontSize: 24, color: '#888' }}>{global.siteName}</div>
    </div>
  ),
  { ...size },
)
```

Logo + title + site name is a common pattern.

## Caching

`opengraph-image.tsx` is cached at the route level — first hit generates the PNG; subsequent hits serve it from cache. Cache invalidation follows the same `revalidate` rules as the page itself.

For dynamic images with frequent changes, you may want shorter `revalidate`:

```tsx
export const revalidate = 60  // regenerate every 60 seconds
```

## Multiple variants per page

```tsx
// app/[slug]/opengraph-image.tsx — default
// app/[slug]/twitter-image.tsx — Twitter-specific
```

Same shape, just a different filename. Twitter Card uses `twitter-image.tsx` if present, falls back to OG.

## Linking from generateMetadata

If you have `opengraph-image.tsx`, Next.js automatically wires it into `og:image`:

```typescript
// generateMetadata picks up opengraph-image.tsx automatically
// You don't need to manually add it to openGraph.images
```

To override:

```typescript
return {
  openGraph: {
    images: [{ url: 'https://example.com/custom-og.jpg', width: 1200, height: 630 }],
  },
}
```

Manual override wins over the convention file.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Used CSS Grid | `ImageResponse` rendering fails | Use Flexbox only |
| Bundle > 500 KB | Build error | Reduce font size, image size, or split text |
| External font URL | Build error | Inline font as ArrayBuffer |
| WOFF2 font | Not supported | Convert to TTF or WOFF |
| Forgot `export const size` | Default 1200×630 used (usually fine) | Be explicit |
| Used Server Component without `params` Promise | Build error | `await params` |
