# Boat Anchor

## Origin

Described in Brown et al., *AntiPatterns* (1998). Named for a piece of equipment that serves no useful purpose but is too heavy (risky) to remove — like a boat anchor on a landlocked vehicle. Also known as "dead weight code."

## Explanation

A Boat Anchor is code, infrastructure, or a system component that was built for a purpose that never materialized or has since been abandoned. Unlike lava flow (dead code from past features), a boat anchor was often built speculatively — "we might need this someday" — and someday never came.

The code sits in the codebase, consuming attention during reviews, confusing new developers, requiring updates during refactors, and occasionally introducing subtle bugs when someone accidentally invokes it.

## TypeScript Code Examples

### Bad: Speculative Code That Was Never Used

```typescript
// "We might need to support multiple database backends someday."
// Written in 2022. It is 2026. PostgreSQL is still the only database.

interface DatabaseAdapter {
  query<T>(sql: string, params?: unknown[]): Promise<T[]>;
  transaction<T>(fn: (tx: Transaction) => Promise<T>): Promise<T>;
  healthCheck(): Promise<boolean>;
}

class PostgresAdapter implements DatabaseAdapter {
  // 150 lines — the only implementation that is actually used
  async query<T>(sql: string, params?: unknown[]): Promise<T[]> { /* ... */ }
  async transaction<T>(fn: (tx: Transaction) => Promise<T>): Promise<T> { /* ... */ }
  async healthCheck(): Promise<boolean> { /* ... */ }
}

class MySQLAdapter implements DatabaseAdapter {
  // 150 lines — NEVER instantiated, NEVER tested with real MySQL
  // Updated during refactors "just in case" — wasted effort
  async query<T>(sql: string, params?: unknown[]): Promise<T[]> { /* ... */ }
  async transaction<T>(fn: (tx: Transaction) => Promise<T>): Promise<T> { /* ... */ }
  async healthCheck(): Promise<boolean> { /* ... */ }
}

class SQLiteAdapter implements DatabaseAdapter {
  // 150 lines — built for "local development" but everyone uses Docker Postgres
  async query<T>(sql: string, params?: unknown[]): Promise<T[]> { /* ... */ }
  async transaction<T>(fn: (tx: Transaction) => Promise<T>): Promise<T> { /* ... */ }
  async healthCheck(): Promise<boolean> { /* ... */ }
}

class MongoAdapter implements DatabaseAdapter {
  // 200 lines — SQL interface over MongoDB. Why? "Just in case."
  // This does not even work correctly because MongoDB is not SQL.
  async query<T>(sql: string, params?: unknown[]): Promise<T[]> { /* ... */ }
  async transaction<T>(fn: (tx: Transaction) => Promise<T>): Promise<T> { /* ... */ }
  async healthCheck(): Promise<boolean> { /* ... */ }
}

// 650 lines of dead code. 3 fake adapters. Zero users.
// Every time someone changes the DatabaseAdapter interface,
// they must update 4 implementations instead of 1.
```

### Good: Build What You Need, Delete What You Don't

```typescript
// Direct PostgreSQL usage. No abstraction layer for hypothetical futures.

import { Pool } from "pg";

const pool = new Pool({ connectionString: config.databaseUrl });

export async function query<T>(sql: string, params?: unknown[]): Promise<T[]> {
  const result = await pool.query(sql, params);
  return result.rows;
}

export async function transaction<T>(
  fn: (client: PoolClient) => Promise<T>
): Promise<T> {
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const result = await fn(client);
    await client.query("COMMIT");
    return result;
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
}

// If we ever need MySQL support (we probably won't),
// we can add the abstraction THEN — with real requirements
// to guide the interface design.
```

### Common Boat Anchors

```typescript
// 1. Unused API endpoints
app.post("/api/v2/users/bulk-import", async (req, res) => {
  // Built because "a client mentioned they might want bulk import."
  // Client never followed up. Endpoint has zero traffic.
  // But it must be maintained, secured, and tested.
});

// 2. Unused configuration options
interface AppConfig {
  port: number;
  database: string;
  enableExperimentalFeatureX: boolean;  // Always false since 2023
  legacyApiCompatMode: boolean;         // Always false
  maxConcurrentImports: number;         // Import feature was never built
  cacheBackend: "redis" | "memcached" | "in-memory";  // Always "redis"
}

// 3. Abstract base classes with one implementation
abstract class BaseNotificationChannel {
  abstract send(message: Notification): Promise<void>;
  abstract getDeliveryStatus(id: string): Promise<DeliveryStatus>;
  abstract retry(id: string): Promise<void>;
  // 100 lines of abstract methods and shared logic
}

class EmailChannel extends BaseNotificationChannel {
  // The only implementation. The abstract class adds nothing.
  // SMS, push, and webhook channels were "planned" but never built.
}
```

## YAGNI Connection

The Boat Anchor is the physical manifestation of violating YAGNI (You Ain't Gonna Need It):

```
YAGNI: "Don't build it until you need it."
Boat Anchor: "We built it. We don't need it. Now it's stuck here."
```

The lifecycle:
1. Developer anticipates future need
2. Developer builds for future need (violating YAGNI)
3. Future need never materializes
4. Code becomes a boat anchor
5. Nobody removes it because "what if we need it later?"
6. Code slowly rots, accumulates bugs, and wastes maintenance effort

## Alternatives and Countermeasures

- **YAGNI discipline:** Do not build for speculative futures. Build for current needs.
- **Regular dead code audits:** Quarterly review of unused code, endpoints, and config.
- **Usage tracking:** Monitor which code paths are actually executed in production.
- **Git as insurance:** Delete boat anchors confidently — they live in version history.
- **Expiration dates:** When building speculative code, set a review date. If unused by then, delete.

## When NOT to Apply (When Keeping Unused Code Is Justified)

- **Backward compatibility:** Public APIs must maintain old endpoints during deprecation periods.
- **Disaster recovery:** Failover code that is never used in normal operation is not a boat anchor — it is insurance.
- **Platform/SDK code:** Libraries must support features their authors do not use. This is by design.
- **Regulatory requirements:** Some industries mandate certain capabilities even if rarely used.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| Keep boat anchors "just in case" | Zero risk of needing to rebuild | Ongoing maintenance cost, confusion |
| Delete aggressively | Clean codebase, clear intent | Risk of rebuilding if needed (usually low) |
| Archive to a branch | Out of active codebase, recoverable | Branch may become stale and incompatible |
| Track with expiration dates | Forced review cycle | Requires discipline |

## Real-World Consequences

- **Enterprise codebases:** Studies show 20-30% of code in large enterprise systems is dead or unreachable. Each dead line adds to build time, review burden, and cognitive load.
- **Y2K remediation:** Companies discovered vast amounts of code that was never executed, making Y2K fixes simultaneously easier (less to fix) and harder (nobody knew what was live).
- **Speculative REST APIs:** Teams build v2 API endpoints "for the mobile app" that is never developed. The endpoints remain, consuming security audit time and API documentation space.

## Further Reading

- Brown, W. et al. (1998). *AntiPatterns*
- Beck, K. (1999). *Extreme Programming Explained* — YAGNI principle
- Fowler, M. (2018). *Refactoring* — "Speculative Generality" smell
- Martin, R. (2008). *Clean Code* — removing dead code
