# External Media Authentication

Every external media provider (Cloudinary, S3, Blob) needs auth on the API route to prevent unauthorized uploads. The `@tinacms/auth` package provides the standard pattern.

## Why auth matters

Without auth, anyone who knows the API route URL can:

- Upload arbitrary files (storage abuse, malware hosting)
- Delete or rename existing files (vandalism)
- Run up your media-store quota

Always gate the media handler.

## The standard pattern

```typescript
// app/api/<provider>/[...path]/route.ts
import { isAuthorized } from '@tinacms/auth'
import { createMediaHandler } from '<provider-package>/dist/handlers'

const handler = createMediaHandler({
  config: { /* provider-specific */ },
  authorized: async (req: any) => {
    // Local dev: skip auth
    if (process.env.NODE_ENV === 'development') return true

    // Production: check via @tinacms/auth
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

## How `isAuthorized` works

For TinaCloud projects: validates the bearer token against TinaCloud's auth API. Editors signed into the admin SPA pass the token automatically.

For self-hosted projects: the auth provider you configured (Auth.js, Clerk, custom) handles this — `isAuthorized` calls into your auth provider's session check.

## Custom auth check

Replace `isAuthorized` with your own:

```typescript
authorized: async (req: any) => {
  // Verify your own session cookie / JWT
  const session = req.cookies?.get?.('session')
  if (!session) return false

  // Check user has upload permission
  const user = await verifySession(session)
  return user.canUploadMedia
}
```

For self-hosted with Clerk:

```typescript
import { auth } from '@clerk/nextjs/server'

authorized: async () => {
  const { userId } = await auth()
  return Boolean(userId)
}
```

## Don't skip auth in production

```typescript
// ❌ DO NOT
authorized: async () => true   // accepts everyone

// ❌ DO NOT
authorized: async () => process.env.NODE_ENV === 'production'  // wrong
```

Both leave the upload endpoint open to the public.

## Allowing unauthenticated reads (rare)

Reads (GET) usually pass through without auth — the public can fetch images. Only writes (POST, DELETE) need auth:

```typescript
authorized: async (req: any) => {
  if (req.method === 'GET') return true   // allow public reads
  // ... auth check for writes
}
```

But `createMediaHandler` typically applies the same check to all methods. Override only if your provider supports per-method auth.

## CORS considerations

For browser-based uploads (which is the standard TinaCMS flow):

- The API route runs on your domain (no CORS issue)
- The upload destination (S3, Cloudinary) needs CORS for your domain (already covered in provider docs)

## Local dev shortcut

```typescript
authorized: async (req: any) => {
  if (process.env.TINA_PUBLIC_IS_LOCAL === 'true') return true
  // ... real auth
}
```

`TINA_PUBLIC_IS_LOCAL=true` is the standard flag for "I'm in local dev, skip auth."

## Auth across providers

The `@tinacms/auth` integration is the same regardless of media provider. Cloudinary, S3, DO Spaces, Vercel Blob — all use `isAuthorized` the same way.

## Token rotation

Media-provider keys (Cloudinary API secret, AWS access key, etc.) are long-lived. Rotate periodically:

1. Generate new key from provider dashboard
2. Update env var in Vercel/CI
3. Redeploy
4. Revoke old key

## Audit log

For high-trust environments, log every upload:

```typescript
authorized: async (req: any) => {
  try {
    const user = await isAuthorized(req)
    if (!user?.verified) return false

    // Log the upload attempt
    console.log(`[media] User ${user.email} uploading at ${req.url}`)
    return true
  } catch {
    return false
  }
}
```

Pipe console logs to Vercel/Datadog/etc. Audit by user.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `authorized: async () => true` | Public uploads allowed | Implement real auth |
| Auth check throws but caught silently | All uploads denied | Log inside catch |
| Forgot `process.env.NODE_ENV` check | Local dev requires auth | Add the dev shortcut |
| Used a Vercel preview URL for production webhook | Webhook fails when preview expires | Use stable production URL |
| Provider key in client bundle | Token leak | Always server-side only |
