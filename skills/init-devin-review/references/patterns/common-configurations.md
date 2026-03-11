# Common Review Configurations

Reusable REVIEW.md patterns organized by concern. Adapt these to your repository — never copy verbatim. Reference actual paths, libraries, and conventions from the target codebase.

---

## Security Patterns

### Authentication and Authorization

```markdown
## Security — Authentication
- All API routes must verify authentication via middleware. Never assume a route is "internal only."
- Session tokens must be validated on every request. Expired or revoked tokens must return 401.
- Role-based access control must be enforced server-side. UI-only access control (hidden buttons) is not sufficient.
- JWT secrets must never be hardcoded. Use environment variables validated at startup.
- Password hashing must use bcrypt with a minimum cost factor of 12.
```

### Input Validation and Injection

```markdown
## Security — Input Validation
- Never interpolate user input into SQL queries. Use parameterized queries exclusively.
- All API endpoints must validate request bodies before processing. Raw body access is prohibited.
- Sanitize HTML output to prevent XSS. Use DOMPurify or equivalent for user-generated content.
- File uploads must be validated for type, size, and content. Never serve uploaded files from the same domain without sanitization.
- URL redirects must validate the target against an allow-list. Open redirects enable phishing attacks.
```

### Secrets and Data Protection

```markdown
## Security — Data Protection
- API keys, tokens, and secrets must never appear in source code. Use environment variables.
- Error responses must not leak stack traces, internal paths, or database schema details to clients.
- Sensitive user data (emails, phone numbers, addresses) must never be logged or included in error messages.
- Use HTTPS for all external API calls. Never downgrade to HTTP, even in development configurations.
- PII must be encrypted at rest. Database columns containing PII should use application-level encryption.
```

---

## Performance Patterns

### Database Performance

```markdown
## Performance — Database
- Flag any database queries inside loops — use batch operations (`findMany`, `bulk_create`) instead.
- Watch for N+1 query patterns: use `include`/`select` (Prisma), `select_related`/`prefetch_related` (Django), or `eager_load` (Rails).
- API responses returning lists must implement server-side pagination. Never return unbounded result sets.
- Large aggregations must be computed server-side (database GROUP BY), not client-side.
- Database indices should exist for columns used in WHERE clauses, JOIN conditions, and ORDER BY.
```

### Frontend Performance

```markdown
## Performance — Frontend
- Images above the fold must set `priority={true}` (Next.js) or `loading="eager"`. All other images should lazy-load.
- Components importing heavy libraries (charts, editors, maps) must use dynamic imports / code splitting.
- Server Components that fetch data should be wrapped in `<Suspense>` with meaningful fallback UI.
- Watch for large client-side JavaScript bundles. Components exceeding 50KB should be reviewed.
- CSS-in-JS must not generate styles at runtime in production. Use build-time extraction.
```

### API Performance

```markdown
## Performance — API
- Rate limiting middleware is required on all public-facing endpoints.
- Response payloads over 1MB should be paginated or streamed.
- Expensive computations must be offloaded to background jobs (queues, workers).
- Cache frequently accessed, rarely changing data (config, feature flags) with appropriate TTLs.
- Avoid synchronous file I/O in request handlers — use async alternatives.
```

---

## Framework-Specific Patterns

### Next.js (App Router)

```markdown
## Conventions — Next.js
- Never use raw `<img>` tags. Always use `next/image` with explicit width/height or fill mode.
- Do not add `'use client'` to components that only render content or fetch data. Only mark as client when using useState, useEffect, event handlers, or browser APIs.
- Never reference `process.env` in client components unless the variable is prefixed with `NEXT_PUBLIC_`.
- Multiple independent data fetches must use `Promise.all()` or separate Suspense boundaries — no sequential awaits that create waterfall fetches.
- Pages must export `generateMetadata()` or a `metadata` object for SEO.
- Server Actions must validate inputs with Zod before processing. Never trust client-submitted form data.
- Loading states must use `loading.tsx` route segments, not client-side spinners.
```

### React (General)

```markdown
## Conventions — React
- Components must be functional components with hooks. No class components.
- Custom hooks must start with `use` prefix and follow the Rules of Hooks.
- Avoid inline function definitions in JSX props — extract to `useCallback` or module-level functions.
- Component props must be typed with TypeScript interfaces, not `any`.
- Side effects belong in `useEffect` with proper dependency arrays. Missing deps cause stale closures.
- Memoization (`useMemo`, `useCallback`) should only be used when there's a measured performance benefit.
```

### Express / Fastify

```markdown
## Conventions — Express/Fastify
- Controllers handle HTTP request/response only. Business logic belongs in service layer.
- All routes must use error-handling middleware. Unhandled rejections crash the process.
- Request validation must happen before business logic — reject invalid requests early.
- Response shapes must be consistent. Use a standard envelope: `{ status, data, error, requestId }`.
- Never use `console.log`. Use the structured logger with request context.
```

### Django REST Framework

```markdown
## Conventions — Django
- All API views must declare `permission_classes` explicitly. Never rely on `DEFAULT_PERMISSION_CLASSES` alone.
- QuerySets in serializers or views must use `select_related()` or `prefetch_related()` to avoid N+1.
- All Django models must implement `__str__` returning a human-readable representation.
- Use `logging` module with structured formatters. No `print()` statements in production code.
- Serializers must validate all input fields. Never pass `validated_data` to model methods without checking required fields.
- New URL patterns must follow RESTful conventions: plural nouns, no verbs in paths.
```

### Go

```markdown
## Conventions — Go
- All errors must be handled explicitly. Never use `_` to discard errors.
- Use `context.Context` as the first parameter for functions that may block or need cancellation.
- Goroutines must have clear ownership and shutdown mechanisms. No fire-and-forget goroutines.
- Use `slog` for structured logging. No `fmt.Println` or `log.Println` in production.
- Prefer returning errors over panicking. Reserve `panic` for truly unrecoverable states.
- Interfaces should be defined by the consumer, not the implementor.
```

### Rust

```markdown
## Conventions — Rust
- Use `Result<T, E>` for fallible operations. Avoid `unwrap()` and `expect()` in library code.
- All public items must have doc comments (`///`).
- Use `clippy` lints as the baseline. Only suppress with explicit justification.
- Prefer `&str` over `String` for function parameters when ownership is not needed.
- Async functions must use `tokio` runtime. No mixing async runtimes.
```

---

## Monorepo Patterns

### Root REVIEW.md (Cross-Cutting)

```markdown
# Review Guidelines

## Security
- [Security rules that apply to ALL packages]

## Conventions
- All packages must use the shared ESLint config from `packages/eslint-config/`.
- Import from sibling packages using workspace aliases (`@acme/shared`), not relative paths.
- Each package must have its own `tsconfig.json` extending the root config.

## Ignore
- Lock files (pnpm-lock.yaml) can be skipped unless dependencies changed.
- Build output in `dist/`, `.next/`, `build/` should never be committed.
- Auto-generated types in `**/generated/` do not need review.
```

### Scoped REVIEW.md (Package-Specific)

```markdown
# packages/api/REVIEW.md

## Critical Areas
- All routes in `src/routes/` must use the auth middleware.
- Database migrations require backward compatibility review.

## Conventions
- [API-specific conventions not covered by root REVIEW.md]
```

---

## Ignore Patterns by Stack

### Node.js / TypeScript

```markdown
## Ignore
- `node_modules/` — dependencies (never committed)
- `dist/`, `build/`, `.next/` — build output
- `*.d.ts` — auto-generated TypeScript declarations
- `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock` — unless dependencies changed
- `__snapshots__/` — test snapshots
- `coverage/` — test coverage reports
- `.env.example` — template files (not actual secrets)
```

### Python

```markdown
## Ignore
- `__pycache__/`, `*.pyc` — bytecode
- `.venv/`, `venv/` — virtual environments
- `*.egg-info/` — build artifacts
- `migrations/` — auto-generated Django migrations (review schema changes only)
- `htmlcov/` — coverage reports
- `.mypy_cache/` — type checker cache
```

### Go

```markdown
## Ignore
- `vendor/` — vendored dependencies
- `*_test.go` — only if test changes are routine (usually should be reviewed)
- `go.sum` — unless dependencies changed
- `*.pb.go` — auto-generated protobuf files
```

---

## Combining REVIEW.md and AGENTS.md

When generating both files, follow this division:

| Concern | Goes in REVIEW.md | Goes in AGENTS.md |
|---------|-------------------|-------------------|
| "Flag SQL injection in diffs" | ✅ | ❌ |
| "Use Prisma for all DB access" | ❌ | ✅ |
| "Skip auto-generated files" | ✅ | ❌ |
| "Run tests before committing" | ❌ | ✅ |
| "Flag N+1 query patterns" | ✅ | ❌ |
| "Use repository/service/controller pattern" | ❌ | ✅ |
| "Error responses must not leak stack traces" | ✅ | ❌ |
| "Maximum function length: 50 lines" | ❌ | ✅ |

The rule of thumb: if it's about **what to catch in a code review**, put it in `REVIEW.md`. If it's about **how to write code**, put it in `AGENTS.md`.
