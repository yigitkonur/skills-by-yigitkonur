# Workflow: Stateful HTTP Server with Redis Sessions and Progress

**Goal:** persist MCP session metadata in Redis and route active SSE notifications across horizontal replicas with Redis Pub/Sub. Progress notifications reach the right client even when tool calls land on a different pod.

## Prerequisites

- Redis 7+ reachable (`docker run -p 6379:6379 redis:7-alpine`).
- Node 22+, mcp-use 1.26.0 or newer.

## Layout

```
streaming-mcp/
├── package.json
├── tsconfig.json
├── docker-compose.yml
└── src/
    ├── server.ts
    └── tools/import.ts
```

## `package.json` (key deps)

```json
{
  "type": "module",
  "scripts": {
    "dev": "mcp-use dev",
    "build": "mcp-use build",
    "start": "mcp-use start"
  },
  "dependencies": {
    "mcp-use": "^1.26.0",
    "zod": "^4.0.0",
    "redis": "^5.0.0"
  }
}
```

## `src/server.ts`

```typescript
import { MCPServer, RedisSessionStore, RedisStreamManager } from "mcp-use/server";
import { createClient } from "redis";
import { registerImportTools } from "./tools/import.js";

const redis = createClient({ url: process.env.REDIS_URL || "redis://localhost:6379" });
const pubSubRedis = redis.duplicate();

await redis.connect();
await pubSubRedis.connect();

const server = new MCPServer({
  name: "streaming-mcp",
  version: "1.0.0",
  description: "Stateful MCP server with Redis-backed sessions",
  stateless: false,
  sessionStore: new RedisSessionStore({
    client: redis,
    prefix: "mcp:session:",
    defaultTTL: 3600,
  }),
  streamManager: new RedisStreamManager({
    client: redis,
    pubSubClient: pubSubRedis,
    prefix: "mcp:stream:",
    heartbeatInterval: 10,
  }),
});

registerImportTools(server);

await server.listen(parseInt(process.env.PORT || "3000", 10));
```

## `src/tools/import.ts` — long-running tool with progress

```typescript
import { object, error } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

interface Row {
  id: string;
  payload: Record<string, unknown>;
}

export function registerImportTools(server: MCPServer) {
  server.tool(
    {
      name: "bulk-import",
      description: "Import N rows with progress reporting",
      schema: z.object({
        rows: z.array(z.object({
          id: z.string(),
          payload: z.record(z.string(), z.unknown()),
        })).min(1).max(10_000),
      }),
    },
    async ({ rows }, ctx) => {
      const total = rows.length;
      const imported: Row[] = [];

      for (let i = 0; i < total; i++) {
        const row = rows[i];

        // Simulate per-row work — replace with DB INSERT.
        await new Promise((r) => setTimeout(r, 5));
        imported.push(row);

        // Push a progress notification on the session SSE stream.
        // ctx.reportProgress is no-op if the client did not send a progressToken.
        await ctx.reportProgress?.(i + 1, total, `Imported ${i + 1} / ${total}`);
      }

      return object({ imported: imported.length, sample: imported.slice(0, 3) });
    }
  );

  server.tool(
    {
      name: "session-info",
      description: "Show the current session id and its Redis stream key",
      schema: z.object({}),
    },
    async (_, ctx) => {
      const sid = ctx.session.sessionId;
      if (!sid) return error("No active session");
      return object({ sessionId: sid, streamKey: `mcp:stream:${sid}` });
    }
  );
}
```

## `docker-compose.yml`

```yaml
services:
  app:
    build: .
    environment:
      - PORT=3000
      - REDIS_URL=redis://redis:6379
    ports: ["3000:3000"]
    depends_on: [redis]
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    volumes: [redis-data:/data]
volumes:
  redis-data:
```

## Run

```bash
docker compose up --build
```

## Test (progress streaming)

```bash
# Open a session and call bulk-import with a progressToken.
curl -N -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "jsonrpc":"2.0","id":1,
    "method":"tools/call",
    "params":{
      "name":"bulk-import",
      "arguments":{"rows":[{"id":"a","payload":{}},{"id":"b","payload":{}},{"id":"c","payload":{}}]},
      "_meta":{"progressToken":"job-1"}
    }
  }'
```

You should see progress events on the SSE stream (`notifications/progress`) before the final tool result.

## Test (distributed progress)

1. `docker compose up --scale app=2` to run two app replicas.
2. Open an SSE-capable session and call `bulk-import` with a `progressToken`.
3. Route the tool call and the SSE stream through different replicas. `RedisStreamManager` publishes the progress event to the replica holding the active stream.

## Notes

- `RedisSessionStore` stores serializable session metadata; `RedisStreamManager` routes active SSE pushes. It does not replay a dead SSE connection after process death.
- Redis Pub/Sub requires two clients: one normal client and one duplicate client for subscriptions.
- Session metadata TTL is 3600 s here; clients that idle longer must re-initialize.
- Progress notifications are dropped silently for clients that did not pass a `progressToken` — that is correct per spec.

## See also

- Sessions deep dive: `../10-sessions/`
- Notifications and progress: `../14-notifications/`
- Real-time push (per-session): `08-real-time-stock-ticker.md`
