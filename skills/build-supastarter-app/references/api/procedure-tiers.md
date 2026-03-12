# Procedure Tiers

> Explains the three oRPC base procedure builders used across the API package and the context each one makes available to handlers. Consult this before adding or reviewing an endpoint so auth checks, role checks, and handler context stay aligned with the rest of the codebase.

> ⚠️ **Steering:** There are exactly three procedure tiers: `publicProcedure`, `protectedProcedure`, `adminProcedure`. There is NO `organizationProcedure`. For org-scoped data, use `protectedProcedure` and add a membership check in the handler body. See the guard pattern section below.

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

## Organization membership guard pattern

> ⚠️ **Steering:** `protectedProcedure` only verifies a session exists — it does NOT verify the user belongs to the target organization. Any authenticated user could access any org's data by guessing a slug or ID. You MUST add an explicit membership check for org-scoped procedures.

```ts
import { protectedProcedure } from "../../../orpc/procedures";
import { ORPCError } from "@orpc/server";
import { db } from "@repo/database";
import { z } from "zod";

export const updateOrgSettings = protectedProcedure
  .route({
    method: "PUT",
    path: "/organizations/{organizationId}/settings",
    tags: ["Organizations"],
    summary: "Update organization settings",
  })
  .input(z.object({
    organizationId: z.string(),
    name: z.string().min(1).optional(),
  }))
  .handler(async ({ input, context }) => {
    // Step 1: Verify org membership
    const membership = await db.member.findFirst({
      where: {
        userId: context.user.id,
        organizationId: input.organizationId,
      },
    });

    if (!membership) {
      throw new ORPCError("FORBIDDEN", {
        message: "Not a member of this organization",
      });
    }

    // Step 2: Optionally check role for write operations
    if (membership.role !== "owner" && membership.role !== "admin") {
      throw new ORPCError("FORBIDDEN", {
        message: "Insufficient role for this action",
      });
    }

    // Step 3: Perform the operation
    return await db.organization.update({
      where: { id: input.organizationId },
      data: { name: input.name },
    });
  });
```

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

---

**Related references:**
- `references/api/overview.md` — Where request context enters from the Hono app
- `references/api/contact-module.md` — Concrete `publicProcedure` example
- `references/api/payments-organizations-modules.md` — Concrete `protectedProcedure` examples
- `references/auth/better-auth-config.md` — Better Auth setup used by `auth.api.getSession(...)`
- `references/auth/server-session-helpers.md` — Server-side auth helpers built on the same auth layer
- `references/tasks/add-api-endpoint.md` — Full endpoint creation task guide with org-scoped example
