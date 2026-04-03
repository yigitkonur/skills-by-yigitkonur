# API Overview

> High-level map of Supastarter's API stack: a Hono app mounted at `/api`, Better Auth and payment webhooks on dedicated paths, and oRPC serving both typed RPC calls and OpenAPI/REST from the same router. Consult this first when tracing a request from Next.js into `packages/api` or deciding where a new backend endpoint belongs.

## Key files

- `packages/api/index.ts`
- `packages/api/orpc/handler.ts`
- `packages/api/orpc/router.ts`
- `apps/web/app/api/[[...rest]]/route.ts`

## Hono entry point

```ts
// packages/api/index.ts
export const app = new Hono()
  .basePath("/api")
  .use(honoLogger((message, ...rest) => logger.log(message, ...rest)))
  .use(
    cors({
      origin: getBaseUrl(),
      allowHeaders: ["Content-Type", "Authorization"],
      allowMethods: ["POST", "GET", "OPTIONS"],
      exposeHeaders: ["Content-Length"],
      maxAge: 600,
      credentials: true,
    }),
  )
  .on(["POST", "GET"], "/auth/**", (c) => auth.handler(c.req.raw))
  .post("/webhooks/payments", (c) => paymentsWebhookHandler(c.req.raw))
  .get("/health", (c) => c.text("OK"))
  .use("*", async (c, next) => {
    const context = { headers: c.req.raw.headers };
    const isRpc = c.req.path.includes("/rpc/");
    const handler = isRpc ? rpcHandler : openApiHandler;
    const prefix = isRpc ? "/api/rpc" : "/api";

    const { matched, response } = await handler.handle(c.req.raw, {
      prefix,
      context,
    });

    if (matched) {
      return c.newResponse(response.body, response);
    }

    await next();
  });
```

## Middleware and mount order

1. **Hono logger** — forwards request logs through `@repo/logs`.
2. **CORS** — allows the app's own base URL from `getBaseUrl()` and keeps credentials enabled.
3. **Better Auth handler** — `POST` and `GET` requests under `/api/auth/**` are delegated directly to `auth.handler(...)`.
4. **Payments webhook handler** — `POST /api/webhooks/payments` is delegated to `@repo/payments`.
5. **Health check** — `GET /api/health` returns plain text `OK`.
6. **oRPC catch-all** — everything else is routed to either the RPC or OpenAPI transport.

## RPC vs OpenAPI split

Supastarter does not maintain separate routers for typed and REST-style access. Instead, the Hono catch-all checks the request path:

- `c.req.path.includes("/rpc/")` → use `rpcHandler` with prefix `/api/rpc`
- everything else under `/api` → use `openApiHandler` with prefix `/api`

That means one set of oRPC procedures powers all of these surfaces:

- typed frontend calls such as `/api/rpc/payments/listPurchases`
- REST/OpenAPI routes such as `/api/payments/purchases`
- generated docs at `/api/docs`

## Request flow

```text
Next.js catch-all route
  -> hono/vercel handle(app)
  -> packages/api/index.ts Hono app
  -> Better Auth / webhook / health / oRPC transport split
  -> packages/api/orpc/router.ts root router
  -> feature module procedure
```

---

**Related references:**
- `references/api/procedure-tiers.md` — Base public/protected/admin procedure builders
- `references/api/root-router.md` — How feature routers are mounted into the shared API surface
- `references/api/transport-handlers.md` — RPC/OpenAPI handler details, docs generation, and coercion
- `references/api/next-route-bridge.md` — The Next.js App Router file that mounts the Hono app
- `references/setup/monorepo-structure.md` — Where `apps/web` and `packages/api` sit in the monorepo
