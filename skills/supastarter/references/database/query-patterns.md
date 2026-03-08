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

## Implementation notes

- Queries are grouped by domain (`users`, `organizations`, `purchases`).
- The app imports these helpers from `@repo/database` instead of issuing raw Prisma calls everywhere.
- Billing/auth helpers rely heavily on organization and purchase query helpers.

---

**Related references:**
- `references/database/schema-overview.md` — Database package structure
- `references/payments/customer-ids.md` — Query helpers used to persist customer IDs
- `references/auth/server-session-helpers.md` — Server auth helpers that read organization and invitation state
