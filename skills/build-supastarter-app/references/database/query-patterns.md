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

## New query file template

> ⚠️ **Steering:** New query files MUST start with `import { db } from "../client"`. Missing this import is a common mistake that prevents the file from compiling — the `db` variable is not globally available.

```ts
// packages/database/prisma/queries/<model>.ts
import { db } from "../client";

export async function get<Model>ById(id: string) {
  return await db.<model>.findFirst({
    where: { id },
  });
}

export async function get<Model>sByOrganization(organizationId: string) {
  return await db.<model>.findMany({
    where: { organizationId },
    orderBy: { createdAt: "desc" },
  });
}

export async function create<Model>(data: { /* fields */ }) {
  return await db.<model>.create({ data });
}

export async function delete<Model>(id: string) {
  return await db.<model>.delete({ where: { id } });
}
```

Then export from the barrel file:

```ts
// packages/database/prisma/queries/index.ts
export * from "./<model>";
```

## Query helpers vs direct `db` calls

| Use query helpers when | Use direct `db` calls when |
|---|---|
| The query is reused across 2+ call sites | One-off query in a single procedure |
| The query encapsulates business logic (e.g., "active members with role") | Simple `findFirst` / `create` with no special logic |
| Other packages need to import it (e.g., auth package needs user queries) | Used only within the same file |

When in doubt, start with a query helper — it is easier to inline later than to extract later.

## Implementation notes

- Queries are grouped by domain (`users`, `organizations`, `purchases`).
- The app imports these helpers from `@repo/database` instead of issuing raw Prisma calls everywhere.
- Billing/auth helpers rely heavily on organization and purchase query helpers.

---

**Related references:**
- `references/database/schema-overview.md` — Database package structure
- `references/database/prisma-client.md` — The singleton client that `db` refers to
- `references/database/generation-exports.md` — Generate/export workflow after schema changes
- `references/payments/customer-ids.md` — Query helpers used to persist customer IDs
- `references/auth/server-session-helpers.md` — Server auth helpers that read organization and invitation state
- `references/tasks/add-database-model.md` — Full database model task guide with new file template
