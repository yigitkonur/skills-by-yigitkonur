# Schema Evolution

## Origin

Schema evolution became a first-class concern with the rise of microservices and continuous deployment. When a monolith has a single database and deploys atomically, schema changes are coordinated. When dozens of services share data via APIs, events, or databases, a schema change in one system can cascade failures to all consumers. The Avro and Protobuf communities formalized backward/forward compatibility rules. The expand-contract pattern emerged from continuous delivery practices at companies like Facebook and Etsy.

## Explanation

### Compatibility Types

**Backward compatible**: New schema can read data written with the old schema. Old data still works. This is the most important compatibility to maintain.

**Forward compatible**: Old schema can read data written with the new schema. New fields are ignored. Useful when producers upgrade before consumers.

**Full compatible**: Both backward and forward compatible simultaneously. The gold standard for event schemas.

### The Expand-Contract Pattern

A three-phase approach to non-breaking schema changes:

1. **Expand**: Add the new column/field alongside the old one. Write to both. Read from old.
2. **Migrate**: Backfill the new column with data from the old column. Switch reads to new column.
3. **Contract**: Remove the old column once all consumers have migrated.

### Breaking vs. Non-Breaking Changes

| Change | Breaking? | Notes |
|--------|-----------|-------|
| Add optional column | No | Old code ignores it |
| Add required column | Yes | Old inserts will fail |
| Remove column | Yes | Old reads will fail |
| Rename column | Yes | Equivalent to remove + add |
| Widen type (int -> bigint) | Usually no | Depends on database |
| Narrow type (text -> varchar(50)) | Yes | Existing data may not fit |
| Add enum value | Depends | Breaking if consumers don't handle unknown values |

## TypeScript Code Examples

### Bad: Breaking Change Deployed at Once

```typescript
// BAD: Rename column in a single migration — breaks all running code
const breakingMigration = `
  -- This will break every query that references 'name'
  ALTER TABLE customers RENAME COLUMN name TO full_name;
`;

// Every service instance still running old code will crash:
// ERROR: column "name" does not exist
```

### Good: Expand-Contract Migration (Three Phases)

```typescript
// GOOD: Phase 1 — EXPAND: Add new column, write to both
const expandMigration = `
  -- Step 1: Add the new column (nullable, no constraint)
  ALTER TABLE customers ADD COLUMN full_name TEXT;

  -- Step 2: Backfill existing data
  UPDATE customers SET full_name = name WHERE full_name IS NULL;

  -- Step 3: Set up trigger to keep both columns in sync during transition
  CREATE OR REPLACE FUNCTION sync_customer_name()
  RETURNS TRIGGER AS $$
  BEGIN
    IF NEW.name IS DISTINCT FROM OLD.name THEN
      NEW.full_name := NEW.name;
    END IF;
    IF NEW.full_name IS DISTINCT FROM OLD.full_name THEN
      NEW.name := NEW.full_name;
    END IF;
    RETURN NEW;
  END;
  $$ LANGUAGE plpgsql;

  CREATE TRIGGER trg_sync_name
  BEFORE UPDATE ON customers
  FOR EACH ROW EXECUTE FUNCTION sync_customer_name();
`;

// Application code during expand phase: write both, read old
async function updateCustomer(id: string, data: UpdateCustomerInput): Promise<void> {
  await db.query(
    "UPDATE customers SET name = $2, full_name = $2 WHERE id = $1",
    [id, data.fullName]
  );
}

// Read still uses old column — safe for old code
async function getCustomer(id: string): Promise<Customer> {
  const result = await db.query(
    "SELECT id, name, email FROM customers WHERE id = $1",
    [id]
  );
  return result.rows[0];
}
```

```typescript
// GOOD: Phase 2 — MIGRATE: Switch reads to new column
// Deploy new application code that reads from full_name
async function getCustomerV2(id: string): Promise<Customer> {
  const result = await db.query(
    "SELECT id, full_name, email FROM customers WHERE id = $1",
    [id]
  );
  return { ...result.rows[0], name: result.rows[0].full_name };
}
```

```typescript
// GOOD: Phase 3 — CONTRACT: Remove old column once all consumers migrated
const contractMigration = `
  DROP TRIGGER trg_sync_name ON customers;
  DROP FUNCTION sync_customer_name();
  ALTER TABLE customers DROP COLUMN name;
  ALTER TABLE customers ALTER COLUMN full_name SET NOT NULL;
`;
```

### Good: Safe Migration with Zero Downtime

```typescript
// GOOD: Adding a column with a default — safe in PostgreSQL 11+
const safeMigration = `
  -- PostgreSQL 11+ does not rewrite the table for a default value
  ALTER TABLE orders ADD COLUMN priority TEXT NOT NULL DEFAULT 'normal';

  -- Add index concurrently (does not lock the table)
  CREATE INDEX CONCURRENTLY idx_orders_priority ON orders(priority);
`;

// GOOD: Migration runner with advisory locks to prevent concurrent runs
async function runMigration(name: string, sql: string): Promise<void> {
  const lockId = hashStringToInt(name);

  await db.query("SELECT pg_advisory_lock($1)", [lockId]);
  try {
    const applied = await db.query(
      "SELECT 1 FROM schema_migrations WHERE name = $1",
      [name]
    );

    if (applied.rowCount === 0) {
      await db.query(sql);
      await db.query(
        "INSERT INTO schema_migrations (name, applied_at) VALUES ($1, NOW())",
        [name]
      );
      console.log(`Migration ${name} applied`);
    } else {
      console.log(`Migration ${name} already applied`);
    }
  } finally {
    await db.query("SELECT pg_advisory_unlock($1)", [lockId]);
  }
}
```

### Good: Event Schema Evolution with Avro-Style Rules

```typescript
// GOOD: Type-safe event schema evolution
// Rule: New fields must have defaults. Never remove or rename fields.

// Version 1
interface OrderCreatedV1 {
  schemaVersion: 1;
  orderId: string;
  customerId: string;
  totalCents: number;
  createdAt: string;
}

// Version 2 — backward compatible: new optional field with default
interface OrderCreatedV2 {
  schemaVersion: 2;
  orderId: string;
  customerId: string;
  totalCents: number;
  createdAt: string;
  currency: string;  // New field — default "USD" for old events
  metadata: Record<string, string>;  // New field — default {} for old events
}

// Consumer that handles both versions
function handleOrderCreated(event: OrderCreatedV1 | OrderCreatedV2): void {
  const currency = "currency" in event ? event.currency : "USD";
  const metadata = "metadata" in event ? event.metadata : {};

  processOrder({
    orderId: event.orderId,
    customerId: event.customerId,
    totalCents: event.totalCents,
    currency,
    metadata,
  });
}
```

## Alternatives

| Approach | Best For | Trade-off |
|----------|----------|-----------|
| **Expand-contract** | Relational databases with zero-downtime deploys | Three-phase process is slower |
| **Schema registry (Avro/Protobuf)** | Event streaming (Kafka) | Requires additional infrastructure |
| **GraphQL deprecation** | API field evolution | Relies on client discipline |
| **Feature flags** | Gradual rollout of schema-dependent features | Adds code complexity |
| **Blue-green database migration** | Risky migrations | Requires duplicate infrastructure |

## When NOT to Apply

- **Greenfield projects with no consumers**: If nobody is reading your data yet, just make the change. The expand-contract ceremony is for live systems.
- **Single-deployment monoliths with maintenance windows**: If you can take the system offline, a direct migration is simpler and faster.
- **Schemaless databases**: Document stores like MongoDB allow any shape. Evolution is implicit (but you trade schema enforcement for it).

## Trade-offs

- **Safety vs. speed**: Expand-contract is safe but slow — each phase requires a deployment and verification period. For a simple column rename, this can mean three PRs over multiple days.
- **Sync triggers add write overhead**: During the expand phase, triggers or application-level dual-writes increase write latency and complexity.
- **Backfill cost**: Large tables (100M+ rows) take significant time to backfill. Run backfills in batches with rate limiting to avoid locking or overwhelming the database.
- **Testing complexity**: You must test both old and new code paths simultaneously during the transition period. Integration tests need scenarios for both schema versions.

## Further Reading

- [Martin Fowler — Evolutionary Database Design](https://martinfowler.com/articles/evodb.html)
- [Flyway — Database Migrations](https://flywaydb.org/)
- [Confluent — Schema Evolution and Compatibility](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html)
- [PostgreSQL — ALTER TABLE Performance](https://www.postgresql.org/docs/current/sql-altertable.html)
- [Expand-Contract Pattern — Prisma](https://www.prisma.io/dataguide/types/relational/expand-and-contract-pattern)
