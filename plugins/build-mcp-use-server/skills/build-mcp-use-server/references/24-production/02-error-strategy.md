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
    outputSchema: z.object({ name: string; email: string }),
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
- **Do NOT throw** — exceptions become raw HTTP 500 errors that bypass the MCP response layer.
- Log the full exception internally (see middleware section below) without exposing stack traces to the client.

## Middleware exception handling

Uncaught exceptions in tool callbacks are caught by the SDK and returned as `{ isError: true }` automatically. To add custom logging:

```typescript
server.use("mcp:tools/call:complete", async (ctx) => {
  if (ctx.result.isError) {
    console.error(`Tool ${ctx.params.name} failed:`, ctx.result.content);
  }
});
```

Or use an event listener (cannot block, only observe):

```typescript
server.on("mcp:tools/call:complete", async (ctx) => {
  if (ctx.result.isError) {
    // Log to external service (Sentry, DataDog, etc.)
    await logToMonitoring({
      tool: ctx.params.name,
      error: ctx.result.content,
      timestamp: new Date(),
    });
  }
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
    return c.status(503).json({ status: "not-ready" });
  }
  return c.json({ status: "ok" });
});
```

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
    if (err.name === "AbortError") {
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
  const sanitized = err.message
    .replace(/Bearer\s+\S+/g, "Bearer [REDACTED]")
    .replace(/sk_\w+/g, "[REDACTED]");
  return {
    isError: true,
    content: [{ type: "text", text: sanitized }],
  };
}
```

Better: Log the full error to an internal service; return a generic message to the client:

```typescript
catch (err) {
  await ctx.sendLog("error", {
    tool: ctx.params.name,
    error: err,
    requestState: ctx.requestState,
  }, "mcp-server");
  return {
    isError: true,
    content: [{ type: "text", text: "Tool execution failed" }],
  };
}
```

## Monitoring and alerting

Use MCP event listeners + external observability to monitor production errors:

```typescript
server.on("mcp:*", async (ctx) => {
  if (ctx.result?.isError) {
    await metrics.recordError({
      method: ctx.request?.method,
      path: ctx.request?.path,
      timestamp: Date.now(),
    });
  }
});
```

See `references/15-logging/` for structured logging and `references/25-deploy/` for platform-specific monitoring integrations.
