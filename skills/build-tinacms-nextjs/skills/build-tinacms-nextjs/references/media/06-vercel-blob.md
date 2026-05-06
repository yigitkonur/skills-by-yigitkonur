# Vercel Blob

Vercel-native object storage. Best when you're already on Vercel and want zero-config integration.

## Why Vercel Blob

- Native Vercel integration (no separate account)
- Automatic CDN via Vercel's edge network
- Pay-as-you-go pricing
- Same authentication as Vercel deployments

## Install

```bash
pnpm add next-tinacms-blob @vercel/blob @tinacms/auth
```

## Setup

Enable Vercel Blob in your Vercel project: **Project Settings → Storage → Blob**.

Vercel auto-injects `BLOB_READ_WRITE_TOKEN` into your project's env.

## `tina/config.ts`

```typescript
export default defineConfig({
  // ...
  media: {
    loadCustomStore: async () => {
      const pack = await import('next-tinacms-blob')
      return pack.TinaCloudVercelBlobMediaStore
    },
  },
  // ...
})
```

## API route

```typescript
// app/api/blob/[...path]/route.ts
import { createMediaHandler } from 'next-tinacms-blob/dist/handlers'
import { isAuthorized } from '@tinacms/auth'

const handler = createMediaHandler({
  token: process.env.BLOB_READ_WRITE_TOKEN!,
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

## Public URL pattern

```
https://<store-id>.public.blob.vercel-storage.com/<filename>
```

Vercel auto-generates the store ID. URLs are stable across deploys.

## next/image config

```typescript
images: {
  remotePatterns: [
    // Pin to your specific Blob store hostname rather than a wildcard so you
    // don't allow arbitrary other Vercel Blob stores to serve through your CDN.
    { protocol: 'https', hostname: '<your-store-id>.public.blob.vercel-storage.com' },
  ],
}
```

## Cost

| Resource | Free tier | Per unit |
|---|---|---|
| Storage | 1 GB | $0.15/GB-month |
| Operations | 100k | varies |

For small sites: free. For media-heavy sites: comparable to S3, slightly more expensive than DO Spaces.

## Limitations

- Vercel-only (lock-in)
- Migration off Vercel = migrate Blob too

For longer-term independence, prefer Cloudinary or S3.

## Local dev

In local dev with `TINA_PUBLIC_IS_LOCAL=true`, the media handler can either:

- Skip auth and write to Vercel Blob (using your token)
- Fall back to local filesystem (more complex)

Simplest: use a separate local-dev store (repo-based) and Vercel Blob in production. Branch in `loadCustomStore`:

```typescript
media: {
  loadCustomStore: process.env.TINA_PUBLIC_IS_LOCAL === 'true'
    ? undefined
    : async () => (await import('next-tinacms-blob')).TinaCloudVercelBlobMediaStore,
  tina: process.env.TINA_PUBLIC_IS_LOCAL === 'true' ? {
    mediaRoot: 'uploads',
    publicFolder: 'public',
  } : undefined,
}
```

## When to choose Vercel Blob over Cloudinary/S3

Pick Vercel Blob if:

- You're committed to Vercel
- You want zero-config integration
- Your media volume is small (< 5 GB)

Pick Cloudinary if you need image optimization (resize, format conversion).

Pick S3/DO Spaces if you want lowest-cost / vendor-independent.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot to enable Blob in Project Settings | Token missing | Enable + redeploy |
| Used `BLOB_READ_WRITE_TOKEN` in client bundle | Security issue | Server-side only |
| Missed `remotePatterns` for next/image | Images blocked | Add Vercel Blob hostname |
| Local dev hits Vercel Blob (uses paid quota) | Unnecessary cost | Use local-dev fallback to repo-based |
