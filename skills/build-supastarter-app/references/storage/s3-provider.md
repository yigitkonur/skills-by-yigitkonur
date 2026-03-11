# S3 Provider

> Documents the concrete S3-compatible storage provider used by the starter. Consult this when changing storage backends, debugging connection config, or adjusting URL generation behavior.

## Key files

- `packages/storage/provider/s3/index.ts`

## Representative code

```ts
const getS3Client = () => {
  if (s3Client) return s3Client;
  s3Client = new S3Client({
    region: process.env.S3_REGION || "auto",
    endpoint: process.env.S3_ENDPOINT,
    forcePathStyle: true,
    credentials: {
      accessKeyId: process.env.S3_ACCESS_KEY_ID,
      secretAccessKey: process.env.S3_SECRET_ACCESS_KEY,
    },
  });
  return s3Client;
};
```

## Implementation notes

- The provider is compatible with AWS S3, MinIO, Cloudflare R2, and similar services.
- The client is a lazy singleton so repeated calls reuse the same SDK client.
- Missing env vars throw early rather than failing later during request handling.

---

**Related references:**
- `references/storage/signed-urls.md` — Upload and download URL generation
- `references/storage/bucket-config.md` — Bucket name mapping
- `references/setup/environment-setup.md` — Storage env var setup and local MinIO usage
- `references/deployment/local-services.md` — Docker compose for local MinIO
