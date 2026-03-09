# Root Router

> Shows how Supastarter composes one root oRPC router from feature routers such as `contact`, `payments`, and `organizations`. Consult this when adding a new API module, checking the client namespace a procedure will appear under, or tracing how one procedure becomes available to both RPC and OpenAPI transports.

## Key file

- `packages/api/orpc/router.ts`

## Root router composition

```ts
// packages/api/orpc/router.ts
import { adminRouter } from "../modules/admin/router";
import { aiRouter } from "../modules/ai/router";
import { contactRouter } from "../modules/contact/router";
import { newsletterRouter } from "../modules/newsletter/router";
import { organizationsRouter } from "../modules/organizations/router";
import { paymentsRouter } from "../modules/payments/router";
import { usersRouter } from "../modules/users/router";
import { publicProcedure } from "./procedures";

export const router = publicProcedure.router({
  admin: adminRouter,
  newsletter: newsletterRouter,
  contact: contactRouter,
  organizations: organizationsRouter,
  users: usersRouter,
  payments: paymentsRouter,
  ai: aiRouter,
});

export type ApiRouterClient = RouterClient<typeof router>;
```

## What this file does

- It is **composition-only**: no business logic lives here.
- Every mounted key becomes part of the API namespace used by both transports.
- `ApiRouterClient` is inferred from this exact object, so frontend types stay synchronized with the mounted modules.

## Module shape pattern

Feature modules export small router objects, for example:

```ts
// packages/api/modules/contact/router.ts
export const contactRouter = {
  submit: submitContactForm,
};

// packages/api/modules/payments/router.ts
export const paymentsRouter = {
  createCheckoutLink,
  createCustomerPortalLink,
  listPurchases,
};
```

That means the frontend accesses procedures through names like:

- `orpc.contact.submit`
- `orpc.payments.createCheckoutLink`
- `orpc.organizations.generateSlug`

## Adding a new module

1. Create `packages/api/modules/<feature>/procedures/*.ts`.
2. Export a router object from `packages/api/modules/<feature>/router.ts`.
3. Import that router into `packages/api/orpc/router.ts`.
4. Mount it under a stable key in `publicProcedure.router({ ... })`.
5. The new namespace is then available to both `RPCHandler` and `OpenAPIHandler` automatically.

---

**Related references:**
- `references/api/procedure-tiers.md` — Procedure builders used inside feature modules
- `references/api/client-integration.md` — `ApiRouterClient` usage on the frontend
- `references/api/transport-handlers.md` — How the shared router is exposed over RPC and OpenAPI
- `references/cheatsheets/file-locations.md` — Where to place new module routers and procedures
