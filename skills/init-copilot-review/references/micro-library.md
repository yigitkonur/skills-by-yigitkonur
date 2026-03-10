# Micro-Instruction Library

A comprehensive library of individual `*.instructions.md` files organized by category. Use these as adaptation references — match relevant ones to the actual codebase and customize, don't copy verbatim.

## Table of Contents

1. [Language-Specific](#language-specific)
   - [TypeScript](#typescript)
   - [Python](#python)
   - [Rust](#rust)
   - [Go](#go)
   - [C#](#c-sharp)
2. [Framework-Specific](#framework-specific)
   - [React](#react)
   - [Next.js App Router](#nextjs-app-router)
   - [Next.js Marketing/SSG](#nextjs-marketing)
   - [Django](#django)
   - [Express/Fastify](#expressfastify)
   - [Tauri v2](#tauri-v2)
   - [Angular](#angular)
3. [Domain-Specific](#domain-specific)
   - [API Routes](#api-routes)
   - [Database/ORM](#databaseorm)
   - [Security-Critical Paths](#security-critical-paths)
   - [Testing](#testing)
   - [Accessibility](#accessibility)
   - [MCP Server](#mcp-server)
   - [CI/CD Workflows](#cicd-workflows)
   - [Docker/Infrastructure](#dockerinfrastructure)
   - [GraphQL](#graphql)
   - [State Management](#state-management)

---

## Language-Specific

### TypeScript

````markdown
---
applyTo: "**/*.{ts,tsx}"
---

# TypeScript Review Guidelines

## Type Safety

- Avoid `any` — use `unknown`, generics, or specific types
- Use strict null checks: handle `null`/`undefined` explicitly
- Define interfaces for all object shapes passed between functions
- Prefer `as const` for literal types over type assertions

```typescript
// Avoid
function fetchUser(id: any): any {
  return db.query(`SELECT * FROM users WHERE id = ${id}`);
}

// Prefer
interface User { id: string; name: string; email: string; }
async function fetchUser(id: string): Promise<User | null> {
  return db.user.findUnique({ where: { id } });
}
```

## Modern Patterns

- Use optional chaining (`?.`) and nullish coalescing (`??`)
- Prefer `const` over `let`; never use `var`
- Use discriminated unions for state modeling
- Prefer `satisfies` operator for type checking with inference

## Error Handling

- Use typed error classes, not raw `throw new Error()`
- Async functions must have try-catch or propagate errors explicitly
- Never silently swallow errors with empty catch blocks
````

### Python

````markdown
---
applyTo: "**/*.py"
---

# Python Review Guidelines

## Code Quality

- Use type hints on all public function signatures
- Use `pathlib.Path` instead of `os.path` for file operations
- Use dataclasses or Pydantic models for structured data — not raw dicts
- Use context managers (`with` statements) for resource management

```python
# Avoid
def get_user(id):
    conn = db.connect()
    result = conn.execute(f"SELECT * FROM users WHERE id = {id}")
    return result

# Prefer
def get_user(user_id: str) -> User | None:
    with db.session() as session:
        return session.query(User).filter_by(id=user_id).first()
```

## Safety

- Use parameterized queries — never f-string interpolation for SQL
- Use `secrets` module for token generation, not `random`
- Validate file paths to prevent directory traversal
- Use `subprocess.run()` with list args, never `shell=True` with user input

## Async

- Use `async with` for async context managers
- Never mix sync and async I/O in the same function
- Use `asyncio.gather()` for concurrent operations, not sequential awaits
````

### Rust

````markdown
---
applyTo: "**/*.rs"
---

# Rust Review Guidelines

## Error Handling

- Use `Result<T, E>` for fallible operations — never panic in library code
- Use `?` operator for error propagation
- Implement `From` for custom error types to enable `?` across boundaries
- Reserve `unwrap()`/`expect()` for tests and provably safe cases only

```rust
// Avoid
fn parse_config(path: &str) -> Config {
    let content = std::fs::read_to_string(path).unwrap();
    serde_json::from_str(&content).unwrap()
}

// Prefer
fn parse_config(path: &Path) -> Result<Config, AppError> {
    let content = std::fs::read_to_string(path)?;
    let config = serde_json::from_str(&content)?;
    Ok(config)
}
```

## Ownership & Borrowing

- Prefer borrowing (`&T`) over cloning when possible
- Use `Cow<'_, str>` when a function might or might not need to allocate
- Keep `Mutex` lock scopes as narrow as possible — never hold across `.await`
- Prefer `Arc<T>` over `Rc<T>` in async or multi-threaded contexts

## Safety

- No `unsafe` blocks without a `// SAFETY:` comment explaining the invariant
- Validate all external input at system boundaries
- Use `secrecy::Secret` for sensitive values to prevent accidental logging
````

### Go

````markdown
---
applyTo: "**/*.go"
---

# Go Review Guidelines

## Error Handling

- Always check returned errors — never use `_` to discard them
- Wrap errors with context: `fmt.Errorf("fetching user %s: %w", id, err)`
- Use sentinel errors or custom error types for expected failure modes
- Return errors; don't panic in library code

```go
// Avoid
result, _ := db.Query(ctx, query)

// Prefer
result, err := db.Query(ctx, query)
if err != nil {
    return nil, fmt.Errorf("querying users: %w", err)
}
```

## Context Propagation

- Pass `context.Context` as the first parameter to all functions that do I/O
- Respect context cancellation in long-running loops
- Never store contexts in structs

## Concurrency

- Use channels for communication, mutexes for shared state
- Close channels from the sender side only
- Use `sync.WaitGroup` for goroutine lifecycle management
- Check for goroutine leaks — every goroutine must have an exit path
````

### C Sharp

````markdown
---
applyTo: "**/*.cs"
---

# C# Review Guidelines

## Async/Await

- Use `async`/`await` throughout — never `.Result` or `.Wait()` (causes deadlocks)
- Suffix async methods with `Async`
- Use `CancellationToken` for cancellable operations
- Prefer `ValueTask<T>` for hot paths that often complete synchronously

```csharp
// Avoid
public User GetUser(string id) {
    return _db.Users.FindAsync(id).Result;
}

// Prefer
public async Task<User?> GetUserAsync(string id, CancellationToken ct = default) {
    return await _db.Users.FindAsync(new object[] { id }, ct);
}
```

## Safety

- Use `string.IsNullOrWhiteSpace()` for input validation, not just null checks
- Dispose `IDisposable` resources via `using` statements
- Never catch `Exception` without rethrowing or logging — no empty catch blocks
- Use parameterized queries with Entity Framework, never string interpolation
````

---

## Framework-Specific

### React

````markdown
---
applyTo: "**/*.{tsx,jsx}"
---

# React Component Review Guidelines

## Component Design

- Use functional components with hooks — no class components
- Keep components under 200 lines; extract sub-components when larger
- Extract reusable logic into custom hooks (`use*` prefix)
- Co-locate component, styles, and tests in the same directory

## Props & State

- Define TypeScript interfaces for all props
- Use `useState` for local state, context/store for shared state
- Avoid prop drilling beyond 2 levels — use composition or context
- Derive state when possible instead of syncing with `useEffect`

```tsx
// Avoid — syncing state
const [filteredItems, setFilteredItems] = useState(items);
useEffect(() => { setFilteredItems(items.filter(i => i.active)); }, [items]);

// Prefer — derived state
const filteredItems = useMemo(() => items.filter(i => i.active), [items]);
```

## Performance

- Wrap expensive computations in `useMemo`
- Use `useCallback` for functions passed to memoized children
- Use `React.lazy` for route-level code splitting
- Avoid creating objects/arrays in JSX props (triggers unnecessary re-renders)

## Accessibility

- Interactive elements must be keyboard accessible
- Include `aria-label` on icon-only buttons
- Use semantic HTML (`button`, `nav`, `main`) not generic `div` with handlers
````

### Next.js App Router

````markdown
---
applyTo: "**/app/**/*.{ts,tsx}"
---

# Next.js App Router Review Guidelines

## Server vs Client Components

- Default to Server Components — add `"use client"` only when needed
- `"use client"` is needed for: hooks, event handlers, browser APIs
- Never import server-only code into client components
- Push `"use client"` boundary as low as possible in the component tree

## Data Fetching

- Fetch data in Server Components, not in client `useEffect`
- Use `Promise.all()` for parallel data fetches — never sequential awaits
- Wrap async Server Components in `<Suspense>` with meaningful fallbacks
- Set `revalidate` or use `revalidateTag()` for cached data

```tsx
// Avoid — sequential fetches
const user = await getUser(id);
const orders = await getOrders(id);

// Prefer — parallel fetches
const [user, orders] = await Promise.all([getUser(id), getOrders(id)]);
```

## Server Actions

- Validate all inputs with Zod at the top of every Server Action
- Server Actions must check authentication before any data mutation
- Return structured results, not just throwing errors
- Never expose internal error details to the client

## Metadata & SEO

- Every page must export `metadata` or `generateMetadata()`
- Use `next/image` instead of raw `<img>` tags
- Add `alt` text to all images
````

### Next.js Marketing

````markdown
---
applyTo: "**/*.{ts,tsx}"
---

# Next.js Marketing Site Review Guidelines

## SEO & Metadata

- Every page route must export `metadata` or `generateMetadata()`
- Include `title`, `description`, and `openGraph` properties
- Add JSON-LD structured data for key pages (home, product, FAQ)
- Use semantic HTML (`article`, `section`, `nav`, `header`, `footer`)

## Performance

- Use `next/image` with explicit `width`/`height` — never raw `<img>`
- Images above the fold must have `priority={true}`
- Use `<Suspense>` boundaries around async components
- Fetch CMS data with ISR (`revalidate`) not on every request
- Use `Promise.all()` for parallel data fetches

## Component Patterns

- Default to Server Components — add `"use client"` only for interactivity
- Keep client components small (form handlers, animations, dropdowns)
- Use `next/link` for internal navigation — never raw `<a>` for same-site links
- External links: add `rel="noopener noreferrer"` and `target="_blank"`
````

### Django

````markdown
---
applyTo: "**/*.py"
---

# Django Review Guidelines

## Query Safety

- Always use `select_related()` / `prefetch_related()` for related objects
- Never perform queries inside loops — batch or prefetch instead
- Use `.only()` or `.defer()` for large models when you need few fields
- Use `F()` expressions for database-level operations, not Python-level math

```python
# Avoid — N+1 query
for order in Order.objects.all():
    print(order.customer.name)

# Prefer
for order in Order.objects.select_related("customer").all():
    print(order.customer.name)
```

## Security

- All views must have `permission_classes` — never leave empty
- Use `get_object_or_404()` for object lookups (prevents information leaks)
- Validate and sanitize all file uploads (type, size, extension)
- Never put raw user input into `extra()` or `raw()` queries

## Conventions

- Define `__str__()` on all models
- Use `get_absolute_url()` for model URL resolution
- Serialize responses with DRF serializers, never raw dicts
- Use structured logging with `structlog` or `logging` module
````

### Express/Fastify

````markdown
---
applyTo: "**/routes/**/*.{ts,js}"
---

# Express/Fastify API Review Guidelines

## Request Handling

- Validate request body with Zod/Joi before processing
- Use typed request/response interfaces, not `any`
- All route handlers must have error middleware or try-catch
- Return consistent response shape: `{ data, error, meta }`

```typescript
// Avoid
app.post("/users", async (req, res) => {
  const user = await db.user.create({ data: req.body });
  res.json(user);
});

// Prefer
app.post("/users", async (req, res, next) => {
  try {
    const body = CreateUserSchema.parse(req.body);
    const user = await userService.create(body);
    res.json({ data: user, error: null });
  } catch (err) { next(err); }
});
```

## Middleware

- Auth middleware must run before any data access
- Rate limiting on public-facing endpoints
- Request ID middleware for distributed tracing
- CORS configuration must be explicit, not `*` in production

## Error Handling

- Use centralized error middleware, not per-route try-catch when possible
- Never expose stack traces or internal errors in responses
- Log errors with structured format including requestId
````

### Tauri v2

````markdown
---
applyTo: "**/src-tauri/**/*.rs"
---

# Tauri v2 Command Review Guidelines

## Command Safety

- Never use `unwrap()` or `expect()` in `#[tauri::command]` handlers — return `Result<T, String>`
- Validate all parameters received from the frontend at the command boundary
- Check file paths against allowed directories before filesystem access
- Never pass raw user input to `Command::new()` or shell execution

```rust
// Avoid
#[tauri::command]
fn read_file(path: String) -> String {
    std::fs::read_to_string(path).unwrap()
}

// Prefer
#[tauri::command]
fn read_file(path: String, app: tauri::AppHandle) -> Result<String, String> {
    let allowed_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let resolved = allowed_dir.join(&path);
    if !resolved.starts_with(&allowed_dir) {
        return Err("Path traversal denied".into());
    }
    std::fs::read_to_string(resolved).map_err(|e| e.to_string())
}
```

## State Management

- Keep `Mutex` lock scopes as narrow as possible
- Never hold a `Mutex` guard across `.await` points
- Use `tauri::State<Mutex<T>>` for shared mutable state
- Prefer `Arc<RwLock<T>>` when reads vastly outnumber writes

## Capabilities

- Request minimal capabilities in `tauri.conf.json`
- Never enable `shell:allow-execute` without scoping to specific commands
- Restrict `fs` permissions to specific directories
- Log IPC calls for security audit trail — but never log sensitive data
````

### Angular

````markdown
---
applyTo: "**/*.{ts,html,scss,css}"
---

# Angular Review Guidelines

## Component Architecture

- One component per file — no multi-component files
- Use OnPush change detection for all components
- Prefer signals over RxJS BehaviorSubject for local state
- Use standalone components — avoid NgModules for new code

## Template Safety

- Never use `[innerHTML]` with unsanitized user input
- Use Angular's built-in pipes for display formatting
- Prefer `@if`/`@for` control flow over `*ngIf`/`*ngFor`
- Always define `trackBy` for `@for` loops

## RxJS

- Unsubscribe from all subscriptions — use `takeUntilDestroyed()` or `async` pipe
- Use `switchMap` for requests that cancel previous (search, navigation)
- Use `concatMap` for requests that must execute in order (form submissions)
- Never nest `.subscribe()` calls — compose with operators
````

---

## Domain-Specific

### API Routes

````markdown
---
applyTo: "**/api/**/*.{ts,js,py}"
---

# API Route Review Guidelines

## Input Validation

- Validate ALL request inputs at the handler boundary (body, params, query)
- Use schema validation (Zod, Joi, Pydantic) — not manual checks
- Return 400 with specific field errors, not generic "invalid request"
- Reject unexpected fields — don't silently ignore them

## Authentication & Authorization

- Every mutating endpoint must verify authentication
- Check authorization (role/permission) after authentication
- Use middleware for auth — don't repeat checks in each handler
- Never trust client-side role claims without server verification

## Response Shape

- Use consistent response envelope: `{ data, error, meta }`
- Include pagination metadata for list endpoints (`total`, `page`, `limit`)
- Set appropriate HTTP status codes (201 for create, 204 for delete)
- Never expose internal IDs, stack traces, or database errors in responses
````

### Database/ORM

````markdown
---
applyTo: "**/{models,entities,repositories,prisma,migrations}/**/*.{ts,py,rs}"
---

# Database & ORM Review Guidelines

## Query Safety

- Never interpolate user input into raw SQL — use parameterized queries
- Use ORM methods for standard CRUD — raw SQL only when necessary
- Wrap multi-step mutations in transactions
- Set query timeouts for all database calls

## Performance

- Add `select_related`/`prefetch_related` (Django) or `include` (Prisma) for relations
- Never query inside loops — batch with `WHERE IN` or equivalent
- Use pagination for all list queries — never unbounded `SELECT *`
- Add database indexes for columns used in WHERE, ORDER BY, JOIN

## Migrations

- Migrations must be backwards-compatible (can run while old code still serves)
- Never delete columns in the same deploy that removes code using them
- Add NOT NULL with a DEFAULT, not bare NOT NULL on existing columns
- Test migrations against a copy of production data volume
````

### Security-Critical Paths

````markdown
---
applyTo: "**/{auth,security,payment,billing,admin}/**/*.{ts,js,py,rs,go}"
---

# Security-Critical Path Review Guidelines

## Authentication

- Hash passwords with bcrypt/argon2 — never MD5/SHA for passwords
- Use constant-time comparison for token/hash comparison
- Implement rate limiting on login and password reset endpoints
- Session tokens must be cryptographically random (min 128 bits)

## Authorization

- Check permissions on every request — never cache authorization decisions
- Use RBAC or ABAC — not ad-hoc `if (user.role === 'admin')` checks
- Log all authorization failures with user ID and attempted resource
- Deny by default — explicitly grant access, don't explicitly deny

## Sensitive Data

- Never log passwords, tokens, API keys, or PII
- Mask credit card numbers (show last 4 digits only)
- Use encryption at rest for PII columns
- Set appropriate `Secure`, `HttpOnly`, `SameSite` flags on auth cookies

## Payment

- All payment operations must be idempotent (use idempotency keys)
- Validate amounts server-side — never trust client-sent prices
- Log all payment events with correlation IDs for audit trail
- Use `Decimal` types for money — never floating point
````

### Testing

````markdown
---
applyTo: "**/*.{test,spec}.{ts,tsx,js,jsx}"
---

# Test Review Guidelines

## Test Quality

- Each test must test ONE behavior — not multiple assertions of unrelated things
- Test names should describe the scenario: `should return 404 when user not found`
- Tests must be independent — no shared mutable state between tests
- Use factories/builders for test data, not copy-pasted object literals

```typescript
// Avoid
test("user", async () => {
  const user = await createUser({ name: "test", email: "test@example.com", role: "admin" });
  expect(user.name).toBe("test");
  expect(await getUser(user.id)).toBeTruthy();
  await deleteUser(user.id);
  expect(await getUser(user.id)).toBeNull();
});

// Prefer
test("should find user by ID after creation", async () => {
  const user = await UserFactory.create();
  const found = await getUser(user.id);
  expect(found).toMatchObject({ id: user.id, name: user.name });
});
```

## Mocking

- Mock external services (APIs, databases) — not internal logic
- Use dependency injection to make mocking straightforward
- Reset all mocks in `beforeEach` or `afterEach`
- Prefer integration tests with real database over mocked queries

## Coverage

- New features must include tests covering main path and error cases
- Bug fixes should include a regression test
- Don't test framework internals or third-party library behavior
````

### Accessibility

````markdown
---
applyTo: "**/*.{tsx,jsx,html}"
---

# Accessibility Review Guidelines

## Semantic HTML

- Use `button` for actions, `a` for navigation — not `div` with `onClick`
- Use heading hierarchy (`h1` > `h2` > `h3`) — don't skip levels
- Use `nav`, `main`, `article`, `section` for document structure
- Use `label` elements associated with form inputs via `htmlFor`

## Keyboard & Focus

- All interactive elements must be reachable via Tab key
- Custom components need appropriate `role`, `tabIndex`, and keyboard handlers
- Focus must be visible — never `outline: none` without a replacement
- Modal dialogs must trap focus and return focus on close

## ARIA

- Use ARIA attributes only when native HTML semantics are insufficient
- Icon-only buttons must have `aria-label`
- Dynamic content updates need `aria-live` regions
- Form errors must be associated with inputs via `aria-describedby`

## Visual

- Text contrast ratio: minimum 4.5:1 (WCAG AA)
- Don't use color alone to convey information
- Support `prefers-reduced-motion` for animations
- Minimum touch target size: 44x44px
````

### MCP Server

````markdown
---
applyTo: "**/src/**/*.ts"
---

# MCP Server Review Guidelines

## Protocol Compliance

- Tool parameter schemas must match Zod validation in handlers
- Return structured content arrays, not raw strings
- Use `isError: true` for tool execution failures
- Include `_meta` in responses when progress tracking is needed

```typescript
// Avoid
return { content: [{ type: "text", text: result }] };

// Prefer (for errors)
return { content: [{ type: "text", text: errorMessage }], isError: true };
```

## Transport Safety

- Never use `console.log` on stdio transport — it corrupts the JSON-RPC stream
- Use stderr for debug logging: `console.error()`
- Validate all tool inputs at handler entry — don't trust client schemas
- Set timeouts on all external calls (HTTP, DB, file I/O)

## Security

- Sanitize file paths — prevent directory traversal
- Never interpolate user input into shell commands
- Don't expose API keys, tokens, or credentials in error messages
- Validate URL schemes before making HTTP requests (allow http/https only)

## Resource Management

- Close connections in tool handler finally blocks
- Implement graceful shutdown handling
- Respect `AbortSignal` for cancellation
- Log tool invocations with duration and token usage
````

### CI/CD Workflows

````markdown
---
applyTo: "**/.github/workflows/**/*.{yml,yaml}"
---

# CI/CD Workflow Review Guidelines

## Security

- Pin actions to full commit SHA, not tags: `uses: actions/checkout@abc123`
- Never expose secrets in logs — use masking for dynamic secrets
- Set `permissions` explicitly — don't rely on defaults
- Use `GITHUB_TOKEN` with minimum required permissions

```yaml
# Avoid
uses: actions/checkout@v4

# Prefer
uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1
```

## Reliability

- Set `timeout-minutes` on all jobs to prevent hung workflows
- Use `concurrency` groups to prevent duplicate runs
- Cache dependencies (`actions/cache`) for faster builds
- Use matrix strategies for multi-version testing

## Best Practices

- Keep workflows DRY — use reusable workflows for shared steps
- Separate CI (test/lint) from CD (deploy) workflows
- Use environment protection rules for production deployments
- Add `workflow_dispatch` trigger for manual runs when needed
````

### Docker/Infrastructure

````markdown
---
applyTo: "**/Dockerfile*"
---

# Dockerfile Review Guidelines

## Security

- Never use `latest` tag for base images — pin specific versions
- Don't run as root — add `USER nonroot` after installing dependencies
- Don't copy secrets or `.env` files into the image
- Use multi-stage builds to exclude build tools from final image

```dockerfile
# Avoid
FROM node:latest
COPY . .
RUN npm install

# Prefer
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY src/ ./src/

FROM node:20-alpine
USER nonroot
COPY --from=builder /app /app
CMD ["node", "src/index.js"]
```

## Performance

- Order instructions from least to most frequently changing (for cache efficiency)
- Copy `package.json`/`requirements.txt` before source code
- Use `.dockerignore` to exclude `node_modules`, `.git`, test files
- Minimize layers — combine related `RUN` commands with `&&`

## Health

- Include `HEALTHCHECK` instruction for container orchestration
- Set `STOPSIGNAL` if the app needs graceful shutdown
- Document exposed ports with `EXPOSE`
````

### GraphQL

````markdown
---
applyTo: "**/*.{ts,js,graphql,gql}"
---

# GraphQL Review Guidelines

## Schema Design

- Use nullable fields by default — non-null only when guaranteed
- Implement cursor-based pagination for list fields (not offset)
- Use input types for mutations, not individual arguments
- Name mutations as verbs: `createUser`, `updateOrder`, `deleteComment`

## Resolver Safety

- Every resolver must handle authentication before data access
- Use DataLoader for batching — never query inside a field resolver loop
- Set query depth and complexity limits to prevent abuse
- Validate mutation inputs at resolver entry

```typescript
// Avoid — N+1 in resolver
const resolvers = {
  Order: {
    customer: (order) => db.customer.findUnique({ where: { id: order.customerId } })
  }
};

// Prefer — DataLoader
const resolvers = {
  Order: {
    customer: (order, _, { loaders }) => loaders.customer.load(order.customerId)
  }
};
```

## Error Handling

- Use structured error codes, not just messages
- Never expose internal errors (SQL, stack traces) in GraphQL responses
- Use `extensions` field for machine-readable error metadata
````

### State Management

````markdown
---
applyTo: "**/store/**/*.{ts,tsx}"
---

# State Management Review Guidelines

## Store Design

- Keep stores small and focused — one concern per store
- Separate UI state (modals, selection) from domain state (data, entities)
- Derive computed values with selectors, don't duplicate state
- Use immer or immutable patterns for state updates

## Actions & Side Effects

- Name actions as events, not setters: `userLoggedIn` not `setUser`
- Keep side effects (API calls) in middleware/thunks, not reducers
- Handle loading, success, and error states for async operations
- Use optimistic updates for better UX, with rollback on failure

## Performance

- Subscribe to specific slices of state, not the entire store
- Use selectors with memoization for expensive computations
- Batch related state updates to prevent unnecessary re-renders
- Clean up subscriptions when components unmount
````
