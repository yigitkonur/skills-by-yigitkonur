# Error strategy

Two ways to fail in a tool handler:

| Way | When | Effect on client |
|---|---|---|
| `return error("...")` | Expected failure (not-found, validation, rate-limit, auth-denied) | Tool result with `isError: true`, plain message — model can recover |
| `throw err` | Unexpected failure (DB down, null deref, network blew up) | Transport-level error; client retries or surfaces as crash |

Use the wrong one and the client either treats a real bug as "tool returned not-found" or treats expected business errors as "the server crashed".

For helper semantics (`error()` vs `text()` for failures), see `05-responses/07-error-handling.md`.

## Decision table

| Situation | Use |
|---|---|
| Resource not found | `error("User not found")` |
| Input failed business validation (email taken, dates inverted) | `error("Email already in use")` |
| Rate limit hit | `error("Rate limit exceeded. Try again in 60s.")` |
| Auth missing or invalid scope | `error("Unauthorized: missing 'admin' scope")` |
| External API returned 4xx that maps to user mistake | `error(...)` |
| External API returned 5xx | `throw` (let it retry) |
| DB connection lost | `throw` |
| Null deref / unhandled type | `throw` (it's a bug) |
| `JSON.parse` of trusted internal data failed | `throw` |

Rule: if the model can recover by changing its arguments or asking the user something, use `error()`. If only a human operator can fix it, `throw`.

## Wrap handlers with one shared catcher

Don't sprinkle try/catch across every tool. Wrap once:

```typescript
import { error } from "mcp-use/server";
import { Logger } from "mcp-use";

const logger = Logger.get("tool-errors");

class UserError extends Error {
  constructor(message: string, public readonly code?: string) {
    super(message);
  }
}

function handle<T extends (...a: any[]) => Promise<any>>(name: string, fn: T): T {
  return (async (...args: Parameters<T>) => {
    try {
      return await fn(...args);
    } catch (err) {
      if (err instanceof UserError) {
        return error(err.code ? `${err.code}: ${err.message}` : err.message);
      }
      logger.error(`[${name}] unexpected`, err as Error);
      throw err; // unexpected → propagate
    }
  }) as T;
}

server.tool(
  { name: "get-user", schema: z.object({ id: z.string() }) },
  handle("get-user", async ({ id }) => {
    const user = await db.findUser(id);
    if (!user) throw new UserError("User not found", "NOT_FOUND");
    return object(user);
  })
);
```

`UserError` → `error()`. Anything else logs and throws — the transport handles it.

## Logging unexpected errors

Always log unexpected errors with context (tool name, sanitized inputs, request ID if you have tracing). Without context, you'll see hundreds of identical stack traces and no way to correlate.

```typescript
logger.error(`[${name}] failed`, {
  err: (err as Error).message,
  stack: (err as Error).stack,
  input: redact(args[0]), // never log raw secrets
});
```

For tool-level logs visible to the client, use `ctx.log("error", ...)` instead — see `15-logging/`. The Logger goes to your log aggregator; `ctx.log` reaches the model.

## Auth errors

Auth failures are *expected* — the model can present a re-auth prompt or back off. Don't throw:

```typescript
server.tool(
  { name: "delete-user", schema: z.object({ id: z.string() }) },
  async ({ id }, ctx) => {
    if (!ctx.auth?.scopes.includes("admin")) {
      return error("Unauthorized: 'admin' scope required");
    }
    // ...
  }
);
```

For HTTP-layer auth (custom routes, not MCP tools), middleware can reply with a real 401:

```typescript
server.use("/api/admin/*", async (c, next) => {
  if (!c.req.header("authorization")) return c.json({ error: "unauthorized" }, 401);
  await next();
});
```

See `08-server-config/05-middleware-and-custom-routes.md`.

## Retry vs fail

Retry inside the handler only when the failure is transient and idempotent:

| Operation | Retry? |
|---|---|
| `GET` to external API (network glitch) | Yes — bounded retry with backoff |
| `POST` to a non-idempotent API | No — let the model decide |
| DB connection acquired but query failed | No — propagate |
| `INSERT` that may have already succeeded | No — return `error()` describing the ambiguity |

If you do retry inside a handler, cap attempts (3) and total wait (a few seconds). Long retries hold the request open and the orchestrator may shut you down mid-loop.

## Don't

- Don't return `text("Error: ...")` for failures — the model treats it as a normal answer. Use `error()`.
- Don't `error()` on bugs — they're invisible. Throw, and let logging surface them.
- Don't include stack traces, file paths, or secrets in `error()` messages — the model context (and any user-visible transcript) sees them.
- Don't `console.log` from production handlers; use the built-in `Logger` so production log aggregators can ingest structured records (see `15-logging/`).
