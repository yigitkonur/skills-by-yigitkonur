# Roots

Roots are **client-side state** the server can request: the set of filesystem locations (or URIs) the client wants the server to operate within. Servers don't push roots; the server asks (`server.listRoots`) or subscribes to changes (`server.onRootsChanged`).

## Root shape

```typescript
interface Root {
  uri:   string;  // typically starts with "file://"
  name?: string;  // optional human-readable label
}
```

## Subscribing to root changes

Clients send `notifications/roots/list_changed` whenever the user adds, removes, or relabels a root. Register a handler:

```typescript
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({ name: "roots-demo", version: "1.0.0" });

server.onRootsChanged(async (roots) => {
  console.log(`Client updated roots: ${roots.length} root(s)`);
  for (const root of roots) {
    console.log(`  - ${root.name ?? "unnamed"}: ${root.uri}`);
  }
});
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `callback` | `(roots: Root[]) => void \| Promise<void>` | Yes | Invoked with the full new root list each time the client updates |

The callback receives the **complete** new list, not a diff. Replace your cache outright:

```typescript
let cachedRoots: Root[] = [];
server.onRootsChanged((roots) => { cachedRoots = roots; });
```

## Requesting roots on demand

`server.listRoots(sessionId)` queries a specific client session for its current roots. Returns the array, or `null` if the session does not exist or the request fails.

```typescript
const sessions = server.getActiveSessions();
if (sessions.length > 0) {
  const roots = await server.listRoots(sessions[0]);
  if (roots) {
    console.log("Roots:", roots.map((r) => r.uri));
  }
}
```

## When to use which

| Scenario | API |
|---|---|
| React to user changing roots in the client UI | `server.onRootsChanged(cb)` |
| Need current roots at tool-call time | `server.listRoots(ctx.session.sessionId)` in stateful handlers |
| Cache roots with a refresh on change | Combine: cache via `onRootsChanged`, hydrate via `listRoots` on first connect |

## Roots gate on capability

Not every client supports roots. Check before requesting:

```typescript
if (!ctx.client.can("roots")) {
  // Client doesn't support roots — fall back to a default scope
}
```

`ctx.client.can(...)` is documented in `../16-client-introspection/03-can-capabilities.md`.

## Common use cases

| Use case | Pattern |
|---|---|
| File-system tool that respects user scope | `listRoots` on each call, only operate within those URIs |
| Workspace-aware resources | Subscribe with `onRootsChanged`, regenerate `resources/list` on change |
| Multi-project dashboard | Cache roots per session, partition data accordingly |

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Caching roots once at boot, never refreshing | Subscribe to changes via `onRootsChanged` |
| Trusting `roots[0]` exists | Always check `roots.length` |
| Operating outside declared roots | Roots define scope — refuse paths outside them |
| Treating roots as auth | Roots are advisory scope, not access control. Use OAuth (`ctx.auth`) for security |

## Stateless caveat

Root notifications need stateful transport and a client that advertises roots. In stateless mode, `onRootsChanged` never fires; `listRoots` returns `null` when no session can be queried. See `06-when-notifications-fail.md`.
