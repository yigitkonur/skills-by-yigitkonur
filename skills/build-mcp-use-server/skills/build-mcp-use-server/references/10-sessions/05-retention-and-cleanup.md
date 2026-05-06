# Session Retention and Cleanup

Two layers affect retention:

1. **Server-level idle cleanup** — `sessionIdleTimeoutMs` on `MCPServer`. A background interval closes inactive runtime sessions.
2. **Store-level expiry** — `defaultTTL` (Redis) or `maxAgeMs` (filesystem). Controls how long backend records survive.

## Server-level: `sessionIdleTimeoutMs`

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  sessionIdleTimeoutMs: 3_600_000, // 1 hour. Default: 86_400_000 (1 day)
});
```

Independent of which session store you pick. The runtime checks active sessions every minute and closes those whose `lastAccessedAt` is older than this threshold. A later request whose store record is gone returns 404 and should re-initialize.

## Store-level TTL

| Store | Knob | Default | What it does |
|---|---|---|---|
| `InMemorySessionStore` | `setWithTTL(...)` if called directly | none | Process-local; built-in server cleanup handles active runtime sessions |
| `FileSystemSessionStore` | `maxAgeMs` | `86_400_000` (24h) | Prune stale entries when the file is loaded |
| `RedisSessionStore` | `defaultTTL` | `3600` (sec, 1h) | Redis-side TTL on each key |

Match these to `sessionIdleTimeoutMs` so backend records and server enforcement agree.

## Recommended timeouts

| Workload | Suggested timeout | Why |
|---|---|---|
| Local desktop tools | 24 hours | Users reconnect frequently on the same machine |
| Browser apps | 15–60 minutes | Balance convenience with cleanup |
| High-volume APIs | 5–15 minutes | Prevent buildup |
| Long-running operator consoles | 1–8 hours | Active workflows without endless retention |

## Tuning checklist

| Question | Shorter timeout if yes |
|---|---|
| Are clients easy to re-initialize? | yes |
| Do you run many short requests? | yes |
| Is memory or Redis pressure a concern? | yes |
| Do users expect day-long continuity? | no |
| Are sessions tied to expensive setup state? | no |

## Aligned config — short-lived browser clients

```typescript
const server = new MCPServer({
  name: "browser-server",
  version: "1.0.0",
  sessionIdleTimeoutMs: 15 * 60 * 1000, // 15 min
  sessionStore: new RedisSessionStore({
    client: redis,
    defaultTTL: 900,                    // 15 min — match the server-level value
  }),
});
```

## Anti-patterns

**BAD** — week-long Redis TTL with no plan to reap idle sessions:

```typescript
new RedisSessionStore({ client: redis, defaultTTL: 604_800 }) // 7 days — accumulates
```

**BAD** — server idle timeout much shorter than store TTL:

```typescript
new MCPServer({ sessionIdleTimeoutMs: 60_000 }) // 1 min
new RedisSessionStore({ client: redis, defaultTTL: 86_400 })
// Runtime transports close quickly; Redis metadata can linger for 24h.
```

**GOOD** — match both, match the client behavior:

```typescript
new MCPServer({ sessionIdleTimeoutMs: 900_000 })
new RedisSessionStore({ client: redis, defaultTTL: 900 })
```

## What triggers cleanup

- **Server-level:** `startIdleCleanup` runs every minute for active runtime sessions and closes/removes idle transports from memory.
- **`FileSystemSessionStore`:** prunes expired entries on startup load; normal writes are debounced and persisted atomically.
- **`RedisSessionStore`:** Redis itself expires keys at TTL.
- **Explicit `DELETE /mcp`:** removes the record from the store immediately, regardless of TTL.

## Persistence-across-restart matrix

| Store | After restart |
|---|---|
| `InMemorySessionStore` | All sessions gone |
| `FileSystemSessionStore` | Sessions reload from disk; expired ones pruned during load |
| `RedisSessionStore` | Sessions remain until TTL expires |

For containerized filesystem persistence, mount a persistent volume — don't write into ephemeral `/tmp`. See `stores/03-filesystem.md`.
