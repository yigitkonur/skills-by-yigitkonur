# Scenarios

Complete example instruction file sets for 8 different tech stacks. Each scenario shows the full file tree and all generated files with reasoning.

These are reference examples — adapt them to the actual codebase, don't copy verbatim.

## Table of Contents

1. [Scenario A: TypeScript Backend API (Express + Prisma)](#scenario-a-typescript-backend-api)
2. [Scenario B: Next.js Admin Dashboard (App Router + NextAuth)](#scenario-b-nextjs-admin-dashboard)
3. [Scenario C: Python Django REST API](#scenario-c-python-django-rest-api)
4. [Scenario D: Go Microservice](#scenario-d-go-microservice)
5. [Scenario E: Tauri v2 Desktop App (Rust + React)](#scenario-e-tauri-v2-desktop-app)
6. [Scenario F: MCP Server (TypeScript)](#scenario-f-mcp-server-typescript)
7. [Scenario G: TypeScript Monorepo (API + Web + Shared)](#scenario-g-typescript-monorepo)
8. [Scenario H: Next.js Marketing Website (App Router + Sanity CMS)](#scenario-h-nextjs-marketing-website)

---

## Scenario A: TypeScript Backend API

**Stack:** Express/Fastify + Prisma ORM + TypeScript + Jest
**Existing linting:** ESLint + Prettier configured
**Key concerns:** Database safety, API standards, auth, error handling

### Generated File Tree

```
.github/
├── copilot-instructions.md
└── instructions/
    ├── typescript.instructions.md
    ├── api-routes.instructions.md
    ├── database.instructions.md
    ├── security.instructions.md
    └── testing.instructions.md
```

**Reasoning:** ESLint/Prettier handle formatting so no style rules needed. Five micro-files covering language, API layer, database layer, security, and tests.

### .github/copilot-instructions.md

```markdown
# Code Review Standards

## Security

- Check for hardcoded secrets, API keys, or credentials
- Verify input validation on all external boundaries
- Look for SQL injection via raw queries or string interpolation
- Review authentication and authorization logic on mutating endpoints

## Error Handling

- All async operations must have try-catch or error propagation
- Never expose internal error details or stack traces in API responses
- Use structured logging: { error, requestId, userId, action }
- Never silently swallow errors with empty catch blocks

## Performance

- Flag N+1 database queries (queries inside loops)
- List endpoints must have pagination — no unbounded queries
- Check for missing database indexes on frequently queried columns
- Flag synchronous operations that should be async

## Code Quality

- Functions should be focused and under 50 lines
- Remove dead code and unused imports
- No commented-out code in production
```

### .github/instructions/typescript.instructions.md

````markdown
---
applyTo: "**/*.{ts,tsx}"
---

# TypeScript Standards

## Type Safety

- Avoid `any` — use `unknown`, generics, or specific interfaces
- Define interfaces for all data shapes passed between functions
- Use strict null checks: handle `null`/`undefined` explicitly
- Export types alongside functions that return them

```typescript
// Avoid
function getUser(id: any): any {
  return db.query(`SELECT * FROM users WHERE id = ${id}`);
}

// Prefer
interface User { id: string; name: string; email: string; }
async function getUser(id: string): Promise<User | null> {
  return prisma.user.findUnique({ where: { id } });
}
```

## Patterns

- Use `const` over `let`; never use `var`
- Use optional chaining (`?.`) and nullish coalescing (`??`)
- Use discriminated unions for modeling states
- Prefer `Map`/`Set` over plain objects for dynamic keys
````

### .github/instructions/api-routes.instructions.md

````markdown
---
applyTo: "**/routes/**/*.ts"
---

# API Route Guidelines

## Input Validation

- Validate ALL request inputs (body, params, query) with Zod at handler entry
- Return 400 with specific field errors, not generic messages
- Reject unexpected fields — use `.strict()` on Zod schemas

```typescript
// Avoid
app.post("/users", async (req, res) => {
  const user = await prisma.user.create({ data: req.body });
  res.json(user);
});

// Prefer
app.post("/users", async (req, res, next) => {
  try {
    const body = CreateUserSchema.parse(req.body);
    const user = await userService.create(body);
    res.status(201).json({ data: user, error: null });
  } catch (err) { next(err); }
});
```

## Response Format

- Use consistent envelope: `{ data, error, meta }`
- Return 201 for creation, 204 for deletion
- Include pagination metadata in list responses: `{ total, page, limit }`
- Never return raw Prisma objects — use DTOs to control exposed fields

## Auth

- Every mutating endpoint must verify authentication via middleware
- Check authorization (role/permission) after authentication
- Log failed auth attempts with user identifier and endpoint
````

### .github/instructions/database.instructions.md

````markdown
---
applyTo: "**/{prisma,models,repositories,services}/**/*.ts"
---

# Database & Prisma Guidelines

## Query Safety

- Never use `$queryRaw` with string interpolation — use `$queryRaw` with tagged template or `Prisma.sql`
- Use `include` or `select` for related data — never lazy load in loops
- Wrap multi-step mutations in `$transaction`
- Set `take` limit on all `findMany` — no unbounded queries

```typescript
// Avoid — N+1 query pattern
const orders = await prisma.order.findMany();
for (const order of orders) {
  const items = await prisma.orderItem.findMany({ where: { orderId: order.id } });
}

// Prefer
const orders = await prisma.order.findMany({
  include: { items: true },
  take: 50,
});
```

## Migrations

- Migrations must be backwards-compatible with currently running code
- Add new nullable columns or columns with DEFAULT — never bare NOT NULL on existing tables
- Never delete columns in the same deploy that removes code using them
- Test migrations against production-volume data before merging

## Models

- Use `@map` and `@@map` for database naming conventions
- Define `@unique` constraints for natural keys
- Add `@updatedAt` to all models that track modification time
````

### .github/instructions/security.instructions.md

````markdown
---
applyTo: "**/{auth,middleware,security}/**/*.ts"
---

# Security-Critical Path Guidelines

## Authentication

- Password hashing must use bcrypt with cost factor ≥ 12
- Session tokens: minimum 128-bit cryptographically random values
- Implement rate limiting on login and password reset endpoints
- Use constant-time comparison for token validation

## Authorization

- Check permissions on every request — never cache auth decisions
- Use RBAC middleware, not ad-hoc role checks in handlers
- Log all authorization failures with userId and attempted resource
- Deny by default — routes require explicit auth middleware

## Data Protection

- Never log passwords, tokens, API keys, or PII
- Mask sensitive data in responses (e.g., last 4 digits of card numbers)
- Set `Secure`, `HttpOnly`, `SameSite` flags on auth cookies
- Use encryption at rest for PII columns

## Headers

- Set `Content-Security-Policy` headers
- Enable `X-Content-Type-Options: nosniff`
- Set `Strict-Transport-Security` for HTTPS enforcement
````

### .github/instructions/testing.instructions.md

````markdown
---
applyTo: "**/*.{test,spec}.ts"
---

# Test Guidelines

## Structure

- Each test covers one behavior — not multiple unrelated assertions
- Test names describe the scenario: `should return 404 when user not found`
- Tests are independent — no shared mutable state between tests
- Use test factories for data creation, not copy-pasted literals

```typescript
// Avoid
test("user", async () => {
  const user = await createUser({ name: "test", email: "a@b.com", role: "admin" });
  expect(user.name).toBe("test");
  expect(await getUser(user.id)).toBeTruthy();
  await deleteUser(user.id);
  expect(await getUser(user.id)).toBeNull();
});

// Prefer
test("should find user by id after creation", async () => {
  const user = await UserFactory.create();
  const found = await getUser(user.id);
  expect(found).toMatchObject({ id: user.id, name: user.name });
});
```

## Mocking

- Mock external services (APIs, email) — not internal business logic
- Reset all mocks in `beforeEach`
- Prefer integration tests with test database over mocked Prisma calls
- Use dependency injection to make services testable

## Coverage

- New features require tests for main path and error cases
- Bug fixes must include a regression test
- Don't test Prisma internals or Express framework behavior
````

---

## Scenario B: Next.js Admin Dashboard

**Stack:** Next.js 15 App Router + NextAuth + TypeScript + Prisma
**Existing linting:** ESLint + Prettier
**Key concerns:** Auth on every route, Server Action validation, RBAC, no env leaks

### Generated File Tree

```
.github/
├── copilot-instructions.md
└── instructions/
    ├── typescript.instructions.md
    ├── nextjs-app.instructions.md
    ├── server-actions.instructions.md
    ├── api-routes.instructions.md
    ├── security.instructions.md
    └── testing.instructions.md
```

**Reasoning:** The dashboard has specific auth concerns at every layer — separate files for App Router patterns, Server Actions (which handle mutations), API routes, and security-critical paths.

### .github/copilot-instructions.md

```markdown
# Admin Dashboard Review Standards

## Security — Highest Priority

- Never expose `process.env` variables in client components (only `NEXT_PUBLIC_*`)
- All data mutations must verify authentication and authorization
- No PII in client-side logs or error messages
- Review RBAC enforcement on every new route and action

## Error Handling

- Every route segment should have an `error.tsx` boundary
- Server Actions must return structured results, not throw to the client
- Log errors server-side with structured format including userId and action
- Never expose database errors or stack traces to the browser

## Performance

- Fetch data in Server Components — not in client `useEffect`
- Use `Promise.all()` for parallel data fetches
- All list views must have server-side pagination
- Use `loading.tsx` for meaningful loading states

## Quality

- Remove dead code and unused imports
- No commented-out code in production
- Keep components focused and under 200 lines
```

### .github/instructions/nextjs-app.instructions.md

````markdown
---
applyTo: "**/app/**/*.{ts,tsx}"
---

# Next.js App Router Guidelines

## Server vs Client

- Default to Server Components — `"use client"` only for hooks/events/browser APIs
- Push `"use client"` boundary as low as possible in the component tree
- Never import `@/lib/server/*` modules in client components
- Server Components handle data fetching; client components handle interactivity

## Data Fetching

- Fetch in Server Components, not in `useEffect`
- Use `Promise.all()` for parallel data needs — never sequential awaits
- Wrap async Server Components in `<Suspense>` with skeleton fallbacks
- Use `revalidatePath()` or `revalidateTag()` after mutations

```tsx
// Avoid
const user = await getUser(id);
const stats = await getStats(id);

// Prefer
const [user, stats] = await Promise.all([getUser(id), getStats(id)]);
```

## Route Protection

- Dashboard routes must check session in `layout.tsx` or middleware
- Redirect unauthenticated users to `/login`
- Check role permissions before rendering admin-only content
- Never rely on client-side route guards alone

## Metadata

- Every page must export `metadata` or `generateMetadata()`
- Include `title` at minimum
````

### .github/instructions/server-actions.instructions.md

````markdown
---
applyTo: "**/actions/**/*.ts"
---

# Server Action Guidelines

## Input Validation

- Validate ALL inputs with Zod at the top of every Server Action
- Use `.strict()` to reject unexpected fields
- Return typed results, not raw throws

```typescript
// Avoid
"use server";
export async function updateUser(formData: FormData) {
  const name = formData.get("name") as string;
  await db.user.update({ where: { id: userId }, data: { name } });
}

// Prefer
"use server";
const UpdateUserSchema = z.object({ name: z.string().min(1).max(100) });

export async function updateUser(formData: FormData): Promise<ActionResult> {
  const session = await requireAuth();
  const parsed = UpdateUserSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: parsed.error.flatten() };
  await db.user.update({ where: { id: session.userId }, data: parsed.data });
  revalidatePath("/dashboard/profile");
  return { success: true };
}
```

## Authentication & Authorization

- Every Server Action must call `requireAuth()` before any data access
- Check RBAC permissions for the specific operation
- Use the session userId — never accept userId from the client
- Log mutation events with userId and action type

## Error Handling

- Return `{ success, error }` objects — don't throw unstructured errors
- Log errors server-side with context
- Never expose internal error details to the client
````

---

## Scenario C: Python Django REST API

**Stack:** Django 5 + Django REST Framework + PostgreSQL + Celery
**Existing linting:** Ruff + Black configured
**Key concerns:** N+1 queries, permission_classes, SQL safety, task reliability

### Generated File Tree

```
.github/
├── copilot-instructions.md
└── instructions/
    ├── python.instructions.md
    ├── django-views.instructions.md
    ├── django-models.instructions.md
    ├── celery-tasks.instructions.md
    ├── security.instructions.md
    └── testing.instructions.md
```

**Reasoning:** Ruff/Black handle formatting. Django's views, models, and Celery tasks each have distinct review concerns. Six micro-files for focused coverage.

### .github/copilot-instructions.md

```markdown
# Django API Review Standards

## Security

- Check for hardcoded secrets, API keys, or credentials
- Verify parameterized queries — no f-string SQL interpolation
- All views must have `permission_classes` defined
- Validate and sanitize all file uploads (type, size, extension)
- No PII in log messages

## Performance

- Flag N+1 queries: queries inside loops without prefetching
- List endpoints must have pagination — no unbounded querysets
- Use database-level operations (`F()`, `Q()`, `Subquery`) over Python-level
- Check for missing database indexes on filtered columns

## Quality

- Remove dead code and unused imports
- No commented-out code in production
- Use structured logging, not print statements
```

### .github/instructions/django-views.instructions.md

````markdown
---
applyTo: "**/{views,viewsets}/**/*.py"
---

# Django View Guidelines

## Permissions

- Every view MUST define `permission_classes` — never leave as empty list
- Use `IsAuthenticated` as minimum for non-public endpoints
- Custom permission classes for role-based access
- Object-level permissions for resource ownership checks

```python
# Avoid
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Prefer
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
```

## Query Optimization

- Use `select_related()` for ForeignKey/OneToOne relations
- Use `prefetch_related()` for ManyToMany/reverse relations
- Apply both on the queryset, not in the serializer
- Use `.only()` for large models when few fields are needed

## Serialization

- Use DRF serializers for all response data — never return raw dicts
- Validate input with serializer `.is_valid(raise_exception=True)`
- Use `read_only_fields` for computed/auto-generated fields
- Separate read and write serializers when they differ significantly
````

### .github/instructions/django-models.instructions.md

````markdown
---
applyTo: "**/{models,migrations}/**/*.py"
---

# Django Model Guidelines

## Model Design

- Define `__str__()` on all models — used in admin and debugging
- Add `class Meta: ordering` for default query ordering
- Use `get_absolute_url()` for URL resolution
- Define `@property` for computed values, not database columns

## Migrations

- Migrations must be backwards-compatible with running code
- Add new columns as nullable or with default values
- Never remove columns in the same deploy that removes code using them
- Squash migrations periodically to keep history manageable

```python
# Avoid — will fail on existing rows
class Migration(migrations.Migration):
    operations = [
        migrations.AddField("order", "tracking_id", models.CharField(max_length=100)),
    ]

# Prefer
class Migration(migrations.Migration):
    operations = [
        migrations.AddField("order", "tracking_id", models.CharField(max_length=100, null=True)),
    ]
```

## Indexes

- Add `db_index=True` on fields used in `filter()`, `order_by()`, `get()`
- Use `unique_together` or `UniqueConstraint` for composite uniqueness
- Add indexes in the same migration that adds the field
````

### .github/instructions/celery-tasks.instructions.md

````markdown
---
applyTo: "**/tasks/**/*.py"
---

# Celery Task Guidelines

## Reliability

- All tasks must be idempotent — safe to run multiple times
- Set `max_retries` and `default_retry_delay` on every task
- Use `self.retry()` for transient failures (network, timeout)
- Use `acks_late=True` for tasks that must complete

```python
# Avoid
@shared_task
def send_email(user_id):
    user = User.objects.get(id=user_id)
    send(user.email, "Welcome!")

# Prefer
@shared_task(bind=True, max_retries=3, default_retry_delay=60, acks_late=True)
def send_email(self, user_id):
    try:
        user = User.objects.get(id=user_id)
        send(user.email, "Welcome!")
    except User.DoesNotExist:
        logger.warning("User %s not found, skipping email", user_id)
    except ConnectionError as exc:
        self.retry(exc=exc)
```

## Arguments

- Pass IDs, not model instances — objects can't be serialized safely
- Use JSON-serializable arguments only
- Avoid large payloads — pass references, not data

## Monitoring

- Log task start and completion with task_id
- Set `time_limit` and `soft_time_limit` to prevent hung tasks
- Use structured logging with task context
````

---

## Scenario D: Go Microservice

**Stack:** Go 1.22 + chi router + sqlx + gRPC
**Existing linting:** golangci-lint configured
**Key concerns:** Error handling, context propagation, goroutine safety

### Generated File Tree

```
.github/
├── copilot-instructions.md
└── instructions/
    ├── go.instructions.md
    ├── api-handlers.instructions.md
    ├── database.instructions.md
    └── grpc.instructions.md
```

**Reasoning:** golangci-lint covers style. Four focused files for language conventions, HTTP handlers, database layer, and gRPC service definitions.

### .github/copilot-instructions.md

```markdown
# Go Microservice Review Standards

## Security

- Check for hardcoded secrets or credentials
- Verify input validation on all external boundaries
- No user input in `fmt.Sprintf` for SQL — use parameterized queries
- Review authentication middleware on all handlers

## Error Handling

- Every returned error must be checked — never discard with `_`
- Wrap errors with context: `fmt.Errorf("fetching user %s: %w", id, err)`
- Return errors; don't panic in production code
- Use sentinel errors or custom types for expected failure modes

## Performance

- Check for goroutine leaks — every goroutine must have an exit path
- Respect context cancellation in long-running operations
- Use connection pooling for database and HTTP clients
- Close response bodies and other resources in defer

## Quality

- No unused variables or imports (enforced by compiler, but review intent)
- Keep functions focused and under 50 lines
- Use table-driven tests for multiple input scenarios
```

### .github/instructions/api-handlers.instructions.md

````markdown
---
applyTo: "**/handlers/**/*.go"
---

# API Handler Guidelines

## Request Handling

- Validate request body before processing — use a validation library or manual checks
- Extract and validate path parameters and query strings explicitly
- Return consistent JSON response shape: `{"data": ..., "error": ...}`
- Set appropriate status codes (201 for create, 204 for delete, 400 for invalid input)

```go
// Avoid
func CreateUser(w http.ResponseWriter, r *http.Request) {
    var user User
    json.NewDecoder(r.Body).Decode(&user)
    db.Create(&user)
    json.NewEncoder(w).Encode(user)
}

// Prefer
func CreateUser(w http.ResponseWriter, r *http.Request) {
    var req CreateUserRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        respondError(w, http.StatusBadRequest, "invalid request body")
        return
    }
    if err := req.Validate(); err != nil {
        respondError(w, http.StatusBadRequest, err.Error())
        return
    }
    user, err := svc.CreateUser(r.Context(), req)
    if err != nil {
        respondError(w, http.StatusInternalServerError, "internal error")
        return
    }
    respondJSON(w, http.StatusCreated, user)
}
```

## Context

- Pass `r.Context()` to all downstream calls (service, database, external APIs)
- Check `ctx.Err()` in long-running operations
- Never store request context in structs
````

### .github/instructions/database.instructions.md

````markdown
---
applyTo: "**/{db,repository,store}/**/*.go"
---

# Database Guidelines (sqlx)

## Query Safety

- Use parameterized queries with `$1, $2` placeholders — never `fmt.Sprintf`
- Use `sqlx.NamedExec` for inserts with many fields
- Wrap multi-step operations in transactions via `sqlx.Tx`
- Set query timeouts via context: `context.WithTimeout`

```go
// Avoid
query := fmt.Sprintf("SELECT * FROM users WHERE id = '%s'", id)
db.QueryRow(query)

// Prefer
db.QueryRowContext(ctx, "SELECT id, name, email FROM users WHERE id = $1", id)
```

## Performance

- Use `SELECT` with explicit columns — avoid `SELECT *`
- Use `LIMIT` on all list queries
- Batch inserts with `sqlx.NamedExec` and slice parameters
- Close `sql.Rows` in defer immediately after query

## Connections

- Use connection pool settings: `SetMaxOpenConns`, `SetMaxIdleConns`, `SetConnMaxLifetime`
- Ping database on startup to fail fast
- Handle `sql.ErrNoRows` as a normal case, not an error to log
````

---

## Scenario E: Tauri v2 Desktop App

**Stack:** Tauri v2 + Rust backend + React + TypeScript frontend
**Existing linting:** ESLint + Prettier (frontend), clippy (Rust)
**Key concerns:** IPC safety, no panics in commands, Mutex discipline, shell injection

### Generated File Tree

```
.github/
├── copilot-instructions.md
└── instructions/
    ├── tauri-commands.instructions.md
    ├── tauri-frontend.instructions.md
    ├── rust.instructions.md
    ├── react.instructions.md
    └── security.instructions.md
```

**Reasoning:** Tauri's IPC boundary is the critical security surface. Separate files for Rust commands, frontend invoke patterns, general Rust safety, React components, and security-critical paths.

### .github/copilot-instructions.md

```markdown
# Tauri Desktop App Review Standards

## Security — Highest Priority

- Every `#[tauri::command]` handler is a security boundary — treat inputs as untrusted
- Never pass user input to shell commands or `Command::new()`
- Validate all file paths against allowed directories
- Never log sensitive data (SSH keys, credentials, file paths with usernames)
- Review `capabilities` in tauri.conf.json for minimal permissions

## Error Handling

- No `unwrap()` or `expect()` in command handlers — always return `Result`
- Frontend must handle invoke errors gracefully (show user-friendly messages)
- Log errors to file, not stdout (which is not visible in desktop apps)

## Performance

- Keep Mutex lock scopes narrow — never hold across `.await`
- Heavy computation must run on background threads, not main thread
- Frontend must show loading states during IPC calls

## Quality

- Type the invoke call and response on the frontend side
- Keep command handlers thin — delegate to service functions
```

### .github/instructions/tauri-commands.instructions.md

````markdown
---
applyTo: "**/src-tauri/src/**/*.rs"
---

# Tauri Command Handler Guidelines

## Safety

- Return `Result<T, String>` from all commands — never panic
- No `unwrap()`, `expect()`, or `panic!()` in any command handler
- Validate parameters at command entry before any processing
- Check file paths against allowed directories (app_data_dir, app_config_dir)

```rust
// Avoid
#[tauri::command]
fn read_config(path: String) -> String {
    std::fs::read_to_string(path).unwrap()
}

// Prefer
#[tauri::command]
fn read_config(path: String, app: tauri::AppHandle) -> Result<String, String> {
    let base = app.path().app_config_dir().map_err(|e| e.to_string())?;
    let resolved = base.join(&path).canonicalize().map_err(|e| e.to_string())?;
    if !resolved.starts_with(&base) {
        return Err("Access denied: path outside config directory".into());
    }
    std::fs::read_to_string(resolved).map_err(|e| e.to_string())
}
```

## State Management

- Use `tauri::State<Mutex<T>>` for shared mutable state
- Lock scope must be as narrow as possible
- Never hold a Mutex guard across an `.await` point
- Prefer `RwLock` when reads vastly outnumber writes

## Shell Safety

- Never pass user input to `std::process::Command` without validation
- Whitelist allowed commands and arguments
- Use the Tauri shell plugin with scoped permissions, not raw `Command::new()`
````

### .github/instructions/tauri-frontend.instructions.md

````markdown
---
applyTo: "**/src/**/*.{ts,tsx}"
---

# Tauri Frontend Guidelines

## IPC Safety

- Type all `invoke()` calls with expected return types
- Handle invoke errors with try-catch — commands can fail
- Show user-friendly error messages, not raw Rust error strings
- Use loading states during IPC calls to prevent double-submission

```typescript
// Avoid
const result = await invoke("read_config", { path: userInput });
setData(result);

// Prefer
try {
  setLoading(true);
  const result = await invoke<ConfigData>("read_config", { path: sanitized });
  setData(result);
} catch (err) {
  setError("Failed to load configuration. Please try again.");
  console.error("read_config failed:", err);
} finally {
  setLoading(false);
}
```

## Event Handling

- Use `listen()` for backend-to-frontend events with typed payloads
- Unlisten in component cleanup (useEffect return)
- Never assume event order — handle out-of-order delivery

## Environment

- Never access `process.env` — use Tauri APIs for platform info
- Use `@tauri-apps/api/path` for filesystem paths, not hardcoded strings
- Check platform with `@tauri-apps/api/os` for platform-specific behavior
````

---

## Scenario F: MCP Server (TypeScript)

**Stack:** TypeScript + MCP SDK + stdio transport + Zod
**Existing linting:** ESLint
**Key concerns:** Protocol compliance, stdio safety, input validation, tool handler errors

### Generated File Tree

```
.github/
├── copilot-instructions.md
└── instructions/
    ├── typescript.instructions.md
    ├── mcp-tools.instructions.md
    ├── mcp-transport.instructions.md
    └── security.instructions.md
```

**Reasoning:** MCP has unique protocol requirements and the stdio transport has a critical constraint (no console.log). Separate files for tools, transport, and security.

### .github/copilot-instructions.md

```markdown
# MCP Server Review Standards

## Protocol Compliance

- Tool parameter schemas in registry must match Zod validation in handlers
- Responses must use structured content arrays, not raw strings
- Use `isError: true` for tool execution failures
- Respect `AbortSignal` for cancellation support

## Security

- Never interpolate user input into shell commands
- Validate and sanitize file paths — prevent directory traversal
- Never expose API keys, tokens, or credentials in error messages
- Validate URL schemes (allow http/https only)

## Quality

- All tool handlers must have try-catch
- Set timeouts on all external calls (HTTP, DB, file I/O)
- Close connections and clean up resources in finally blocks
- Log tool invocations with duration for monitoring
```

### .github/instructions/mcp-tools.instructions.md

````markdown
---
applyTo: "**/tools/**/*.ts"
---

# MCP Tool Handler Guidelines

## Input Validation

- Validate all parameters with Zod at handler entry
- Zod schema must match the tool's registered `inputSchema`
- Return `isError: true` for validation failures with clear message
- Never trust client-provided parameter types

```typescript
// Avoid
async function handleSearch(params: any) {
  const results = await search(params.query);
  return { content: [{ type: "text", text: JSON.stringify(results) }] };
}

// Prefer
const SearchSchema = z.object({ query: z.string().min(1).max(500) });

async function handleSearch(params: unknown) {
  const parsed = SearchSchema.safeParse(params);
  if (!parsed.success) {
    return { content: [{ type: "text", text: `Invalid params: ${parsed.error.message}` }], isError: true };
  }
  const results = await search(parsed.data.query);
  return { content: [{ type: "text", text: JSON.stringify(results, null, 2) }] };
}
```

## Error Handling

- Wrap every tool handler body in try-catch
- Return `isError: true` with user-friendly message on failure
- Log the full error server-side; return sanitized message to client
- Never let unhandled exceptions crash the server process

## Response Format

- Return `content` as array of typed blocks (`text`, `image`, `resource`)
- Include `_meta` for progress tracking on long operations
- Keep text responses well-structured (JSON or markdown)
````

### .github/instructions/mcp-transport.instructions.md

````markdown
---
applyTo: "**/src/**/*.ts"
---

# MCP Transport Guidelines

## stdio Safety

- NEVER use `console.log()` on stdio transport — it corrupts the JSON-RPC stream
- Use `console.error()` or a file logger for debug output
- All diagnostic output must go to stderr, never stdout
- Test that no dependency writes to stdout unexpectedly

```typescript
// WRONG — breaks stdio transport
console.log("Processing request:", params);

// CORRECT — stderr for diagnostics
console.error("[DEBUG] Processing request:", JSON.stringify(params));

// BETTER — structured file logger
logger.debug("Processing request", { params, toolName });
```

## Connection Lifecycle

- Implement graceful shutdown on SIGTERM/SIGINT
- Clean up all open connections (DB, HTTP) before exit
- Handle transport disconnection without crashing
- Set up health checks for long-running server instances

## Performance

- Set timeouts on all external operations
- Use AbortController/AbortSignal for cancellable operations
- Stream large responses when supported by transport
- Monitor memory usage — MCP servers can be long-lived processes
````

---

## Scenario G: TypeScript Monorepo

**Stack:** Turborepo + packages/api (Express + Prisma) + packages/web (Next.js) + packages/shared
**Existing linting:** ESLint + Prettier at root
**Key concerns:** Package boundaries, shared code safety, different review needs per package

### Generated File Tree

```
.github/
├── copilot-instructions.md
└── instructions/
    ├── typescript.instructions.md
    ├── packages-api.instructions.md
    ├── packages-web.instructions.md
    ├── packages-shared.instructions.md
    ├── database.instructions.md
    ├── security.instructions.md
    └── testing.instructions.md
```

**Reasoning:** Root copilot-instructions.md for universal standards. TypeScript for language rules across all packages. Three package-specific files for API, web, and shared concerns. Plus database, security, and testing.

### .github/copilot-instructions.md

```markdown
# Monorepo Review Standards

## Architecture

- Packages must not import from each other's internal modules — use the package's public API
- Shared code belongs in `packages/shared` — don't duplicate across packages
- Type definitions shared across packages must be exported from `packages/shared`
- No circular dependencies between packages

## Security

- Check for hardcoded secrets, API keys, or credentials
- Verify input validation on all external boundaries
- No PII in log messages across any package

## Quality

- Use the shared logger from `@repo/shared` — not `console.log`
- Structured logging: { level, message, context, timestamp }
- Remove dead code and unused imports
- No commented-out code in production
```

### .github/instructions/packages-api.instructions.md

````markdown
---
applyTo: "packages/api/**/*.ts"
---

# API Package Guidelines

## Request Handling

- Validate all request inputs with Zod at handler entry
- Return consistent response shape: `{ data, error, meta }`
- Auth middleware must run before any data access
- Rate limiting on public endpoints

## Database

- Use Prisma `include`/`select` — no lazy loading in loops
- Wrap multi-step mutations in `$transaction`
- All list queries must have `take` limit and pagination
- Never use `$queryRaw` with string interpolation

## Error Handling

- Use centralized error middleware
- Never expose internal errors or stack traces in responses
- Log errors with requestId for distributed tracing
- Return appropriate HTTP status codes
````

### .github/instructions/packages-web.instructions.md

````markdown
---
applyTo: "packages/web/**/*.{ts,tsx}"
---

# Web Package Guidelines (Next.js)

## Server vs Client

- Default to Server Components
- `"use client"` only for hooks, events, browser APIs
- Push client boundary as low as possible
- Fetch data in Server Components, not in `useEffect`

## Data Fetching

- Use `Promise.all()` for parallel fetches
- Wrap async components in `<Suspense>` with skeleton fallbacks
- Call internal API routes for mutations, not direct Prisma from web package
- Set revalidation strategy for cached data

## Auth

- Check session in dashboard layouts via middleware
- Never render admin content without server-side auth check
- Role-based UI: hide elements AND verify server-side

## Accessibility

- Interactive elements must be keyboard accessible
- Icon-only buttons need `aria-label`
- Use semantic HTML elements
````

### .github/instructions/packages-shared.instructions.md

````markdown
---
applyTo: "packages/shared/**/*.ts"
---

# Shared Package Guidelines

## API Surface

- Export only what other packages need — keep internals private
- Every export must have TypeScript type annotations
- Use barrel exports (`index.ts`) for clean import paths
- Document breaking changes in exports

## Compatibility

- Changes to shared types affect ALL consuming packages
- Test shared utilities with inputs from all known consumers
- Avoid runtime dependencies — shared package should be lightweight
- Use peer dependencies for framework-specific code

## Conventions

- Shared types use PascalCase and end in descriptive suffix: `UserResponse`, `OrderInput`
- Shared utilities are pure functions when possible
- Logger, error classes, and validation schemas live here
- No side effects on import
````

---

## Scenario H: Next.js Marketing Website

**Stack:** Next.js 15 App Router + Sanity CMS + TypeScript + Tailwind
**Existing linting:** ESLint + Prettier
**Key concerns:** SEO, metadata, performance, image optimization, minimal client JS

### Generated File Tree

```
.github/
├── copilot-instructions.md
└── instructions/
    ├── typescript.instructions.md
    ├── nextjs-pages.instructions.md
    ├── nextjs-components.instructions.md
    ├── cms-integration.instructions.md
    └── a11y.instructions.md
```

**Reasoning:** Marketing site priorities are SEO, performance, and accessibility. Separate files for page-level concerns (metadata, data fetching), component patterns, CMS integration, and accessibility.

### .github/copilot-instructions.md

```markdown
# Marketing Website Review Standards

## SEO — Highest Priority

- Every page route must export `metadata` or `generateMetadata()`
- Include `title`, `description`, and `openGraph` properties minimum
- Add JSON-LD structured data for key pages (home, product, FAQ, blog)
- Use semantic HTML: `article`, `section`, `nav`, `header`, `footer`, `main`

## Performance

- Use `next/image` with explicit `width`/`height` — never raw `<img>`
- Images above the fold must have `priority={true}`
- Minimize `"use client"` — keep pages as Server Components
- Use ISR with `revalidate` for CMS content, not on-demand for every request

## Security

- External links: add `rel="noopener noreferrer"` and `target="_blank"`
- Never hardcode API keys or CMS tokens in client code
- Server Actions must validate input with Zod
- Sanitize CMS-provided HTML before rendering

## Quality

- No dead code or unused imports
- Keep components under 200 lines
```

### .github/instructions/nextjs-pages.instructions.md

````markdown
---
applyTo: "**/app/**/page.{ts,tsx}"
---

# Page-Level Guidelines

## Metadata

- Every page must export `metadata` or `generateMetadata()`
- Include: `title`, `description`, `openGraph` (title, description, images)
- Dynamic pages use `generateMetadata()` with data from CMS
- Add canonical URL for pages accessible via multiple paths

```tsx
// Every page.tsx needs this
export const metadata: Metadata = {
  title: "Product Features | Brand Name",
  description: "Discover the features that make Brand Name the best choice for...",
  openGraph: {
    title: "Product Features | Brand Name",
    description: "Discover the features...",
    images: ["/og-features.png"],
  },
};
```

## Data Fetching

- Fetch CMS data with ISR: `export const revalidate = 3600`
- Use `Promise.all()` for multiple CMS queries
- Wrap content sections in `<Suspense>` with skeleton fallbacks
- Handle empty/missing CMS data gracefully — show fallback, not crash

## Structured Data

- Add JSON-LD for key pages:
  - Home → Organization schema
  - Blog posts → Article schema
  - FAQ → FAQPage schema
  - Product → Product schema
````

### .github/instructions/nextjs-components.instructions.md

````markdown
---
applyTo: "**/components/**/*.{tsx,jsx}"
---

# Marketing Component Guidelines

## Server-First

- Default to Server Components — no `"use client"` unless required
- Client components only for: interactive forms, animations, dropdowns, carousels
- Keep client components small and leaf-level
- Never fetch data in client components — pass as props from server parent

## Images

- Always use `next/image` — never raw `<img>` tags
- Set explicit `width` and `height` to prevent layout shift
- Above-the-fold images: `priority={true}`
- Use `sizes` prop for responsive images
- Provide meaningful `alt` text for all images

```tsx
// Avoid
<img src="/hero.png" />

// Prefer
<Image src="/hero.png" alt="Product dashboard showing analytics" width={1200} height={600} priority />
```

## Links

- Use `next/link` for internal navigation
- External links: `target="_blank"` with `rel="noopener noreferrer"`
- CTA buttons with links use `<Link>` styled as button, not `<button>` with onClick navigation
````

### .github/instructions/cms-integration.instructions.md

````markdown
---
applyTo: "**/lib/{sanity,cms}/**/*.ts"
---

# CMS Integration Guidelines (Sanity)

## Query Safety

- Use GROQ type generation for typed queries
- Validate CMS response shape before rendering — content can be null/missing
- Set reasonable `revalidate` values (3600 for static pages, 60 for frequently updated)
- Handle draft/preview mode separately from production

```typescript
// Avoid — trusting CMS data blindly
const page = await sanity.fetch(`*[_type == "page" && slug == $slug][0]`, { slug });
return <h1>{page.title}</h1>;

// Prefer — defensive data handling
const page = await sanity.fetch<PageData>(pageQuery, { slug });
if (!page) { notFound(); }
return <h1>{page.title ?? "Untitled"}</h1>;
```

## Image Handling

- Use Sanity image URL builder for responsive images
- Generate proper `srcSet` and `sizes` attributes
- Always extract and provide alt text from CMS image metadata
- Use blur placeholders generated from LQIP

## Content Rendering

- Sanitize rich text/portable text before rendering
- Use typed block renderers for portable text components
- Handle unknown block types gracefully (log warning, skip rendering)
````

### .github/instructions/a11y.instructions.md

````markdown
---
applyTo: "**/*.{tsx,jsx}"
---

# Accessibility Guidelines

## Semantic Structure

- Use heading hierarchy: one `h1` per page, then `h2` > `h3` — don't skip levels
- Use `nav`, `main`, `article`, `section`, `footer` for document landmarks
- Use `button` for actions, `a` for navigation — not `div` with `onClick`
- Form inputs must have associated `label` elements

## Keyboard & Focus

- All interactive elements reachable via Tab
- Visible focus indicators — never `outline: none` without replacement
- Skip-to-content link at the top of every page
- Modal/dropdown components trap focus and close on Escape

## ARIA

- Use ARIA only when native semantics are insufficient
- Icon-only buttons: `aria-label="Close menu"`
- Dynamic content areas: `aria-live="polite"` for updates
- Form errors: `aria-describedby` linking error message to input

## Visual

- Minimum 4.5:1 contrast ratio for body text (WCAG AA)
- Don't rely on color alone to convey information
- Respect `prefers-reduced-motion` for animations
- Minimum 44x44px touch targets for mobile
````
