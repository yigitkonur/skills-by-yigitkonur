# Error Handling — `error()` vs `throw`

Two error mechanisms with different semantics. Choose deliberately.

## `error(message)` — expected failures

Returns a `CallToolResult` with `isError: true`. The MCP response shape is intact; the client and the model see a graceful tool failure they can correct against.

```typescript
import { error, text } from "mcp-use/server";

server.tool(
  { name: "divide", schema: z.object({ a: z.number(), b: z.number() }) },
  async ({ a, b }) => {
    if (b === 0) return error("Division by zero is not allowed");
    return text(`Result: ${a / b}`);
  }
);

if (!user) return error(`User ${id} not found.`);
if (!ctx.auth) return error("Authentication required.");
if (!ctx.client.can("sampling")) return error("Sampling not supported by this client.");
if (orderTotal > limit) return error(`Order exceeds limit of ${limit}.`);
```

Signature: `error(message: string): CallToolResult`.

The message is what the model sees. Write it as a self-correction hint when possible — name the field that's wrong, the constraint that was violated, the precondition that wasn't met.

## `throw` — unexpected failures

Throw when the handler hits a state that isn't supposed to happen: bug, infrastructure crash, corrupted dependency, broken invariant. The transport returns a server error (`-32603` Internal Error / 500) to the client.

```typescript
try {
  return text(await db.query());
} catch (err) {
  await ctx.log("error", `DB failed: ${err.message}`);
  return error("Database temporarily unavailable. Try again shortly.");
}

// Programmer-bug throw
if (!Array.isArray(internal.cache)) {
  throw new Error("Cache invariant violated — should be unreachable.");
}
```

Throws are observable as server errors, not as tool errors. The model has less context to retry with. Use them only for the truly unexpected.

## When to use which

| Scenario | Use |
|---|---|
| Resource not found | `error()` |
| Validation failure inside the handler (post-Zod check) | `error()` |
| Permission denied / scope missing | `error()` |
| Quota / rate limit hit | `error()` |
| Client capability missing (`can("sampling")` is false) | `error()` |
| Business-logic precondition unmet | `error()` |
| Bug — state that can't legally happen | `throw` |
| Upstream service crash, recoverable | catch, log, `error()` |
| Upstream service crash, unrecoverable | `throw` |
| Programmer error / contract violation | `throw` |

## What clients see

| Mechanism | Client sees | Model can self-correct? |
|---|---|---|
| `error("...")` | `CallToolResult` with `isError: true`, message readable | Yes — the message guides retry |
| `throw new Error(...)` | JSON-RPC error response (server error) | No — opaque server failure |

## Recovery patterns

Wrap risky calls and convert exceptions to `error()`:

```typescript
server.tool(
  { name: "get-order", schema: z.object({ orderId: z.string() }) },
  async ({ orderId }, ctx) => {
    try {
      const order = await db.getOrder(orderId);
      if (!order) return error(`Order ${orderId} not found.`);
      return object({ id: order.id, status: order.status, items: order.items });
    } catch (err) {
      await ctx.log("error", `Failed to fetch order ${orderId}: ${err.message}`);
      return error("Failed to retrieve order. Please try again.");
    }
  }
);
```

Layer common error handling in middleware so individual handlers stay focused on the happy path.

## Anti-patterns

| Bad | Good |
|---|---|
| `throw "Failed"` (string) | `return error("Operation failed: <reason>")` |
| `throw new Error("not found")` for missing record | `return error("Record <id> not found")` |
| Swallow exceptions silently | Log with `ctx.log("error", ...)` and `return error(...)` |
| Hide the cause from the model | Include the actionable detail in the `error()` message |
| `error()` for programmer bugs | `throw` so it surfaces in monitoring as a server error |
