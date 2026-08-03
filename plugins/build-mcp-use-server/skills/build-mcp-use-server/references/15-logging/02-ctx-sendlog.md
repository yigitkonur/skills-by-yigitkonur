# ctx.sendLog()

*Read this when emitting structured log messages to the client during tool execution.*

Send a log message to the client on the originating request's response stream.

## Signature

```typescript
ctx.sendLog(
  level: "debug" | "info" | "notice" | "warning" | "error" | "critical" | "alert" | "emergency",
  data: unknown,
  logger?: string
): Promise<void>
```

## Parameters

- **level** (string): Severity level. Eight levels from debug to emergency (syslog-compatible).
- **data** (unknown): Log message or object. Sent as-is; typically a string or JSON-serializable object.
- **logger** (optional string): Logger name, e.g., `"database"`, `"auth"`, `"processor"`. Helps clients filter and categorize logs.

## Usage

```typescript
export const queryDatabase = server.tool(
  { name: "query_db", inputSchema: z.object({ sql: z.string() }) },
  async ({ sql }, ctx) => {
    await ctx.sendLog("info", "Query started", "database");

    try {
      const result = await db.query(sql);
      await ctx.sendLog("debug", { rows: result.length }, "database");
      return {
        content: [{ type: "text", text: JSON.stringify(result) }],
      };
    } catch (error) {
      await ctx.sendLog(
        "error",
        { message: String(error), sql },
        "database"
      );
      return {
        isError: true,
        content: [{ type: "text", text: String(error) }],
      };
    }
  }
);
```

## Levels Guide

| Level | Use when |
|-------|----------|
| `"debug"` | Detailed tracing for developers (lowest priority) |
| `"info"` | General informational messages |
| `"notice"` | Notable but non-error events |
| `"warning"` | Potentially harmful situations |
| `"error"` | Errors that don't stop execution |
| `"critical"` | Severe errors |
| `"alert"` | Action needed immediately |
| `"emergency"` | System unusable (highest priority) |

## Key points

- **Must await before return.** Logs are sent on the request's response stream; once your callback returns, the HTTP response ends.
- **Not filtered by `logging/setLevel`.** A client may call `logging/setLevel` to request a minimum severity threshold, and the request succeeds (mcp-use always declares the `logging` capability). But `ctx.sendLog()` sends every call over the wire unconditionally — it does not check that threshold before sending. If you need to throttle by severity, compare against your own level before calling `ctx.sendLog()`; do not rely on the client's requested level being honored server-side.
- **Client-side display is up to the client.** Once delivered, a client UI may still choose to hide low-severity messages locally. Clients without log support simply ignore `notifications/message`.
- **No guaranteed delivery.** Logs are one-way notifications; if the connection drops, logs are lost.
- **Namespaced context.** Use the `logger` parameter to group related logs (e.g., all database logs under `"database"`).

See also: `ctx.sendNotification()` for custom events, `ctx.reportProgress()` for progress updates.
