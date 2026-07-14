# InMemorySessionStore

Default store in production. All session data lives in process memory, in a `Map` keyed by session ID.

## Constructor

```typescript
new InMemorySessionStore()
```

Takes no options. Process-local and ephemeral.

## Usage

```typescript
import { MCPServer, InMemorySessionStore, text } from "mcp-use/server";

const server = new MCPServer({
  name: "memory-sessions",
  version: "1.0.0",
  sessionStore: new InMemorySessionStore(), // default in prod — can be omitted
});

server.tool({ name: "whoami" }, async (_args, ctx) =>
  text(`Session id: ${ctx.session?.sessionId ?? "none"}`),
);
```

## Tradeoffs

| Pro | Con |
|---|---|
| Fast — no I/O, no network | Sessions lost on restart |
| Zero dependencies | Cannot share across instances |
| All stateful MCP features work on one server (notifications, sampling, subscriptions) | Memory grows with active sessions until idle timeout |

## When sufficient

- Local development and tests.
- Single-instance production where a small reconnection blip on restart is acceptable.
- Disposable deployments (CI smoke tests, ephemeral previews).
- When auto-detection lands you here in production: this is correct for a single replica.

## When to upgrade

| Symptom | Upgrade to |
|---|---|
| Sessions disappear after every deploy and clients have to re-init | `FileSystemSessionStore` (single VM) or `RedisSessionStore` (distributed) |
| Adding a second replica behind a load balancer | `RedisSessionStore` |
| Need notifications/sampling/subscriptions across replicas | `RedisSessionStore` + `RedisStreamManager` |
| Need to inspect session state from another tool / job | `RedisSessionStore` or custom |

## Anti-pattern

**BAD** — `InMemorySessionStore` behind a load balancer:

```typescript
const server = new MCPServer({
  sessionStore: new InMemorySessionStore(), // breaks: session created on A, request lands on B
});
```

A client's `Mcp-Session-Id` from instance A is unknown to instance B → 404 → client re-inits → lands on A again or C → keeps thrashing.

**GOOD** — Redis when the client may hit different instances:

```typescript
new RedisSessionStore({ client: redis })
```

## Memory pressure

Every active session is a metadata object (capabilities, version, log level, timestamp, optional progress token). If memory grows unboundedly, your idle timeout is too generous or clients are not closing sessions — see `../05-retention-and-cleanup.md`.
