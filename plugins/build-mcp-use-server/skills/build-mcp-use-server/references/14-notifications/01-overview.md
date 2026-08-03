# Notifications Overview

*Read this when you need to understand what notifications can and cannot do in a stateless v2 server.*

MCP v2 sends notifications via two distinct mechanisms:

| Mechanism | Scope | Delivery | When to use |
|-----------|-------|----------|------------|
| **Request-scoped** | Single tool call | Arrives on same request's response stream | Progress during long operations; status within a tool |
| **Cross-request** | Server-wide | Sent to clients with active subscriptions | List/resource changes after tool execution |

## Request-scoped (ctx methods)

Within a tool callback, call `ctx.sendNotification()`, `ctx.reportProgress()`, or `ctx.sendLog()` to send a one-way message to the originating request before the result is returned. The client receives these on the same connection it used to invoke the tool.

**Key constraint:** The HTTP response ends when your callback returns. Any notifications must be **awaited and sent before callback completion**:

```typescript
await ctx.sendNotification("com.example/started", { status: "processing" });
// ... work ...
await ctx.reportProgress(50, 100, "halfway there");
// ... more work ...
const result = { /* ... */ };
return result;  // connection closes after this
```

Post-response pushes are impossible in a stateless HTTP model — v2 has no persistent connection to the client.

## Cross-request (server methods)

Use `server.notifyToolsChanged()`, `server.notifyPromptsChanged()`, `server.notifyResourcesChanged()`, or `server.notifyResourceUpdated(uri)` to signal a change to clients with an active `subscriptions/listen` request. These server methods may be called from tool callbacks, custom routes, or background/external events; they are not restricted to gaps between requests.

This is not a durable delivery system. If no client is listening when the notification fires, it is lost. Clients read the updated resource on their next explicit `resources/read` call.

## Stateless limitations

- **No delivery queue:** If a client connects after a notification fires, it does not receive a backlog.
- **No server-push after response:** Once a tool callback returns, the HTTP response ends. New notifications cannot be sent to that request.
- **Subscription recovery:** Clients handle re-sync by re-reading resources after receiving a `resourceUpdated` notification.
- **Response mode defaults to auto-upgrade.** The default transport mode (`"auto"`) automatically upgrades a request's response to an SSE stream the moment a mid-call notification, progress update, or log needs to go out, so request-scoped notifications are not lost under normal `MCPServer` usage. Forcing the underlying handler's response mode to `"json"` (only reachable through the low-level `createMcpMount`/`CreateMcpHandlerOptions` API, not the standard `new MCPServer({...})` config) drops any notification emitted before the final result — avoid setting it explicitly if you rely on `ctx.sendNotification`/`ctx.reportProgress`/`ctx.sendLog`.

See `references/06-resources/06-subscriptions-listen.md` for stateless subscription workflow.
