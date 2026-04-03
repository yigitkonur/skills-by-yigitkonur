# Scenario Library

Complete example REVIEW.md files for common repository types. Use as inspiration, but adapt every rule to the actual repository context — never copy verbatim.

### Scenario Selection Guide

| Your stack | Start with scenario |
|---|---|
| TypeScript + Express/Fastify | A |
| Next.js (App Router) | B or C |
| Django + DRF | D |
| Django + GraphQL | I |
| Go + HTTP server | H |
| Tauri desktop | E |
| MCP server (TS) | F |
| Python mcp-use | G |
| Monorepo (any) | J — adapt with above |

---

If no scenario matches exactly, choose the nearest one by primary language/runtime and keep only the section order and severity style. Rewrite every rule from repo evidence and delete stack-specific guidance that does not belong.

---

## Scenario A: TypeScript Backend API (Express/Fastify + Prisma)

### `REVIEW.md`
```markdown
# Review Guidelines

## Critical Areas
- All changes to `src/auth/` must be reviewed for security implications — this handles JWT validation, session management, and RBAC.
- Database migration files in `prisma/migrations/` must be checked for backward compatibility and potential data loss.
- Payment processing in `src/billing/` requires extra scrutiny for PCI compliance — no PII in logs, idempotent mutations only.

## Security
- Never interpolate user input into SQL queries. Use Prisma's parameterized queries exclusively.
- API keys, tokens, and secrets must never appear in source code. Use environment variables validated at startup.
- All API routes must verify authentication via middleware. Never assume a route is "internal only."
- Error responses must not leak stack traces, internal paths, or database schema details to clients.
- Rate limiting middleware is required on all public-facing endpoints.

## Conventions
- API endpoints must validate request bodies using Zod schemas from `src/schemas/`. Raw `req.body` access is prohibited.
- All public functions require explicit TypeScript return types. Do not use `any` or `unknown` without justification.
- Use the structured logger (`src/utils/logger`). Never use `console.log`, `console.warn`, or `console.error`.
- Controllers handle HTTP request/response only. Business logic belongs in `src/services/`.
- Services receive dependencies via constructor injection. No direct imports of other service instances.

## Performance
- Flag any database queries inside loops — use `findMany` or batch operations.
- Watch for N+1 query patterns: use `include` or `select` in Prisma queries to eager-load relations.
- API responses returning lists must implement pagination. Never return unbounded result sets.

## Patterns

### Error Handling
**Good:**
\`\`\`typescript
async function getUser(id: string): Promise<User> {
  try {
    return await prisma.user.findUniqueOrThrow({ where: { id } });
  } catch (error) {
    logger.error('getUser failed', { id, error });
    throw new AppError('USER_NOT_FOUND', { cause: error });
  }
}
\`\`\`

**Bad:**
\`\`\`typescript
async function getUser(id: string) {
  return await prisma.user.findUnique({ where: { id } }); // no error handling, nullable return
}
\`\`\`

### API Response Shape
**Good:**
\`\`\`typescript
return res.status(404).json({
  status: 404,
  message: 'User not found',
  requestId: req.id,
  timestamp: new Date().toISOString(),
});
\`\`\`

**Bad:**
\`\`\`typescript
return res.status(404).send('not found'); // no structure, no request ID
\`\`\`

## Ignore
- Auto-generated Prisma client in `node_modules/.prisma/` does not need review.
- Lock files (package-lock.json, pnpm-lock.yaml) can be skipped unless dependencies changed.
- TypeScript declaration files (`*.d.ts`) are auto-generated.
- Test snapshots in `__snapshots__/` don't need review.

## Testing
- All new API endpoints must have integration tests covering success, validation error, auth error, and not-found cases.
- Service methods must have unit tests with mocked dependencies.
- Test files must be co-located: `user.service.test.ts` next to `user.service.ts`.
```

> 💡 Pairing with AGENTS.md? See `references/agents-md/configuration.md`

---

## Scenario B: Next.js Marketing Website (App Router + CMS)

### `REVIEW.md`
```markdown
# Review Guidelines

## Critical Areas
- All pages in `app/` must export `generateMetadata()` or a `metadata` object — missing metadata degrades SEO rankings.
- Changes to `middleware.ts` affect all routes. Review for performance impact and correct matcher patterns.
- Content fetching in `lib/` must use ISR with appropriate revalidation — stale content hurts user experience.

## Conventions
- Never use raw `<img>` tags. Always use `next/image` with explicit width/height or fill mode.
- Do not add `'use client'` to components that only render content or fetch data. Only mark as client when using useState, useEffect, event handlers, or browser APIs.
- Never reference `process.env` in client components unless the variable is prefixed with `NEXT_PUBLIC_`.
- Multiple independent data fetches must use `Promise.all()` or separate Suspense boundaries — no sequential awaits that create waterfall fetches.
- Content pages (blog, product, FAQ) must include JSON-LD structured data using appropriate schema.org types.

## Performance
- Server Components that fetch data should be wrapped in `<Suspense>` with meaningful fallback UI.
- Images above the fold must set `priority={true}`. All other images should lazy-load (default behavior).
- Pages with dynamic content must declare a revalidation strategy (`export const revalidate = N` or `revalidateTag`/`revalidatePath`).
- Watch for large client-side JavaScript bundles. Components that import heavy libraries should be dynamically imported.

## Security
- Form submissions must use Server Actions with Zod validation. Never trust client-submitted data.
- All external links must use `rel="noopener noreferrer"` to prevent tab-napping.

## Ignore
- Files in `public/` are static assets and don't need code review.
- Sanity schema files in `sanity/schemas/` are content definitions, not application code.
- Lock files (pnpm-lock.yaml) can be skipped unless dependencies changed.
- `.next/` build output should never be committed.

## Testing
- New pages must render without errors in both development and production builds.
- Metadata must be verified: title, description, and OpenGraph tags present.
```

---

## Scenario C: Next.js Dashboard / Admin Panel

### `REVIEW.md`
```markdown
# Review Guidelines

## Critical Areas
- All routes under `app/dashboard/` must be protected by authentication middleware in `middleware.ts`.
- Server Actions in `actions/` that perform mutations (create, update, delete) must verify the user's role before executing.
- Route Handlers in `app/api/` must independently verify authentication — never assume middleware protection carries over.

## Security
- All Server Actions must validate inputs using Zod before processing. Never trust client-submitted form data.
- Role-based access control must be enforced server-side. UI-only access control (hidden buttons) is not sufficient — direct API calls bypass it.
- Never reference `process.env` in client components unless prefixed with `NEXT_PUBLIC_`. Dashboard components often need API URLs — pass them from Server Components as props.
- Session tokens must be validated on every request. Expired or revoked tokens must return 401.
- Sensitive user data (emails, phone numbers, addresses) must never be logged or included in error messages.

## Conventions
- Data fetching (database queries, API calls, auth checks) must happen in Server Components. Client Components handle interactive state only.
- Data tables and list views must implement server-side pagination via URL search params. Never fetch all records client-side.
- Every major route segment under `/dashboard` must have an `error.tsx` boundary that catches rendering errors.
- Form state management must use `useActionState` (React 19) or `useFormState` for Server Actions — not manual fetch calls.
- Loading states must use `loading.tsx` route segments, not client-side spinners.

## Performance
- Database queries for table views must include pagination (LIMIT/OFFSET or cursor-based).
- Chart data must be aggregated server-side. Never send raw data points to the client for aggregation.
- Avoid importing large charting libraries in Server Components — use dynamic imports in Client Components.

## Ignore
- Lock files can be skipped unless dependencies changed.
- Generated TypeScript types from database schemas don't need review.
- Storybook files (`*.stories.tsx`) are for development only.

## Testing
- Auth middleware must be tested: unauthenticated → redirect to login, unauthorized → 403.
- Server Actions must be tested with invalid inputs to verify Zod validation catches them.
- RBAC must be tested: admin can mutate, viewer cannot.
```

---

## Scenario D: Python Django REST API

### `REVIEW.md`
```markdown
# Review Guidelines

## Critical Areas
- All changes to `views.py` and `viewsets.py` must be reviewed for authentication and permission handling.
- Model changes require checking migration files for backward compatibility and data integrity.
- Celery task definitions must be reviewed for idempotency and error handling.

## Security
- Never use string formatting for SQL queries. Use Django ORM or `RawSQL` with parameterized inputs.
- All API views must declare `permission_classes` explicitly. Never rely on `DEFAULT_PERMISSION_CLASSES` alone.
- User-uploaded files must be validated for type and size. Never serve uploaded files from the same domain without sanitization.
- Celery tasks that process user data must not log PII. Use structured logging with user IDs only.

## Conventions
- QuerySets used in serializers or views must use `select_related()` or `prefetch_related()` to avoid N+1 queries.
- All Django models must implement `__str__` returning a human-readable representation.
- Use the `logging` module with structured formatters. No `print()` statements in production code.
- Serializers must validate all input fields. Never pass `validated_data` to model methods without checking required fields.
- New URL patterns must follow RESTful conventions: plural nouns, no verbs in paths.

## Performance
- Flag any database queries inside loops — use `bulk_create`, `bulk_update`, or `Subquery`.
- QuerySets in templates must be evaluated once and cached. Avoid `.all()` in template loops.
- Large response payloads must use pagination (`PageNumberPagination` or `CursorPagination`).

## Patterns

### View Permission
**Good:**
\`\`\`python
class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    queryset = User.objects.select_related('profile').all()
\`\`\`

**Bad:**
\`\`\`python
class UserViewSet(viewsets.ModelViewSet):
    # Missing permission_classes — relies on global default
    queryset = User.objects.all()  # No select_related — N+1 on profile access
\`\`\`

## Ignore
- Migration files in `*/migrations/` are auto-generated — only review if schema changes are unexpected.
- Static files in `static/` and media files in `media/` don't need code review.
- `__pycache__/` directories should never be committed.

## Testing
- All new views must have tests covering: authenticated success, unauthenticated 401, unauthorized 403.
- Celery tasks must have tests that verify idempotency (running twice produces same result).
```

> 💡 Pairing with AGENTS.md? See `references/agents-md/configuration.md`

---

## Scenario E: Tauri Desktop App (Rust + TypeScript)

### `REVIEW.md`
```markdown
# Review Guidelines

## Critical Areas
- All `#[tauri::command]` handlers in `src-tauri/src/` are the security boundary between webview and OS. Review every command for input validation and error handling.
- Changes to `tauri.conf.json` capabilities affect the app's permission scope. Verify minimal permissions.
- Shell plugin usage and `std::process::Command` calls must be reviewed for injection risks.

## Security
- Never use `.unwrap()` or `.expect()` inside `#[tauri::command]` handlers — panics crash the entire application. Use `.map_err()` to convert errors.
- All command parameters that accept user-provided data (strings, paths, IDs) must be validated before use. Never pass unsanitized IPC input to file operations, shell commands, or SQL queries.
- When using `tauri-plugin-shell` or `std::process::Command`, never interpolate user input into command strings. Use argument arrays and validate against an allowlist.
- Never log file paths containing user home directories, API keys, tokens, or credentials in command handlers.
- New Tauri commands must be registered in capabilities with minimal required permissions. Do not add to the default capability.

## Conventions
- All `#[tauri::command]` functions must return `Result<T, String>` or a custom error type. Never return bare values without error handling.
- Shared state via `State<Mutex<T>>` must hold locks for the shortest possible scope. Never hold a lock across an `.await` point — this causes deadlocks.
- Frontend `invoke()` calls must use typed parameters: `invoke<ReturnType>('command', args)`. Never pass untyped objects.
- All frontend `invoke()` calls must handle errors with try-catch or `.catch()`. Never fire-and-forget.

## Patterns

### Command Error Handling
**Good:**
\`\`\`rust
#[tauri::command]
async fn read_file(path: String) -> Result<String, String> {
    std::fs::read_to_string(&path)
        .map_err(|e| format!("Failed to read {}: {}", path, e))
}
\`\`\`

**Bad:**
\`\`\`rust
#[tauri::command]
async fn read_file(path: String) -> String {
    std::fs::read_to_string(&path).unwrap() // panics crash the app!
}
\`\`\`

### Mutex Lock Scope
**Good:**
\`\`\`rust
let data = {
    let guard = state.lock().map_err(|e| e.to_string())?;
    guard.data.clone()
}; // guard dropped here
do_async_work(data).await?;
\`\`\`

**Bad:**
\`\`\`rust
let guard = state.lock().map_err(|e| e.to_string())?;
do_async_work(guard.data.clone()).await?; // lock held across await!
\`\`\`

## Ignore
- `src-tauri/target/` is Rust build output — never review.
- `node_modules/` and lock files don't need review.
- `*.d.ts` declaration files are auto-generated.

## Testing
- Command handlers must be tested with both valid and invalid inputs.
- Frontend invoke calls must be tested for error handling paths.
```

---

## Scenario F: MCP Server (TypeScript)

### `REVIEW.md`
```markdown
# Review Guidelines

## Critical Areas
- Tool handler implementations in `src/tools/` or `src/mcp/tools/` are the primary attack surface. Every handler must validate inputs and handle errors.
- Registry/tool definitions must match runtime validation schemas exactly. Schema divergence causes silent failures.
- Middleware pipeline changes affect all tool calls — review for error boundary coverage.

## Security
- Tool handlers must never interpolate user-provided parameters into shell commands. Use `child_process.execFile` with argument arrays.
- File system operations must validate paths against an allowed root directory. Reject paths containing `..` or absolute paths outside scope.
- Error responses must never include API keys, authentication credentials, or internal server URLs. Sanitize all error messages.
- Never log raw tool parameters that may contain secrets. Log parameter names only.

## Conventions
- All tool handlers must validate inputs using Zod schemas that match the advertised `inputSchema`. Use `safeParse()` and return structured errors on validation failure.
- Tool responses must return `{ content: [{ type: 'text', text: string }] }`. Error responses must set `isError: true`.
- All tool handlers must be wrapped in try-catch. Unhandled exceptions crash the MCP server.
- Use the structured logger for all logging. On stdio transport, `console.log`/`console.error` corrupts the JSON-RPC stream.
- All external API calls must propagate the request's `AbortSignal` for timeout support. Never allow tool execution to hang indefinitely.

## Performance
- Tool handlers returning variable-length data must enforce limits (maxItems, pagination). Never return unbounded arrays.
- External API calls should use the circuit breaker for repeated failure protection.

## Patterns

### Tool Handler
**Good:**
\`\`\`typescript
const parsed = InputSchema.safeParse(args);
if (!parsed.success) {
  return { content: [{ type: "text", text: \`Invalid: \${parsed.error.message}\` }], isError: true };
}
try {
  const result = await doWork(parsed.data, { signal });
  return { content: [{ type: "text", text: formatResult(result) }] };
} catch (error) {
  return { content: [{ type: "text", text: \`Error: \${sanitize(error.message)}\` }], isError: true };
}
\`\`\`

**Bad:**
\`\`\`typescript
const result = await doWork(args); // no validation, no error handling, no signal
return { content: [{ type: "text", text: JSON.stringify(result) }] }; // unbounded output
\`\`\`

## Ignore
- `dist/` and `build/` directories are compiled output.
- `*.d.ts` declaration files are auto-generated.
- Lock files don't need review.
- `node_modules/` should never be committed.

## Testing
- Every tool handler must have tests covering: valid input, invalid input (schema violation), external service failure.
- Schema consistency: test that registered inputSchema matches runtime Zod schema.
```

---

## Scenario G: Python Agent using mcp-use

### `REVIEW.md`
```markdown
# Review Guidelines

## Critical Areas
- Agent initialization and MCP server connection code must be reviewed for proper lifecycle management.
- Tool call implementations must handle errors and enforce timeouts — hanging tool calls block the entire agent.
- Any file that imports secrets, API keys, or credentials must be reviewed for proper environment variable usage.

## Security
- MCP server URLs, API keys, and credentials must never be hardcoded. Use `os.environ`, `.env` files with `python-dotenv`, or `keyring`.
- Tool call results from external MCP servers must be treated as untrusted input. Validate before using in subsequent operations.
- Never log raw tool parameters or API responses that may contain user data or secrets.

## Conventions
- `MCPClient` and `MCPAgent` must use async context managers (`async with MCPAgent(...) as agent:`) or explicit `await agent.close()` in a finally block. Leaked connections exhaust server resources.
- All `agent.call_tool()` invocations must handle `MCPToolCallError` and inspect `error.data` for debugging context.
- Tool calls must specify a timeout parameter. The default 60s is too long for most operations.
- When using multiple MCP servers, verify tool namespaces don't collide. Configure explicit routing or namespace prefixes.
- After server restarts or config changes, call `agent.refresh_tools()` to reload schemas.

## Performance
- Connection error recovery must use exponential backoff with a maximum retry count.
- Batch tool calls when possible instead of sequential single calls.
- Monitor agent token usage — large context from tool results can exhaust LLM token limits.

## Ignore
- `__pycache__/` directories should never be committed.
- `.venv/` and `venv/` are local environments.
- `.mypy_cache/` and `.pytest_cache/` are tooling caches.
- Lock files don't need review.

## Testing
- Agent initialization must be tested with both successful and failed server connections.
- Tool calls must be tested for timeout handling and error recovery.
- Connection cleanup must be verified — no leaked async resources.
```

---

## Scenario H: Go HTTP Service

### `REVIEW.md`
```markdown
# Review Guidelines

## Critical Areas
- All error returns must use `fmt.Errorf("context: %w", err)` for proper error wrapping. Bare `err` returns lose context across call boundaries.
- Goroutine lifecycle must be explicitly managed. Every `go func()` needs a cancellation path via `context.Context` or a `done` channel. Leaked goroutines are memory leaks.
- `defer` ordering matters — defers execute LIFO. Review that cleanup of dependent resources happens in the correct order (e.g., close response body before closing client).

## Security
- All HTTP handler inputs (query params, path params, request bodies) must be validated before use. Use a validation library or explicit checks.
- Database queries must use parameterized statements (`db.QueryContext(ctx, "SELECT ... WHERE id = $1", id)`). Never use `fmt.Sprintf` to build SQL.
- Secrets must come from environment variables or a secrets manager. Never hardcode API keys, tokens, or credentials.

## Conventions
- Use `log/slog` for structured logging. No `fmt.Println` or `log.Printf` in production code.
- Tests must be table-driven with clear test case names: `tests := []struct{ name string; ... }`.
- Internal packages belong in `internal/`. Public API surface must be intentionally exported.
- HTTP handlers must accept `http.ResponseWriter, *http.Request` — never wrap these in custom types that hide the interface.

## Performance
- Database connections must use `sql.DB` with `SetMaxOpenConns`, `SetMaxIdleConns`, and `SetConnMaxLifetime` configured. Never create per-request connections.
- All I/O operations must propagate `context.Context` for cancellation and timeout support.
- Hot-path allocations should consider `sync.Pool` for frequently allocated and discarded objects. Profile before optimizing.

## Patterns

### Error Handling
**Good:**
\`\`\`go
func getUser(ctx context.Context, id string) (*User, error) {
    u, err := db.QueryRowContext(ctx, "SELECT ... WHERE id = $1", id)
    if err != nil {
        return nil, fmt.Errorf("getUser(%s): %w", id, err)
    }
    return u, nil
}
\`\`\`

**Bad:**
\`\`\`go
func getUser(id string) *User {
    u, _ := db.QueryRow("SELECT ... WHERE id = " + id) // SQL injection, ignored error, no context
    return u
}
\`\`\`

## Ignore
- `vendor/` directory is managed by `go mod vendor` — don't review.
- `*_test.go` files don't need security review unless they test auth flows.
- `go.sum` is auto-generated — skip.
- `*.pb.go` files are generated by protoc — don't review.

## Testing
- All handlers must have tests covering success, validation error, and internal error paths.
- Table-driven tests must cover edge cases (empty input, max-length strings, zero values).
```

> 💡 Pairing with AGENTS.md? See `references/agents-md/configuration.md`

---

## Scenario I: Django GraphQL (Graphene / Strawberry)

### `REVIEW.md`
```markdown
# Review Guidelines

## Critical Areas
- Resolvers that access related objects must use DataLoader to prevent N+1 query explosions. A single list query without DataLoader can generate hundreds of SQL queries.
- Mutations must validate all inputs before performing writes. Use serializer validation or explicit field checks — never trust client-submitted GraphQL variables.
- Schema must enforce query depth limits (max 5–7 levels) and query complexity analysis to prevent denial-of-service via deeply nested queries.

## Security
- All mutations and sensitive queries must use `@login_required` or `@permission_required` decorators. A missing decorator means unauthenticated access.
- Object-level permissions must be enforced in resolvers, not just type-level. Verify the requesting user owns or has access to the resolved object.
- String inputs in filters and search arguments must be sanitized. Never pass raw GraphQL arguments into ORM `.extra()` or `.raw()` calls.
- Introspection must be disabled in production (`GRAPHENE = {"SCHEMA_INTROSPECTION": False}` or equivalent).

## Conventions
- Resolvers that return querysets must use `select_related()` / `prefetch_related()` even when DataLoaders handle nested relations — the initial queryset still benefits from joins.
- Celery tasks triggered by mutations must be idempotent. Use a mutation ID or natural key for deduplication.
- Schema changes (new types, fields, mutations) must update the schema documentation and changelog.

## Performance
- List queries must enforce pagination via `first`/`after` (Relay-style) or `limit`/`offset`. Never return unbounded result sets.
- Expensive resolver computations should be cached using Django's cache framework with appropriate TTLs.

## Ignore
- `*/migrations/` are auto-generated — only review if schema changes are unexpected.
- `__pycache__/` directories should never be committed.
- `*.pyc` compiled files should never be committed.
- `staticfiles/` collected assets don't need code review.

## Testing
- Schema snapshot tests must catch unintended type/field removals (breaking changes).
- Resolver tests must verify correct data loading, permission enforcement, and DataLoader usage.
- Mutation tests must cover: valid input → success, invalid input → validation error, unauthorized → permission error.
```

> 💡 Pairing with AGENTS.md? See `references/agents-md/configuration.md`

---

## Scenario J: Monorepo with Scoped REVIEW.md

### Root `REVIEW.md`
```markdown
# Review Guidelines

## Conventions
- All new files must be TypeScript. Do not add new `.js` files.
- Use the structured logger from `@acme/shared/logger`. No `console.log` in production code.
- Import shared utilities from `@acme/shared`. Do not reimplement existing utilities.

## Security
- API keys and secrets must never appear in source code. Use environment variables.
- All user input must be validated before processing.

## Ignore
- Lock files (pnpm-lock.yaml) can be skipped unless dependencies changed.
- Generated types in `**/generated/` don't need review.
- Build output in `**/dist/` should never be committed.
```

### `packages/api/REVIEW.md`
```markdown
# API Review Guidelines

## Critical Areas
- All route handlers must verify authentication.
- Database queries must use the ORM. No raw SQL.

## Conventions
- Controllers handle HTTP only. Business logic goes in services.
- All endpoints must validate request bodies with Zod.
- Error responses must use the standard shape: `{ status, message, requestId, timestamp }`.

## Performance
- No database queries in loops. Use batch operations.
- List endpoints must implement pagination.
```

### `packages/payments/REVIEW.md`
```markdown
# Payments Review Guidelines

## Critical Areas
- This service handles financial transactions. Every PR needs security review.
- All mutations must be idempotent with an idempotency key.

## Security
- Never log credit card numbers, CVVs, or full SSNs. Mask all PII in logs.
- Payment state transitions must be atomic. No partial updates.
- All external payment gateway calls must have retry logic with idempotency.

## Conventions
- All monetary amounts must use integer cents, not floating point.
- Payment events must be published to the event bus for audit logging.
```
