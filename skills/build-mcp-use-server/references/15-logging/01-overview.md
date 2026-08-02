# Logging Overview

*Read this when configuring request logging or sending log messages to clients.*

v2 logging has two dimensions:

| Dimension | Where | What |
|-----------|-------|------|
| **Server request logging** | stdout/configured sink | Request timings, MCP operations, errors (infrastructure-level) |
| **Client log messages** | Sent via `ctx.sendLog()` | Tool-emitted logs delivered to the client (application-level) |

## Server Request Logging

Configure at server startup:

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  logging: {
    enabled: true,       // default
    level: "info",       // "info" | "debug" | "trace"
  },
});
```

**Levels:**
- `"info"`: Request summary + MCP method names (default; minimal overhead)
- `"debug"`: Info + input/output summaries
- `"trace"`: Full request/response payloads and headers

Override via environment: `MCP_USE_LOG_LEVEL=debug`

This logging is not delivered to clients; it appears in the server process's stdout/stderr or configured logging sink.

## Client Log Messages

Within a tool callback, send structured log messages to the client:

```typescript
ctx.sendLog(level, data, logger?)
```

Clients receive these as notifications during the request. Modern clients must explicitly opt in (request-level log level); old clients ignore them.

**Levels:** `"debug"` | `"info"` | `"notice"` | `"warning"` | `"error"` | `"critical"` | `"alert"` | `"emergency"`

See `references/15-logging/02-ctx-sendlog.md` for details.

## Key distinction

- **Server logging** is infrastructure diagnostics (when did this request arrive, how fast).
- **Client logging** is application insight (what did this tool do, what warnings occurred).

Use both: server logging for ops; client logging for user-facing context.
