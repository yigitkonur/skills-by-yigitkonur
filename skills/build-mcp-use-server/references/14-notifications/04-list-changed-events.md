# List-Changed Events

*Read this when signaling that tools, prompts, or resources changed between requests.*

Send server-level notifications when capabilities are added, removed, or modified. Use these **outside** tool callbacks to notify clients that cached lists are stale.

## Server Methods

```typescript
await server.notifyToolsChanged(): Promise<void>
await server.notifyPromptsChanged(): Promise<void>
await server.notifyResourcesChanged(): Promise<void>
await server.notifyResourceUpdated(uri: string): Promise<void>
```

## Usage

```typescript
// Dynamically register a tool after server startup
export const deploymentTools = new Map<string, ToolRef>();

server.post("/api/deploy", async (c) => {
  const { toolName } = await c.req.json();

  // Register new tool
  deploymentTools.set(
    toolName,
    server.tool(
      { name: toolName, description: "Dynamic tool" },
      async (params, ctx) => ({ content: [{ type: "text", text: "OK" }] })
    )
  );

  // Notify clients
  await server.notifyToolsChanged();

  return c.json({ ok: true });
});

// Resource updated
server.post("/api/config/update", async (c) => {
  const { newValue } = await c.req.json();
  state.config = newValue;

  // Notify clients with active subscriptions
  await server.notifyResourceUpdated("config://app");

  return c.json({ ok: true });
});
```

## Key points

- **Server-level only.** These methods are on `server`, not `ctx`. Call them outside request handlers.
- **Stateless delivery.** Notifications are sent only to clients with an active `subscriptions/listen` request for that type. If no client is listening, the notification is lost.
- **Client must re-sync.** After receiving `resourceUpdated(uri)`, clients re-read that resource. They do not cache; each notification triggers a new fetch.
- **No backlog.** Clients connecting after a notification fires do not receive past events. They query normally and get the current state.

## When to use each

| Method | Scenario |
|--------|----------|
| `notifyToolsChanged()` | New tool registered, old tool removed, or tool description changed |
| `notifyPromptsChanged()` | New prompt added/removed or prompt args changed |
| `notifyResourcesChanged()` | Resource list structure changed (not content) |
| `notifyResourceUpdated(uri)` | Specific resource content changed; clients re-read this URI |

See also: `references/06-resources/06-subscriptions-listen.md` for the client-side subscription workflow.
