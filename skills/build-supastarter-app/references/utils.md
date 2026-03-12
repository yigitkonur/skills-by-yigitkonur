# Utilities

> Overview of the small shared utilities package. Consult this when you need base URL resolution or are deciding where a tiny cross-package helper should live.

## Current helper

`packages/utils/lib/base-url.ts` provides the shared base-URL helper used to resolve app URLs cleanly across local and deployed environments.

## Practical rule

Prefer importing `@repo/utils` over duplicating deployment-aware URL logic in app code.

## Why it matters

Infrastructure-aware helpers like base URL resolution affect auth callbacks, links in emails, and any server-generated absolute URLs.

---

**Related references:**
- `references/deployment/vercel.md` — Hosted deployment behavior
- `references/setup/import-conventions.md` — Package import style
- `references/setup/environment-setup.md` — Environment variables that influence URL resolution
- `references/logging.md` — Shared logger package
