# Next Route Bridge

> Documents the tiny App Router file that mounts the shared Hono API inside `apps/web`. Consult this when moving the API entry point, adding supported HTTP verbs, or understanding why Supastarter keeps almost all server logic out of `apps/web/app/api`.

## Key files

- `apps/web/app/api/[[...rest]]/route.ts`
- `packages/api/index.ts`

## Catch-all route

```ts
// apps/web/app/api/[[...rest]]/route.ts
import { app } from "@repo/api";
import { handle } from "hono/vercel";

const handler = handle(app);

export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const PATCH = handler;
export const DELETE = handler;
export const OPTIONS = handler;
```

## Why this file is so small

All routing and middleware live in `packages/api/index.ts`. The App Router file only does two things:

1. imports the shared Hono app from `@repo/api`
2. adapts it to the Next.js/Vercel request model with `hono/vercel`

Because the Hono app already calls `.basePath("/api")`, and this file sits at `app/api/[[...rest]]`, every `/api/**` request flows through the same shared stack.

## Supported methods

The bridge exports these methods:

- `GET`
- `POST`
- `PUT`
- `PATCH`
- `DELETE`
- `OPTIONS`

If a new method is ever needed, the pattern is to export the same `handler` again rather than duplicating logic.

## Request path example

```text
GET /api/payments/purchases
  -> apps/web/app/api/[[...rest]]/route.ts
  -> hono/vercel handle(app)
  -> packages/api/index.ts
  -> openApiHandler
  -> payments.listPurchases
```

---

**Related references:**
- `references/api/overview.md` — The Hono app mounted by this route
- `references/api/transport-handlers.md` — How requests are split between RPC and OpenAPI
- `references/api/client-integration.md` — Frontend code that eventually calls this route
- `references/setup/monorepo-structure.md` — Monorepo locations for `apps/web` and `packages/api`
