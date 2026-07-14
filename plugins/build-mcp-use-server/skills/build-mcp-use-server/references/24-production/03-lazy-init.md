# Lazy initialization

Defer expensive resources (DB pools, HTTP clients, ML models) until the first tool that needs them runs. Critical for cold-start time on serverless and edge — booting Postgres pools at module import adds 200–800 ms to every cold invocation, even when the request never touches the DB.

For env-validation at startup (which still must be eager), see `02-env-config.md`. Lazy-init defers the *connection*, not the *config*.

## Pattern: cached singleton

```typescript
import { Pool } from "pg";

let dbPool: Pool | null = null;

export async function getDB(): Promise<Pool> {
  if (dbPool) return dbPool;
  dbPool = new Pool({
    connectionString: config.databaseUrl,
    max: 20,
    idleTimeoutMillis: 30_000,
    connectionTimeoutMillis: 5_000,
  });
  await dbPool.query("SELECT 1"); // verify before returning
  return dbPool;
}
```

The first caller pays the connection cost. Every subsequent caller in this process gets the cached pool.

## Use it from tool handlers

```typescript
server.tool(
  { name: "get-user", schema: z.object({ id: z.string() }) },
  async ({ id }) => {
    const db = await getDB();
    const { rows } = await db.query("SELECT id, name FROM users WHERE id = $1", [id]);
    if (rows.length === 0) return error("User not found");
    return object(rows[0]);
  }
);
```

`getDB()` only initializes on the first call to any tool that uses it. A tool that never touches the DB never pays the cost.

## Concurrent first-call hazard

If two requests arrive simultaneously on a cold container, both can enter `getDB()` before either finishes. You'll create two pools and leak one. Fix with a promise cache:

```typescript
let dbPromise: Promise<Pool> | null = null;

export function getDB(): Promise<Pool> {
  if (!dbPromise) {
    dbPromise = (async () => {
      const pool = new Pool({ connectionString: config.databaseUrl });
      await pool.query("SELECT 1");
      return pool;
    })().catch((err) => {
      dbPromise = null; // allow retry on failure
      throw err;
    });
  }
  return dbPromise;
}
```

Cache the *promise*, not the resolved value. A second caller awaits the same promise instead of starting a fresh init.

## Per-resource singletons

One module per resource, one cached singleton per module:

```
src/lib/
├── db.ts          // getDB() → Pool
├── redis.ts       // getRedis() → RedisClient
├── http.ts        // getHttpClient() → fetch wrapper with keep-alive
└── llm.ts         // getLLM() → OpenAI client
```

```typescript
// src/lib/redis.ts
let client: RedisClientType | null = null;
export async function getRedis() {
  if (client) return client;
  client = createClient({ url: config.redisUrl });
  await client.connect();
  return client;
}
```

## Cleanup on shutdown

Lazy resources still need to close on `SIGTERM`. Track the live ones and close them in `shutdown()`:

```typescript
async function shutdown(signal: string) {
  // ...drain server first (see 01-graceful-shutdown.md)
  if (dbPool) await dbPool.end();
  if (client) await client.quit();
  process.exit(0);
}
```

Reference the lazily-cached singleton directly — don't call `getDB()` again from the shutdown handler (it might initialize *during* shutdown).

## When to keep it eager

Eager-init these at startup, not lazily:

| Resource | Why |
|---|---|
| Env config | Must fail fast; see `02-env-config.md`. |
| Session store | Needed before the first session is created (during `listen()`). |
| Stream manager | Same — passed into the constructor. |
| OAuth config | Needed before `/.well-known/*` is served. |

## Don't

- Don't re-initialize on every call (defeats the cache).
- Don't share the cached resource across processes — each process has its own copy. For cross-process coordination, use the resource itself (Redis, DB).
- Don't skip the readiness check (`SELECT 1` for DB, `PING` for Redis). A misconfigured pool fails on the second query, far from the original cause.
