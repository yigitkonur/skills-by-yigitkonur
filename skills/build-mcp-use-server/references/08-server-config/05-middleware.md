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
| `mcp:*` | Every MCP operation | Pattern-dependent | (pass-through only; must call `next()` or throw — cannot inspect/replace the typed result) |

`server.use()` accepts only these 6 exact patterns plus `mcp:*` (`McpMiddlewarePattern`). `server.on()` additionally accepts **group wildcards** — `mcp:tools/*`, `mcp:resources/*`, `mcp:prompts/*` — that match every method under that prefix; these group forms are event-listener-only and are rejected by `server.use()`.

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
- `session`: Optional `{ sessionId }` transport metadata for the current request. It is not durable identity, server-side storage, or a reason to add session affinity; key policy/state by verified user, API key, or another explicit external identifier.
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

## Fetch Middleware Utilities

`hostValidationMiddleware()`, `originValidationMiddleware()`, and `jsonBodyMiddleware()` use the Fetch signature `(request, next)`, not Hono's `(context, next)`. Do not pass them to `server.use()`. Use constructor configuration for an `MCPServer`, or `composeFetch()` when you own a Fetch boundary.

### Host and Origin validation

Prefer server configuration so validation applies consistently to the MCP endpoint and custom routes:

```typescript
const server = new MCPServer({
  name: "api",
  version: "1.0.0",
  allowedHosts: ["api.example.com", "localhost"],
  allowedOrigins: ["app.example.com"],
});
```

`allowedOrigins` uses the same safe-method behavior as the built-in Origin validation policy: `GET`/`HEAD` remain available for view assets, while unsafe methods are checked. See `03-cors-and-allowed-origins.md` and `04-dns-rebinding-and-host-validation.md`.

### Custom Fetch composition

Use the exported middleware values only around a Fetch terminal:

```typescript
import {
  composeFetch,
  hostValidationMiddleware,
  originValidationMiddleware,
} from "mcp-use";

const validatedFetch = composeFetch(
  server.fetch,
  hostValidationMiddleware(["api.example.com", "localhost"]),
  originValidationMiddleware(["app.example.com"]),
);

export default validatedFetch;
```

Pass `false` as the second `originValidationMiddleware()` argument only when `GET`/`HEAD` must also have an allowed Origin.

### jsonBodyMiddleware

`jsonBodyMiddleware()` parses an `application/json` request once and stores it in a per-`Request` `WeakMap`-backed bag. Invalid JSON short-circuits with `400 "Invalid JSON"`.

mcp-use already mounts this middleware internally. Add it only to an outer custom Fetch pipeline that must inspect JSON before `server.fetch` runs:

```typescript
import { composeFetch, getRequestBag, jsonBodyMiddleware } from "mcp-use";

const inspectJson = async (request: Request, next: () => Promise<Response>) => {
  const parsed = getRequestBag(request).parsedBody;
  console.log("Parsed request:", parsed);
  return next();
};

export default composeFetch(
  server.fetch,
  jsonBodyMiddleware(),
  inspectJson,
);
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

Event patterns match middleware patterns (`mcp:tools/call`, `mcp:resources/read`, etc.) plus the group wildcards `mcp:tools/*`, `mcp:resources/*`, `mcp:prompts/*` (event-only — not valid for `server.use()`). Use listeners for logging, metrics, or side effects that don't affect the response.

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
