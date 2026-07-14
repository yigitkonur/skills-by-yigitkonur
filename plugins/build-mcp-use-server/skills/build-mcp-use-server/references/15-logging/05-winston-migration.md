# Migrating from Winston (v1.12.0+)

mcp-use v1.12.0 removed its `winston` dependency in favor of the built-in `Logger` (a `SimpleConsoleLogger` underneath). If your code or upstream packages import `winston` directly, migrate to `Logger`.

## What changed

| | Before (≤ v1.11.x) | After (v1.12.0+) |
|---|---|---|
| Import | `import winston from "winston"` | `import { Logger } from "mcp-use"` |
| Configure | `winston.createLogger({ ... })` | `Logger.configure({ ... })` |
| Get logger | `winston.createLogger(...)` per use | `Logger.get(name)` per component |
| Transports | Console, File, Stream, etc. | Console only (pipe externally for files) |
| Format API | Composable formatters | `format: "minimal" \| "detailed" \| "emoji"` |
| Custom levels | Yes | No — fixed level set |

## Side-by-side migration

### Basic config

```typescript
// Before — winston
import winston from "winston";
const logger = winston.createLogger({
  level: "info",
  transports: [new winston.transports.Console()],
});
logger.info("Server started");

// After — mcp-use Logger
import { Logger } from "mcp-use";
Logger.configure({ level: "info", format: "minimal" });
const logger = Logger.get();
logger.info("Server started");
```

### Component logger

```typescript
// Before
const dbLogger = winston.createLogger({
  level: "debug",
  defaultMeta: { component: "db" },
  transports: [new winston.transports.Console()],
});

// After
const dbLogger = Logger.get("db");
dbLogger.info("Query executed", { rows: 42 });
```

### Structured logging

```typescript
// Before
logger.info("Order processed", { orderId: "o_1", amount: 19.99 });

// After — same shape
logger.info("Order processed", { orderId: "o_1", amount: 19.99 });
```

The `Logger` API matches winston's `info/warn/error(message, meta?)` shape, so most call sites need no change.

## Field mapping

| Winston field | mcp-use Logger field |
|---|---|
| `level` | `level` |
| `message` | `message` |
| `defaultMeta.component` | Use `Logger.get("component")` |
| Custom format function | `format: "minimal"`, `"detailed"`, or `"emoji"` |
| Multiple transports | Pipe stdout externally |

## File output

`Logger` does not provide a built-in file transport. To persist logs:

```bash
# Pipe stdout to a file
node server.js > /var/log/mcp-server.log 2>&1

# Or use a process supervisor (pm2, systemd) to capture stdout
```

For aggregated logging (Datadog, Loki, CloudWatch), pipe stdout to the agent and let the agent ingest it. Don't try to reinvent winston transports inside your server.

## Removed features

| Removed | Replacement |
|---|---|
| Custom log levels | Use the fixed level table — `error/warn/info/http/verbose/debug/silly` |
| File transport | Pipe stdout |
| Daily-rotate transport | Use logrotate / external rotator |
| Multi-transport routing | One stdout sink, route externally |
| `winston.format.combine(...)` chains | Choose `minimal`, `detailed`, or `emoji` |

## Migration checklist

1. Search for `from "winston"` and `require("winston")`.
2. Replace `winston.createLogger(...)` → `Logger.get(name)`.
3. Replace winston `format.*` chains → `format: "minimal"`, `"detailed"`, or `"emoji"`.
4. Move file transports out — pipe stdout instead.
5. Confirm the level vocabulary you're using matches the new fixed set.
6. Remove `winston` from `package.json` dependencies.

## Anti-patterns during migration

| Anti-pattern | Fix |
|---|---|
| Keeping winston as a parallel logger | Pick one — mixed loggers diverge in format and level |
| Re-implementing custom transports | Pipe stdout; rotation belongs to the OS |
| Mapping winston levels 1:1 to MCP-spec levels | They differ — see `02-ctx-log.md` (8 MCP levels) vs `03-server-logger.md` (7 Logger levels) |

## Related

- Logger API: `03-server-logger.md`
- Tiered debug verbosity: `04-mcp-debug-level.md`
