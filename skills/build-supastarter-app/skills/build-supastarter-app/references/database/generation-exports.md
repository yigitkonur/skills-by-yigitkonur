# Generation and Exports

> Covers the generated artifacts produced from the Prisma schema and how they are surfaced to the rest of the monorepo. Consult this when schema changes require regeneration or when you need typed Zod schemas.

## Generated outputs

```prisma
generator client {
  provider = "prisma-client"
  output   = "./generated"
}

generator zod {
  provider = "prisma-zod-generator"
  output   = "./zod"
}
```

## Export surface

```ts
// packages/database/prisma/index.ts
export * from "./client";
export * from "./queries";
export * from "./zod";

// packages/database/index.ts
export * from "./prisma";
```

## Workflow reminder

After editing `packages/database/prisma/schema.prisma`, regenerate before relying on new fields or types:

```bash
pnpm generate
pnpm db:push
```

This keeps:

- the generated Prisma client up to date
- the generated Zod schemas aligned with the schema
- package-level exports valid for downstream imports

---

**Related references:**
- `references/database/schema-overview.md` — The source schema itself
- `references/cheatsheets/commands.md` — Generate and database commands
- `references/setup/monorepo-structure.md` — Where generated outputs live
