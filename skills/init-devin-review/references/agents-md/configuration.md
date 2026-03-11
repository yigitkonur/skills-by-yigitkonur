# AGENTS.md Configuration for Devin

Complete reference for writing `AGENTS.md` files that guide Devin's behavior during task execution and code review.

---

## AGENTS.md vs REVIEW.md

| Aspect | REVIEW.md | AGENTS.md |
|--------|-----------|-----------|
| **Primary purpose** | Review criteria — what to check in diffs | Agent behavior — how Devin should work |
| **Read by** | Bug Catcher during PR analysis | Devin during task execution and reviews |
| **Scope** | Any directory (`**/REVIEW.md`) | Root only |
| **Content focus** | Rules, patterns, ignore lists | Architecture, coding standards, workflows |
| **Output** | Bugs and Flags on PR diffs | Code changes, suggestions, explanations |

**When to use which:**

- User asks to set up PR review → generate `REVIEW.md` only
- User asks to configure Devin for coding tasks → generate `AGENTS.md` only
- User asks for both review and task execution → generate both, without duplicating content

---

## File Basics

- **Format**: Markdown (H2/H3 headers, bullet lists, code blocks)
- **Location**: Repository root only (not directory-scoped like REVIEW.md)
- **Encoding**: UTF-8
- **Recommended length**: 100–300 lines

---

## Recommended Structure

```markdown
# Agent Guidelines

## Architecture
- [High-level architecture decisions and patterns]

## Coding Standards
- [Language-specific coding conventions]

## Workflow
- [Steps Devin should follow when working on tasks]

## Dependencies
- [Preferred libraries and tools]

## File Organization
- [Where different types of code should live]

## Testing
- [How and when to run tests]

## Communication
- [How Devin should communicate about changes]
```

---

## Section Reference

### Architecture

High-level architecture decisions that Devin should understand and follow.

```markdown
## Architecture
- Use the repository/service/controller pattern for all API code.
- Business logic belongs in `src/services/`, not in route handlers or controllers.
- Data access goes through repository classes in `src/repositories/`.
- Controllers in `src/controllers/` handle HTTP request/response only.
- Shared types and interfaces live in `src/types/`.
- Use dependency injection — services receive dependencies via constructor, not direct imports.
```

### Coding Standards

Language-specific conventions for Devin to follow when writing or modifying code.

```markdown
## Coding Standards
- Use TypeScript strict mode. No `any` types without explicit justification.
- Prefer composition over inheritance.
- All async functions must use try-catch with structured error logging.
- Use `const` by default. Only use `let` when reassignment is necessary.
- Name boolean variables with `is`, `has`, `should` prefixes.
- Maximum function length: 50 lines. Extract helper functions for complex logic.
- Use early returns to reduce nesting depth.
```

### Workflow

Steps Devin should follow when executing tasks. These are instructions for task execution, not review criteria.

```markdown
## Workflow
- Run `pnpm test` before committing any changes.
- Run `pnpm lint` and fix all errors before creating a PR.
- New API endpoints require both unit tests and integration tests.
- Database schema changes must include a migration file generated with `pnpm prisma migrate dev`.
- Always create a feature branch — never commit directly to `main`.
- Write descriptive commit messages: `<type>(<scope>): <description>` format.
- If changing a public API, update the OpenAPI spec in `docs/openapi.yaml`.
```

### Dependencies

Preferred libraries and tools to prevent Devin from introducing unwanted dependencies.

```markdown
## Dependencies
- Use `date-fns` for date manipulation, not `moment` or `dayjs`.
- Use `zod` for runtime validation, not `joi` or `yup`.
- Use `pino` for logging, not `winston` or `console.log`.
- Import shared utilities from `@acme/shared` — don't reimplement common functions.
- New dependencies require justification. Prefer stdlib or existing dependencies first.
- Pin exact versions in `package.json` (no `^` or `~` prefixes).
```

### File Organization

Where different types of code should live. Helps Devin place new files correctly.

```markdown
## File Organization
- API route handlers: `src/routes/<resource>.ts`
- Service classes: `src/services/<resource>.service.ts`
- Repository classes: `src/repositories/<resource>.repository.ts`
- Type definitions: `src/types/<resource>.types.ts`
- Validation schemas: `src/schemas/<resource>.schema.ts`
- Test files: co-located as `<filename>.test.ts` next to the source file
- Database migrations: auto-generated in `prisma/migrations/`
```

### Testing

How and when Devin should run tests, and what testing patterns to follow.

```markdown
## Testing
- Run `pnpm test` before every commit.
- Unit tests mock external dependencies (database, HTTP clients, file system).
- Integration tests use a test database seeded with `prisma/seed.ts`.
- Test naming: `describe('<FunctionName>', () => { it('should <behavior>', ...) })`.
- Minimum coverage: 80% line coverage for new code.
- Never use `test.skip` or `describe.skip` without a tracking issue number.
```

### Communication

How Devin should communicate about changes in PR descriptions and comments.

```markdown
## Communication
- PR descriptions must include: what changed, why, and how to test.
- If a change affects the API contract, call it out explicitly in the PR description.
- Link relevant issues using `Closes #123` or `Fixes #456` syntax.
- If uncertain about an approach, leave a comment explaining the tradeoff and asking for input.
```

---

## AGENTS.md for Review Context

Even though `AGENTS.md` is primarily for task execution, Devin also reads it during PR reviews. This means:

- **Architecture** rules help the Bug Catcher flag violations (e.g., business logic in controllers)
- **Coding Standards** give the Bug Catcher additional patterns to check
- **Dependencies** rules help flag unwanted dependency introductions

However, review-specific rules (severity, ignore patterns, what to flag vs skip) belong in `REVIEW.md`, not `AGENTS.md`.

---

## Complete Example: TypeScript Backend

```markdown
# Agent Guidelines

## Architecture
- Use the repository/service/controller pattern for all API code.
- Business logic belongs in `src/services/`, not in route handlers.
- Data access uses Prisma client in `src/repositories/`.
- Shared types live in `src/types/`. Do not define types inline in route handlers.

## Coding Standards
- TypeScript strict mode. No `any` types.
- All async functions must use try-catch with structured error logging via `src/utils/logger`.
- Use `const` by default. Only `let` when reassignment is necessary.
- Prefer early returns to reduce nesting.
- Maximum function length: 50 lines.

## Workflow
- Run `pnpm test && pnpm lint` before committing.
- New API endpoints require integration tests in `tests/integration/`.
- Database changes require: schema update → `pnpm prisma migrate dev` → test migration.
- Create feature branches from `main`. Never commit directly.

## Dependencies
- Use `date-fns` for dates, `zod` for validation, `pino` for logging.
- Import shared utilities from `@acme/shared`.
- New deps require justification in the PR description.

## File Organization
- Routes: `src/routes/<resource>.ts`
- Services: `src/services/<resource>.service.ts`
- Types: `src/types/<resource>.types.ts`
- Tests: co-located as `<filename>.test.ts`
```

---

## Complete Example: Python Django API

```markdown
# Agent Guidelines

## Architecture
- Follow Django's MVT pattern. Business logic goes in `services.py`, not views or serializers.
- Use Django REST Framework for all API endpoints.
- Celery tasks for async work. Tasks must be idempotent.
- Database access through Django ORM only — no raw SQL without explicit justification.

## Coding Standards
- Follow PEP 8. Use `black` for formatting, `isort` for imports.
- Type hints required on all function signatures (Python 3.10+ style).
- Use `logging` module with structured formatters. No `print()` in production.
- QuerySets must use `select_related()` / `prefetch_related()` to prevent N+1.

## Workflow
- Run `pytest` and `ruff check .` before committing.
- Model changes require `python manage.py makemigrations` → review migration → commit.
- New API views require tests covering: success, 400, 401, 403, 404 cases.

## Dependencies
- Use `httpx` for HTTP clients, not `requests`.
- Use `pydantic` for data validation in services.
- Pin versions in `requirements.txt`. Use `pip-compile` for lock files.

## File Organization
- Views: `<app>/views.py` or `<app>/viewsets.py`
- Services: `<app>/services.py`
- Serializers: `<app>/serializers.py`
- Tests: `<app>/tests/test_<module>.py`
```

---

## Complete Example: Next.js Full-Stack

```markdown
# Agent Guidelines

## Architecture
- App Router only. No Pages Router patterns.
- Server Components by default. Only add `'use client'` when using hooks or browser APIs.
- Data fetching in Server Components. Client Components handle interactive state only.
- Server Actions for mutations. No client-side fetch to API routes for form submissions.

## Coding Standards
- TypeScript strict mode. No `any`.
- Use `next/image` for all images. Never raw `<img>`.
- Never reference `process.env` in client components unless `NEXT_PUBLIC_` prefixed.
- Multiple independent data fetches must use `Promise.all()` or separate Suspense boundaries.

## Workflow
- Run `pnpm build` (not just `dev`) to catch SSR errors before committing.
- New pages must export `generateMetadata()` or a `metadata` object.
- Test with `pnpm test` and verify no TypeScript errors with `pnpm tsc --noEmit`.

## Dependencies
- Use `@tanstack/react-query` for client-side data, `server-only` for server utilities.
- Use `next-safe-action` for type-safe Server Actions.

## File Organization
- Pages: `app/<route>/page.tsx`
- Layouts: `app/<route>/layout.tsx`
- Server Actions: `app/<route>/actions.ts`
- Components: `components/<ComponentName>.tsx`
- Utilities: `lib/<utility>.ts`
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Duplicating REVIEW.md rules | Devin reads both — doubles noise | Keep review criteria in `REVIEW.md`, behavior in `AGENTS.md` |
| Overly prescriptive workflow | "Do X, then Y, then Z in this order" — too rigid | Give goals and constraints, not step-by-step scripts |
| Missing context | "Use the service pattern" — which service pattern? | Reference actual paths and examples from your codebase |
| Too long (300+ lines) | Dilutes important instructions | Focus on decisions that affect code quality, not obvious conventions |
| Generic advice | "Write clean code" | Specific: "Maximum function length: 50 lines. Extract helpers for complex logic" |
