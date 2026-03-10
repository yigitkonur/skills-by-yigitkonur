# AGENTS.md Templates

Pick the template that matches the detected project type. All templates follow the AGENTS.md format: plain markdown, no frontmatter, no special syntax.

Every template includes a **Boundaries** section using the Always/Ask/Never pattern.

---

## 1. Minimal

For small projects, scripts, or when starting fresh.

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

---

## 2. Node.js / TypeScript

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
- `public/` — Static assets (if applicable)

## Conventions
- Strict TypeScript: no `any`, no `as` casts unless justified in comment
- Named exports only, no default exports
- Imports: use path aliases (`@/` → `src/`)
- Error handling: use typed errors, never catch-and-ignore

## Dependencies
- Use `pnpm`, not npm or yarn
- Check existing deps before adding new ones
- Peer dependency issues: use `pnpm --shamefully-hoist` only as last resort

## Boundaries
- Always: Run `pnpm typecheck && pnpm test` before committing
- Always: Update types when changing interfaces
- Ask: Before adding new production dependencies
- Ask: Before changing tsconfig compiler options
- Never: Use `any` type without explicit justification comment
- Never: Disable ESLint rules inline without justification
```

---

## 3. Python

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

---

## 4. Go

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

---

## 5. Rust

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

---

## 6. React / Next.js

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

---

## 7. Monorepo

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

---

## 8. Django / Full-Stack Python

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

---

## Customization Notes

- **Strip sections** you do not need. Shorter is better.
- **Merge sections** if the project is simple enough.
- **Add sections** for project-specific concerns (e.g., "Database", "Deployment", "API Design").
- **Boundaries** should reflect real project risks, not hypothetical ones.
- **Commands** must be verified against actual project config before committing.
