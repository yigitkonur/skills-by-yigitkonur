# Pattern: Direct Upload to S3

> Documents the signed-URL upload approach used for files like avatars. Consult this when adding new client-side uploads.

## Core idea

The app generates a presigned upload URL on the server and uploads directly from the browser to S3-compatible storage, avoiding large file payloads through the main app server.

## Storage package hooks

`packages/storage/provider/s3/index.ts` exposes helpers for signed PUT and GET URLs, while bucket names come from `packages/storage/config.ts`.

## Practical flow

1. Ask the server for a signed upload URL
2. Upload directly to the returned S3 endpoint
3. Persist the resulting object key/URL on the owning entity

---

**Related references:**
- `references/storage/s3-provider.md` — S3 client and signing helpers
- `references/storage/signed-urls.md` — Upload/download URL behavior
- `references/settings/billing-security-and-avatar.md` — Avatar feature that uses this pattern
