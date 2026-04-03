# Task: Add an API Endpoint

> Step-by-step guide for adding a new oRPC endpoint. Consult this when creating a new server procedure and exposing it to the web app.

> ⚠️ **Steering:** There are only three procedure tiers: `publicProcedure`, `protectedProcedure`, `adminProcedure`. There is NO `organizationProcedure`. For org-scoped data, use `protectedProcedure` and add an org-membership check in the handler body.

## File locations

1. Create a procedure in `packages/api/modules/<module>/procedures/<action>.ts`
2. Export it from that module's router in `packages/api/modules/<module>/router.ts`
3. Wire the module router into `packages/api/orpc/router.ts` if this is a new module
4. Consume it through `@shared/lib/orpc-query-utils` on the client

## Minimal procedure (public)

```ts
import { publicProcedure } from "../../../orpc/procedures";
import { z } from "zod";

export const submitContactForm = publicProcedure
  .route({
    method: "POST",
    path: "/contact",
    tags: ["Contact"],
    summary: "Submit a contact form",
  })
  .input(z.object({ name: z.string().min(1), email: z.string().email(), message: z.string().min(1) }))
  .handler(async ({ input }) => {
    // implementation
  });
```

## Org-scoped procedure (with membership guard)

> ⚠️ **Steering:** `protectedProcedure` only verifies a session exists. It does NOT verify the user belongs to the target organization. You MUST add an explicit membership check for any procedure that operates on org-specific data.

```ts
import { protectedProcedure } from "../../../orpc/procedures";
import { ORPCError } from "@orpc/server";
import { db } from "@repo/database";
import { z } from "zod";

export const createProject = protectedProcedure
  .route({
    method: "POST",
    path: "/projects",
    tags: ["Projects"],
    summary: "Create a project in an organization",
  })
  .input(z.object({
    organizationId: z.string(),
    name: z.string().min(1),
  }))
  .handler(async ({ input, context }) => {
    // Verify org membership — protectedProcedure does NOT do this
    const membership = await db.member.findFirst({
      where: {
        userId: context.user.id,
        organizationId: input.organizationId,
      },
    });

    if (!membership) {
      throw new ORPCError("FORBIDDEN", { message: "Not a member of this organization" });
    }

    return await db.project.create({
      data: {
        name: input.name,
        organizationId: input.organizationId,
      },
    });
  });
```

## Wiring a new module router

```ts
// packages/api/modules/projects/router.ts
import { createProject } from "./procedures/create-project";
import { listProjects } from "./procedures/list-projects";

export const projectsRouter = {
  create: createProject,
  list: listProjects,
};
```

Then add to root router:

```ts
// packages/api/orpc/router.ts
import { projectsRouter } from "../modules/projects/router";

export const router = publicProcedure.router({
  // ...existing routers
  projects: projectsRouter,
});
```

## Repo-grounded checklist

- [ ] Chose correct procedure tier (`publicProcedure` / `protectedProcedure` / `adminProcedure`)
- [ ] Added route metadata (`method`, `path`, `tags`, `summary`)
- [ ] Validated input with Zod
- [ ] Added org-membership guard if procedure touches org-scoped data
- [ ] Wired into module router and root router (if new module)
- [ ] Client page uses `orpc.<module>.<action>.queryOptions()` or `.mutationOptions()`

---

**Related references:**
- `references/api/procedure-tiers.md` — Procedure tier details and org-membership guard pattern
- `references/api/root-router.md` — How routers are composed into the API surface
- `references/api/client-integration.md` — Browser-side oRPC client setup
- `references/patterns/react-query-orpc.md` — Client consumption with TanStack Query
- `references/database/query-patterns.md` — Query helper patterns for data access
