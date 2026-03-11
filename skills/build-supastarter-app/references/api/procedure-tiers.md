# Procedure Tiers

> Explains the three oRPC base procedure builders used across the API package and the context each one makes available to handlers. Consult this before adding or reviewing an endpoint so auth checks, role checks, and handler context stay aligned with the rest of the codebase.

## Key file

- `packages/api/orpc/procedures.ts`

## Base builders

```ts
// packages/api/orpc/procedures.ts
export const publicProcedure = os.$context<{
  headers: Headers;
}>();

export const protectedProcedure = publicProcedure.use(async ({ context, next }) => {
  const session = await auth.api.getSession({
    headers: context.headers,
  });

  if (!session) {
    throw new ORPCError("UNAUTHORIZED");
  }

  return await next({
    context: {
      session: session.session,
      user: session.user,
    },
  });
});

export const adminProcedure = protectedProcedure.use(async ({ context, next }) => {
  if (context.user.role !== "admin") {
    throw new ORPCError("FORBIDDEN");
  }

  return await next();
});
```

## What each tier provides

| Procedure | Auth required | Context available in handler | Typical use |
|----------|---------------|------------------------------|-------------|
| `publicProcedure` | No | `headers` | Contact form, newsletter signup, public reads |
| `protectedProcedure` | Yes | `headers`, `session`, `user` | Purchases, account actions, org member actions |
| `adminProcedure` | Yes + `user.role === "admin"` | `headers`, `session`, `user` | Global admin panel procedures |

## Context enrichment pattern

The tiers are intentionally minimal:

- `publicProcedure` only defines the base request context shape coming from the Hono catch-all middleware.
- `protectedProcedure` calls `auth.api.getSession(...)` with the forwarded request headers and stops execution with `UNAUTHORIZED` when no session exists.
- `adminProcedure` builds on `protectedProcedure` and adds one more authorization check for the global admin role.

## Usage pattern in modules

Each feature procedure starts from one of these builders and then chains oRPC configuration:

```ts
publicProcedure
  .route({ method: "POST", path: "/contact" })
  .input(contactFormSchema)
  .handler(async ({ input }) => {
    // ...
  });
```

That keeps authentication logic out of individual handlers unless a module needs extra business-specific authorization, such as organization membership or purchase ownership.

## Organization-membership guard

For organization-scoped procedures that need to verify the user actually belongs to the target organization (not just that they are authenticated), add a membership check inside the handler:

```ts
import { db } from "@repo/database";

// Inside an organization-scoped procedure handler:
const membership = await db.membership.findFirst({
  where: {
    userId: ctx.user.id,
    organizationId: organizationId,
  },
});
if (!membership) {
  throw new ORPCError("FORBIDDEN");
}
```

Use this pattern when the procedure operates on a specific organization's data and the caller might pass an `organizationId` they don't belong to.

---

**Related references:**
- `references/api/overview.md` — Where request context enters from the Hono app
- `references/api/contact-module.md` — Concrete `publicProcedure` example
- `references/api/payments-organizations-modules.md` — Concrete `protectedProcedure` examples
- `references/auth/better-auth-config.md` — Better Auth setup used by `auth.api.getSession(...)`
- `references/auth/server-session-helpers.md` — Server-side auth helpers built on the same auth layer
