# Agent Configuration Templates

For each project type: an AGENTS.md template, a CLAUDE.md thin wrapper, and a CLAUDE.md standalone. Copy, adapt, trim.

Every AGENTS.md template includes a **Boundaries** section (Always/Ask/Never pattern). Every template assumes commands are verified against actual project config before committing.

---

## 1. Minimal

### AGENTS.md

```markdown
# Project Name

Brief project description.

## Commands
- Dev: `command`
- Test: `command`
- Build: `command`

## Conventions
- Key convention 1
- Key convention 2

## Boundaries
- Always: Run tests before committing
- Never: Commit directly to main
```

### CLAUDE.md (Thin Wrapper)

```markdown
@AGENTS.md
```

### CLAUDE.md (Standalone)

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

---

## 2. Node.js / TypeScript

### AGENTS.md

```markdown
# Project Name

TypeScript application using [framework].

## Commands
- Dev: `pnpm dev`
- Test: `pnpm test`
- Test single: `pnpm test -- path/to/file.test.ts`
- Build: `pnpm build`
- Lint: `pnpm lint`
- Type check: `pnpm typecheck`

## Structure
- `src/` — Application source
- `src/lib/` — Shared utilities
- `tests/` — Test suites

## Conventions
- Strict TypeScript: no `any`, no `as` casts unless justified in comment
- Named exports only, no default exports
- Imports: use path aliases (`@/` → `src/`)
- Error handling: use typed errors, never catch-and-ignore

## Dependencies
- Use `pnpm`, not npm or yarn
- Check existing deps before adding new ones

## Boundaries
- Always: Run `pnpm typecheck && pnpm test` before committing
- Always: Update types when changing interfaces
- Ask: Before adding new production dependencies
- Ask: Before changing tsconfig compiler options
- Never: Use `any` type without explicit justification comment
- Never: Disable ESLint rules inline without justification
```

### CLAUDE.md (Thin Wrapper)

```markdown
@AGENTS.md

## Claude-Specific
- Path-scoped rules in `.claude/rules/` for API vs frontend conventions
- Use `/compact` when context grows large
```

### CLAUDE.md (Standalone)

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

---

## 3. Python

### AGENTS.md

```markdown
# Project Name

Python application using [framework].

## Commands
- Dev: `python -m [module]` or `uvicorn app:main --reload`
- Test: `pytest`
- Test single: `pytest path/to/test_file.py -v`
- Lint: `ruff check .`
- Format: `ruff format .`
- Type check: `mypy .`

## Structure
- `src/[package]/` — Application source
- `tests/` — Test suites
- `pyproject.toml` — Project config and dependencies

## Conventions
- Type hints on all public function signatures
- Docstrings on public modules, classes, and functions
- Use `pathlib.Path` not `os.path`
- Prefer dataclasses or Pydantic models over raw dicts

## Dependencies
- Use `uv` for dependency management (or `pip` if uv not available)
- Pin versions in `pyproject.toml`
- Virtual env: `.venv/` (do not use system Python)

## Boundaries
- Always: Run `pytest` before committing
- Always: Run `ruff check` before committing
- Ask: Before adding dependencies to pyproject.toml
- Ask: Before changing Python version requirement
- Never: Use `import *`
- Never: Catch bare `Exception` without re-raising or logging
```

### CLAUDE.md (Thin Wrapper)

```markdown
@AGENTS.md

## Claude-Specific
- Use `uv run` prefix for all Python commands in this environment
```

### CLAUDE.md (Standalone)

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

---

## 4. Go

### AGENTS.md

```markdown
# Project Name

Go service using [framework/stdlib].

## Commands
- Dev: `go run ./cmd/[service]`
- Test: `go test ./...`
- Test single: `go test ./path/to/package -run TestName -v`
- Build: `go build ./cmd/[service]`
- Lint: `golangci-lint run`

## Structure
- `cmd/` — Entry points
- `internal/` — Private packages
- `pkg/` — Public packages (if any)

## Conventions
- Return errors, do not panic
- Use `context.Context` as first parameter
- Table-driven tests
- `internal/` for all non-public packages

## Boundaries
- Always: Run `go test ./...` before committing
- Always: Run `go vet ./...` before committing
- Ask: Before adding external dependencies
- Never: Use `panic` for error handling in library code
- Never: Use global mutable state
```

### CLAUDE.md (Thin Wrapper)

```markdown
@AGENTS.md
```

### CLAUDE.md (Standalone)

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

---

## 5. Rust

### AGENTS.md

```markdown
# Project Name

Rust application using [framework].

## Commands
- Dev: `cargo run`
- Test: `cargo test`
- Test single: `cargo test test_name -- --nocapture`
- Build: `cargo build --release`
- Lint: `cargo clippy -- -D warnings`
- Format: `cargo fmt`

## Structure
- `src/` — Source code
- `src/main.rs` or `src/lib.rs` — Entry point
- `tests/` — Integration tests
- `benches/` — Benchmarks (if any)

## Conventions
- Use `Result<T, E>` for fallible operations
- Derive `Debug` on all public types
- Use `thiserror` for library errors, `anyhow` for application errors
- Prefer `&str` over `String` in function parameters

## Boundaries
- Always: Run `cargo test` and `cargo clippy` before committing
- Always: Run `cargo fmt` before committing
- Ask: Before adding new crate dependencies
- Ask: Before using `unsafe`
- Never: Use `.unwrap()` in library code without comment
- Never: Ignore compiler warnings
```

### CLAUDE.md (Thin Wrapper)

```markdown
@AGENTS.md
```

### CLAUDE.md (Standalone)

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

---

## 6. React / Next.js

### AGENTS.md

```markdown
# Project Name

Next.js application with App Router.

## Commands
- Dev: `pnpm dev`
- Test: `pnpm test`
- Build: `pnpm build`
- Lint: `pnpm lint`

## Structure
- `src/app/` — App Router pages and layouts
- `src/app/api/` — API routes
- `src/components/` — React components
- `src/lib/` — Shared utilities
- `public/` — Static assets

## Conventions
- App Router only, NOT Pages Router
- Server Components by default; add `'use client'` only when needed
- Component files: PascalCase (`UserProfile.tsx`)
- Use `next/image` for images, `next/link` for navigation
- CSS: [Tailwind / CSS Modules / styled-components]

## Boundaries
- Always: Run `pnpm build` before opening a PR (catches SSR errors)
- Always: Use Server Components unless client interactivity is needed
- Ask: Before adding client-side state management libraries
- Ask: Before creating new API routes
- Never: Use `useEffect` for data fetching (use Server Components or SWR)
- Never: Import server-only code in client components
```

### CLAUDE.md (Thin Wrapper)

```markdown
@AGENTS.md

## Claude-Specific
- Path rules: `.claude/rules/frontend.md` for component conventions
- No barrel exports (no `index.ts` re-exports)
- Data fetching in Server Components, not client-side
```

### CLAUDE.md (Standalone)

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

---

## 7. Monorepo

### AGENTS.md

```markdown
# Project Name

Monorepo managed with [pnpm workspaces / Turborepo / Nx].

## Commands
- Dev (all): `pnpm dev`
- Dev (specific): `pnpm --filter [package] dev`
- Test: `pnpm test`
- Test (specific): `pnpm --filter [package] test`
- Build: `pnpm build`
- Lint: `pnpm lint`

## Structure
- `packages/` — Shared libraries
- `apps/` or `services/` — Deployable applications
- `tooling/` — Build and dev tooling (if applicable)

## Conventions
- Internal packages use workspace protocol: `"@repo/shared": "workspace:*"`
- Changes to shared packages require testing all dependents
- Each package has its own tsconfig extending root
- Shared types live in `packages/types/`

## Boundaries
- Always: Run affected tests when changing shared packages
- Always: Use workspace protocol for internal dependencies
- Ask: Before creating a new package
- Ask: Before adding cross-package dependencies
- Never: Import from another package's `src/` directly (use package exports)
- Never: Hoist dependencies that should be package-local

## Per-Package Instructions

Each package may have its own AGENTS.md with specific conventions. See:
- `apps/web/AGENTS.md` — Web application specifics
- `apps/api/AGENTS.md` — API service specifics
- `packages/shared/AGENTS.md` — Shared library rules
```

### CLAUDE.md (Thin Wrapper)

```markdown
@AGENTS.md

## Claude-Specific
- Path-scoped rules in `.claude/rules/` for per-package conventions
- Use `claudeMdExcludes` in settings to skip irrelevant packages

## Supplemental Docs
- `agent_docs/building.md` — Per-app build instructions
- `agent_docs/testing.md` — Test runner and coverage
- `agent_docs/service-architecture.md` — Service boundaries and data flow
```

### CLAUDE.md (Standalone)

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

---

## 8. Django / Full-Stack Python

### AGENTS.md

```markdown
# Project Name

Django application with [DRF / HTMX / GraphQL].

## Commands
- Dev: `python manage.py runserver`
- Test: `python manage.py test`
- Test single: `python manage.py test app.tests.TestClass.test_method`
- Migrate: `python manage.py migrate`
- Make migrations: `python manage.py makemigrations`
- Shell: `python manage.py shell_plus`

## Structure
- `apps/` — Django applications
- `config/` or `project/` — Settings and root URL config
- `templates/` — HTML templates
- `static/` — Static assets
- `tests/` — Test suites (or per-app `tests/`)

## Conventions
- Fat models, thin views
- Use class-based views for CRUD, function views for custom logic
- Settings split: `base.py`, `local.py`, `production.py`
- Use `get_user_model()`, never import User directly

## Boundaries
- Always: Run `python manage.py test` before committing
- Always: Create migrations for model changes (`makemigrations`)
- Ask: Before changing existing migration files
- Ask: Before adding new Django apps
- Never: Modify existing migration files (create new ones)
- Never: Put secrets in settings files (use environment variables)
- Never: Use raw SQL when ORM queries suffice
```

### CLAUDE.md (Thin Wrapper)

```markdown
@AGENTS.md

## Claude-Specific
- Use `python manage.py shell_plus` for interactive exploration
- Path rules: `.claude/rules/models.md` for model conventions
```

### CLAUDE.md (Standalone)

```markdown
# Project Name

Django application with [DRF / HTMX / GraphQL].

## Stack
- Python 3.11+ with Django 5.x
- [API: DRF / Ninja / GraphQL]
- [Database: PostgreSQL]
- uv for dependency management

## Structure
- `apps/` — Django applications
- `config/` — Settings and root URL config
- `templates/` — HTML templates
- `static/` — Static assets

## Commands
- Dev: `python manage.py runserver`
- Test: `python manage.py test`
- Migrate: `python manage.py migrate`
- Make migrations: `python manage.py makemigrations`
- Shell: `python manage.py shell_plus`

## Conventions
- Fat models, thin views
- Class-based views for CRUD, function views for custom logic
- Settings: `base.py`, `local.py`, `production.py`
- `get_user_model()`, never import User directly

## Git
- Branch: `feature/description`
- Conventional Commits
```

---

## Bonus: Monorepo with Path-Scoped Rules

For monorepos using Claude Code's `.claude/rules/` for per-package instructions:

```
project/
├── AGENTS.md                    # Universal instructions (all agents)
├── CLAUDE.md                    # @AGENTS.md + Claude-specific
├── .claude/
│   └── rules/
│       ├── shared.md            # No paths → universal rules (always loads)
│       ├── api.md               # paths: ["apps/api/**"]
│       ├── web.md               # paths: ["apps/web/**"]
│       ├── ui-library.md        # paths: ["packages/ui/**"]
│       └── database.md          # paths: ["packages/db/**"]
├── apps/
│   ├── api/
│   │   └── AGENTS.md            # API-specific (Codex, Cursor, VS Code)
│   └── web/
│       └── AGENTS.md            # Web-specific
└── packages/
    ├── ui/
    │   └── AGENTS.md
    └── db/
        └── AGENTS.md
```

**How this works:**
- All agents read root `AGENTS.md` (universal)
- Codex, Cursor, VS Code also read nested `AGENTS.md` files
- Claude Code additionally loads path-scoped `.claude/rules/` files
- Root CLAUDE.md stays under 60 lines — all detail lives in rules and nested files

---

## Customization Notes

- **Strip sections** you do not need. Shorter is better.
- **Merge sections** if the project is simple enough.
- **Add sections** for project-specific concerns (e.g., "Database", "Deployment", "API Design").
- **Boundaries** should reflect real project risks, not hypothetical ones.
- **Commands** must be verified against actual project config before committing.
- **AGENTS.md Boundaries section** is the most impactful section — invest time here.
- **Thin wrappers** are preferred when the team uses multiple agents. Only use standalone CLAUDE.md for Claude-only teams.
