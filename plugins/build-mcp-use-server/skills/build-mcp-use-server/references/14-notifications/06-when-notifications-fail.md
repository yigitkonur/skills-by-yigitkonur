# When Notifications Fail

Notifications are stateful-only. They require a session with a server-to-client notification path. In stateless HTTP mode (Deno / edge defaults, serverless handlers, or single-shot HTTP requests), there is no active session to target; broadcast sends iterate zero sessions, targeted sends return `false`, and request-scoped helpers may be absent.

## Mode by transport

| Transport | Mode | Notifications work? |
|---|---|---|
| `stdio` | Process-scoped | Yes, through the active JSON-RPC connection |
| `sse` | Stateful | Yes |
| `http-streamable` | Stateful | Yes |
| `http-streamable` (stateless config) | Stateless | **No** |
| Deno auto-detect | Stateless | **No** |
| Edge runtime (Cloudflare Workers, Vercel Edge) | Stateless | **No** |

See `../09-transports/` for transport selection details.

## What is unavailable in stateless mode

In stateless mode, this category is effectively unavailable:

- `server.getActiveSessions()` returns `[]`.
- `server.sendNotification(...)` has no active sessions to iterate.
- `server.sendNotificationToSession(...)` returns `false` for missing sessions.
- `ctx.sendNotification(...)` / `ctx.sendNotificationToSession(...)` require a request session.
- `ctx.reportProgress` is absent without a progress token + notification transport.
- `ctx.log` is not a reliable stateless UX channel; use server-side `Logger` instead.
- `server.notifyResourceUpdated(...)` has no active subscriber sessions.
- `server.sendToolsListChanged()` / resources / prompts have no connected clients to notify.
- `server.onRootsChanged(...)` callback never fires.
- `server.listRoots(...)` returns `null` when no session can be queried.

Server broadcast calls return `Promise<void>` even when there are zero sessions. Treat notifications as best-effort.

## Detection

There is no generic `ctx.client.can("notifications")` or `ctx.client.can("stateful")` API in mcp-use 1.26.0. Use the specific signal for the feature you need:

```typescript
if (!ctx.client.can("roots")) {
  // Do not call server.listRoots(...) as a required path.
}

await ctx.reportProgress?.(0, 100, "Starting");
```

For server-wide broadcasts, inspect `server.getActiveSessions()`. For configured deployments, branch on your own `stateless: true` setting; the request-level auto-detection is transport behavior, not a `ctx.client.can(...)` capability.

## Pattern: graceful degradation

Wrap notification-emitting code so the tool still works when notifications fail:

```typescript
server.tool(
  { name: "long-job", description: "Long task with optional progress." },
  async (_args, ctx) => {
    // Optional chaining is safe when no progress token / notification path exists.
    for (let i = 0; i <= 100; i += 10) {
      await doWork(i);
      await ctx.reportProgress?.(i, 100, `Step ${i}/100`);
    }
    return text("Done.");
  }
);
```

The optional call improves UX when progress is available and disappears cleanly when it is not.

## When to actually branch

Branch only when a tool's behavior fundamentally needs notifications:

```typescript
server.tool(
  { name: "watch-config", description: "Subscribe to config changes." },
  async (_args, ctx) => {
    if (!ctx.session?.sessionId) {
      return text("This tool requires a stateful connection. Reconnect over SSE.");
    }
    // ... subscription logic
  }
);
```

## Failure-mode triage

| Symptom | Likely cause | Fix |
|---|---|---|
| Notifications never arrive | Stateless transport | Switch to SSE / StreamableHTTP stateful |
| Only first client gets updates | Used `ctx.sendNotification` | Use `server.sendNotification` to broadcast |
| UI widgets not updating | Forgot `notifyResourceUpdated()` after mutation | Call after every content change |
| Progress stuck at 0% | Client did not send `progressToken`, or helper is absent | Check `if (ctx.reportProgress)` and provide polling fallback |
| `onRootsChanged` never fires | Stateless transport, or client doesn't support roots | Confirm transport; check `ctx.client.can("roots")` |

## Debug checklist

1. Confirm deployment mode: `stateless: true` disables sessions by design.
2. Verify the session is alive: `server.getActiveSessions()` should return non-empty for server-level sends.
3. Use the MCP Inspector to watch incoming notifications on the wire.
4. Log `notification.method` and `notification.params` on the client side.
5. Validate payloads are JSON-serializable (no functions, no circular refs).

## Trade-offs of stateless

| | Stateless | Stateful |
|---|---|---|
| Horizontal scaling | Trivial — each request stands alone | Requires sticky sessions or Redis |
| Edge deployment | Yes | Limited |
| Notifications | No | Yes |
| Long-running tools | Bounded by HTTP timeout | Effectively unbounded with progress |
| Subscriptions | No | Yes |

If your tools genuinely don't need notifications/progress/subscriptions, stateless deployment is simpler. If they do, choose SSE or stateful StreamableHTTP. See `../09-transports/`.
