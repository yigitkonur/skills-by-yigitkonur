# Middleware

*Read this to intercept MCP operations (tools/list, tools/call, resources/read, etc.), use middleware utilities for validation, or listen to read-only events.*

## MCP Middleware

MCP middleware runs at the operation level (tool calls, resource reads, prompt requests, etc.), **not** at the HTTP level. Each pattern matches a specific MCP operation.

```typescript
server.use("mcp:tools/call", async (ctx, next) => {
  console.log(`Calling tool: ${ctx.params.name}`);
  const result = await next();
  return result;
});
```

### MCP Middleware Patterns

| Pattern | Matches | ctx.params | Return Type |
|---------|---------|-----------|-------------|
| `mcp:tools/list` | `tools/list` request | SDK list params | Tool descriptor array |
| `mcp:tools/call` | `tools/call` request | SDK tool-call params | Tool handler result |
| `mcp:resources/list` | `resources/list` request | SDK list params | Resource descriptor array |
| `mcp:resources/read` | `resources/read` request | SDK resource-read params | Resource handler result |
| `mcp:prompts/list` | `prompts/list` request | SDK list params | Prompt descriptor array |
| `mcp:prompts/get` | `prompts/get` request | SDK prompt-get params | Prompt handler result |
| `mcp:*` | Every MCP operation | Pattern-dependent | (pass-through only) |

Completion observers use `server.on()` with a `:complete` event pattern; `server.use()` does not accept `:complete`.

```typescript
const startedAt = new Map<string, number>();
server.on("mcp:tools/call", (ctx) => {
  startedAt.set(ctx.params.name, Date.now());
});
server.on("mcp:tools/call:complete", (ctx, result) => {
  const start = startedAt.get(ctx.params.name) ?? Date.now();
  console.log(`Tool ${ctx.params.name} took ${Date.now() - start}ms`);
});
```

### Middleware Context

Each middleware receives a context object with:
- `method`: Matched MCP operation
- `params`: Operation-specific parameters (tool name, resource URI, etc.)
- `auth`: SDK `AuthInfo` when authentication is present
- `request`: Hono request object
- `session`: Optional `{ sessionId }`
- `state`: Shared `Map<string, unknown>`
- Standard Hono context properties (get/set/var, env, executionCtx, etc.)

## HTTP Middleware (Hono)

Add HTTP middleware for routes outside the MCP endpoint using standard Hono syntax.

```typescript
// Global middleware
server.use(async (c, next) => {
  c.header("x-server", "my-api");
  await next();
});

// Path-specific middleware
server.use("/health", async (c, next) => {
  c.header("cache-control", "max-age=60");
  await next();
});
```

See `06-custom-routes.md` for adding custom routes.

## Middleware Utilities

mcp-use exports utilities for common validation scenarios:

### hostValidationMiddleware

Validates `Host` header against an allowlist.

```typescript
import { hostValidationMiddleware } from "mcp-use";

server.use(hostValidationMiddleware(["api.example.com", "localhost"]));
// Rejects requests with Host header not on allowlist
```

See `04-dns-rebinding-and-host-validation.md`.

### originValidationMiddleware

Validates `Origin` header (non-GET/HEAD only) against an allowlist.

```typescript
import { originValidationMiddleware } from "mcp-use";

server.use(originValidationMiddleware(["https://app.example.com"]));
// Rejects POST/PUT/DELETE with Origin not in allowlist
```

See `03-cors-and-allowed-origins.md`.

### jsonBodyMiddleware

Parses JSON request body once and stores in request context for reuse.

```typescript
import { jsonBodyMiddleware } from "mcp-use";

server.use(jsonBodyMiddleware());
// Body parsed; available via ctx.var.body or context bag
```

### composeMiddleware

`composeMiddleware()` is an internal-facing MCP middleware-chain utility. It accepts registered MCP middleware entries, an MCP method, and a terminal handler; use `server.use()` for normal registration.

### composeFetch

Wraps `server.fetch` with additional fetch middleware handlers (for mounting in fetch-first runtimes).

```typescript
import { composeFetch, hostValidationMiddleware } from "mcp-use";

const validatedFetch = composeFetch(
  server.fetch,
  hostValidationMiddleware(["api.example.com"]),
);

export default validatedFetch;
```

## Event Listeners (Read-Only)

Use `server.on()` to listen to MCP events without blocking or modifying results. Listeners cannot throw (errors are logged).

```typescript
server.on("mcp:tools/call", async (ctx) => {
  console.log(`Tool called: ${ctx.params.name}`);
  // Cannot modify result; cannot throw
});
```

Event patterns match middleware patterns (`mcp:tools/call`, `mcp:resources/read`, etc.). Use listeners for logging, metrics, or side effects that don't affect the response.

## Stacking: Order Matters

Middleware is called in registration order.

```typescript
server.use("mcp:tools/call", async (ctx, next) => {
  console.log("1. Before");
  const result = await next();
  console.log("3. After");
  return result;
});

server.use("mcp:tools/call", async (ctx, next) => {
  console.log("2. Nested before");
  const result = await next();
  console.log("4. Nested after");
  return result;
});

// Call order: 1 → 2 → handler → 4 → 3
```

## Error Handling in Middleware

Throw to reject a request (converts to error response). Catch to intercept errors from nested handlers.

```typescript
server.use("mcp:tools/call", async (ctx, next) => {
  if (ctx.params.name === "dangerous_tool") {
    throw new Error("Tool not allowed");
  }
  try {
    return await next();
  } catch (err) {
    console.error(`Tool ${ctx.params.name} failed:`, err);
    throw err;  // Re-throw to client
  }
});
```

For authenticated access control, check `ctx.auth` and throw 403 if needed.
