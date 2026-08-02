# Session storage roadmap

*Read this when planning persistent session management for a future v2 release.*

## Planned (not in beta.66)

When session stores land in v2, the API will look like this:

```typescript
import { MCPServer, InMemorySessionStore, RedisSessionStore } from "mcp-use";

// In-memory (single instance only; lost on restart)
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  sessionStore: new InMemorySessionStore(),
});

// Redis (distributed; requires RedisStreamManager for multi-instance)
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  sessionStore: new RedisSessionStore(redisClient),
  streamManager: new RedisStreamManager(redisClient),
});

// Filesystem (single instance; persistent across restarts)
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  sessionStore: new FileSystemSessionStore({ dir: "./.mcp-sessions" }),
});
```

Documented but not shipped in 2.0.0-beta.66 — verify against your installed version.

See beta docs at `/tmp/mcp-use-beta/docs/typescript/server/session-management/` for planned interfaces.

## Current reality (beta.66)

v2 is stateless: every request is independent. No session configuration is available. If your use case requires multi-round or persistent workflows, use an external database or `requestState` codec for round-trip validation.

See `03-state-patterns-without-sessions.md` for alternatives.