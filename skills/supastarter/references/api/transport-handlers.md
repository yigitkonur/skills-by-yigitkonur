# Transport Handlers

> Explains how Supastarter serves the same oRPC router over two transports: a typed RPC endpoint for the app itself and an OpenAPI/REST surface for standard HTTP access and docs. Consult this when debugging `/api/rpc` requests, GET query coercion, or the generated docs at `/api/docs`.

## Key files

- `packages/api/orpc/handler.ts`
- `packages/api/index.ts`

## Handler definitions

```ts
// packages/api/orpc/handler.ts
export const rpcHandler = new RPCHandler(router, {
  clientInterceptors: [
    onError((error) => {
      logger.error(error);
    }),
  ],
});

export const openApiHandler = new OpenAPIHandler(router, {
  plugins: [
    new SmartCoercionPlugin({
      schemaConverters: [new ZodToJsonSchemaConverter()],
    }),
    new OpenAPIReferencePlugin({
      schemaConverters: [new ZodToJsonSchemaConverter()],
      specGenerateOptions: async () => {
        const authSchema = await auth.api.generateOpenAPISchema();

        authSchema.paths = Object.fromEntries(
          Object.entries(authSchema.paths).map(([path, pathItem]) => [
            `/auth${path}`,
            pathItem,
          ]),
        );

        return {
          ...(authSchema as any),
          info: { title: "supastarter API", version: "1.0.0" },
          servers: [{ url: "/api" }],
        };
      },
      docsPath: "/docs",
    }),
  ],
  clientInterceptors: [
    onError((error) => {
      logger.error(error);
    }),
  ],
});
```

## Responsibilities

### `rpcHandler`

- Serves the typed oRPC transport under `/api/rpc/*`
- Powers the app's frontend client in `apps/web/modules/shared/lib/orpc-client.ts`
- Uses a client interceptor to send transport-level errors to `@repo/logs`

### `openApiHandler`

- Serves REST/OpenAPI routes under `/api/*` when the path does not include `/rpc/`
- Applies `SmartCoercionPlugin` so GET query parameters are coerced to the shapes expected by Zod schemas
- Generates docs at `/api/docs`
- Merges Better Auth's generated OpenAPI schema into the same spec, prefixing auth routes with `/auth`

## How the Hono app selects a transport

```ts
// packages/api/index.ts
const isRpc = c.req.path.includes("/rpc/");
const handler = isRpc ? rpcHandler : openApiHandler;
const prefix = isRpc ? "/api/rpc" : "/api";
```

That is the whole split. There is no separate router tree for REST vs RPC.

## Practical impact

- Define a procedure once in a module.
- Mount it once in `packages/api/orpc/router.ts`.
- The procedure becomes available to typed frontend code and OpenAPI/REST consumers together.

---

**Related references:**
- `references/api/overview.md` — Where the handlers are mounted in the Hono app
- `references/api/root-router.md` — The shared router both handlers consume
- `references/api/client-integration.md` — The frontend consumer of the RPC transport
- `references/api/next-route-bridge.md` — The Next.js route file exposing the Hono app
- `references/auth/better-auth-config.md` — Better Auth schema merged into the OpenAPI docs
