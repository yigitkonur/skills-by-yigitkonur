# Handler Context Mapping (extra → ctx)

Every tool, resource, and prompt handler in v1 receives `extra` as its second argument (or only argument if the tool has no input). v2 replaces this with `ctx` (`ServerContext`), restructured so HTTP-specific fields live under `ctx.http` and protocol-request fields live under `ctx.mcpReq`.

## Why it changed

v1's flat `extra` mixed three concerns:

- **Protocol-request data** (request id, abort signal, sending notifications)
- **HTTP transport data** (auth info, request metadata, SSE close hooks)
- **Per-session task data** (task id, task store)

In v2 these are namespaced. The benefit: handlers running under stdio transport (no HTTP) get a `ctx` where `ctx.http` is `undefined`, making the nullability explicit at the type level.

## Full field mapping

| v1 `extra` | v2 `ctx` | Notes |
|---|---|---|
| `extra.signal` | `ctx.mcpReq.signal` | AbortSignal — moved under `mcpReq` |
| `extra.requestId` | `ctx.mcpReq.id` | Renamed |
| `extra._meta` | `ctx.mcpReq._meta` | Same shape, moved |
| `extra.sendNotification(n)` | `ctx.mcpReq.notify(n)` | Renamed |
| `extra.sendRequest(r, s)` | `ctx.mcpReq.send(r, s)` | Renamed |
| `extra.authInfo` | `ctx.http?.authInfo` | Moved under nullable `http` — undefined in stdio |
| `extra.requestInfo` | `ctx.http?.req` | Renamed and moved |
| `extra.closeSSEStream?.()` | `ctx.http?.closeSSE?.()` | Renamed and moved |
| `extra.closeStandaloneSSEStream?.()` | `ctx.http?.closeStandaloneSSE?.()` | Renamed and moved |
| `extra.sessionId` | `ctx.sessionId` | Top-level, unchanged |
| `extra.taskId` | `ctx.task?.id` | Moved under nullable `task` |
| `extra.taskStore` | `ctx.task?.store` | Moved under nullable `task` |
| (none) | `ctx.mcpReq.method` | New: the JSON-RPC method string |
| (none) | `ctx.mcpReq.log(level, data, logger?)` | New: structured logging shortcut |
| (none) | `ctx.mcpReq.elicitInput(params)` | New: convenience for `elicitation/create` |
| (none) | `ctx.mcpReq.requestSampling(params)` | New: convenience for `sampling/createMessage` |

## Nullability is the trap

In v1, handlers running under stdio transport still received `extra.authInfo` as `undefined`, but the field existed on the type. In v2, `ctx.http` itself can be `undefined`, so the dereference path changes:

```typescript
// v1 — extra always has authInfo, just possibly undefined
const userId = extra.authInfo?.subject;

// v2 — ctx.http can be undefined entirely
const userId = ctx.http?.authInfo?.subject;
```

If you grep for `extra.authInfo` and rewrite to `ctx.authInfo`, the type-checker won't catch it (TypeScript will report a missing property). Rewrite to `ctx.http?.authInfo` with the optional chain.

The same applies to `requestInfo`, `closeSSE`, and `closeStandaloneSSE`.

## No-args tool handlers

```typescript
// v1 — no inputSchema means handler signature is just (extra)
server.registerTool("status", {}, async (extra) => {
  return { content: [{ type: "text", text: "ok" }] };
});

// v2 — same shape, renamed argument
server.registerTool("status", {}, async (ctx) => {
  return { content: [{ type: "text" as const, text: "ok" }] };
});
```

The `as const` on the content type is a v2-friendly habit — Zod v4 strict literal inference benefits from it. Not strictly required but recommended.

## Convenience methods that replace v1 patterns

The new `ctx.mcpReq.log/elicitInput/requestSampling` methods package v1 patterns that previously required dropping to `server.server.*`.

```typescript
// v1 — manual sendRequest
import { ElicitRequestSchema } from "@modelcontextprotocol/sdk/types.js";
const result = await extra.sendRequest(
  { method: "elicitation/create", params: { ... } },
  ElicitRequestSchema
);

// v2 — direct convenience method
const result = await ctx.mcpReq.elicitInput({ ... });
```

```typescript
// v1 — sendNotification with hand-built params
await extra.sendNotification({
  method: "notifications/message",
  params: { level: "info", data: "Processing..." },
});

// v2 — direct log shortcut
await ctx.mcpReq.log("info", "Processing...");
```

When porting, prefer the convenience methods for new code paths. For existing call sites that already manually shape the JSON-RPC, the literal `notify` / `send` translations are fine — the convenience methods are an optional improvement, not a required rewrite.

## Pre-flight checklist for this rewrite

- [ ] Every handler signature `(args, extra)` rewritten to `(args, ctx)`.
- [ ] Every no-args handler signature `(extra)` rewritten to `(ctx)`.
- [ ] All `extra.signal` → `ctx.mcpReq.signal`.
- [ ] All `extra.requestId` → `ctx.mcpReq.id`.
- [ ] All `extra.sendNotification` → `ctx.mcpReq.notify`.
- [ ] All `extra.sendRequest` → `ctx.mcpReq.send`.
- [ ] All `extra.authInfo` → `ctx.http?.authInfo` (with optional chain).
- [ ] All `extra.requestInfo` → `ctx.http?.req`.
- [ ] All `extra.closeSSEStream` → `ctx.http?.closeSSE`.
- [ ] All `extra.taskId` / `extra.taskStore` → `ctx.task?.id` / `ctx.task?.store`.
- [ ] Stdio code paths reviewed for `ctx.http?` nullability — they will land on `undefined`.
- [ ] (Optional improvement) Manual `sendNotification` for logs replaced with `ctx.mcpReq.log()`.
- [ ] (Optional improvement) Manual `sendRequest` for elicitation replaced with `ctx.mcpReq.elicitInput()`.
- [ ] (Optional improvement) Manual `sendRequest` for sampling replaced with `ctx.mcpReq.requestSampling()`.
