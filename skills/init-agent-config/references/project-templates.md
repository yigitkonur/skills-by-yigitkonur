# Project Templates

AGENTS-first starter templates for common repository shapes. Use these only after discovery. Every template assumes:

- root `AGENTS.md` is written first
- meaningful `src/*`, app, package, or service folders get local `AGENTS.md`
- each finalized `AGENTS.md` gets a sibling `CLAUDE.md -> AGENTS.md`
- if symlinks are impossible, use `@AGENTS.md` as the fallback wrapper

## Shared Folder Template

Use this for any local subtree after Wave 2 confirms it needs its own file.

```markdown
# <folder>

## Local Focus
- What this folder owns

## Local Commands
- Verified local command

## Local Conventions
- Folder-specific rule

## Local Boundaries
- Always: local invariant
- Never: local mistake to avoid
```

## 1. Minimal Project

### Root `AGENTS.md`

```markdown
# Project Name

## Commands
- Dev: `verified command`
- Test: `verified command`

## Architecture
- `src/` — core code

## Boundaries
- Always: run tests before committing
- Never: guess commands
```

### Companion files

```text
CLAUDE.md -> AGENTS.md
```

## 2. Node.js / TypeScript

### Root `AGENTS.md`

```markdown
# Project Name

## Commands
- Dev: `pnpm dev`
- Test: `pnpm test`
- Build: `pnpm build`
- Typecheck: `pnpm typecheck`

## Architecture
- `src/api/` — HTTP and contracts
- `src/web/` — UI
- `src/lib/` — shared runtime helpers

## Conventions
- Use `pnpm`, not npm
- Named exports only

## Boundaries
- Always: run `pnpm typecheck && pnpm test`
- Ask: before adding production dependencies
- Never: bypass shared validation utilities
```

### Local `src/api/AGENTS.md`

```markdown
# src/api

## Local Focus
- Request validation, response contracts, transport errors

## Local Commands
- API tests: `pnpm test -- src/api`

## Local Boundaries
- Always: update schemas and handlers together
- Never: return ad-hoc error shapes
```

### Local `src/web/AGENTS.md`

```markdown
# src/web

## Local Focus
- Pages, components, data loading boundaries

## Local Boundaries
- Always: preserve server/client boundaries
- Never: import server-only modules into client code
```

## 3. Python Service

### Root `AGENTS.md`

```markdown
# Project Name

## Commands
- Dev: `uv run uvicorn src.main:app --reload`
- Test: `uv run pytest`
- Lint: `uv run ruff check .`

## Architecture
- `src/app/` — request handling
- `src/domain/` — business rules
- `tests/` — automated checks

## Boundaries
- Always: run `uv run pytest`
- Ask: before changing Python version or dependency manager
- Never: use system Python for project tasks
```

### Local `src/domain/AGENTS.md`

```markdown
# src/domain

## Local Focus
- Domain entities, pure business rules, policy code

## Local Boundaries
- Always: keep framework concerns out of domain code
- Never: import web-layer modules here
```

## 4. React / Next.js

### Root `AGENTS.md`

```markdown
# Project Name

## Commands
- Dev: `pnpm dev`
- Test: `pnpm test`
- Build: `pnpm build`

## Architecture
- `src/app/` — routes and layouts
- `src/components/` — reusable UI
- `src/lib/` — shared helpers

## Conventions
- App Router only
- Server Components by default

## Boundaries
- Always: run `pnpm build` before shipping route changes
- Never: fetch primary data in `useEffect` when a server path exists
```

### Local `src/components/AGENTS.md`

```markdown
# src/components

## Local Focus
- Shared UI primitives and composed components

## Local Boundaries
- Always: keep component APIs stable and predictable
- Never: hide data fetching inside reusable presentational components
```

## 5. Monorepo

### Root `AGENTS.md`

```markdown
# Project Name

## Commands
- Dev: `pnpm dev`
- Test: `pnpm test`
- Build: `pnpm build`

## Architecture
- `apps/` — deployable applications
- `packages/` — shared libraries

## Boundaries
- Always: run affected tests when changing shared packages
- Ask: before creating new workspace packages
- Never: import from another package's private source path
```

### Local `apps/api/AGENTS.md`

```markdown
# apps/api

## Local Focus
- HTTP boundary, auth, persistence integration

## Local Commands
- API tests: `pnpm --filter api test`

## Local Boundaries
- Always: update contracts and handlers together
- Never: bypass shared auth middleware
```

### Local `packages/contracts/AGENTS.md`

```markdown
# packages/contracts

## Local Focus
- Shared schema and type contracts

## Local Boundaries
- Always: version contract changes deliberately
- Never: make breaking schema changes without updating dependents
```

## 6. Library / OSS Package

### Root `AGENTS.md`

```markdown
# Package Name

## Commands
- Test: `verified command`
- Build: `verified command`
- Lint: `verified command`

## Architecture
- `src/` — library implementation
- `tests/` — consumer-facing coverage

## Boundaries
- Always: run the full test suite before release work
- Ask: before adding runtime dependencies
- Never: break public API contracts silently
```

### Local `src/AGENTS.md`

```markdown
# src

## Local Focus
- Public API surface, implementation internals, error contracts

## Local Boundaries
- Always: preserve documented exports
- Never: change runtime behavior without updating tests and release notes
```

## 7. Docs / Skills / Standards Repository

### Root `AGENTS.md`

```markdown
# Repository Name

## Structure
- Canonical guidance lives in `skills/` or `docs/`
- Contributor rules live in `CONTRIBUTING.md`

## Commands
- Validation: `python3 scripts/validate-skills.py`

## Boundaries
- Always: ground edits in repo-local references
- Never: invent build or runtime workflows the repo does not expose
```

### Local `skills/<name>/AGENTS.md`

```markdown
# skills/<name>

## Local Focus
- Skill body, references, install docs for this one skill

## Local Boundaries
- Always: keep the skill's naming and reference routing consistent
- Never: leave unreferenced files in `references/`
```

## 8. CLI Tool

### Root `AGENTS.md`

```markdown
# CLI Name

## Commands
- Dev: `verified command`
- Test: `verified command`
- Build: `verified command`

## Architecture
- `cmd/` or `src/cli/` — entry points
- `src/core/` — business logic

## Boundaries
- Always: validate `--help` and common flows before shipping
- Never: introduce interactive prompts without non-interactive flags
```

### Local `src/cli/AGENTS.md`

```markdown
# src/cli

## Local Focus
- Argument parsing, output formatting, exit codes

## Local Boundaries
- Always: keep stdout and stderr responsibilities separate
- Never: print human text from core business logic modules
```

## Customization Rules

- strip sections you do not need
- add sections only when discovery found 3+ facts that justify them
- keep folder files smaller than the root file
- if a folder has only one important local rule, a 3-6 line file is fine
- create the companion `CLAUDE.md` after the AGENTS file is finalized, not before
