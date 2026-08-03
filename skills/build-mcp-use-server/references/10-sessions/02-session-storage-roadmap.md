# What v1 had: session storage (migration reference)

*Read this when migrating a v1 server that configured `sessionStore`/`streamManager`, to understand what has no v2 equivalent.*

## v1 session stores (not a v2 feature — historical only)

v1's `mcp-use/server` accepted a `sessionStore` (and optionally `streamManager`) on `MCPServer` config. The real v1 API, for migration reference:

```typescript
// v1 — mcp-use/server import, NOT valid in v2
import { MCPServer, InMemorySessionStore } from "mcp-use/server";

const server = new MCPServer({
  name: "single-instance-server",
  version: "1.0.0",
  sessionStore: new InMemorySessionStore(), // production default when omitted
});

await server.listen(3000);
```

```typescript
// v1 — Redis-backed, distributed
import { MCPServer, RedisSessionStore, RedisStreamManager } from "mcp-use/server";
import { createClient } from "redis";

const redis = createClient({ url: process.env.REDIS_URL });
const pubSubRedis = redis.duplicate();
await redis.connect();
await pubSubRedis.connect();

const server = new MCPServer({
  name: "distributed-session-server",
  version: "1.0.0",
  sessionStore: new RedisSessionStore({ client: redis }),
  streamManager: new RedisStreamManager({ client: redis, pubSubClient: pubSubRedis }),
});
```

```typescript
// v1 — Filesystem-backed (non-production default: NODE_ENV !== "production")
import { FileSystemSessionStore, MCPServer } from "mcp-use/server";

const server = new MCPServer({
  name: "dev-server",
  version: "1.0.0",
  sessionStore: new FileSystemSessionStore({ path: ".mcp-use/sessions.json" }),
});
```

`InMemorySessionStore` kept session metadata (client capabilities, client info, protocol version, log level, access timestamps) in a process-local `Map`. `RedisSessionStore` persisted the same metadata externally; `RedisStreamManager` routed active server-to-client stream messages (notifications, sampling/elicitation responses) across instances via Redis Pub/Sub. `FileSystemSessionStore` wrote metadata to a JSON file for local hot-reload persistence.

## Not a v2 roadmap item

This is **not** a v2 feature that is delayed or coming later. The v2 engineering spec explicitly excludes session stores from the port: "Do not port: session stores/StreamManager... These are obsolete under the stateless model." The v2 migration guide lists "Session stores, active-session registries, stream managers, session recovery, and session affinity are not part of v2" as a standing limitation of the beta, not a gap to be filled. Do not plan a v2 architecture around a future `sessionStore` config landing — none is documented as forthcoming.

## Current reality (beta.66)

v2 is stateless: every request is independent. No session configuration exists. For multi-round or persistent workflows, use an external database keyed by verified identity, or the `requestState` codec for round-trip integrity within a single elicitation flow.

See `03-state-patterns-without-sessions.md` for the v2-native alternatives.