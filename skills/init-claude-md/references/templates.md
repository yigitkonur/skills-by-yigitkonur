# CLAUDE.md Templates by Project Type

Copy, adapt, and trim. Remove any section that does not apply.

## Minimal Template

For simple projects. Under 30 lines.

```markdown
# Project Name

Brief description.

## Stack
- Language/Framework
- Key dependencies

## Commands
- Dev: `command`
- Test: `command`
- Build: `command`

## Conventions
- Key convention 1
- Key convention 2
```

## Node.js / TypeScript

```markdown
# Project Name

One-line description.

## Stack
- Node.js 20 LTS with TypeScript 5.x
- [Framework: Express/Fastify/Hono]
- [Database: Prisma/Drizzle + Postgres/SQLite]
- [Package manager: pnpm/npm/bun]

## Structure
- `src/` — Application code
- `src/routes/` — API endpoints
- `src/services/` — Business logic
- `src/lib/` — Shared utilities
- `tests/` — Test suites

## Commands
- Dev: `pnpm dev`
- Test: `pnpm test`
- Build: `pnpm build`
- Types: `pnpm typecheck`

## Conventions
- Strict TypeScript (no `any`)
- Functional style, avoid classes
- Errors via Result types, not exceptions
- Tests required for new features

## Git
- Branch: `feat/description` or `fix/description`
- Commits: Conventional format
- Squash merge to main
```

## Python

```markdown
# Project Name

One-line description.

## Stack
- Python 3.11+
- [Framework: FastAPI/Django/Flask]
- [ORM: SQLAlchemy/Django ORM]
- uv for dependency management

## Structure
- `src/` — Application code
- `src/api/` — API endpoints
- `src/models/` — Data models
- `tests/` — Pytest suites

## Commands
- Dev: `uv run uvicorn src.main:app --reload`
- Test: `uv run pytest`
- Lint: `uv run ruff check .`
- Types: `uv run mypy src/`

## Conventions
- Type hints required (strict mypy)
- Pydantic for validation
- Async by default
- Docstrings for public APIs

## Git
- Branch: `feature/description`
- Conventional Commits
- Rebase before merge
```

## Go

```markdown
# Project Name

One-line description.

## Stack
- Go 1.22+
- [Framework: stdlib/chi/gin/echo]
- [Database: pgx/sqlc/ent]

## Structure
- `cmd/` — Entry points
- `internal/` — Private packages
- `pkg/` — Public packages
- `api/` — OpenAPI specs

## Commands
- Dev: `go run ./cmd/server`
- Test: `go test ./...`
- Lint: `golangci-lint run`
- Build: `go build -o bin/server ./cmd/server`

## Conventions
- Accept interfaces, return structs
- Errors are values — wrap with context
- Table-driven tests
- No global state

## Git
- Branch: `feat/description`
- Conventional Commits
```

## Rust

```markdown
# Project Name

One-line description.

## Stack
- Rust (stable channel)
- [Framework: Axum/Actix/Rocket]
- [Async: Tokio]

## Structure
- `src/` — Library and binary code
- `src/lib.rs` — Library root
- `src/main.rs` — Binary entry point
- `tests/` — Integration tests
- `benches/` — Benchmarks

## Commands
- Dev: `cargo run`
- Test: `cargo test`
- Lint: `cargo clippy -- -D warnings`
- Format: `cargo fmt`
- Build: `cargo build --release`

## Conventions
- No `unwrap()` in production code — use `?` or explicit error handling
- Derive Debug for all public types
- Document public items with `///`
- Prefer owned types in APIs over references when lifetime complexity grows

## Git
- Branch: `feat/description`
- Conventional Commits
```

## React / Next.js

```markdown
# Project Name

One-line description.

## Stack
- Next.js 14+ (App Router, NOT Pages)
- React 18+ with TypeScript
- [CSS: Tailwind/CSS Modules]
- [State: Zustand/React Query]

## Structure
- `app/` — App Router pages and layouts
- `components/` — Reusable UI components
- `lib/` — Utilities and helpers
- `hooks/` — Custom React hooks
- `types/` — TypeScript type definitions

## Commands
- Dev: `pnpm dev`
- Test: `pnpm test`
- Build: `pnpm build`
- Lint: `pnpm lint`

## Conventions
- Server Components by default, `'use client'` only when needed
- Colocate files: component + test + styles in same directory
- No barrel exports (no `index.ts` re-exports)
- Data fetching in Server Components, not client-side

## Git
- Branch: `feat/description`
- Conventional Commits
- Squash merge to main
```

## Monorepo

```markdown
# Project Name

One-line description.

## Stack
- [Monorepo tool: Turborepo/Nx/pnpm workspaces]
- [Primary language]
- [Key shared dependencies]

## Structure
- `apps/web/` — Web application
- `apps/api/` — API server
- `packages/shared/` — Shared utilities
- `packages/ui/` — Component library
- `packages/db/` — Database client

## Commands
- Dev (all): `pnpm dev`
- Dev (specific): `pnpm --filter @scope/web dev`
- Test: `pnpm test`
- Build: `pnpm build`
- Lint: `pnpm lint`

## Conventions
- Changes to `packages/` require running affected app tests
- Shared types live in `packages/shared/types`
- No cross-app imports — use packages

## Supplemental Docs
- `agent_docs/building.md` — Per-app build instructions
- `agent_docs/testing.md` — Test runner and coverage
- `agent_docs/service-architecture.md` — Service boundaries and data flow

## Git
- Branch: `feat/app-name/description`
- Conventional Commits with scope
```

## Monorepo with Path-Scoped Rules

For monorepos that benefit from `.claude/rules/`:

```
.claude/rules/
├── shared.md              # No paths → universal rules
├── api.md                 # paths: ["apps/api/**"]
├── web.md                 # paths: ["apps/web/**"]
├── ui-library.md          # paths: ["packages/ui/**"]
└── database.md            # paths: ["packages/db/**"]
```

This keeps the root `CLAUDE.md` under 60 lines while giving each package its own focused instruction set.
