# Signed URLs

> Documents the presigned PUT and GET URL flows used for direct client uploads and controlled file access. Consult this when working on avatar/logo uploads or debugging storage permissions.

## Key files

- `packages/storage/provider/s3/index.ts`
- `packages/storage/index.ts`

## Representative code

```ts
export const getSignedUploadUrl = async (path, { bucket }) => {
  return await getS3SignedUrl(
    s3Client,
    new PutObjectCommand({ Bucket: bucketName, Key: path, ContentType: "image/jpeg" }),
    { expiresIn: 60 },
  );
};

export const getSignedUrl = async (path, { bucket, expiresIn }) => {
  return getS3SignedUrl(
    s3Client,
    new GetObjectCommand({ Bucket: bucketName, Key: path }),
    { expiresIn },
  );
};
```

## Implementation notes

- Uploads happen client-side via a presigned PUT URL, not through a file-uploading server action.
- Read access is also presigned because buckets are expected to stay private.
- The package root re-exports the active provider implementation.

---

**Related references:**
- `references/storage/s3-provider.md` — S3 client initialization and env requirements
- `references/storage/bucket-config.md` — Logical bucket-name mapping
- `references/api/payments-organizations-modules.md` — Organization logo upload URL endpoint
