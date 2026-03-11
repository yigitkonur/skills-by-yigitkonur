# Query Patterns

> Documents the reusable Prisma query helpers that sit between raw Prisma calls and the rest of the app. Consult this when adding data access logic so it stays in the package layer instead of spreading through pages, routes, or auth configuration.

## Key files

- `packages/database/prisma/queries/users.ts`
- `packages/database/prisma/queries/organizations.ts`
- `packages/database/prisma/queries/purchases.ts`
- `packages/database/prisma/queries/index.ts`

## Pattern

```ts
export async function getUserById(id: string) {
  return await db.user.findFirst({
    where: { id },
  });
}
```

## New file template

When creating a new query file (e.g., `packages/database/prisma/queries/projects.ts`):

```ts
import { db } from "../client";

export async function getProjectsByOrganization(organizationId: string) {
  return await db.project.findMany({
    where: { organizationId },
    orderBy: { createdAt: "desc" },
  });
}

export async function getProjectById(id: string) {
  return await db.project.findFirst({
    where: { id },
  });
}
```

Then re-export from `packages/database/prisma/queries/index.ts`.

## When to use query helpers vs direct db calls

- **Use query helpers** when the same query is reused across multiple procedures, server components, or auth checks. Put these in `packages/database/prisma/queries/`.
- **Use direct `db` calls** for one-off queries scoped to a single procedure handler where reuse is unlikely.

## Implementation notes

- Queries are grouped by domain (`users`, `organizations`, `purchases`).
- The app imports these helpers from `@repo/database` instead of issuing raw Prisma calls everywhere.
- Billing/auth helpers rely heavily on organization and purchase query helpers.

---

**Related references:**
- `references/database/schema-overview.md` — Database package structure
- `references/payments/customer-ids.md` — Query helpers used to persist customer IDs
- `references/auth/server-session-helpers.md` — Server auth helpers that read organization and invitation state
