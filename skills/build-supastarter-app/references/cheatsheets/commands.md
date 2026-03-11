# CLI Commands Cheatsheet

> All pnpm and Turbo commands for the Supastarter monorepo.

## Development

```bash
pnpm dev                    # Start all apps in dev mode (web + docs + mail-preview)
pnpm dev --filter=web       # Start only the web app
```

## Build

```bash
pnpm build                  # Build all packages and apps
pnpm build --filter=web     # Build only the web app
```

## Database

> ⚠️ **Steering:** After ANY `schema.prisma` change, you must run BOTH `pnpm generate` AND `pnpm db:push`. Running only one is not enough — `generate` updates the Prisma client and Zod schemas, while `db:push` syncs the actual database.

```bash
pnpm generate               # Generate Prisma client + Zod schemas
pnpm db:push                # Push schema changes to database (dev)
pnpm generate && pnpm db:push  # Common workflow: do both together
pnpm db:seed                # Seed database with initial data
pnpm db:migrate             # Run production migrations
pnpm db:studio              # Open Prisma Studio (database GUI)
```

## Code Quality

```bash
pnpm lint                   # Run Biome linter on all files
pnpm format                 # Run Biome formatter on all files
pnpm type-check             # TypeScript type checking across all packages
```

## Testing

```bash
pnpm test                   # Run Playwright E2E tests
pnpm e2e                    # Run Playwright with UI mode
```

## Infrastructure

```bash
docker compose up -d        # Start PostgreSQL + MinIO
docker compose down         # Stop services
docker compose down -v      # Stop and remove volumes (fresh DB)
```

## Common Workflows

```bash
# After adding a new Prisma model:
pnpm generate && pnpm db:push

# After pulling latest code:
pnpm install && pnpm generate

# Full clean rebuild:
pnpm clean && pnpm install && pnpm generate && pnpm build
```

## Turbo Filters

```bash
pnpm turbo <task> --filter=<package>     # Run task for specific package
pnpm turbo <task> --filter=web           # Filter to web app
pnpm turbo <task> --filter=@repo/auth    # Filter to auth package
pnpm turbo <task> --filter=./packages/*  # All packages
```

## Package Management

```bash
pnpm add <pkg> --filter=web              # Add dep to web app
pnpm add <pkg> --filter=@repo/api        # Add dep to API package
pnpm add -D <pkg> --filter=web           # Add dev dep
pnpm add <pkg> -w                        # Add to root workspace
```

## Clean

```bash
pnpm clean                  # Clean all build outputs (dist, .next, etc.)
```

---

**Related references:**
- `references/setup/monorepo-structure.md` — Package layout
- `references/setup/environment-setup.md` — Environment setup guide
- `references/database/generation-exports.md` — What `pnpm generate` produces
- `references/tasks/add-database-model.md` — Full database model workflow
