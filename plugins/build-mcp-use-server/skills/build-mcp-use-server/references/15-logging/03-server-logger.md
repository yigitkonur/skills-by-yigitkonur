# Server-Side `Logger`

The `Logger` class is mcp-use's built-in server-process logger (since v1.12.0, replacing `winston`). It works in Node.js and browser environments and writes to stdout / stderr.

```typescript
import { Logger } from "mcp-use";
```

> Source note: `mcp-use@1.26.0` exports `Logger` from `dist/index.d.ts`; `dist/src/server/index.d.ts` does not export it, even though the canonical logging page currently imports from `"mcp-use/server"`.

## Configuring the global logger

```typescript
Logger.configure({
  level:  "debug",     // server log level — see table below
  format: "detailed",  // "minimal" | "detailed" | "emoji"
});
```

| Option | Type | Default | Effect |
|---|---|---|---|
| `level` | `LogLevel` | `"info"` | Minimum level emitted (lower = more verbose) |
| `format` | `"minimal"` \| `"detailed"` \| `"emoji"` | `"minimal"` | Output formatter |

## Log levels (server-side)

The `Logger` levels are inherited from the prior winston API and differ from `ctx.log`'s eight MCP-spec levels.

| Level | Use case |
|---|---|
| `error` | Errors that need attention |
| `warn` | Potential issues |
| `info` | General messages (default) |
| `http` | HTTP request/response logging |
| `verbose` | Verbose informational |
| `debug` | Detailed debugging |
| `silly` | Very detailed debug (rare) |

## Formats

| Format | Example output |
|---|---|
| `minimal` | `14:23:45 [mcp-use] info: Session initialized: abc123` |
| `detailed` | `14:23:45 [mcp-use] INFO: Session initialized: abc123` (more context, ALL CAPS levels) |
| `emoji` | Emoji-prefixed level labels for local debugging |

## Named component loggers

Get a child logger keyed to a component name. The label appears in every line.

```typescript
const log = Logger.get("orders");
log.info("Component initialized");
log.debug("Processing request", { userId: 123 });
log.error("Operation failed", new Error("Connection timeout"));
```

`Logger.get()` (no name) returns the default `mcp-use` logger.

## Structured fields

Pass an object as the second argument. The formatter merges it into the line:

```typescript
log.info("Order created", {
  orderId:  "ord_42",
  userId:   user.subject,
  amountUsd: 19.99,
});
```

Keep field values primitives or simple objects — circular refs and large payloads will degrade output.

## Numeric debug shorthand

If you only need to flip verbosity, `Logger.setDebug(level)` is a one-liner:

```typescript
Logger.setDebug(0); // info
Logger.setDebug(1); // info, and sets DEBUG=1
Logger.setDebug(2); // debug, and sets DEBUG=2
```

This affects the root `Logger` instances and the legacy `DEBUG` env. It is separate from the HTTP request logger's `MCP_DEBUG_LEVEL`; see `04-mcp-debug-level.md`.

## Per-component overrides

You can configure individual component loggers if your app has noisy subsystems:

```typescript
const dbLog   = Logger.get("db");
const httpLog = Logger.get("http");

// Most code stays quiet at info; db gets verbose for debugging
Logger.configure({ level: "info" });
// Component-level override:
dbLog.level = "debug";
```

## Browser / edge compatibility

`Logger` writes via `console.*` in browser environments and direct stdout/stderr in Node.js. Both branches are safe to call. There is no native filesystem transport; pipe stdout to your aggregator if you need persistence.

## When to use `Logger` vs `ctx.log`

| | `Logger` | `ctx.log` |
|---|---|---|
| Audience | Operator | End user via their client |
| Stateless-mode safe | Yes | No |
| Structured fields | Yes | No |
| Per-call (request scope) | No | Yes |

Most production servers use both: `Logger` for ops + `ctx.log` for user-visible progress.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Calling `console.log` directly | Use `Logger` so format and level are consistent |
| Logging full request bodies at `info` | Drop to `debug` and redact secrets |
| Creating `Logger.get(name)` inside a hot path | Hoist to module scope |
| Mixing `winston` imports with `Logger` | `winston` is removed — see `05-winston-migration.md` |
