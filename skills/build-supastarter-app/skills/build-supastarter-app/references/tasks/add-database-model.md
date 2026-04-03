# Task: Add a Database Model

> Checklist for extending the Prisma schema and query layer. Consult this when you need a new persisted entity.

## Standard path

> ⚠️ **Steering:** Step 2 (`pnpm generate && pnpm db:push`) is mandatory after any `schema.prisma` change. Without it, the Prisma client won't know about new models and TypeScript will show type errors in all downstream code (API procedures, query helpers, pages). Run it immediately after editing the schema, before writing any code that imports the new model.

1. Add the model and relations in `packages/database/prisma/schema.prisma`
2. **Run `pnpm generate && pnpm db:push`** to regenerate the Prisma client and sync the database
3. Add focused query helpers under `packages/database/prisma/queries/<model>.ts`
4. Re-export new helpers through `packages/database/prisma/queries/index.ts`
5. Create API procedures that use those queries
6. Build the page that calls the API

## New model example

```prisma
model Project {
  id             String       @id @default(cuid())
  name           String
  description    String?
  organizationId String
  organization   Organization @relation(fields: [organizationId], references: [id])
  createdAt      DateTime     @default(now())
  updatedAt      DateTime     @updatedAt

  @@index([organizationId])
}
```

Don't forget to add the reverse relation on the parent model:

```prisma
model Organization {
  // ... existing fields
  projects Project[]
}
```

## New query helper file template

> ⚠️ **Steering:** New query files MUST import `db` from the client. Missing this import is a common error that prevents compilation.

```ts
// packages/database/prisma/queries/projects.ts
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

export async function createProject(data: { name: string; organizationId: string; description?: string }) {
  return await db.project.create({ data });
}

export async function deleteProject(id: string) {
  return await db.project.delete({ where: { id } });
}
```

Then export from the barrel:

```ts
// packages/database/prisma/queries/index.ts
export * from "./projects"; // add this line
```

## Existing examples

The current schema already models users, organizations, memberships, invitations, purchases, sessions, passkeys, and two-factor records. Query helpers exist in:

- `queries/users.ts`
- `queries/organizations.ts`
- `queries/purchases.ts`

## Decision: query helpers vs direct `db` calls

| Use query helpers when | Use direct `db` calls when |
|---|---|
| The query is reused across 2+ call sites | One-off query in a single procedure |
| The query encapsulates business logic | Simple find/create with no special logic |
| Other packages need to import it | Used only within the same file |

When in doubt, start with a query helper — it is easier to inline later than to extract later.

## Practical rule

Application code should import `@repo/database` rather than instantiating its own Prisma client.

---

**Related references:**
- `references/database/schema-overview.md` — Existing models and relations
- `references/database/query-patterns.md` — Query helper conventions
- `references/database/generation-exports.md` — Generate/export workflow
- `references/database/prisma-client.md` — Singleton client setup
- `references/cheatsheets/commands.md` — `pnpm generate` and `pnpm db:push` commands
