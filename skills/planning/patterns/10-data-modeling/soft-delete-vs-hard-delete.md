# Soft Delete vs Hard Delete

## Origin

The soft delete pattern has been used in enterprise software since the 1980s, originally to provide an "undo" capability and to preserve referential integrity in relational databases. The pattern gained renewed attention with GDPR (2018) and other privacy regulations that introduced a legal tension: businesses want to keep data for auditing and analytics, but regulations require actual deletion of personal data. This tension forced engineering teams to be deliberate about their deletion strategy rather than defaulting to soft deletes everywhere.

## Explanation

### Hard Delete

Remove the row from the database permanently. The data is gone. Foreign key constraints may cascade or prevent the deletion.

```sql
DELETE FROM users WHERE id = 'abc-123';
```

### Soft Delete

Mark the row as deleted without removing it. Typically done with a `deleted_at` timestamp column or an `is_deleted` boolean.

```sql
UPDATE users SET deleted_at = NOW() WHERE id = 'abc-123';
```

All queries must then filter out soft-deleted rows:

```sql
SELECT * FROM users WHERE deleted_at IS NULL;
```

### Archival Tables

Move deleted data to a separate archive table. The main table stays clean; the archive retains history.

```sql
INSERT INTO users_archive SELECT * FROM users WHERE id = 'abc-123';
DELETE FROM users WHERE id = 'abc-123';
```

### The GDPR Complication

GDPR and similar regulations require "right to erasure" — actual deletion of personal data when requested. Soft delete does NOT satisfy GDPR because the data still exists. You must either hard delete personal fields, anonymize the record, or implement a true purge process.

## TypeScript Code Examples

### Bad: Soft Delete with Leaked Queries

```typescript
// BAD: Soft delete where you constantly forget the filter
interface User {
  id: string;
  email: string;
  name: string;
  deletedAt: Date | null; // Soft delete flag
}

// Every single query must remember to add this filter.
// Miss one and deleted users appear in search results, reports, or API responses.

async function getUser(id: string): Promise<User | null> {
  // OOPS: Forgot the deleted_at filter — returns "deleted" users
  const result = await db.query("SELECT * FROM users WHERE id = $1", [id]);
  return result.rows[0] ?? null;
}

async function listActiveUsers(): Promise<User[]> {
  // Remembered here, but will you remember in all 47 other queries?
  const result = await db.query("SELECT * FROM users WHERE deleted_at IS NULL");
  return result.rows;
}
```

### Good: Soft Delete with Enforced Filtering

```typescript
// GOOD: Base query builder that always filters deleted records
class UserRepository {
  private baseQuery(includeDeleted = false): string {
    return includeDeleted
      ? "SELECT * FROM users"
      : "SELECT * FROM users WHERE deleted_at IS NULL";
  }

  async findById(id: string): Promise<User | null> {
    const result = await db.query(
      `${this.baseQuery()} AND id = $1`,
      [id]
    );
    return result.rows[0] ?? null;
  }

  async listAll(): Promise<User[]> {
    const result = await db.query(this.baseQuery());
    return result.rows;
  }

  async softDelete(id: string): Promise<void> {
    await db.query(
      "UPDATE users SET deleted_at = NOW() WHERE id = $1 AND deleted_at IS NULL",
      [id]
    );
  }

  async restore(id: string): Promise<void> {
    await db.query(
      "UPDATE users SET deleted_at = NULL WHERE id = $1 AND deleted_at IS NOT NULL",
      [id]
    );
  }

  // Admin-only: includes deleted records
  async findByIdIncludingDeleted(id: string): Promise<User | null> {
    const result = await db.query(
      `${this.baseQuery(true)} WHERE id = $1`,
      [id]
    );
    return result.rows[0] ?? null;
  }
}
```

### Good: PostgreSQL Row-Level Security for Soft Deletes

```typescript
// GOOD: Database-level enforcement — impossible to forget the filter
const rlsSetup = `
  -- Enable RLS on the table
  ALTER TABLE users ENABLE ROW LEVEL SECURITY;

  -- Default policy: only show non-deleted rows
  CREATE POLICY users_default_policy ON users
    FOR ALL
    USING (deleted_at IS NULL);

  -- Admin role can see everything
  CREATE POLICY users_admin_policy ON users
    FOR ALL
    TO admin_role
    USING (true);

  -- Application connects with a role that has the default policy
  -- Deleted rows are invisible without any application code changes
`;
```

### Good: Archival Table Pattern

```typescript
// GOOD: Move deleted records to an archive table
const archivalSchema = `
  CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );

  CREATE TABLE users_archive (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    deleted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_by TEXT, -- who initiated the deletion
    deletion_reason TEXT -- why it was deleted
  );
`;

async function archiveUser(userId: string, deletedBy: string, reason: string): Promise<void> {
  await db.transaction(async (tx) => {
    // Copy to archive
    await tx.query(
      `INSERT INTO users_archive (id, email, name, created_at, deleted_by, deletion_reason)
       SELECT id, email, name, created_at, $2, $3
       FROM users WHERE id = $1`,
      [userId, deletedBy, reason]
    );

    // Remove from active table
    await tx.query("DELETE FROM users WHERE id = $1", [userId]);
  });
}

async function restoreUser(userId: string): Promise<void> {
  await db.transaction(async (tx) => {
    // Restore from archive
    await tx.query(
      `INSERT INTO users (id, email, name, created_at)
       SELECT id, email, name, created_at
       FROM users_archive WHERE id = $1`,
      [userId]
    );

    // Remove from archive
    await tx.query("DELETE FROM users_archive WHERE id = $1", [userId]);
  });
}
```

### Good: GDPR-Compliant Deletion

```typescript
// GOOD: Actual data erasure for GDPR compliance
interface DeletionRequest {
  userId: string;
  requestedAt: Date;
  processedAt: Date | null;
  status: "pending" | "processing" | "completed" | "failed";
}

async function processGdprDeletion(userId: string): Promise<void> {
  await db.transaction(async (tx) => {
    // Option A: Full hard delete if no referential integrity issues
    // await tx.query("DELETE FROM users WHERE id = $1", [userId]);

    // Option B: Anonymize — preserve the record for analytics but remove PII
    await tx.query(
      `UPDATE users SET
        email = 'deleted-' || id || '@anonymized.local',
        name = 'Deleted User',
        phone = NULL,
        address = NULL,
        ip_address = NULL,
        deleted_at = NOW(),
        anonymized_at = NOW()
       WHERE id = $1`,
      [userId]
    );

    // Delete from all secondary stores
    await tx.query("DELETE FROM user_sessions WHERE user_id = $1", [userId]);
    await tx.query("DELETE FROM user_preferences WHERE user_id = $1", [userId]);

    // Log the deletion for compliance audit (without PII)
    await tx.query(
      `INSERT INTO deletion_audit_log (user_id, action, processed_at)
       VALUES ($1, 'gdpr_erasure', NOW())`,
      [userId]
    );
  });

  // Clean up external systems
  await searchIndex.delete(`user:${userId}`);
  await cache.del(`user:${userId}`);
  await analyticsService.anonymize(userId);
}
```

## Alternatives

| Approach | Best For | Trade-off |
|----------|----------|-----------|
| **Hard delete** | Simple systems, GDPR compliance | No undo, referential integrity issues |
| **Soft delete (flag)** | Undo capability, audit trails | Query complexity, storage growth |
| **Archive table** | Clean active tables, long-term retention | Migration complexity, restore logic |
| **Anonymization** | GDPR + analytics preservation | Complex to ensure all PII is covered |
| **Event sourcing** | Full history by design | Significant implementation cost |
| **TTL-based expiry** | Ephemeral data (sessions, logs) | No manual deletion needed |

## When NOT to Apply (Soft Delete)

- **GDPR/privacy-regulated data**: Soft delete does not satisfy "right to erasure." You must actually remove or anonymize personal data.
- **High-volume transactional tables**: Soft-deleted rows accumulate, bloating table size and slowing queries. If you delete millions of rows per month, archival or hard delete is better.
- **When you never restore data**: If "restore" is not a real use case, soft delete adds complexity for no benefit. Consider an audit log instead.
- **Unique constraints**: A soft-deleted user with email `alice@example.com` still occupies that unique constraint. New users cannot use that email unless you use partial unique indexes (`WHERE deleted_at IS NULL`).

## Trade-offs

- **Undo capability vs. data hygiene**: Soft delete enables "undelete" but pollutes the active dataset. Every query, every index, every backup includes dead data.
- **Referential integrity**: Hard delete of a user breaks foreign keys in orders, comments, and logs. Soft delete preserves references but makes "deleted user" a state your application must handle everywhere.
- **Index performance**: Partial indexes (`WHERE deleted_at IS NULL`) mitigate the cost of filtering, but not all databases support them efficiently.
- **Cascading deletion**: When a user is soft-deleted, should their orders also be soft-deleted? Their comments? Their uploaded files? Define the cascade policy explicitly.
- **Unique constraints**: Use partial unique indexes: `CREATE UNIQUE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;` This allows the same email to be reused after soft deletion.

## Further Reading

- [GDPR Article 17 — Right to Erasure](https://gdpr-info.eu/art-17-gdpr/)
- [Brandur Leach — Soft Deletion Probably Isn't Worth It](https://brandur.org/soft-deletion)
- [PostgreSQL — Partial Indexes](https://www.postgresql.org/docs/current/indexes-partial.html)
- [PostgreSQL — Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
