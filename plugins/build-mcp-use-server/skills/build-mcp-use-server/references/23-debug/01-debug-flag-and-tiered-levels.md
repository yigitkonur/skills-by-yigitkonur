# Debug Flag and Tiered Levels

mcp-use uses a tiered log level via `MCP_DEBUG_LEVEL`. This replaces the older boolean `DEBUG=1 / DEBUG=2` env var.

For the bare environment-variable reference (where to set it, defaults, precedence), see `../02-setup/09-env-vars.md` and `../03-cli/14-environment-variables.md`. This file documents **what each level emits** and **how to scope it per component**.

---

## Levels

| Level | Emits | Use when |
|---|---|---|
| `silent` | Nothing | Production where logs go elsewhere |
| `error` | Errors only | Production noise floor |
| `warn` | Errors + warnings | Production with limited insight |
| `info` (default) | Lifecycle: server start, session create/destroy, tool registrations, capability advertisement | Daily dev work, deployed staging |
| `debug` | Above + JSON-RPC method names, session ID lookups, tool call entry/exit (no payloads), middleware decisions | Diagnosing why a tool isn't appearing or a session is dropping |
| `trace` | Above + full JSON-RPC request/response payloads, raw HTTP headers, internal state transitions | Reproducing a wire-level bug, exporting evidence for a support ticket |

---

## Setting the level

```bash
# One-shot
MCP_DEBUG_LEVEL=debug mcp-use dev

# Persistent in shell
export MCP_DEBUG_LEVEL=trace
mcp-use start

# In a process manager / Docker / Railway
MCP_DEBUG_LEVEL=info  # default; explicit is better than implicit
```

---

## What each level looks like

### `info` (default)

```
[mcp-use] server starting on :3000
[mcp-use] registered 4 tools, 2 resources, 1 prompt
[mcp-use] session created: abc123
[mcp-use] session ended: abc123 (duration: 42s)
```

### `debug`

Above plus:

```
[mcp-use:rpc] → tools/list (id=2, session=abc123)
[mcp-use:rpc] ← tools/list (id=2, 4 tools)
[mcp-use:rpc] → tools/call name=greet (id=3, session=abc123)
[mcp-use:rpc] ← tools/call (id=3, 12ms)
[mcp-use:middleware] auth: passed for session=abc123
```

Tool call entry/exit are logged but **arguments and results are not** — payloads might contain secrets.

### `trace`

Above plus full payloads, with `Authorization` header values redacted:

```
[mcp-use:rpc:trace] →
  POST /mcp
  Mcp-Session-Id: abc123
  MCP-Protocol-Version: 2025-11-25
  Body: {"jsonrpc":"2.0","method":"tools/call","params":{"name":"greet","arguments":{"name":"World"}},"id":3}

[mcp-use:rpc:trace] ←
  Body: {"jsonrpc":"2.0","result":{"content":[{"type":"text","text":"Hello, World!"}]},"id":3}
```

---

## Per-component overrides

Crank a single component to `trace` while keeping the rest at `info`:

```bash
# Comma-separated component:level pairs override the global level
MCP_DEBUG_LEVEL=info,rpc:trace mcp-use dev

# Multiple components
MCP_DEBUG_LEVEL=info,rpc:trace,middleware:debug mcp-use dev

# All defaults except silence one
MCP_DEBUG_LEVEL=info,session:silent mcp-use dev
```

| Component name | Covers |
|---|---|
| `rpc` | JSON-RPC requests/responses |
| `session` | Session create/destroy/lookup |
| `middleware` | Middleware chain decisions |
| `auth` | OAuth, bearer-token validation |
| `transport` | HTTP/SSE/stdio transport details |
| `widget` | Widget asset serving, CSP enforcement |
| `hmr` | Hot-reload events |

---

## Programmatic Logger API

For library-style code or when you want structured logs in your own components:

```typescript
import { Logger } from "mcp-use";

Logger.configure({ level: "debug", format: "detailed" });
// Levels: silent | error | warn | info | http | verbose | debug | silly
// Formats: "minimal" (default) | "detailed"

const logger = Logger.get("my-component");
logger.info("Initialized");
logger.debug("Processing", { userId: 123 });
logger.error("Failed", err);
```

`Logger.get(name)` namespaces output so `MCP_DEBUG_LEVEL=info,my-component:trace` works on user-defined components, not just built-ins.

---

## Tool-level logging via `ctx.log`

Inside a tool handler, `ctx.log(level, message, [name])` sends log events to the **connected client**, not to the server's stdout. Clients with a Notifications pane (Inspector, some chat clients) display these inline.

```typescript
server.tool(
  { name: "process", schema: z.object({ items: z.array(z.string()) }) },
  async ({ items }, ctx) => {
    await ctx.log("info", "starting");
    for (const item of items) {
      if (!item.trim()) {
        await ctx.log("warning", "skipping empty");
        continue;
      }
      await ctx.log("debug", `processing ${item}`, "process");
    }
    return text("done");
  }
);
```

Client-side log levels (per the MCP spec): `debug`, `info`, `notice`, `warning`, `error`, `critical`, `alert`, `emergency`.

---

## stdio servers — never `console.log`

stdio transports use stdout for JSON-RPC. `console.log()` corrupts the protocol stream. Always use `console.error()` for stdio server logging, or use the Logger API which handles this correctly.

```typescript
console.log("debug message");   // ❌ corrupts JSON-RPC over stdio
console.error("debug message"); // ✅ goes to stderr, safe
Logger.get("my-tool").debug("…"); // ✅ routes through configured transport-aware sink
```

---

## Migration from boolean DEBUG

| Old | New |
|---|---|
| `DEBUG=1` | `MCP_DEBUG_LEVEL=debug` |
| `DEBUG=2` | `MCP_DEBUG_LEVEL=trace` |
| Unset | `MCP_DEBUG_LEVEL=info` (default) |

The boolean form may still work for backward compatibility but is deprecated. Migrate scripts and CI to the tiered form.
