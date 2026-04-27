# File Storage, Upload, Download, And Document IDs

## Use This When
- Uploading files from Swift.
- Designing file metadata tables and secure serving behavior.
- Explaining Convex document IDs and storage IDs in Swift models.

## Default Upload Flow
- Ask Convex for an upload URL.
- Upload bytes with `URLSession`.
- Persist the returned `storageId` in your own table through a mutation.
- Query metadata or serving URLs separately for display.

## Operational Limits To Keep Visible
- Upload URLs expire after one hour.
- Upload POSTs time out after two minutes.
- Custom HTTP-action upload flows have their own size ceiling; verify the current limit before promising support for large uploads.
- These are product constraints, not just transport trivia.

## Serving Rule
- `ctx.storage.getUrl()` is fine when authorization can be decided at URL-generation time.
- If access must be checked at serve time, use a custom HTTP action instead.
- Separate file metadata policy from file-byte transport policy.

## Swift Modeling Rule
- Treat Convex document IDs and storage IDs as explicit model fields.
- Map `_id` and `_creationTime` intentionally when those matter in SwiftUI.
- Keep file metadata small, queryable, and authorization-aware.

## Avoid
- Assuming the Swift SDK has a high-level file-storage API comparable to richer web ergonomics.
- Burying authorization decisions inside the client.
- Treating storage objects and app-level metadata rows as the same thing.

## Read Next
- [03-testing-debugging-and-observability.md](03-testing-debugging-and-observability.md)
- [../backend/04-auth-rules-and-server-ownership.md](../backend/04-auth-rules-and-server-ownership.md)
- [../operations/02-known-gaps-limitations-and-non-goals.md](../operations/02-known-gaps-limitations-and-non-goals.md)
