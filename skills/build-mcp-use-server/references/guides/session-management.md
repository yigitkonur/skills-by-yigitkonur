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
- **Idle timeout** — Expires after inactivity (default: 1 day, controlled by your session store/runtime policy)
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

By default:

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
  stateless: false,  // Explicitly enable stateful mode
});

// Force stateless — no sessions, no SSE, no notifications
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  stateless: true,  // Force stateless mode
});
```

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

**Session file format** — sessions are stored as a JSON object mapping session IDs to metadata:

```json
{
  "session-id-1": {
    "clientCapabilities": {},
    "clientInfo": {},
    "protocolVersion": "2024-11-05",
    "logLevel": "info",
    "lastAccessedAt": 1234567890
  },
  "session-id-2": {}
}
```

### RedisSessionStore

Stores session metadata in Redis. Required for production multi-instance deployments.

```bash
npm install redis
# or
npm install ioredis
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

## Session Retention

Control how long sessions remain active without requests using the top-level `sessionIdleTimeoutMs` option:

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  sessionIdleTimeoutMs: 3600000,  // 1 hour (default: 1 day)
});
```

You can also configure retention per-store (e.g., `defaultTTL` in `RedisSessionStore`, `maxAgeMs` in `FileSystemSessionStore`) to control when session keys expire in their respective backends.

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
    return text(`Session: ${ctx.session?.sessionId ?? 'none'}`);
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
    pubSubClient: pubSubRedis,  // required dedicated Pub/Sub client (separate connection)
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
  sessionStore: new RedisSessionStore({
    client: redis,
    prefix: "mcp:session:",  // optional; default is "mcp:session:"
    defaultTTL: 3600,        // optional; default is 3600 (1 hour)
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
  sessionStore: new RedisSessionStore({ client: redis }),
  streamManager: new RedisStreamManager({
    client: redis,
    pubSubClient: pubSubRedis,  // required; must be a separate client for Pub/Sub
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
  const user = ctx.client.user();
  return text(`Hello, ${user?.subject ?? "anonymous"}`);
});
```

The session store persists session metadata (capabilities, protocol version) while the OAuth provider manages token storage and refresh independently. Both share the same session ID for correlation.

---

## Session Store Constructor Reference

mcp-use ships three server-side session stores. All of them implement the same conceptual contract — save session metadata, retrieve it by `Mcp-Session-Id`, update last-used timestamps, and delete expired state — but they differ in durability, latency, and operational complexity.

### Import pattern

```typescript
import {
  MCPServer,
  InMemorySessionStore,
  FileSystemSessionStore,
  RedisSessionStore,
} from 'mcp-use/server'
```

### `InMemorySessionStore`

The default store keeps everything in process memory. It is ideal for single-process development and disposable deployments.

| Option | Type | Default | Notes |
|---|---|---|---|
| *(constructor takes no options)* | — | — | Store is process-local and ephemeral |

```typescript
import { MCPServer, InMemorySessionStore, text } from 'mcp-use/server'

const server = new MCPServer({
  name: 'memory-sessions',
  version: '1.0.0',
  sessionStore: new InMemorySessionStore(),
})

server.tool({ name: 'whoami', description: 'Return session scope.' }, async (_args, ctx) => {
  return text(`Session id: ${ctx.session?.sessionId ?? 'none'}`)
})
```

### `FileSystemSessionStore({ path, debounceMs, maxAgeMs })`

Use the filesystem store when you want sessions to survive process restarts on a single machine without introducing Redis. It is especially useful in development, demos, or small self-hosted deployments.

| Option | Type | Default | Use for |
|---|---|---|---|
| `path` | `string` | `.mcp-use/sessions.json` | Location of the persisted session file; directory is created automatically |
| `debounceMs` | `number` | `100` | Batch frequent writes to disk (ms) |
| `maxAgeMs` | `number` | `86400000` (24 hours) | Prune stale sessions during load |

```typescript
import { MCPServer, FileSystemSessionStore } from 'mcp-use/server'

const server = new MCPServer({
  name: 'durable-dev-server',
  version: '1.0.0',
  sessionStore: new FileSystemSessionStore({
    path: '.mcp-use/sessions.json',
    debounceMs: 250,
    maxAgeMs: 7 * 24 * 60 * 60 * 1000,
  }),
})
```

### `RedisSessionStore({ client, prefix, defaultTTL })`

Redis is the production option for horizontally scaled or multi-instance deployments. It keeps sessions outside the process and supports shared access across nodes.

| Option | Type | Default | Use for |
|---|---|---|---|
| `client` | Redis client | required | Primary Redis connection (connected `redis`/`ioredis` client) |
| `prefix` | `string` | `"mcp:session:"` | Namespacing keys per environment/app |
| `defaultTTL` | `number` | `3600` (1 hour) | TTL for session keys in Redis, in seconds |

```typescript
import { MCPServer, RedisSessionStore } from 'mcp-use/server'
import { createClient } from 'redis'

const redis = createClient({ url: process.env.REDIS_URL })
await redis.connect()

const server = new MCPServer({
  name: 'redis-backed-server',
  version: '1.0.0',
  sessionStore: new RedisSessionStore({
    client: redis,
    prefix: 'prod:mcp:',
    defaultTTL: 86400,
  }),
})
```

### Store comparison table

| Store | Survives restart | Multi-instance | Operational cost | Best for |
|---|---|---|---|---|
| `InMemorySessionStore` | ❌ | ❌ | Lowest | Local dev, tests |
| `FileSystemSessionStore` | ✅ | ❌ | Low | Single-server demos, self-hosted apps |
| `RedisSessionStore` | ✅ | ✅ | Medium | Production, HA, horizontal scale |

❌ **BAD** — Use in-memory sessions behind a load balancer:

```typescript
const server = new MCPServer({ sessionStore: new InMemorySessionStore() })
```

✅ **GOOD** — Use Redis when the client may hit different instances:

```typescript
const server = new MCPServer({
  name: 'ha-server',
  version: '1.0.0',
  sessionStore: new RedisSessionStore({ client: redis }),
})
```

❌ **BAD** — Put the filesystem session file in `/tmp` and assume it is durable everywhere:

```typescript
new FileSystemSessionStore({ path: '/tmp/sessions.json' })
```

✅ **GOOD** — Put the session file in an app-owned persistent directory:

```typescript
new FileSystemSessionStore({ path: '.mcp-use/sessions.json', debounceMs: 250 })
```

---

## Session Lifecycle Deep Dive

A session is more than an ID. It is a compact record of what the client negotiated with the server and whether that relationship is still alive.

### Typical lifecycle phases

| Phase | Server action | Store action |
|---|---|---|
| Initialize | Create ID, negotiate capabilities | Insert new record |
| Active request | Validate session, refresh last-used timestamp | Read + update |
| Streaming | Keep channel metadata available | Optionally coordinate stream state |
| Idle timeout | Reject stale IDs with 404 | Expire or delete |
| Explicit close | Honor `DELETE /mcp` | Remove immediately |

### What is usually stored?

- Protocol version
- Client capabilities
- Negotiated features such as elicitation/sampling support
- Log level or negotiated settings
- Auth/session correlation metadata
- Last-used timestamp for idle timeout enforcement

### Lifecycle recommendations

1. Treat session IDs as opaque.
2. Do not store large business payloads inside the session store.
3. Expire aggressively in production if clients are short-lived.
4. Align session retention with auth token lifetime when possible.
5. Expect 404 re-initialization when sessions expire or are deleted.

### Example: observing the lifecycle

```typescript
server.tool(
  {
    name: 'session-debug',
    description: 'Return current session diagnostics.',
  },
  async (_args, ctx) => object({
    sessionId: ctx.session?.sessionId ?? null,
    canNotify: !!ctx.client?.can?.('notifications'),
    protocolVersion: ctx.session?.protocolVersion ?? null,
  })
)
```

---

## Tuning session retention

Session retention controls when inactive sessions expire. Tune it in your chosen session store (for example `defaultTTL` in `RedisSessionStore` or `maxAgeMs` in `FileSystemSessionStore`).

| Workload | Suggested timeout | Why |
|---|---|---|
| Local desktop tools | 24 hours | Users reconnect frequently on the same machine |
| Browser apps | 15–60 minutes | Balances convenience with cleanup |
| High-volume APIs | 5–15 minutes | Prevents excessive buildup |
| Long-running operator consoles | 1–8 hours | Supports active workflows without endless retention |

Use `sessionIdleTimeoutMs` on `MCPServer` for process-level idle enforcement, and store-level TTL options for backend expiry:

```typescript
// Short-lived browser sessions
const server = new MCPServer({
  name: 'short-lived-sessions',
  version: '1.0.0',
  sessionIdleTimeoutMs: 15 * 60 * 1000,  // 15 minutes
  sessionStore: new RedisSessionStore({
    client: redis,
    defaultTTL: 900,  // 15 minutes in seconds
  }),
});
```

### Timeout tuning checklist

| Question | Shorter timeout if yes |
|---|---|
| Are clients easy to re-initialize? | ✅ |
| Do you run many short requests? | ✅ |
| Is memory pressure a concern? | ✅ |
| Do users expect day-long continuity? | ❌ |
| Are sessions tied to expensive setup state? | ❌ |

❌ **BAD** — Set a week-long idle timeout for short-lived browser clients without a cleanup plan:

```typescript
new RedisSessionStore({ client: redis, defaultTTL: 604800 })  // 7 days — sessions accumulate
```

✅ **GOOD** — Match timeout to actual client behavior:

```typescript
new RedisSessionStore({ client: redis, defaultTTL: 900 })  // 15 minutes for browser clients
```

---

## Persistence Across Restarts

Persistence means a client can reconnect after a server restart and still present the same session ID successfully.

### Restart behavior by store

| Store | What happens after restart? |
|---|---|
| In-memory | All sessions disappear |
| Filesystem | Sessions reload from disk |
| Redis | Sessions remain as long as TTL has not expired |

### Filesystem persistence tips

- Store the file under a directory you control.
- Keep `debounceMs` low enough to reduce data loss on abrupt shutdown.
- Use file permissions appropriate for auth/session metadata.
- In containers, mount a persistent volume if restart continuity matters.

### Redis persistence tips

- Use a dedicated prefix per environment.
- Ensure Redis eviction settings will not unexpectedly purge session keys.
- Align `defaultTTL` with your desired session retention window.
- Monitor key counts so abandoned clients do not accumulate indefinitely.

---

## Distributed Streaming with `RedisStreamManager`

`RedisStreamManager({ client, pubSubClient })` coordinates server-initiated events across instances. It matters when one node receives a tool invocation that needs to notify or stream to a client connected through another node.

### Constructor options

| Option | Type | Default | Notes |
|---|---|---|---|
| `client` | Redis client | required | General Redis operations (commands, availability checks) |
| `pubSubClient` | Redis client | required | Dedicated Pub/Sub connection — must be a separate client from `client` |
| `prefix` | `string` | `"mcp:stream:"` | Channel prefix for Pub/Sub |
| `heartbeatInterval` | `number` | `10` (seconds) | Interval to keep sessions alive; keys expire after `heartbeatInterval * 2` |

```typescript
import {
  MCPServer,
  RedisSessionStore,
  RedisStreamManager,
} from 'mcp-use/server'
import { createClient } from 'redis'

const client = createClient({ url: process.env.REDIS_URL })
const pubSubClient = client.duplicate()
await client.connect()
await pubSubClient.connect()

const server = new MCPServer({
  name: 'distributed-streams',
  version: '1.0.0',
  sessionStore: new RedisSessionStore({ client, prefix: 'prod:mcp:' }),
  streamManager: new RedisStreamManager({
    client,
    pubSubClient,  // required; must be a separate Redis client for Pub/Sub
  }),
})
```

### When you need it

| Situation | Need `RedisStreamManager`? | Why |
|---|---|---|
| One instance only | No | In-memory stream tracking is enough |
| Multiple instances, no notifications | Usually no | Stateless request/response may be sufficient |
| Multiple instances with notifications/progress/widgets | Yes | Clients may be connected to any node |
| Legacy SSE compatibility across nodes | Yes | Stream ownership must be shared |

❌ **BAD** — Reuse one Redis connection for commands and Pub/Sub:

```typescript
new RedisStreamManager({ client: redis, pubSubClient: redis })
```

✅ **GOOD** — Use a duplicated dedicated Pub/Sub client:

```typescript
new RedisStreamManager({ client: redis, pubSubClient: redis.duplicate() })
```

❌ **BAD** — Pair distributed streams with in-memory sessions:

```typescript
const server = new MCPServer({ streamManager: new RedisStreamManager({ client, pubSubClient }) })
```

✅ **GOOD** — Pair distributed streams with Redis-backed sessions:

```typescript
const server = new MCPServer({
  name: 'correct-distributed-server',
  version: '1.0.0',
  sessionStore: new RedisSessionStore({ client }),
  streamManager: new RedisStreamManager({ client, pubSubClient }),
})
```

---

## Stateless Mode and When to Use It

Stateless mode disables session persistence and long-lived per-client state. It is not a downgrade — it is often the **right architecture** for edge runtimes, short-lived API requests, and fire-and-forget tools.

### Good stateless fits

| Scenario | Why stateless works |
|---|---|
| Edge functions | No guarantee of warm process reuse |
| Simple read-only tools | Each request is self-contained |
| High-scale HTTP APIs | Easier cache/proxy/load-balancer behavior |
| Webhook-style invocations | Client does not need a durable session |

### What you lose in stateless mode

- Long-lived session identity
- Stream-oriented notifications tied to a session
- Session continuity for resumed browser workflows
- Some richer multi-step behaviors that rely on persistent negotiated state

```typescript
const server = new MCPServer({
  name: 'stateless-edge-server',
  version: '1.0.0',
  stateless: true,
})
```

### Decision rule

If a request contains all the information needed to produce a result and you do not need per-client continuation, choose stateless mode first.

---

## Recommended Configurations

| Deployment | `sessionStore` | `streamManager` | Notes |
|---|---|---|---|---|
| Localhost HTTP dev server | none / default | none | Fine for disposable local work |
| Single HTTP node | `InMemorySessionStore` or `FileSystemSessionStore` | default | Choose store retention to match client behavior |
| Single persistent VM | `FileSystemSessionStore` | default | Filesystem-backed retention |
| Multi-node production | `RedisSessionStore` | `RedisStreamManager` | Tune Redis TTLs and stream retention explicitly |
| Edge/serverless | none | none | Prefer request/response handlers and external persistence if needed |

## Summary checklist

- Use **in-memory** for disposable local work.
- Use **filesystem** when you want restart persistence on one machine.
- Use **Redis** for horizontally scaled production.
- Pair **Redis sessions** with **RedisStreamManager** when notifications or distributed streaming matter.
- Tune **session retention** to client behavior, not habit.
- Prefer **stateless mode** on serverless and edge runtimes.
