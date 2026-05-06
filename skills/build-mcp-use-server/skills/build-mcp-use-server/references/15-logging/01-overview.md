# Logging Overview

mcp-use ships **two complementary logging surfaces**. Pick by audience:

| API | Audience | Use for |
|---|---|---|
| `ctx.log(...)` | The connected client (per-request) | Tool-call progress visible inside the client UI |
| `Logger` from `mcp-use` | Server process (stdout / stderr) | Operator-facing diagnostic logs |
| `MCP_DEBUG_LEVEL` env | HTTP request logger | Request-log verbosity: `info`, `debug`, or `trace` |

Use `ctx.log` to talk to the user via their MCP client. Use `Logger` to talk to your ops dashboard / log aggregator. They are not interchangeable.

## Where each section lives

| Topic | File |
|---|---|
| Per-tool logging via `ctx.log` | `02-ctx-log.md` |
| `Logger` server-side class | `03-server-logger.md` |
| `MCP_DEBUG_LEVEL` and tiered debug | `04-mcp-debug-level.md` |
| Migration from Winston (v1.12.0+) | `05-winston-migration.md` |

## Side-by-side example

```typescript
import { MCPServer, text } from "mcp-use/server";
import { Logger } from "mcp-use";
import { z } from "zod";

// Server-process log (operator audience)
const log = Logger.get("orders");

const server = new MCPServer({ name: "orders", version: "1.0.0" });

server.tool(
  {
    name: "process-order",
    schema: z.object({ orderId: z.string() }),
  },
  async ({ orderId }, ctx) => {
    log.info("Processing order", { orderId });          // → server stdout
    await ctx.log?.("info", `Processing ${orderId}`);    // → connected client UI

    try {
      await processOrder(orderId);
      log.info("Order complete", { orderId });
      await ctx.log?.("info", "Order complete");
      return text(`Order ${orderId} processed.`);
    } catch (err) {
      log.error("Order failed", { orderId, err });
      await ctx.log?.("error", `Failed: ${(err as Error).message}`);
      throw err;
    }
  }
);
```

## Stateful caveat for `ctx.log`

`ctx.log` is a notification — it requires a stateful request path. Guard it for stateless / edge code paths; see `../14-notifications/06-when-notifications-fail.md`.

`Logger` (server-side) and `MCP_DEBUG_LEVEL` work in any mode — they write to stdout/stderr. `MCP_DEBUG_LEVEL` affects the HTTP request logger; `Logger.configure(...)` controls your application logger instances.

## Related

- Notifications surface: `../14-notifications/01-overview.md`
- Sampling progress (a sibling notification): `../13-sampling/05-progress-during-sampling.md`

**Canonical doc:** https://manufact.com/docs/typescript/server/logging
