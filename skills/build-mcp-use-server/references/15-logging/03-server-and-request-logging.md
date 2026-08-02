# Server and Request Logging

*Read this when configuring server-level request logging.*

Server logging is infrastructure diagnostics: request arrival, method invocations, timing, errors. Configured at server startup and emitted to stdout/process logs, not delivered to clients.

## Configuration

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  logging: {
    enabled: true,       // Enable/disable logging
    level: "info",       // "info" | "debug" | "trace"
  },
});
```

**Default:** Enabled at `"info"` level.

## Levels

| Level | Output | Overhead |
|-------|--------|----------|
| `"info"` | One-line request summary + MCP method name (e.g., `tools/call`) | Minimal |
| `"debug"` | Info level + compact input/output summaries | Low |
| `"trace"` | Debug + full request/response payloads, headers | High |

## Environment Override

Set `MCP_USE_LOG_LEVEL` to override config:

```bash
MCP_USE_LOG_LEVEL=trace node server.js
```

Useful for debugging without code changes.

## requestLogger() Function

For custom logging integration, import and use the `requestLogger` function:

```typescript
import { requestLogger } from "mcp-use";

const logger = requestLogger({ level: "debug" });
server.use(logger);  // Apply as middleware
```

This is primarily for integrating into custom logging ecosystems. Most servers use the built-in config.

## Key points

- **Not delivered to clients.** Server logs appear only in the process stdout/stderr or configured sink.
- **Stateless per-request.** Each HTTP request is logged independently; no session or connection context.
- **No message-level control.** The server logs all requests at the configured level; individual requests cannot override it (use `ctx.sendLog()` for client-visible logs).

See `references/15-logging/02-ctx-sendlog.md` for application-level logs sent to clients.
