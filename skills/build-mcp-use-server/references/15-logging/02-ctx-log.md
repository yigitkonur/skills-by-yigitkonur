# `ctx.log`

Per-tool-call logging that goes to the connected client. The client decides how to display the log lines — typically inline with the tool's UI, in a debug panel, or in a console.

## Signature

```typescript
ctx.log(level: LogLevel, message: string, logger?: string): Promise<void>
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `level` | `LogLevel` | Yes | One of the eight standard levels (table below) |
| `message` | `string` | Yes | The message text |
| `logger` | `string` | No | Logger name for client-side categorization (defaults to `'tool'`) |

## Eight log levels

These are the MCP-spec levels. Use the lowest level that conveys the right urgency.

| Level | Use case |
|---|---|
| `debug` | Verbose debugging output |
| `info` | General progress messages |
| `notice` | Normal but significant events |
| `warning` | Recoverable issue |
| `error` | Failure that doesn't stop execution |
| `critical` | Critical condition needing attention |
| `alert` | Action must be taken immediately |
| `emergency` | System is unusable |

In practice, 95% of tool logging is `info` for progress and `error` for failures.

## Example: progress-style logging

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

server.tool(
  {
    name: "process-data",
    schema: z.object({ items: z.array(z.string()) }),
  },
  async ({ items }, ctx) => {
    await ctx.log?.("info", "Starting data processing");
    await ctx.log?.("debug", `Processing ${items.length} items`, "my-tool");

    for (const item of items) {
      if (!item.trim()) {
        await ctx.log?.("warning", "Empty item found, skipping");
        continue;
      }
      try {
        await processItem(item);
      } catch (err) {
        await ctx.log?.("error", `Failed to process item: ${(err as Error).message}`);
      }
    }

    await ctx.log?.("info", "Processing completed");
    return text("All items processed");
  }
);
```

## When to use `ctx.log` vs `ctx.reportProgress`

| Need | Use |
|---|---|
| Visible status text per stage | `ctx.log?.("info", ...)` |
| Numeric % progress (and timeout reset) | `ctx.reportProgress?.(progress, total, msg)` |
| Both | Both — they're not redundant |

`ctx.reportProgress` updates a progress bar UI **and** resets the client's request-timeout counter. `ctx.log` is text-only and does not affect timeouts. For long-running tools, prefer `ctx.reportProgress` to keep the request alive; layer `ctx.log` on top for richer text.

## When to use `ctx.log` vs `Logger`

| | `ctx.log` (per-request) | `Logger` (server-process) |
|---|---|---|
| Audience | The end user via their client | Operators / your ops console |
| Visible to user | Yes | No |
| Available in stateless mode | No | Yes |
| Accepts structured fields | No (string + logger name only) | Yes |
| Per-call | Yes (uses `ctx`) | No (server-wide) |

A common pattern is to dual-log: `ctx.log` for client UX, `Logger.get("component").info(..., { fields })` for ops.

## Stateful caveat

`ctx.log` sends `notifications/message`, so it needs a request context with a notification path. The 1.26.0 declarations type it as present, while the runtime returns no method when `sendNotification` is unavailable; guard if your code must run in stateless or edge paths.

> Source note: `mcp-use@1.26.0` `dist/src/server/types/tool-context.d.ts` declares `ctx.log`; `dist/src/server/index.cjs` `createLogMethod` returns `undefined` without `sendNotification`.

```typescript
if (ctx.log) {
  await ctx.log("info", "Processing started");
}
```

See `../14-notifications/06-when-notifications-fail.md`.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Logging every loop iteration at `info` | Use `debug` for verbose, throttle by count or time |
| Putting secrets / tokens in messages | Log a hash or length only |
| Using `ctx.log` for ops metrics | Use `Logger` — `ctx.log` lines belong to the user |
| Synchronous-feel API misuse — forgetting `await` | All `ctx.log` calls return `Promise<void>` — `await` them in order-sensitive paths |
