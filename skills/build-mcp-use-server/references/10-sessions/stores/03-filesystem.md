# FileSystemSessionStore

Persists session metadata to a JSON file on disk. Single-node only. **Default in development** (`NODE_ENV !== "production"`) so sessions survive hot reloads.

Loads sessions synchronously on startup, prunes expired entries during load, debounces writes, and uses atomic file operations.

## Constructor

```typescript
new FileSystemSessionStore({ path, debounceMs, maxAgeMs })
```

| Option | Type | Default | Notes |
|---|---|---|---|
| `path` | `string` | `.mcp-use/sessions.json` | Persisted file path; parent directory created automatically |
| `debounceMs` | `number` | `100` | Batch frequent writes (ms) |
| `maxAgeMs` | `number` | `86_400_000` (24h) | Prune stale entries when the file is loaded |

## Usage

```typescript
import { MCPServer, FileSystemSessionStore } from "mcp-use/server";

const server = new MCPServer({
  name: "durable-dev-server",
  version: "1.0.0",
  sessionStore: new FileSystemSessionStore({
    path: ".mcp-use/sessions.json",
    debounceMs: 250,
    maxAgeMs: 7 * 24 * 60 * 60 * 1000, // 7 days
  }),
});
```

## Tradeoffs

| Pro | Con |
|---|---|
| Survives restarts and hot reloads | Single-node only — multi-instance coordination is undefined |
| Zero external dependencies | Not suitable for high-throughput production |
| Atomic writes, debounced for throughput | Disk I/O on writes; not for write-heavy workloads |

## When to use

- Local development with hot reload (Next.js dev, tsx watch, nodemon) — default for `NODE_ENV !== "production"`.
- Demos and self-hosted single-VM apps that need restart continuity without operating Redis.
- Small internal tools where one server is enough.

## When **not** to use

- Anything horizontally scaled — multiple processes writing the same file fight each other. Use `RedisSessionStore`.
- Containers without a persistent volume — the file vanishes with the container. Use a mounted volume or Redis.
- High-volume APIs — debounced disk writes become the bottleneck.

## Session file format

```json
{
  "session-id-1": {
    "clientCapabilities": {},
    "clientInfo": {},
    "protocolVersion": "2024-11-05",
    "logLevel": "info",
    "progressToken": 123,
    "lastAccessedAt": 1234567890
  },
  "session-id-2": {}
}
```

Don't rely on this layout — treat it as opaque persistence.

## Anti-patterns

**BAD** — `/tmp` and assume durability everywhere:

```typescript
new FileSystemSessionStore({ path: "/tmp/sessions.json" })
// /tmp can be wiped on container restart or host cleanup.
```

**GOOD** — app-owned persistent directory:

```typescript
new FileSystemSessionStore({ path: ".mcp-use/sessions.json", debounceMs: 250 })
```

In a container, mount a volume:

```yaml
# docker-compose excerpt
volumes:
  - mcp-sessions:/app/.mcp-use
```

**BAD** — filesystem store with multiple replicas:

```typescript
// Two replicas writing /shared/sessions.json over NFS
// Last writer wins; corruption likely under load.
```

Use Redis instead.

## Operational tips

- Keep `debounceMs` low (≤250ms) if abrupt shutdowns are likely — fewer in-memory updates lost.
- File permissions should match a directory containing session metadata; restrict to the app user.
- Match `maxAgeMs` with `sessionIdleTimeoutMs` on `MCPServer` (see `../05-retention-and-cleanup.md`).
