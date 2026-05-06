# DigitalOcean Spaces

S3-compatible object storage. Works with `next-tinacms-s3` since it implements the S3 API.

## Why DO Spaces

- $5/month flat (250GB storage, 1TB egress) — cheaper than S3 for medium sites
- S3-compatible API (same SDK, same code)
- Built-in CDN
- Simpler pricing than AWS

## Install

```bash
pnpm add next-tinacms-s3 @tinacms/auth @aws-sdk/client-s3
```

Same package as S3.

## Credentials

From DO Console → Spaces → Generate Spaces Keys:

```env
DO_SPACES_KEY=your-access-key
DO_SPACES_SECRET=your-secret-key
DO_SPACES_REGION=nyc3
DO_SPACES_BUCKET=your-bucket
DO_SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com
```

## `tina/config.ts`

Same as S3:

```typescript
media: {
  loadCustomStore: async () => {
    const pack = await import('next-tinacms-s3')
    return pack.TinaCloudS3MediaStore
  },
}
```

## API route — point at DO endpoint

```typescript
// app/api/s3/[...path]/route.ts
import { createMediaHandler } from 'next-tinacms-s3/dist/handlers'
import { isAuthorized } from '@tinacms/auth'

const handler = createMediaHandler({
  config: {
    region: process.env.DO_SPACES_REGION!,           // e.g. 'nyc3'
    endpoint: process.env.DO_SPACES_ENDPOINT!,        // e.g. 'https://nyc3.digitaloceanspaces.com'
    credentials: {
      accessKeyId: process.env.DO_SPACES_KEY!,
      secretAccessKey: process.env.DO_SPACES_SECRET!,
    },
  },
  bucket: process.env.DO_SPACES_BUCKET!,
  authorized: /* same as S3 */,
})

export { handler as GET, handler as POST, handler as DELETE }
```

The key difference from AWS S3: set `endpoint` to the DO Spaces endpoint URL.

## Public URL pattern

```
https://<bucket>.<region>.digitaloceanspaces.com/<key>
# OR with CDN enabled (recommended):
https://<bucket>.<region>.cdn.digitaloceanspaces.com/<key>
```

## Enable CDN

In DO Console → Spaces → your-bucket → Settings → enable CDN. Use the `cdn.digitaloceanspaces.com` URL for production.

## next/image config

```typescript
images: {
  remotePatterns: [
    { protocol: 'https', hostname: '*.digitaloceanspaces.com' },
  ],
}
```

## Region availability

DO Spaces regions:

- `nyc3` — New York
- `ams3` — Amsterdam
- `sgp1` — Singapore
- `sfo3` — San Francisco
- `fra1` — Frankfurt

Pick the region closest to your audience or your deploy region.

## Cost comparison (rough)

For 50 GB storage, 200 GB egress per month:

| Provider | Cost |
|---|---|
| AWS S3 + CloudFront | ~$25–35 |
| DigitalOcean Spaces | $5 |
| Cloudinary (paid plan) | ~$50+ |

DO Spaces is the cheapest at moderate volumes.

## Migration from S3 to DO Spaces

If you started on S3 and want to move:

1. Use `aws s3 sync` or `s3-rsync` to copy bucket contents
2. Update env vars to point at DO
3. Update content URLs (script over `content/**/*.{md,mdx,json}`) to swap hostnames
4. Verify a few pages, then deploy

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `endpoint` in config | SDK calls AWS S3 by default | Set `endpoint` to DO URL |
| Used wrong region | Bucket not found | Match the bucket's region |
| Didn't enable CDN | Slow asset delivery | Enable in DO Console |
| Missed `remotePatterns` for `next/image` | Images don't render | Add hostname |
| ACL not "public-read" | Images 403 | Set ACL on upload or bucket policy |
