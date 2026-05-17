# `server.sendNotification`

Broadcast a notification to every connected client, or target a single session.

## Signature

```typescript
server.sendNotification(method: string, params?: Record<string, unknown>): Promise<void>
server.sendNotificationToSession(sessionId: string, method: string, params?: Record<string, unknown>): Promise<boolean>
ctx.sendNotification(method: string, params?: Record<string, unknown>): Promise<void>
ctx.sendNotificationToSession(sessionId: string, method: string, params?: Record<string, unknown>): Promise<boolean>
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `method` | `string` | Yes | Notification method name. Any string is accepted; use a namespace the receiving client understands. |
| `params` | `Record<string, unknown>` | No | JSON-serializable payload. |
| `sessionId` | `string` | Yes (session variant only) | Target a specific session. |

`server.sendNotificationToSession` returns `true` if delivered, `false` if the session is not found / expired.

## Three targeting modes

| Mode | API | Scope |
|---|---|---|
| Broadcast | `server.sendNotification(...)` | All connected sessions |
| Specific session | `server.sendNotificationToSession(id, ...)` | One session by ID |
| Current caller | `ctx.sendNotification(...)` (inside tool) | Only the calling client |
| Specific session from a tool | `ctx.sendNotificationToSession(id, ...)` | One session by ID |

## Broadcast

```typescript
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({ name: "demo", version: "1.0.0" });

await server.sendNotification("custom/status/ready", {
  status: "ready",
  timestamp: Date.now(),
});
```

## Target one session

```typescript
const sessions = server.getActiveSessions();
if (sessions.length > 0) {
  const ok = await server.sendNotificationToSession(
    sessions[0],
    "custom/welcome",
    { message: "Hello!" }
  );
  if (!ok) console.log("Session not found or expired");
}
```

## Notify only the calling client

```typescript
server.tool(
  { name: "start-job", description: "Kick off a job and notify the caller." },
  async (_args, ctx) => {
    await ctx.sendNotification("custom/job-started", {
      jobId: "j_42",
      startedAt: Date.now(),
    });
    return text("Job started.");
  }
);
```

## Custom method naming

Use `custom/<domain>/<action>` to namespace ordinary application events. mcp-use also ships UI bridge code that handles `ui/notifications/*` methods for MCP Apps; use that prefix only when you are speaking that client protocol. Bump a `vN` suffix when your payload shape changes.

```typescript
// Bad — no namespace, easy to collide with future protocol methods
await server.sendNotification("status",  { state: "ready" });

// Good — namespaced, evolvable
await server.sendNotification("custom/status/ready",   { state: "ready" });
await server.sendNotification("custom/analytics/v2",    { region: "us-east-1" });

// Also valid when targeting an MCP Apps UI bridge that expects it
await server.sendNotification("ui/notifications/size-changed", {
  width: 640,
  height: 480,
});
```

## Payload schema checklist

| Practice | Why |
|---|---|
| Include a stable identifier (`jobId`, `deploymentId`, `resourceUri`) | Lets clients correlate events |
| Add `emittedAt` ISO timestamps | Lets clients order events |
| Send full state, not deltas | Idempotent; out-of-order delivery is safe |
| Avoid raw error objects | Send `{ errorCode, message }` instead |

## Idempotency: send full state

Notifications are fire-and-forget — there's no delivery guarantee or ordering guarantee across reconnects. Send full state so a missed event is harmless.

```typescript
// BAD — drops if missed
await server.sendNotification("custom/credits", { delta: -1 });

// GOOD — full state
await server.sendNotification("custom/credits", {
  remaining: 42,
  accountId: "acct_123",
  emittedAt: new Date().toISOString(),
});
```

## Fanout pattern with correlation IDs

```typescript
function broadcastDeployment({ id, status }: { id: string; status: string }) {
  return server.sendNotification("custom/deploy/status", {
    deploymentId:  id,
    status,
    correlationId: `deploy-${id}`,
    emittedAt:     new Date().toISOString(),
  });
}
```

## Targeted broadcast with filters

When you need to notify only a subset of sessions, iterate `getActiveSessions()`:

```typescript
async function notifyPaidAccounts() {
  for (const sessionId of server.getActiveSessions()) {
    // Filter on whatever metadata your app stores per session
    await server.sendNotificationToSession(sessionId, "custom/billing-summary", {
      plan: "pro",
      reportUrl: "https://billing.example.com/reports/2024-11",
    });
  }
}
```

## Failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Notifications never arrive | Stateless transport | Switch to SSE / StreamableHTTP — see `06-when-notifications-fail.md` |
| Only the calling client gets the event | Used `ctx.sendNotification` instead of `server.sendNotification` | Use the `server.*` form for broadcast |
| Session-targeted send returns `false` | Session expired between `getActiveSessions()` and send | Treat as best-effort; ignore non-existent sessions |
