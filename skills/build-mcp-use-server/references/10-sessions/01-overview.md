# Sessions Overview

A **session** is a server-side record of one client's negotiated state — protocol version, capabilities, log level, progress token, last-used timestamp — keyed by the `Mcp-Session-Id` header. Sessions exist only when the server runs in **stateful mode**.

## When a session exists

| Mode | Sessions | SSE | Notifications | Use for |
|---|---|---|---|---|
| **Stateful** | yes | yes | yes | Long-lived clients, sampling, subscriptions |
| **Stateless** | no | no | no | Edge runtimes, serverless, simple HTTP APIs |

Auto-detection (default — leave `stateless` unset):

- Deno → defaults to stateless. Edge/serverless handlers should set `stateless: true`.
- Node.js → per-request based on `Accept`:
  - `application/json, text/event-stream` → stateful.
  - `application/json` only → stateless.

Force a mode explicitly:

```typescript
new MCPServer({ name: "x", version: "1.0.0", stateless: false }) // always stateful
new MCPServer({ name: "x", version: "1.0.0", stateless: true })  // always stateless
```

Stateless mode skips the session store entirely. There is no `ctx.session.sessionId`, no SSE, no server→client notifications. If a request is self-contained and you do not need per-client continuation, stateless wins.

## What lives in a session

- Protocol version
- Client capabilities and `clientInfo`
- Negotiated features via client capabilities (sampling, elicitation, roots, logging)
- Log level
- Current tool-call `progressToken` when one is available
- Last-used timestamp (drives idle expiry)

Tool handlers see only the session ID at `ctx.session?.sessionId`; read capabilities from `ctx.client.*`. Treat session IDs as **opaque**. Do not put business payloads in the session store — use your own database keyed by user/conversation ID.

## Pick a session store

| Scenario | Store | Stream manager |
|---|---|---|
| Local dev, prototyping | `FileSystemSessionStore` (auto in dev) | `InMemoryStreamManager` |
| Single-instance prod, restart-loss OK | `InMemorySessionStore` | `InMemoryStreamManager` |
| Single VM needing restart persistence | `FileSystemSessionStore` | `InMemoryStreamManager` |
| Multi-instance prod, metadata persistence only | `RedisSessionStore` | `InMemoryStreamManager` |
| Multi-instance prod with notifications/sampling/subscriptions | `RedisSessionStore` | `RedisStreamManager` |
| Edge / serverless | none (`stateless: true`) | none |

Rule: **put `RedisStreamManager` only on top of `RedisSessionStore`.** Mixing distributed streams with in-process sessions is an architectural bug — clients reconnect and find the stream but lose the session.

## Cluster contents

- `02-lifecycle.md` — initialize → use → expire → 404 re-init.
- `03-stream-manager.md` — in-process SSE fan-out (default).
- `04-distributed-stream-manager-redis.md` — Redis Pub/Sub fan-out for multi-instance.
- `05-retention-and-cleanup.md` — `sessionIdleTimeoutMs` and per-store TTL.
- `06-multi-tenant-and-chatgpt.md` — `ctx.client.user()` for ChatGPT-style shared sessions.
- `stores/01-overview.md` — store decision tree.
- `stores/02-memory.md` — `InMemorySessionStore`.
- `stores/03-filesystem.md` — `FileSystemSessionStore`.
- `stores/04-redis.md` — `RedisSessionStore`.
- `stores/05-custom-store.md` — implementing a custom `SessionStore`.

**Canonical doc:** https://manufact.com/docs/typescript/server/session-management
