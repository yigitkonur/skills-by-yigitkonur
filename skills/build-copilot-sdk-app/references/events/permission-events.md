# Permission Events

Events related to permission requests and their resolution. Protocol v3 broadcasts these to all connected clients.

## Events

### `permission.requested`

Broadcast when the agent needs permission to perform an action. In multi-client setups (protocol v3), all connected clients receive this event simultaneously.

```typescript
session.on("permission.requested", (event) => {
  const { requestId, permissionRequest } = event.data;
  console.log(`Permission needed: ${permissionRequest.kind}`);
  console.log(`Request ID: ${requestId}`);
});
```

**Data shape:**

```typescript
{
  requestId: string;          // UUID — use to respond via session.respondToPermission()
  permissionRequest: {
    kind: "shell" | "write" | "read" | "mcp" | "custom-tool" | "url" | "memory";
    toolCallId?: string;      // Tool call that triggered this request
    // Additional fields depend on kind:
  };
}
```

**Kind-specific fields:**

| Kind | Extra fields |
|------|-------------|
| `shell` | `fullCommandText`, `intention`, `commands: Array<{ name, args }>` |
| `write` | `filePath`, `description` |
| `read` | `filePath` |
| `mcp` | `serverName`, `toolName` |
| `custom-tool` | `toolName`, `arguments` |
| `url` | `url` |
| `memory` | `operation` |

**Multi-client behavior:** When multiple clients are connected via TCP (protocol v3), `permission.requested` is broadcast to all clients. The first client to respond wins — other clients should dismiss their UI when they receive `permission.completed`.

```typescript
// Multi-client permission handler
session.on("permission.requested", async (event) => {
  const { requestId, permissionRequest } = event.data;

  if (permissionRequest.kind === "shell") {
    // Show shell command to user for approval
    const approved = await showApprovalDialog(
      `Allow: ${permissionRequest.fullCommandText}?`
    );
    // Respond — first responder across all clients wins
    await session.rpc.session.respondToPermission({
      requestId,
      approved,
    });
  }
});
```

### `permission.completed`

Emitted when a permission request has been resolved (approved or denied). Use this to dismiss permission UI.

```typescript
session.on("permission.completed", (event) => {
  const { requestId, result } = event.data;
  console.log(`Permission ${requestId}: ${result.kind}`);
  dismissPermissionUI(requestId);
});
```

**Data shape:**

```typescript
{
  requestId: string;      // Matches the original permission.requested
  result: {
    kind:
      | "approved"
      | "denied-by-rules"
      | "denied-no-approval-rule-and-could-not-request-from-user"
      | "denied-interactively-by-user"
      | "denied-by-content-exclusion-policy";
  };
}
```

**Denial kinds:**
- `approved` — permission was granted
- `denied-by-rules` — a preconfigured rule blocked it
- `denied-no-approval-rule-and-could-not-request-from-user` — no handler could process the request
- `denied-interactively-by-user` — the user explicitly rejected it
- `denied-by-content-exclusion-policy` — content policy blocked the action

## Protocol v2 vs v3

In protocol v2 (SDK < 0.1.30), permissions arrive as JSON-RPC requests via the `onPermissionRequest` handler in SessionConfig. In protocol v3, they arrive as broadcast session events AND are handled by `onPermissionRequest`.

The SDK handles this automatically. Always set `onPermissionRequest` on `createSession()` — it works in both protocol versions.

```typescript
// This handles permissions in both v2 and v3
const session = await client.createSession({
  model: "gpt-4.1",
  onPermissionRequest: async (request) => {
    if (request.kind === "read") return { approved: true };
    if (request.kind === "shell") {
      return { approved: isSafeCommand(request.fullCommandText) };
    }
    return { approved: false, message: "Not allowed" };
  },
});
```

## Monitoring permission flow

```typescript
// Track all permission events
session.on("permission.requested", (e) => {
  metrics.permissionRequested(e.data.permissionRequest.kind);
});
session.on("permission.completed", (e) => {
  metrics.permissionResolved(e.data.result.kind);
});
```
