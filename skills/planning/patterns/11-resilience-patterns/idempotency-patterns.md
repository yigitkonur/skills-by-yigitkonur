# Idempotency Patterns

**Ensure that performing an operation multiple times produces the same result as performing it once.**

---

## Origin / History

Idempotency is a mathematical concept (f(f(x)) = f(x)) that entered computing through HTTP's design. RFC 2616 defined GET, PUT, and DELETE as idempotent methods, while POST was explicitly not. The practical importance exploded with distributed systems and message queues, where at-least-once delivery is the norm and exactly-once delivery is theoretically impossible in the general case (per the Two Generals' Problem). Stripe popularized the idempotency key pattern in 2016 with their API, giving developers a simple, practical mechanism for safe retries of payment operations. Today, idempotency keys are a standard feature of payment APIs (Stripe, Square, Adyen) and cloud APIs (AWS, GCP).

## The Problem It Solves

In distributed systems, operations can be executed more than once due to retries, duplicate messages, network partitions, or user double-clicks. Without idempotency, these duplicate executions cause real damage: customers are charged twice, inventory is decremented twice, emails are sent twice, database records are duplicated. The fundamental issue is that the network does not guarantee exactly-once delivery, so the application must handle duplicates itself.

## The Principle Explained

An idempotent operation produces the same outcome regardless of how many times it is executed. There are several strategies to achieve this:

**Natural idempotency** means the operation is inherently idempotent. Setting a value (`user.email = "new@example.com"`) is naturally idempotent — doing it twice has the same effect as doing it once. Incrementing a counter (`balance += 10`) is NOT naturally idempotent.

**Idempotency keys** attach a unique client-generated identifier to each operation. The server stores the key and its result. On subsequent requests with the same key, the server returns the stored result without re-executing the operation. This is the most common pattern for APIs.

**Deduplication** at the receiver side uses message IDs or content hashes to detect and discard duplicate messages. This is essential for message queue consumers, where the queue guarantees at-least-once but not exactly-once delivery.

**Idempotent receivers** design the processing logic so that reprocessing a message is safe. Instead of "add $10 to balance," the operation becomes "set balance to $110 for transaction TX-123." The second execution is a no-op because the transaction is already applied.

## Code Examples

### GOOD: Idempotency key middleware with stored results

```typescript
interface IdempotencyRecord {
  key: string;
  statusCode: number;
  responseBody: string;
  createdAt: Date;
  expiresAt: Date;
}

class IdempotencyStore {
  constructor(private readonly db: Database) {}

  async getOrLock(key: string): Promise<IdempotencyRecord | "locked" | null> {
    // Atomic: either find existing record, acquire lock, or return null
    return this.db.transaction(async (tx) => {
      const existing = await tx.query<IdempotencyRecord>(
        `SELECT * FROM idempotency_keys WHERE key = $1 AND expires_at > NOW()`,
        [key]
      );

      if (existing) {
        if (existing.statusCode === 0) return "locked"; // Another request is processing
        return existing;
      }

      // Insert a "processing" placeholder to lock this key
      await tx.query(
        `INSERT INTO idempotency_keys (key, status_code, response_body, created_at, expires_at)
         VALUES ($1, 0, '', NOW(), NOW() + INTERVAL '24 hours')`,
        [key]
      );

      return null; // Key is new; caller should proceed
    });
  }

  async store(key: string, statusCode: number, body: string): Promise<void> {
    await this.db.query(
      `UPDATE idempotency_keys SET status_code = $2, response_body = $3 WHERE key = $1`,
      [key, statusCode, body]
    );
  }

  async release(key: string): Promise<void> {
    // If processing fails, release the lock so the client can retry
    await this.db.query(`DELETE FROM idempotency_keys WHERE key = $1 AND status_code = 0`, [key]);
  }
}

// Express-style middleware
function idempotencyMiddleware(store: IdempotencyStore) {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    const idempotencyKey = req.headers["idempotency-key"] as string | undefined;

    if (!idempotencyKey) {
      // No key provided — process normally (not idempotent)
      return next();
    }

    const result = await store.getOrLock(idempotencyKey);

    if (result === "locked") {
      res.status(409).json({ error: "A request with this idempotency key is already being processed" });
      return;
    }

    if (result !== null) {
      // Return the stored response
      res.status(result.statusCode).json(JSON.parse(result.responseBody));
      return;
    }

    // Intercept the response to store it
    const originalJson = res.json.bind(res);
    res.json = (body: unknown) => {
      store.store(idempotencyKey, res.statusCode, JSON.stringify(body));
      return originalJson(body);
    };

    try {
      await next();
    } catch (error) {
      // Release the lock so the client can retry with the same key
      await store.release(idempotencyKey);
      throw error;
    }
  };
}

// Idempotent message consumer
interface PaymentEvent {
  eventId: string;
  orderId: string;
  amount: number;
  currency: string;
}

async function processPaymentEvent(event: PaymentEvent): Promise<void> {
  // Instead of "charge amount," we "ensure this specific charge exists"
  const existingCharge = await db.query(
    `SELECT id FROM charges WHERE event_id = $1`,
    [event.eventId]
  );

  if (existingCharge) {
    logger.info(`Charge for event ${event.eventId} already processed. Skipping.`);
    return; // Idempotent: already processed
  }

  await db.transaction(async (tx) => {
    // Insert with the event ID as a unique constraint
    await tx.query(
      `INSERT INTO charges (event_id, order_id, amount, currency, created_at)
       VALUES ($1, $2, $3, $4, NOW())
       ON CONFLICT (event_id) DO NOTHING`,
      [event.eventId, event.orderId, event.amount, event.currency]
    );

    // Update the order status idempotently
    await tx.query(
      `UPDATE orders SET status = 'paid', paid_at = NOW()
       WHERE id = $1 AND status = 'pending'`,
      [event.orderId]
    );
  });
}
```

### BAD: Non-idempotent payment processing

```typescript
// If this function runs twice (due to a retry, duplicate message,
// or network timeout where the first request actually succeeded),
// the customer is charged twice.
async function processPayment(orderId: string, amount: number): Promise<void> {
  // No check for duplicate processing
  const charge = await paymentGateway.charge({
    amount,
    currency: "usd",
    // No idempotency key — gateway will create a new charge each time
  });

  // No deduplication on insert — creates duplicate records
  await db.query(
    `INSERT INTO charges (order_id, amount, gateway_id) VALUES ($1, $2, $3)`,
    [orderId, amount, charge.id]
  );

  // Incrementing is NOT idempotent
  await db.query(
    `UPDATE orders SET total_paid = total_paid + $1 WHERE id = $2`,
    [amount, orderId]
  );
}
```

## Alternatives & Related Approaches

| Approach | When to prefer it |
|---|---|
| **Exactly-once delivery** | Impossible in the general case. Some systems (Kafka with transactions) approximate it within a bounded system |
| **Database transactions** | When all operations are within a single database and ACID guarantees are sufficient |
| **Compensating transactions** | When you cannot prevent duplicates but can detect and reverse them after the fact |
| **Event sourcing** | When you can replay events to reconstruct state — naturally supports deduplication via event IDs |

## When NOT to Apply

- **Read operations** are inherently idempotent. Do not add idempotency key infrastructure to GET requests.
- **Naturally idempotent writes** like absolute updates (`SET status = 'active'`) do not need keys.
- **Low-consequence operations** where duplicates are harmless (logging, analytics events) — the overhead is not worth it.
- **Interactive user sessions** where the user controls retries. A "submit" button with client-side debouncing may be sufficient.

## Tensions & Trade-offs

- **Storage overhead:** Idempotency keys must be stored and indexed. For high-throughput systems, this means millions of key records that need TTL-based cleanup.
- **Key expiration:** Keys must expire eventually, but if they expire too soon, a late retry may be processed as a new request. Typical TTLs are 24-72 hours.
- **Concurrent requests with the same key:** Two requests with the same key arriving simultaneously must be serialized (one processes, one waits or is rejected). This requires locking, which adds complexity and latency.
- **Response consistency:** The stored response must be returned exactly as the original. If the response format changes between code deployments, cached responses may be incompatible.
- **Partial failures:** If the operation partially completes before failing, the idempotency key should be released (not stored), allowing the client to retry. But determining "partial completion" requires careful transaction management.

## Real-World Consequences

Stripe processes billions of dollars in payments. Their idempotency key system ensures that a client timeout followed by a retry never results in a double charge. The client generates a UUID, attaches it as the `Idempotency-Key` header, and Stripe guarantees that the charge is executed at most once per key.

A major food delivery platform suffered a $2M loss from double-charging customers during a network instability event. Their payment API lacked idempotency keys. Retried requests created duplicate charges. The fix was straightforward (add idempotency keys to the payment gateway call), but the damage was already done in customer trust and refund processing costs.

## Further Reading

- [Stripe: Idempotent Requests](https://stripe.com/docs/api/idempotent_requests)
- [AWS: Idempotency in Event-Driven Architecture](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)
- [Martin Kleppmann: Designing Data-Intensive Applications](https://dataintensive.net/) — exactly-once semantics discussion
- [Brandur Leach: Implementing Stripe-like Idempotency Keys in Postgres](https://brandur.org/idempotency-keys)
