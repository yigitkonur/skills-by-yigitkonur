# Monorepo Structure

> Full directory tree, package roles, and Turborepo pipeline. Consult this when navigating the codebase, adding new packages, or understanding the build system.

## Directory Tree

```
/
├── apps/
│   ├── web/                        # Main Next.js application
│   │   ├── app/                    # App Router routes
│   │   │   ├── (marketing)/        # Public marketing pages (locale-based routing)
│   │   │   ├── (saas)/             # Protected SaaS application
│   │   │   │   ├── app/            # Dashboard routes (org-scoped)
│   │   │   │   └── auth/           # Authentication pages
│   │   │   └── api/                # API route handlers
│   │   │       ├── [[...rest]]/    # Catch-all oRPC/Hono handler
│   │   │       └── auth/[...all]/  # Better Auth handler
│   │   ├── modules/                # Feature modules
│   │   │   ├── marketing/          # Marketing page components
│   │   │   ├── saas/               # SaaS feature components
│   │   │   │   ├── admin/          # Admin panel
│   │   │   │   ├── auth/           # Auth forms, hooks, helpers
│   │   │   │   ├── organizations/  # Org management
│   │   │   │   ├── onboarding/     # Onboarding wizard
│   │   │   │   ├── settings/       # User & org settings
│   │   │   │   └── shared/         # SaaS-wide shared components
│   │   │   ├── shared/             # Cross-cutting components & utilities
│   │   │   │   ├── components/     # Document, ClientProviders, NavBar, etc.
│   │   │   │   └── lib/            # oRPC client, query utils
│   │   │   ├── analytics/          # Analytics integration
│   │   │   └── i18n/               # i18n utilities
│   │   ├── content/                # MDX content (blog, legal, docs)
│   │   ├── tests/                  # Playwright E2E tests
│   │   ├── config.ts               # Feature flags
│   │   ├── proxy.ts                # Middleware (auth, i18n, feature flags)
│   │   └── next.config.ts          # Next.js configuration
│   ├── docs/                       # Documentation app (optional)
│   └── mail-preview/               # Email template preview
├── packages/
│   ├── api/                        # oRPC procedures + Hono HTTP server
│   │   ├── index.ts                # Hono app with middleware chain
│   │   ├── orpc/                   # Procedure definitions, router, handlers
│   │   └── modules/                # Feature-scoped API modules
│   │       ├── admin/              # Admin procedures
│   │       ├── ai/                 # AI procedures
│   │       ├── contact/            # Contact form
│   │       ├── newsletter/         # Newsletter subscription
│   │       ├── organizations/      # Organization CRUD
│   │       ├── payments/           # Checkout, portal
│   │       └── users/              # User procedures
│   ├── auth/                       # Better Auth configuration
│   ├── database/                   # Prisma/Drizzle schema + queries
│   │   └── prisma/
│   │       ├── schema.prisma       # Database schema
│   │       ├── client.ts           # Singleton Prisma client
│   │       ├── queries/            # Reusable query functions
│   │       ├── generated/          # Generated Prisma client
│   │       └── zod/                # Generated Zod schemas
│   ├── ai/                         # AI SDK integration
│   ├── i18n/                       # Translations, locale config
│   ├── logs/                       # Consola logger
│   ├── mail/                       # Email providers + React Email templates
│   ├── payments/                   # Payment provider abstraction
│   ├── storage/                    # S3 file storage
│   ├── ui/                         # Shadcn UI components
│   └── utils/                      # Shared utilities (getBaseUrl, etc.)
├── tooling/
│   ├── tailwind/                   # Shared Tailwind config + theme.css
│   └── typescript/                 # Shared tsconfig bases
├── config/                         # App-level config
├── turbo.json                      # Turborepo pipeline
├── biome.json                      # Linting/formatting
├── docker-compose.yml              # PostgreSQL + MinIO
└── package.json                    # Root scripts, engine constraints
```

## Package Roles

| Package | Import As | Purpose |
|---------|-----------|---------|
| `@repo/api` | `@repo/api` | oRPC procedures, Hono HTTP server |
| `@repo/auth` | `@repo/auth` | Better Auth config, session types |
| `@repo/database` | `@repo/database` | Prisma client, queries, generated types |
| `@repo/ai` | `@repo/ai` | Vercel AI SDK models, prompts |
| `@repo/i18n` | `@repo/i18n` | Locale config, translations |
| `@repo/logs` | `@repo/logs` | Consola logger instance |
| `@repo/mail` | `@repo/mail` | Email templates, send function |
| `@repo/payments` | `@repo/payments` | Checkout, portal, webhooks |
| `@repo/storage` | `@repo/storage` | S3 presigned URLs |
| `@repo/ui` | `@repo/ui` or `@repo/ui/components/*` | Shadcn components, cn() |
| `@repo/utils` | `@repo/utils` | getBaseUrl, shared utilities |

## Turborepo Pipeline

From `turbo.json`:

```json
{
  "tasks": {
    "build": {
      "dependsOn": ["^generate", "^build"],
      "outputs": ["dist/**", ".next/**", "!.next/cache/**"]
    },
    "dev": {
      "cache": false,
      "dependsOn": ["^generate"],
      "persistent": true
    },
    "generate": {
      "cache": false
    },
    "type-check": {},
    "clean": {
      "cache": false
    },
    "start": {
      "cache": false,
      "dependsOn": ["^generate", "^build"],
      "persistent": true
    }
  }
}
```

**Key behaviors:**
- `^generate` runs first — generates Prisma client before builds/dev
- `build` caches `.next/**` and `dist/**` outputs
- `dev` is persistent (long-running) and never cached
- `globalDependencies: ["**/.env.*local"]` — env file changes invalidate all caches

## Root Scripts

```bash
pnpm dev          # Start all apps in dev mode
pnpm build        # Build all packages and apps
pnpm generate     # Generate Prisma client + Zod schemas
pnpm db:push      # Push Prisma schema to database
pnpm db:seed      # Seed database
pnpm lint         # Run Biome linter
pnpm format       # Run Biome formatter
pnpm type-check   # TypeScript type checking
pnpm clean        # Clean all build outputs
```

All scripts use `dotenv -c -- turbo <task>` to load `.env.local` before running.

---

**Related references:**
- `references/setup/import-conventions.md` — Path aliases and import patterns
- `references/cheatsheets/commands.md` — All CLI commands
- `references/cheatsheets/file-locations.md` — "Where do I put...?" guide
- `references/setup/tooling-biome.md` — Lint/format config
