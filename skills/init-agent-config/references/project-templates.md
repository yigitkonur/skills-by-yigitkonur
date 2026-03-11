# Project Templates

Copy-paste templates for AGENTS.md and CLAUDE.md organized by project type. Each template includes AGENTS.md, CLAUDE.md thin wrapper, and CLAUDE.md standalone variants.

Every AGENTS.md template includes a **Boundaries** section. Every template assumes commands are verified against actual project config before committing. **Strip sections you don't need — shorter is better.**

---

## 1. Minimal (Any Project)

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
- Node.js 20+ with TypeScript 5.x
- [Framework: Express/Fastify/Hono]
- [Database: Prisma/Drizzle + Postgres/SQLite]
- [Package manager: pnpm/npm/bun]

## Commands
- Dev: `pnpm dev`
- Test: `pnpm test`
- Build: `pnpm build`
- Types: `pnpm typecheck`

## Conventions
- Strict TypeScript (no `any`)
- Named exports, no default exports
- Errors via Result types, not exceptions

## Git
- Branch: `feat/description` or `fix/description`
- Conventional Commits
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

### CLAUDE.md (Standalone)

```markdown
# Project Name

One-line description.

## Stack
- Go 1.22+
- [Framework: stdlib/chi/gin/echo]
- [Database: pgx/sqlc/ent]

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

## Conventions
- App Router only, NOT Pages Router
- Server Components by default; add `'use client'` only when needed
- Component files: PascalCase (`UserProfile.tsx`)
- Use `next/image` for images, `next/link` for navigation

## Boundaries
- Always: Run `pnpm build` before opening a PR (catches SSR errors)
- Always: Use Server Components unless client interactivity is needed
- Ask: Before adding client-side state management libraries
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

## Conventions
- Internal packages use workspace protocol: `"@repo/shared": "workspace:*"`
- Changes to shared packages require testing all dependents
- Each package has its own tsconfig extending root

## Boundaries
- Always: Run affected tests when changing shared packages
- Always: Use workspace protocol for internal dependencies
- Ask: Before creating a new package
- Ask: Before adding cross-package dependencies
- Never: Import from another package's `src/` directly (use package exports)
- Never: Hoist dependencies that should be package-local

## Per-Package Instructions

Each package may have its own AGENTS.md:
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
| Area | File | Load When |
|------|------|-----------|
| Building | `agent_docs/building.md` | Build/deploy tasks |
| Testing | `agent_docs/testing.md` | Test runner, coverage |
| Architecture | `agent_docs/service-architecture.md` | Cross-service changes |
```

---

## 8. Django

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
- `config/` — Settings and root URL config
- `templates/` — HTML templates
- `static/` — Static assets

## Conventions
- Fat models, thin views
- Class-based views for CRUD, function views for custom logic
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

---

## Monorepo with Path-Scoped Rules (Claude Code)

For monorepos using Claude Code's `.claude/rules/` for per-package instructions:

```
project/
├── AGENTS.md                    # Universal instructions (all agents)
├── CLAUDE.md                    # @AGENTS.md + Claude-specific
├── .claude/
│   └── rules/
│       ├── shared.md            # No paths → universal (always loads)
│       ├── api.md               # paths: ["apps/api/**"]
│       ├── web.md               # paths: ["apps/web/**"]
│       └── database.md          # paths: ["packages/db/**"]
├── apps/
│   ├── api/
│   │   └── AGENTS.md            # API-specific (Codex, Cursor, VS Code)
│   └── web/
│       └── AGENTS.md            # Web-specific
└── packages/
    └── db/
        └── AGENTS.md
```

**How this works:**
- All agents read root `AGENTS.md` (universal)
- Codex, Cursor, VS Code also read nested `AGENTS.md` files
- Claude Code additionally loads path-scoped `.claude/rules/` files
- Root CLAUDE.md stays under 60 lines — detail lives in rules and nested files

---

## 9. Library / OSS Package

Use this for published libraries, SDKs, or open-source packages. Language-agnostic -- replace `[placeholders]` with your actual values.

### AGENTS.md

```markdown
# [Package Name]

[One-line description of what this package does.]

## Commands
- Install: `[install command]`
- Test: `[test command]`
- Lint: `[lint command]`
- Build: `[build command]`
- Publish: `[publish command]` (maintainers only)

## Architecture
- Source: `[src/lib directory]`
- Tests: `[test directory]`
- Public API surface: `[entry point file]`

## Conventions
- [Key convention 1 -- e.g., "All exports must be named, no default exports"]
- [Key convention 2 -- e.g., "Every public function needs a JSDoc/docstring"]
- [Key convention 3 -- e.g., "Semver strictly -- breaking changes require major bump"]

## Boundaries
- Always: Run full test suite before opening a PR
- Always: Update CHANGELOG for user-facing changes
- Never: Add runtime dependencies without maintainer approval
- Never: Change public API signatures without a deprecation path
- Ask: Before adding a new dependency
```

### CLAUDE.md (Thin Wrapper)

```markdown
@AGENTS.md

## Claude-Specific
<!-- Only add the next line if .claude/rules/ exists or you are creating rule files -->
- See `.claude/rules/` for path-scoped rules
```

### CLAUDE.md (Standalone)

```markdown
# [Package Name]

[One-line description.]

## Stack
- Language: [language and version]
- Build: [build tool]
- Test: [test framework]
- Package manager: [manager]

## Commands
- Test: `[test command]`
- Build: `[build command]`
- Lint: `[lint command]`

## Conventions
- [Convention 1]
- [Convention 2]

## Boundaries
- Always: Run tests before committing
- Never: Publish without CI green
```

---

## 10. CLI Tool

Use this for command-line applications, developer tools, or scripts.

### AGENTS.md

```markdown
# [CLI Name]

[One-line description -- what the CLI does and who uses it.]

## Commands
- Dev: `[run command]`
- Test: `[test command]`
- Build: `[build command]`
- Install locally: `[local install command]`

## Architecture
- Entry point: `[main file or bin/]`
- Commands: `[commands directory]`
- Config parsing: `[config module]`
- Output formatting: `[output module]`

## Conventions
- [Key convention 1 -- e.g., "All CLI output goes through the formatter module"]
- [Key convention 2 -- e.g., "Exit codes: 0=success, 1=user error, 2=internal error"]
- [Key convention 3 -- e.g., "Flags use --kebab-case, env vars use UPPER_SNAKE"]

## Boundaries
- Always: Test with --help and common subcommands before committing
- Always: Handle stdin/stdout/stderr correctly -- never mix output and errors
- Never: Add interactive prompts without a --yes/--no-input flag
- Ask: Before adding a new subcommand
```

### CLAUDE.md (Thin Wrapper)

```markdown
@AGENTS.md

## Claude-Specific
- When testing CLI changes, run the binary directly, not through a test harness
```

---

## Go Thin Wrapper Example

For Go projects using the dual-file pattern:

```markdown
@AGENTS.md

## Claude-Specific
- Run `go vet ./...` before committing
- Use `go test -race ./...` for concurrency tests
```

## Rust Thin Wrapper Example

For Rust projects using the dual-file pattern:

```markdown
@AGENTS.md

## Claude-Specific
- Run `cargo clippy -- -D warnings` before committing
- Use `cargo test` for all tests, `cargo test --doc` for doc tests
```

---

## Customization Notes

- **Strip sections** you don't need -- shorter is better
- **Merge sections** if the project is simple enough
- **Add sections** for project-specific concerns (Database, Deployment, API Design)
- **Boundaries** should reflect real project risks, not hypothetical ones
- **Commands** must be verified against actual project config
- **Thin wrappers** are preferred when the team uses multiple agents
- **Canonical thin wrapper:** Step 3 of SKILL.md is the authoritative thin wrapper template. The thin wrappers in this file are project-type customizations -- adapt them, but defer to SKILL.md Step 3 for the base pattern
- **Language-agnostic templates** (like Library/OSS) use `[placeholders]` -- replace every `[placeholder]` with actual project values
