# Custom Session Stores

Implement the `SessionStore` interface to back sessions with anything else — Postgres, DynamoDB, Cosmos DB, Cloudflare KV, libSQL, etc.

## When to build a custom store

| You need | Pick |
|---|---|
| A backend you already operate, not Redis | Custom |
| Strong consistency / transactional guarantees alongside other tables | Custom (Postgres, DynamoDB) |
| Multi-region replication beyond what Redis offers | Custom |
| Anything the three built-ins cover | Use the built-in |

## The `SessionStore` interface

The store implements the exported `SessionStore` contract:

```typescript
import type { SessionMetadata, SessionStore } from "mcp-use/server";

interface SessionStore {
  get(sessionId: string): Promise<SessionMetadata | null>;
  set(sessionId: string, data: SessionMetadata): Promise<void>;
  delete(sessionId: string): Promise<void>;
  has(sessionId: string): Promise<boolean>;
  keys(): Promise<string[]>;
  setWithTTL?(sessionId: string, data: SessionMetadata, ttlMs: number): Promise<void>;
}
```

Confirm the exact method signatures against the version of `mcp-use/server` you depend on — the interface is exported from the same module as the built-in stores.

## Implementation skeleton

```typescript
import type { SessionMetadata, SessionStore } from "mcp-use/server";

export class NamespacedSessionStore implements SessionStore {
  private rows = new Map<string, SessionMetadata>();

  async get(sessionId: string) {
    return this.rows.get(sessionId) ?? null;
  }

  async set(sessionId: string, data: SessionMetadata) {
    this.rows.set(sessionId, data);
  }

  async delete(sessionId: string) {
    this.rows.delete(sessionId);
  }

  async has(sessionId: string) {
    return this.rows.has(sessionId);
  }

  async keys() {
    return Array.from(this.rows.keys());
  }

  async setWithTTL(sessionId: string, data: SessionMetadata, ttlMs: number) {
    await this.set(sessionId, data);
    setTimeout(() => this.rows.delete(sessionId), ttlMs);
  }
}
```

Wire it up:

```typescript
const server = new MCPServer({
  name: "custom-sessions",
  version: "1.0.0",
  sessionStore: new NamespacedSessionStore(),
});
```

## Implementation rules

1. **Return `null` for unknown or expired sessions.** Never throw on lookup miss — the server treats `null` as "not found" and emits 404.
2. **Treat `sessionId` as opaque.** Do not parse, hash, or derive structure.
3. **Store metadata, not business data.** Keep records small. Application data belongs in your own tables keyed by `user.subject` (see `../06-multi-tenant-and-chatgpt.md`).
4. **Respect TTL at the storage layer** — Postgres partial indexes, DynamoDB TTL attribute, Cosmos `ttl`. Don't rely on the server to delete every record.
5. **Keep `set` and `setWithTTL` idempotent.** Retries must be safe.
6. **Tolerate concurrent writes.** Two requests on the same session may race — last-write-wins on the metadata is acceptable; do not throw on conflict.
7. **Match `sessionIdleTimeoutMs`** on `MCPServer` with the store's expiry policy. See `../05-retention-and-cleanup.md`.

## Backend-specific notes

| Backend | Notes |
|---|---|
| **Postgres** | Store metadata JSON plus a last-used timestamp; reap stale rows with your normal job runner. |
| **DynamoDB** | Use table-level expiry and also gate `get` on the timestamp because expiry sweeps can lag. |
| **Cloudflare KV** | Use per-key expiry for session rows. Eventual consistency is fine for session metadata. |
| **libSQL / SQLite** | Single-writer is fine for a single instance. For multi-instance, prefer Postgres. |

## Testing a custom store

1. Round-trip a record: `set` → `get` returns it.
2. Update refreshes `lastAccessedAt`: `set` with a newer record, then `get` returns the refreshed timestamp.
3. Expired records: insert with a stale timestamp → `get` returns `null`.
4. Delete: `delete` then `get` returns `null`.
5. Concurrency: two parallel `set` calls don't corrupt the row.
6. Plug into `MCPServer` and run a real `initialize → tool call → DELETE /mcp` cycle end-to-end.

## When it's overkill

If Postgres/DynamoDB persistence is the only reason — and you already operate Redis — `RedisSessionStore` is the lower-effort path. Only build a custom store when the operational fit (existing infra, transactional alignment, region topology) is genuinely better than Redis.
