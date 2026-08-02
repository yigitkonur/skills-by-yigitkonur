# Subscriptions and Notification Delivery

*Read this when understanding how clients receive notifications and manage subscriptions.*

Notifications are only delivered to clients with active `subscriptions/listen` requests. This is a stateless model with no session storage or delivery queue.

## How Subscriptions Work

1. **Client initiates:** A client sends `subscriptions/listen` with a notification type it wants (e.g., `"resources/updated"`).
2. **Open connection:** The server keeps that subscription active as an open request stream.
3. **Notification published:** When you call `server.notifyResourceUpdated(uri)`, it broadcasts to all clients currently listening for that type.
4. **Client re-syncs:** Upon receiving the notification, the client re-reads the resource via `resources/read`.

## Notification Types

| Type | Method | Clients must listen for | Notes |
|------|--------|------------------------|----|
| `"tools/list_changed"` | `server.notifyToolsChanged()` | `"tools/list_changed"` | Sent when tool list or metadata changes |
| `"prompts/list_changed"` | `server.notifyPromptsChanged()` | `"prompts/list_changed"` | Sent when prompt list changes |
| `"resources/list_changed"` | `server.notifyResourcesChanged()` | `"resources/list_changed"` | Sent when resource URIs change |
| `"resources/updated"` | `server.notifyResourceUpdated(uri)` | `"resources/updated"` | Sent when a specific resource changes |

## Stateless Constraints

- **No backlog:** If a client connects after a notification fires, it receives nothing. Backlog requires session storage (not in v2 beta.66).
- **No queue:** Notifications are fire-and-forget. If the network drops mid-notification, it is not retried.
- **No acknowledgment:** Clients do not send "ack" back to the server; the server has no way to know if a notification was received.

## Resource Workflow Example

```typescript
// Server publishes a resource
server.resource(
  { name: "status", uri: "app://status", description: "App status" },
  async (uri, ctx) => ({
    contents: [{
      uri: uri.href,
      mimeType: "application/json",
      text: JSON.stringify({ health: state.health }),
    }],
  })
);

// Somewhere, status changes
server.post("/api/health", async (c) => {
  state.health = "degraded";
  await server.notifyResourceUpdated("app://status");
  return c.json({ ok: true });
});

// Client side (not in this skill):
// 1. Opens subscriptions/listen("resources/updated")
// 2. Server sends notification: { type: "resources/updated", uri: "app://status" }
// 3. Client calls resources/read("app://status")
// 4. Server responds with current state: { health: "degraded" }
```

See `references/06-resources/06-subscriptions-listen.md` for the client-side subscription model and `references/06-resources/01-overview.md` for resource URIs.
