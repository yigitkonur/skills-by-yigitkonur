# Prisma Client

> Documents the singleton Prisma client used across the monorepo. Consult this when debugging connection issues, changing the database URL, or understanding why the client is cached on `globalThis` in development.

## Key files

- `packages/database/prisma/client.ts`

## Representative code

```ts
const prismaClientSingleton = () => {
  if (!process.env.DATABASE_URL) {
    throw new Error("DATABASE_URL is not set");
  }

  const adapter = new PrismaPg({
    connectionString: process.env.DATABASE_URL,
  });

  return new PrismaClient({ adapter });
};

const prisma = globalThis.prisma ?? prismaClientSingleton();
if (process.env.NODE_ENV !== "production") {
  globalThis.prisma = prisma;
}
export { prisma as db };
```

## Implementation notes

- The client uses `@prisma/adapter-pg` instead of the default Prisma driver.
- `DATABASE_URL` is validated eagerly so bad config fails fast.
- Development caches the client globally to avoid exhausting connections during hot reloads.

---

**Related references:**
- `references/database/schema-overview.md` — Package-level database structure
- `references/database/schema-overview.md` — Models queried through this client
- `references/setup/environment-setup.md` — Required database environment variables
