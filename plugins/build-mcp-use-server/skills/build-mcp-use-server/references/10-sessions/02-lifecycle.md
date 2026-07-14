# Session Lifecycle

Five phases. Server actions on the left, store actions on the right.

| Phase | Server action | Store action |
|---|---|---|
| Initialize | Generate ID, negotiate capabilities, return `Mcp-Session-Id` header | Insert record |
| Active request | Validate ID, refresh `lastAccessedAt` | Read + update |
| Streaming | Keep SSE channel metadata alive | Coordinate stream state (see `03-stream-manager.md`) |
| Idle timeout | Background cleanup closes inactive runtime sessions; missing/expired store records return 404 on the next request | Expire / delete by store policy |
| Explicit close | Honor `DELETE /mcp` with the session ID | Remove immediately |

## 1. Initialization

The client sends `initialize` **without** a session ID. The server:

1. Negotiates protocol version and capabilities.
2. Generates an opaque session ID.
3. Returns it in the `Mcp-Session-Id` response header.
4. Inserts a session record into the configured `SessionStore`.

## 2. Subsequent requests

Every later request includes `Mcp-Session-Id: <id>`. The server:

1. Looks up the record in the store.
2. Refreshes `lastAccessedAt`.
3. Restores capability state into `ctx.client`; `ctx.session` exposes only the session ID.

## 3. Termination paths

- **Client closes** — `DELETE /mcp` with the session ID. Store removes the record immediately.
- **Idle timeout** — Active runtime sessions are checked by `sessionIdleTimeoutMs`; store records expire by their own TTL/load policy. See `05-retention-and-cleanup.md`.
- **Server restart** — `InMemorySessionStore` loses everything. `FileSystemSessionStore` reloads from disk. `RedisSessionStore` keeps records as long as TTL has not expired.

## 4. Session Not Found → 404

Per the MCP spec, an invalid or expired `Mcp-Session-Id` returns HTTP `404`. Compliant clients re-run `initialize` and continue. Do **not** return 401/410/500 here — only 404 triggers the spec-defined re-init flow.

## Lifecycle rules

1. Treat session IDs as opaque — never parse them.
2. Do not store large business payloads in the session record.
3. In production, expire aggressively if clients are short-lived.
4. Align session retention with auth-token lifetime when both are present.
5. Expect clients to re-initialize on 404 — do not retain associated business state inside the session store.

## Inspecting the lifecycle from a tool

```typescript
import { object } from "mcp-use/server";

server.tool(
  { name: "session-debug", description: "Return current session diagnostics." },
  async (_args, ctx) => object({
    sessionId: ctx.session?.sessionId ?? null,
    canLog: !!ctx.client?.can?.("logging"),
    client: ctx.client?.info?.() ?? null,
  }),
);
```

`ctx.session` is `undefined` in stateless mode. Always guard with `?.`.
