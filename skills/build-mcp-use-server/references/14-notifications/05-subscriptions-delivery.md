# Subscriptions and Notification Delivery

*Read this when understanding how clients receive notifications and manage subscriptions.*

Notifications are only delivered to clients with active `subscriptions/listen` requests. This is a stateless model with no session storage or delivery queue.

## How Subscriptions Work

1. **Client initiates:** A client sends `subscriptions/listen` with a required `notifications` filter object, not a single type string:
   ```typescript
   {
     toolsListChanged?: boolean;
     promptsListChanged?: boolean;
     resourcesListChanged?: boolean;
     resourceSubscriptions?: string[]; // exact URIs to receive resources/updated for
   }
   ```
   An absent or invalid filter is rejected with `-32602`.
2. **Open connection:** The server narrows the requested filter against its own advertised capabilities and echoes the honored subset back as a `notifications/subscriptions/acknowledged` message, then keeps the request open as a live stream.
3. **Notification published:** When you call `server.notifyResourceUpdated(uri)`, it broadcasts to every open listener whose filter matches — for resource updates, only listeners that included that exact `uri` in `resourceSubscriptions`.
4. **Client re-syncs:** Upon receiving the notification, the client re-reads the resource via `resources/read`.

## Notification Types

| Wire method | Method to send it | Filter field the client sets | Notes |
|------|--------|------------------------|----|
| `notifications/tools/list_changed` | `server.notifyToolsChanged()` | `toolsListChanged: true` | Sent when tool list or metadata changes |
| `notifications/prompts/list_changed` | `server.notifyPromptsChanged()` | `promptsListChanged: true` | Sent when prompt list changes |
| `notifications/resources/list_changed` | `server.notifyResourcesChanged()` | `resourcesListChanged: true` | Sent when resource URIs change |
| `notifications/resources/updated` | `server.notifyResourceUpdated(uri)` | `resourceSubscriptions: [uri, ...]` | Sent when a specific resource changes; the exact URI must be listed, not just a boolean flag |

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
// 1. Opens subscriptions/listen({ notifications: { resourceSubscriptions: ["app://status"] } })
// 2. Server sends notification: { method: "notifications/resources/updated", params: { uri: "app://status" } }
// 3. Client calls resources/read("app://status")
// 4. Server responds with current state: { health: "degraded" }
```

See `references/06-resources/06-subscriptions-listen.md` for the client-side subscription model and `references/06-resources/01-overview.md` for resource URIs.
