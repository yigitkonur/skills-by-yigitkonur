# Task: Add a Database Model

> Checklist for extending the Prisma schema and query layer. Consult this when you need a new persisted entity.

## Standard path

1. Add the model and relations in `packages/database/prisma/schema.prisma`
2. Regenerate the Prisma client and Zod schemas with `pnpm generate`
3. Add focused query helpers under `packages/database/prisma/queries/`
4. Re-export new helpers through the Prisma/database barrels

## Existing examples

The current schema already models users, organizations, memberships, invitations, purchases, sessions, passkeys, and two-factor records. Query helpers exist in:

- `queries/users.ts`
- `queries/organizations.ts`
- `queries/purchases.ts`

## Practical rule

Application code should import `@repo/database` rather than instantiating its own Prisma client.

---

**Related references:**
- `references/database/schema-overview.md` — Existing models and relations
- `references/database/query-patterns.md` — Query helper conventions
- `references/database/generation-exports.md` — Generate/export workflow
