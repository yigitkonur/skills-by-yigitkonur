# Error handling strategy for production

*Read this when designing tool error responses and runtime exception handling.*

In production, errors must be **informative to the caller** (model or client) without exposing internal implementation details. Return structured errors from tool callbacks; let middleware handle uncaught exceptions.

## Tool-level error responses

Return `{ isError: true, content: [...] }` from your tool callback. The SDK sends this to the client as a failed tool result; the model can retry or escalate.

```typescript
server.tool(
  {
    name: "fetch-user",
    description: "Fetch a user by ID",
    inputSchema: z.object({ id: z.string() }),
    outputSchema: z.object({ name: z.string(), email: z.string() }),
  },
  async ({ id }, ctx) => {
    try {
      const user = await db.users.get(id);
      if (!user) {
        return {
          isError: true,
          content: [{ 
            type: "text", 
            text: `User not found: ${id}` 
          }],
        };
      }
      return {
        content: [{ 
          type: "text", 
          text: JSON.stringify(user) 
        }],
        structuredContent: { name: user.name, email: user.email },
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      return {
        isError: true,
        content: [{ 
          type: "text", 
          text: `Failed to fetch user: ${message}` 
        }],
      };
    }
  }
);
```

**Rules:**
- Return `isError: true` for expected failures (not found, validation, permission denied, timeout).
- Include a human-readable message in the content block.
- **Prefer returning `{ isError: true, content: [...] }` over throwing.** A thrown error IS caught by the SDK's `tools/call` handler — it does not become a raw HTTP 500 and does not bypass the MCP response layer — but the SDK converts it to `{ content: [{ type: "text", text: error.message }], isError: true }` using the *raw, unsanitized* `error.message`. An explicit return gives you control to redact secrets/internals before the message reaches the client; a throw does not.
- Log the full exception internally (see middleware section below) without exposing stack traces to the client.

## Middleware exception handling

Uncaught exceptions in tool callbacks are caught by the SDK and returned as `{ isError: true }` automatically, using the raw error message (see above). To inspect or log the result after the handler completes, use an event listener — `:complete` is only valid on `server.on()`, not `server.use()`, and the result arrives as the listener's **second parameter**, never as a field on `ctx`:

```typescript
server.on("mcp:tools/call:complete", (ctx, result) => {
  if (result.isError) {
    console.error(`Tool ${ctx.params.name} failed:`, result.content);
  }
});
```

Event listeners cannot block, override, or mutate the result — only observe:

```typescript
server.on("mcp:tools/call:complete", async (ctx, result) => {
  if (result.isError) {
    // Log to external service (Sentry, DataDog, etc.)
    await logToMonitoring({
      tool: ctx.params.name,
      error: result.content,
      timestamp: new Date(),
    });
  }
});
```

To block or mutate a result before it's returned, use `server.use()` on the exact method and capture `next()`'s return value instead:

```typescript
server.use("mcp:tools/call", async (ctx, next) => {
  const result = await next();
  if (result.isError) {
    console.error(`Tool ${ctx.params.name} failed:`, result.content);
  }
  return result;
});
```

## HTTP errors vs. MCP errors

- **MCP operation error** (tool call fails): Return `{ isError: true, content: [...] }` from callback — SDK wraps it in the MCP error envelope.
- **HTTP transport error** (auth, payload too large, server crash): SDK returns HTTP 400/401/413/500 with an MCP error envelope or plain text.
- **Custom HTTP route error**: Your handler decides; use `ctx.status(500)` + `ctx.text("error message")` for Hono routes.

Example:

```typescript
// Custom health check that can fail
server.get("/health", (c) => {
  if (!isReady) {
    return c.json({ status: "not-ready" }, 503);
  }
  return c.json({ status: "ok" });
});
```

Hono's `c.status(code)` sets the status for a later `c.body()`/`c.text()` call and returns `void` — it is not chainable with `.json()`. Pass the status as `c.json(data, statusCode)` instead.

## Timeout handling

The MCP transport layer has no built-in timeout. If a tool call hangs:

- **Local dev**: Press Ctrl+C to abort the process; `ctx.signal` fires.
- **Production**: Platform timeout (Vercel 25s, Cloud Run default 900s) terminates the request. Return errors promptly; use `ctx.signal.addEventListener("abort", ...)` to detect cancellation.

```typescript
async ({ url }, ctx) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    const response = await fetch(url, { signal: controller.signal });
    // …
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") {
      return {
        isError: true,
        content: [{ type: "text", text: "Request timed out" }],
      };
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}
```

## Secrets in errors

**Never expose secrets in error messages.** Sanitize API responses before returning:

```typescript
catch (err) {
  const message = err instanceof Error ? err.message : String(err);
  const sanitized = message
    .replace(/Bearer\s+\S+/g, "Bearer [REDACTED]")
    .replace(/sk_\w+/g, "[REDACTED]");
  return {
    isError: true,
    content: [{ type: "text", text: sanitized }],
  };
}
```

Better: log the full error to a real server-side sink; return a generic message to the client:

```typescript
catch (err) {
  console.error(`[${ctx.params?.name ?? "tool"}] execution failed:`, err); // Or Sentry/DataDog/etc.
  return {
    isError: true,
    content: [{ type: "text", text: "Tool execution failed" }],
  };
}
```

`ctx.sendLog(level, data, logger?)` sends an MCP `notifications/message` notification **to the connected client**, not to a server-side log — never route sensitive errors or secrets through it. It also fires unconditionally: unlike the SDK's own internal logging path (which checks the client's `logging/setLevel` threshold and the server's declared `logging` capability before sending), `ctx.sendLog()` calls the notify transport directly and does not filter by level. Use it only for status updates the client should see (see `references/14-notifications/`).

## Monitoring and alerting

Use MCP event listeners + external observability to monitor production errors. The completed result arrives as the listener's second parameter, not `ctx.result`. `isError` only exists on `tools/call`, `resources/read`, and `prompts/get` results (not on the `*/list` array results), so target the exact method rather than the `mcp:*:complete` wildcard when checking it:

```typescript
server.on("mcp:tools/call:complete", async (ctx, result) => {
  if (result.isError) {
    await metrics.recordError({
      tool: ctx.params.name,
      timestamp: Date.now(),
    });
  }
});
```

See `references/15-logging/` for structured logging and `references/25-deploy/` for platform-specific monitoring integrations.
