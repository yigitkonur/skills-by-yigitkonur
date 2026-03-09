# Bucket Configuration

> Documents the logical-to-physical bucket mapping used by the storage package. Consult this when adding a new bucket or checking which environment variable controls an existing one.

## Key files

- `packages/storage/config.ts`
- `packages/storage/types.ts`

## Representative code

```ts
export const config = {
  bucketNames: {
    avatars: process.env.NEXT_PUBLIC_AVATARS_BUCKET_NAME ?? "avatars",
  },
} as const;
```

## Why this layer exists

- App code refers to logical bucket keys like `avatars`
- Provider code resolves those keys into actual bucket names
- Type definitions keep signed URL helpers constrained to configured buckets

---

**Related references:**
- `references/storage/signed-urls.md` — How bucket keys are consumed
- `references/cheatsheets/env-vars.md` — Bucket-related env vars
- `references/storage/s3-provider.md` — Provider implementation
