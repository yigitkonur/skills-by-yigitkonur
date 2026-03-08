# Optimistic vs. Pessimistic Locking

**Two strategies for handling concurrent access to shared resources: assume conflicts are rare and detect them (optimistic), or prevent conflicts by acquiring exclusive access upfront (pessimistic).**

---

## Origin / History

Pessimistic locking is the older approach, rooted in database systems of the 1970s. IBM's System R (1974) and its descendants used locks (shared and exclusive) to prevent concurrent transactions from interfering. The two-phase locking protocol (2PL) became the standard for serializable isolation.

Optimistic concurrency control (OCC) was formalized by H.T. Kung and John T. Robinson in 1981 at Carnegie Mellon. Instead of acquiring locks, transactions execute without restriction and are validated at commit time — if a conflict is detected, the transaction is rolled back and retried. HTTP ETags (RFC 7232, 1999) brought optimistic concurrency to web APIs. Compare-and-swap (CAS) CPU instructions, used in lock-free data structures, are the hardware-level manifestation of optimistic concurrency.

Modern systems often combine both: PostgreSQL uses MVCC (multi-version concurrency control) with optimistic reads and pessimistic writes. DynamoDB uses optimistic locking via version attributes. Redis provides optimistic transactions via WATCH/MULTI/EXEC.

---

## The Problem It Solves

When two operations try to modify the same resource simultaneously, the result without coordination is a lost update: one operation's changes silently overwrite the other's. In a web application, this manifests as the "last write wins" problem — two users edit the same document, and one user's changes disappear.

Pessimistic locking prevents the problem by ensuring only one operation can access the resource at a time. But locking has costs: reduced throughput (operations queue behind the lock), deadlock risk (two operations each hold a lock the other needs), and complexity (lock management, timeout handling, cleanup on crashes).

Optimistic locking avoids these costs by allowing concurrent access and detecting conflicts at commit time. If conflicts are rare (the common case in many applications), optimistic locking provides higher throughput with lower complexity. If conflicts are frequent, optimistic locking degrades into a retry storm — each failed operation retries, increasing contention.

---

## The Principle Explained

Pessimistic locking acquires an exclusive lock before modifying a resource. In SQL, this is `SELECT ... FOR UPDATE` — the row is locked until the transaction commits or rolls back. In application code, it is a mutex or semaphore. The lock guarantees no other operation can read or write the resource while the lock is held. The cost is reduced concurrency: other operations must wait.

Optimistic locking reads the resource along with a version indicator (version number, timestamp, ETag, or hash). When writing, it includes the version in the write condition: "update this resource, but only if the version is still X." If another operation modified the resource in the meantime, the version has changed, the write fails, and the application retries with the new version. No locks are held during the read-modify-write cycle.

The choice between them depends on conflict probability and conflict cost. Low contention (many resources, few writers) favors optimistic locking — locks would add overhead for conflicts that almost never happen. High contention (single resource, many writers) favors pessimistic locking — optimistic retries would waste more time than waiting for a lock.

---

## Code Examples

### Pessimistic locking — SELECT FOR UPDATE

```typescript
import { Pool } from "pg";

const pool = new Pool();

// Pessimistic: lock the row before modifying
async function transferFunds(
  fromAccountId: string,
  toAccountId: string,
  amount: number,
): Promise<void> {
  const client = await pool.connect();
  try {
    await client.query("BEGIN");

    // Lock both rows — consistent ordering prevents deadlocks
    const [id1, id2] = [fromAccountId, toAccountId].sort();
    const res1 = await client.query(
      "SELECT balance FROM accounts WHERE id = $1 FOR UPDATE",
      [id1],
    );
    const res2 = await client.query(
      "SELECT balance FROM accounts WHERE id = $1 FOR UPDATE",
      [id2],
    );

    const fromRow = id1 === fromAccountId ? res1.rows[0] : res2.rows[0];
    const toRow = id1 === fromAccountId ? res2.rows[0] : res1.rows[0];

    if (fromRow.balance < amount) {
      await client.query("ROLLBACK");
      throw new Error("Insufficient funds");
    }

    await client.query(
      "UPDATE accounts SET balance = balance - $1 WHERE id = $2",
      [amount, fromAccountId],
    );
    await client.query(
      "UPDATE accounts SET balance = balance + $1 WHERE id = $2",
      [amount, toAccountId],
    );

    await client.query("COMMIT");
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
}
```

### Optimistic locking — version column

```typescript
// Optimistic: read version, write conditionally, retry on conflict
async function updateUserProfile(
  userId: string,
  updates: Partial<UserProfile>,
  maxRetries: number = 3,
): Promise<UserProfile> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    // Read current state with version
    const result = await pool.query(
      "SELECT *, version FROM user_profiles WHERE id = $1",
      [userId],
    );
    const current = result.rows[0];
    if (!current) throw new Error("User not found");

    const merged = { ...current, ...updates };

    // Write with version check — succeeds only if nobody else updated
    const updateResult = await pool.query(
      `UPDATE user_profiles
       SET name = $1, email = $2, bio = $3, version = version + 1
       WHERE id = $4 AND version = $5
       RETURNING *`,
      [merged.name, merged.email, merged.bio, userId, current.version],
    );

    if (updateResult.rowCount === 1) {
      return updateResult.rows[0]; // Success — no conflict
    }

    // Conflict detected: version changed between read and write
    console.warn(`Optimistic lock conflict (attempt ${attempt + 1}/${maxRetries})`);

    // Optional: exponential backoff before retry
    if (attempt < maxRetries - 1) {
      await new Promise((r) => setTimeout(r, 50 * Math.pow(2, attempt)));
    }
  }

  throw new Error("Failed to update after maximum retries — high contention");
}
```

### HTTP ETag-based optimistic concurrency

```typescript
import express, { Request, Response } from "express";
import crypto from "node:crypto";

function computeETag(data: unknown): string {
  return crypto.createHash("md5").update(JSON.stringify(data)).digest("hex");
}

// GET returns the current state with an ETag header
app.get("/api/documents/:id", async (req: Request, res: Response) => {
  const doc = await getDocument(req.params.id);
  if (!doc) return res.status(404).end();

  const etag = computeETag(doc);
  res.set("ETag", `"${etag}"`);
  res.json(doc);
});

// PUT requires If-Match header with the ETag
app.put("/api/documents/:id", async (req: Request, res: Response) => {
  const ifMatch = req.headers["if-match"];
  if (!ifMatch) {
    return res.status(428).json({ error: "If-Match header required" });
  }

  const current = await getDocument(req.params.id);
  if (!current) return res.status(404).end();

  const currentETag = `"${computeETag(current)}"`;
  if (ifMatch !== currentETag) {
    // 409 Conflict: someone else modified the document
    return res.status(409).json({
      error: "Document was modified by another request",
      currentETag,
      yourETag: ifMatch,
    });
  }

  const updated = await updateDocument(req.params.id, req.body);
  const newETag = computeETag(updated);
  res.set("ETag", `"${newETag}"`);
  res.json(updated);
});
```

### Compare-and-Swap (CAS) — atomic optimistic update

```typescript
// In-memory CAS for a simple counter (illustrative)
class AtomicCounter {
  private value = 0;

  get(): number {
    return this.value;
  }

  // CAS: update only if current value matches expected
  compareAndSwap(expected: number, newValue: number): boolean {
    if (this.value === expected) {
      this.value = newValue;
      return true; // Success
    }
    return false; // Conflict — value changed since we read it
  }

  // Increment using CAS with retry
  increment(): number {
    while (true) {
      const current = this.get();
      if (this.compareAndSwap(current, current + 1)) {
        return current + 1;
      }
      // Conflict: another caller incremented between get and CAS — retry
    }
  }
}
```

---

## Alternatives & Related Approaches

| Approach | Trade-off |
|---|---|
| **CRDTs (Conflict-free Replicated Data Types)** | Data structures that merge automatically without conflicts. No locks or versions needed. Limited to specific operations (counters, sets, registers). |
| **Event Sourcing** | Append-only log — no updates, no conflicts on writes. Conflicts are resolved at read time through event replay. Higher storage cost. |
| **Eventual Consistency** | Accept temporary inconsistency. No locking at all. Suitable when "stale reads are okay" and the system converges. |
| **Last Write Wins (LWW)** | No conflict detection — latest timestamp wins. Simple but loses data. Acceptable only when overwrites are non-destructive. |
| **Application-level merge** | Detect conflicts, present both versions to the user for manual resolution (like Git merge conflicts). Best UX but complex implementation. |

---

## When NOT to Apply

- **Pessimistic locking on read-heavy workloads**: If 99% of operations are reads and 1% are writes, pessimistic locks on reads unnecessarily serialize the system. Use MVCC or optimistic reads.
- **Optimistic locking on high-contention resources**: If many writers target the same row simultaneously (e.g., a global counter), optimistic retries create a retry storm. Use pessimistic locking or atomic operations.
- **Either approach for idempotent operations**: If the operation is naturally idempotent (setting a value rather than incrementing), concurrent execution produces correct results without any locking.
- **Distributed systems without a coordinator**: Traditional locking requires a lock manager. In distributed systems without a single coordinator, consider CRDTs, vector clocks, or consensus algorithms instead.

---

## Tensions & Trade-offs

- **Throughput vs. Correctness**: Pessimistic locking guarantees correctness at the cost of throughput. Optimistic locking offers higher throughput but requires retry logic and conflict resolution.
- **Simplicity vs. Scalability**: `SELECT FOR UPDATE` is simple and correct. But it creates a serialization bottleneck that does not scale horizontally.
- **Retry storms vs. Waiting**: Under contention, optimistic locking retries (wasting work), while pessimistic locking waits (wasting time). The optimal choice depends on operation cost and conflict frequency.
- **Deadlock risk vs. Retry risk**: Pessimistic locking risks deadlocks (two locks held in different order). Optimistic locking risks livelocks (two operations repeatedly conflicting).

---

## Real-World Consequences

**DynamoDB conditional writes**: DynamoDB's entire concurrency model is optimistic — there are no locks. Conditional writes (`ConditionExpression: "version = :v"`) implement optimistic locking. AWS documentation explicitly recommends this pattern for all concurrent updates. Teams that skip it experience silent data loss from concurrent writes.

**Git as optimistic concurrency**: Git uses optimistic concurrency for collaboration. Multiple developers work on branches without locks. Conflicts are detected at merge time and resolved manually. This model scaled to the Linux kernel with thousands of concurrent contributors.

**Inventory overselling**: An e-commerce company used optimistic locking for inventory. During a flash sale, 100 concurrent buyers tried to purchase the last 5 items. Without proper retry limits, the retry storm caused the database connection pool to exhaust. The fix was a hybrid approach: optimistic for low-contention products, pessimistic (`SELECT FOR UPDATE`) for flash sale items.

---

## Further Reading

- [H.T. Kung, J.T. Robinson — On Optimistic Methods for Concurrency Control (1981)](https://www.cs.cmu.edu/~pavlMDO/courses/15-721/papers/p213-kung.pdf)
- [PostgreSQL Documentation — Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html)
- [Martin Kleppmann — Designing Data-Intensive Applications, Chapter 7: Transactions](https://dataintensive.net/)
- [RFC 7232 — HTTP Conditional Requests (ETags)](https://tools.ietf.org/html/rfc7232)
- [AWS DynamoDB — Optimistic Locking with Version Numbers](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBMapper.OptimisticLocking.html)
