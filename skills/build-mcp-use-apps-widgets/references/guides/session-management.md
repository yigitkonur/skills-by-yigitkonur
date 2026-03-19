# Session Management

Configure how mcp-use servers track client state across requests using pluggable session stores and stream managers.

---

## Session Lifecycle

### 1. Initialization

A session begins when a client sends an `initialize` request without a session ID. The server generates a unique ID and returns it in the `Mcp-Session-Id` response header.

### 2. Subsequent Requests

The client includes the session ID in all requests via `Mcp-Session-Id`. The server validates the ID, retrieves session data, and processes with full context.

### 3. Termination

- **Client closes** — `DELETE /mcp` with the session ID
- **Idle timeout** — Expires after inactivity (default: 1 day, configurable via `sessionIdleTimeoutMs`)
- **Server restart** — In-memory sessions are lost; use `RedisSessionStore` or `FileSystemSessionStore` to persist

### 4. Session Not Found (404)

Per the MCP spec, invalid or expired session IDs return HTTP 404. Compliant clients automatically re-initialize.

---

## Stateful vs Stateless Mode

| Mode | Sessions | SSE | Notifications | Best For |
|---|---|---|---|---|
| **Stateful** | ✅ | ✅ | ✅ | Long-lived clients, sampling, subscriptions |
| **Stateless** | ❌ | ❌ | ❌ | Edge functions, serverless, simple APIs |

### Auto-Detection (Default)

When `stateless` is not explicitly set:

- **Deno / edge runtimes** → always stateless
- **Node.js** → per-request based on `Accept` header:
  - `Accept: application/json, text/event-stream` → stateful
  - `Accept: application/json` only → stateless

### Forcing a Mode

```typescript
import { MCPServer } from "mcp-use/server";

// Force stateful
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  stateless: false,
});

// Force stateless — no sessions, no SSE, no notifications
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  stateless: true,
});
```

> **Tip:** Leave `stateless` unset in most cases. Auto-detection handles both SSE-capable and HTTP-only clients transparently.

---

## Session Stores

Session metadata (client capabilities, log level, protocol version) is stored in a pluggable `SessionStore`. Three backends ship with `mcp-use/server`.

### InMemorySessionStore

Default store. All session data lives in process memory.

```typescript
import { MCPServer, InMemorySessionStore } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  sessionStore: new InMemorySessionStore(), // default — can be omitted
});
```

- ✅ Fast — no I/O overhead, zero dependencies
- ✅ All features work (notifications, sampling, subscriptions)
- ❌ Sessions lost on restart
- ❌ Cannot share sessions across instances

**Use when:** Development, single-instance production, or when session loss on restart is acceptable.

### FileSystemSessionStore

Persists session metadata to a JSON file on disk. **Default in development** (`NODE_ENV !== "production"`) so sessions survive hot reloads. Loads sessions synchronously on startup, cleans expired sessions during load, debounces writes, and uses atomic file operations.

```typescript
import { MCPServer, FileSystemSessionStore } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  sessionStore: new FileSystemSessionStore({
    path: ".mcp-use/sessions.json", // session file path (default)
    debounceMs: 100,                // write debounce in ms (default: 100)
    maxAgeMs: 86400000,             // max session age in ms (default: 24h)
  }),
});
```

- ✅ Survives restarts and hot reloads, no external dependencies
- ❌ Not suitable for horizontal scaling or high-throughput production

**Use when:** Development with hot reloads, or single-server setups needing persistence without Redis.

### RedisSessionStore

Stores session metadata in Redis. Required for production multi-instance deployments.

```bash
yarn add redis
# or
yarn add ioredis
```

```typescript
import { MCPServer, RedisSessionStore } from "mcp-use/server";
import { createClient } from "redis";

const redis = createClient({
  url: process.env.REDIS_URL,
  password: process.env.REDIS_PASSWORD,
});
await redis.connect();

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  sessionStore: new RedisSessionStore({
    client: redis,              // connected redis/ioredis client (required)
    prefix: "mcp:session:",     // key prefix (default: "mcp:session:")
    defaultTTL: 3600,           // TTL in seconds (default: 3600 = 1 hour)
  }),
});
```

- ✅ Sessions persist across restarts, shared across all instances
- ✅ Clients resume sessions without re-initializing after deploys
- ❌ Requires a running Redis instance

**Use when:** Production deployments, multi-instance setups behind a load balancer.

---

## Session Idle Timeout

Control how long sessions remain active without requests:

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  sessionIdleTimeoutMs: 3600000, // 1 hour (default: 86400000 = 1 day)
});
```

This is a top-level `MCPServer` option, independent of the session store.

---

## Accessing Session Data in Tool Handlers

Use `ctx.session` inside tool handlers to access the current session:

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });

server.tool(
  { name: "session-info", schema: z.object({}) },
  async (_args, ctx) => {
    return text(`Session: ${ctx.session.sessionId}`);
  }
);
```

### ChatGPT Multi-Tenant Model

ChatGPT establishes a single MCP session for all users. Use `ctx.client.user()` for per-user identity:

```typescript
import { object } from "mcp-use/server";

server.tool({ name: "identify-caller", schema: z.object({}) }, async (_args, ctx) => {
  const caller = ctx.client.user();
  return object({
    mcpSession: ctx.session.sessionId,          // shared transport session
    user: caller?.subject ?? null,              // individual user ID
    conversation: caller?.conversationId ?? null, // this chat conversation
  });
});
```

---

## Distributed Stream Management

Stream managers control how SSE streams route notifications to the correct client session across server instances.

### InMemoryStreamManager (Default)

Routes SSE streams within a single process. Notifications only reach clients connected to the same instance.

```typescript
import { MCPServer, InMemoryStreamManager } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  streamManager: new InMemoryStreamManager(), // same as default
});
```

### RedisStreamManager

Routes SSE streams across instances via Redis Pub/Sub. Required when notifications must reach clients regardless of which server they're connected to.

```typescript
import { MCPServer, RedisSessionStore, RedisStreamManager } from "mcp-use/server";
import { createClient } from "redis";

const redis = createClient({ url: process.env.REDIS_URL });
const pubSubRedis = redis.duplicate(); // Pub/Sub requires a dedicated client
await redis.connect();
await pubSubRedis.connect();

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  sessionStore: new RedisSessionStore({ client: redis }),
  streamManager: new RedisStreamManager({
    client: redis,              // for session availability checks
    pubSubClient: pubSubRedis,  // optional; recommended for Pub/Sub isolation
  }),
});
```

**How it works:** Client connects to Server A → SSE stream created, Server A subscribes to that session's channel. Client's next request hits Server B → Server B publishes notification to Redis → Server A receives it → pushes via SSE to the client.

> **Always pair `RedisStreamManager` with `RedisSessionStore`.** Using a Redis stream manager with in-memory sessions defeats the purpose — a reconnecting client would find its stream but lose its session state.

---

## Session Store Decision Matrix

| Scenario | Session Store | Stream Manager | Notes |
|---|---|---|---|
| **Development / prototyping** | `FileSystemSessionStore` (auto) | `InMemoryStreamManager` (auto) | Sessions survive hot reloads |
| **Single-instance production** | `InMemorySessionStore` | `InMemoryStreamManager` | Fast, zero deps. Sessions lost on restart. |
| **Single server + persistence** | `RedisSessionStore` | `InMemoryStreamManager` | Metadata persists. SSE still local. |
| **Single server, no Redis** | `FileSystemSessionStore` | `InMemoryStreamManager` | Disk persistence without Redis |
| **Horizontal scaling** | `RedisSessionStore` | `RedisStreamManager` | Full distributed MCP support |
| **Serverless / edge** | *(none)* | *(none)* | Use `stateless: true` |

---

## Complete Configuration Examples

### Development (Default — No Config Needed)

```typescript
import { MCPServer } from "mcp-use/server";

// Auto-selects FileSystemSessionStore + InMemoryStreamManager in dev
const server = new MCPServer({ name: "dev-server", version: "1.0.0" });
await server.listen(3000);
```

### Production with Session Persistence

```typescript
import { MCPServer, RedisSessionStore } from "mcp-use/server";
import { createClient } from "redis";

const redis = createClient({ url: process.env.REDIS_URL });
await redis.connect();

const server = new MCPServer({
  name: "prod-server",
  version: "1.0.0",
  sessionIdleTimeoutMs: 3600000,
  sessionStore: new RedisSessionStore({
    client: redis,
    prefix: "mcp:session:",  // optional; default: "mcp:session:"
    defaultTTL: 3600,        // optional; default: 3600 (1 hour)
  }),
});

await server.listen(3000);
```

### Full Distributed Deployment

```typescript
import {
  MCPServer,
  RedisSessionStore,
  RedisStreamManager,
} from "mcp-use/server";
import { createClient } from "redis";

const redis = createClient({ url: process.env.REDIS_URL });
const pubSubRedis = redis.duplicate();
await redis.connect();
await pubSubRedis.connect();

const server = new MCPServer({
  name: "prod-server",
  version: "1.0.0",
  sessionIdleTimeoutMs: 3600000,
  sessionStore: new RedisSessionStore({ client: redis }),
  streamManager: new RedisStreamManager({
    client: redis,
    pubSubClient: pubSubRedis,  // recommended for Pub/Sub isolation
  }),
});

await server.listen(3000);
```

### Serverless / Edge Functions

```typescript
import { MCPServer, text } from "mcp-use/server";

const server = new MCPServer({
  name: "edge-server",
  version: "1.0.0",
  stateless: true,
});

server.tool({ name: "hello" }, async () => text("Hello from the edge!"));

await server.listen(3000);
```

---

## Session Data in Auth Flows

When OAuth is configured, session metadata and auth tokens coexist within the same session lifecycle. Access authenticated user info via `ctx.client.user()` — the session ensures continuity between auth and tool execution.

```typescript
import { MCPServer, oauthAuth0Provider, RedisSessionStore, text } from "mcp-use/server";
import { createClient } from "redis";
import { z } from "zod";

const redis = createClient({ url: process.env.REDIS_URL });
await redis.connect();

const server = new MCPServer({
  name: "auth-server",
  version: "1.0.0",
  oauth: oauthAuth0Provider(),
  sessionStore: new RedisSessionStore({ client: redis }),
});

server.tool({ name: "whoami", schema: z.object({}) }, async (_args, ctx) => {
  return text(`Hello, ${ctx.auth?.user.name ?? "anonymous"}`);
});
```

The session store persists session metadata (capabilities, protocol version) while the OAuth provider manages token storage and refresh independently. Both share the same session ID for correlation.
