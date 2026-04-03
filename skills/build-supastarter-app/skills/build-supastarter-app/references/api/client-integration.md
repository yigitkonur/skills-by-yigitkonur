# Client Integration

> Covers the frontend oRPC client setup and the TanStack Query helper layer used by client components. Consult this when wiring a new query or mutation, debugging why the browser targets `/api/rpc`, or understanding how frontend code gets end-to-end types from the shared router.

## Key files

- `apps/web/modules/shared/lib/orpc-client.ts`
- `apps/web/modules/shared/lib/orpc-query-utils.ts`
- `packages/api/orpc/router.ts`

## oRPC client setup

```ts
// apps/web/modules/shared/lib/orpc-client.ts
const link = new RPCLink({
  url: () => {
    if (typeof window === "undefined") {
      throw new Error("RPCLink is not allowed on the server side.");
    }

    return `${window.location.origin}/api/rpc`;
  },
  headers: async () => ({}),
  interceptors: [
    onError((error) => {
      if (error instanceof Error && error.name === "AbortError") {
        return;
      }

      console.error(error);
    }),
  ],
});

export const orpcClient: ApiRouterClient =
  globalThis.$orpcClient ?? createORPCClient(link);
```

## TanStack Query wrapper

```ts
// apps/web/modules/shared/lib/orpc-query-utils.ts
import { createTanstackQueryUtils } from "@orpc/tanstack-query";
import { orpcClient } from "./orpc-client";

export const orpc = createTanstackQueryUtils(orpcClient);
```

## Usage pattern in client components

The common pattern is:

```ts
import { orpc } from "@shared/lib/orpc-query-utils";
import { useMutation, useQuery } from "@tanstack/react-query";

const purchasesQuery = useQuery(
  orpc.payments.listPurchases.queryOptions({
    input: {},
  }),
);

const checkoutMutation = useMutation(
  orpc.payments.createCheckoutLink.mutationOptions(),
);
```

## Important behavior

- The browser transport always points at `window.location.origin + "/api/rpc"`.
- The RPC link intentionally returns empty headers on the client; the browser sends cookies automatically.
- `AbortError` is ignored so canceled requests do not produce noisy errors.
- `orpcClient` falls back to `globalThis.$orpcClient` when one is already injected, otherwise it creates an HTTP client from the RPC link.
- `ApiRouterClient` comes from `packages/api/orpc/router.ts`, so mounted router changes propagate into frontend types.

---

**Related references:**
- `references/api/root-router.md` — Source of the `ApiRouterClient` type and namespaces
- `references/api/transport-handlers.md` — Why the frontend targets `/api/rpc`
- `references/api/next-route-bridge.md` — How `/api/rpc/*` reaches the Hono app
- `references/setup/import-conventions.md` — Path aliases such as `@shared/*` and `@repo/*`
