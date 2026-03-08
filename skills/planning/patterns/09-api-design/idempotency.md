# Idempotency in API Design

## Origin

The concept of idempotency comes from mathematics: an operation is idempotent if applying it multiple times produces the same result as applying it once. In distributed systems, network failures, timeouts, and retries make idempotency essential. Stripe popularized the idempotency key pattern for payment APIs, making safe retries a first-class design concern.

## Explanation

An API operation is idempotent if making the same request N times has the same effect as making it once.

### HTTP Method Idempotency (by specification)

| Method | Idempotent | Safe | Notes |
|--------|-----------|------|-------|
| GET | Yes | Yes | Must never cause side effects |
| HEAD | Yes | Yes | Same as GET without body |
| PUT | Yes | No | Full replacement; same input = same result |
| DELETE | Yes | No | Deleting twice = resource still gone |
| PATCH | No* | No | Depends on implementation |
| POST | No | No | Requires explicit idempotency handling |

### Why It Matters

Consider a payment flow: a client sends a POST to charge $100. The server processes it but the response is lost due to a network timeout. The client retries. Without idempotency, the customer is charged $200. With an idempotency key, the server recognizes the duplicate and returns the original response.

### Idempotency Key Pattern

1. Client generates a unique key (typically a UUID) and sends it in a header.
2. Server checks if this key has been seen before.
3. If yes, return the stored response without re-executing.
4. If no, execute the operation, store the response keyed by the idempotency key, and return it.

## TypeScript Code Examples

### Bad: Non-Idempotent Payment Endpoint

```typescript
// BAD: Every retry creates a new charge
app.post("/charges", async (req, res) => {
  const { amount, currency, customerId } = req.body;

  // No idempotency check — retries will duplicate the charge
  const charge = await paymentGateway.charge({
    amount,
    currency,
    customerId,
  });

  await db.charges.insert(charge);
  res.status(201).json({ data: charge });
});
```

### Good: Idempotency Key Implementation

```typescript
// GOOD: Idempotency keys prevent duplicate processing
interface StoredResult {
  statusCode: number;
  body: unknown;
  createdAt: Date;
}

async function getIdempotencyResult(key: string): Promise<StoredResult | null> {
  return db.idempotencyKeys.findOne({ key });
}

async function storeIdempotencyResult(
  key: string,
  statusCode: number,
  body: unknown
): Promise<void> {
  await db.idempotencyKeys.insert({
    key,
    statusCode,
    body,
    createdAt: new Date(),
  });
}

app.post("/charges", async (req, res) => {
  const idempotencyKey = req.headers["idempotency-key"] as string;

  if (!idempotencyKey) {
    return res.status(400).json({
      error: "Idempotency-Key header is required for POST requests",
    });
  }

  // Check for existing result
  const existing = await getIdempotencyResult(idempotencyKey);
  if (existing) {
    res.setHeader("X-Idempotent-Replayed", "true");
    return res.status(existing.statusCode).json(existing.body);
  }

  // Process the charge
  const { amount, currency, customerId } = req.body;
  const charge = await paymentGateway.charge({ amount, currency, customerId });
  await db.charges.insert(charge);

  // Store result for future replays
  const responseBody = { data: charge };
  await storeIdempotencyResult(idempotencyKey, 201, responseBody);

  res.status(201).json(responseBody);
});
```

### Good: Middleware-Based Idempotency with Locking

```typescript
// GOOD: Reusable middleware with concurrent request protection
import { randomUUID } from "crypto";

interface IdempotencyRecord {
  key: string;
  lockId: string | null;
  statusCode: number | null;
  body: unknown | null;
  lockedAt: Date | null;
  completedAt: Date | null;
}

function idempotencyMiddleware(options: { ttlSeconds: number }) {
  return async (req: Request, res: Response, next: NextFunction) => {
    if (req.method !== "POST") return next();

    const key = req.headers["idempotency-key"] as string;
    if (!key) return next(); // Optional: make it required

    const lockId = randomUUID();

    // Attempt to acquire lock or find completed result
    const record = await db.idempotencyKeys.findOneAndUpdate(
      { key, lockId: null, completedAt: null },
      { $set: { lockId, lockedAt: new Date() } },
      { upsert: true, returnDocument: "after" }
    );

    // Already completed — replay the response
    if (record.completedAt) {
      res.setHeader("X-Idempotent-Replayed", "true");
      return res.status(record.statusCode!).json(record.body);
    }

    // Another request holds the lock — conflict
    if (record.lockId !== lockId) {
      return res.status(409).json({ error: "Request already in progress" });
    }

    // Intercept res.json to capture the response
    const originalJson = res.json.bind(res);
    res.json = (body: unknown) => {
      db.idempotencyKeys.updateOne(
        { key, lockId },
        {
          $set: {
            statusCode: res.statusCode,
            body,
            completedAt: new Date(),
            lockId: null,
          },
        }
      );
      return originalJson(body);
    };

    next();
  };
}

app.use("/payments", idempotencyMiddleware({ ttlSeconds: 86400 }));
```

### Good: Making PUT Truly Idempotent

```typescript
// GOOD: PUT as full replacement is naturally idempotent
app.put("/orders/:id", async (req, res) => {
  const { id } = req.params;
  const orderData: OrderInput = req.body;

  // Full replacement — same input always produces the same state
  const order = await db.orders.replaceOne(
    { id },
    { ...orderData, id, updatedAt: new Date() },
    { upsert: false }
  );

  if (!order) return res.status(404).json({ error: "Order not found" });
  res.status(200).json({ data: order });
});
```

## Alternatives

| Approach | Best For | Trade-off |
|----------|----------|-----------|
| **Client-generated IDs** | Resources where the client controls identity | Requires UUID coordination |
| **Conditional requests (ETag/If-Match)** | Update operations | Only prevents lost updates, not duplicate creation |
| **Database unique constraints** | Simple deduplication | Limited to insert operations |
| **Message deduplication (SQS, Kafka)** | Async event processing | Infrastructure-level, not API-level |

## When NOT to Apply

- **GET, HEAD, OPTIONS requests**: These are safe and idempotent by definition. Adding idempotency keys to reads is pointless overhead.
- **Internal synchronous calls in a monolith**: If there is no network boundary, there is no retry ambiguity.
- **Fire-and-forget analytics events**: Occasional duplicates in analytics are usually acceptable and the deduplication cost is not justified.
- **Streaming endpoints**: Idempotency keys do not map well to continuous data flows.

## Trade-offs

- **Storage cost**: Every idempotency key and its response must be stored. Set a TTL (24-48 hours is typical) and clean up expired records.
- **Locking complexity**: Concurrent retries of the same key need protection. Without locking, two requests might both pass the "not seen" check and execute the operation twice.
- **Payload matching**: Should you verify that retried requests have the same body? Stripe returns an error if the body differs for the same key. This prevents misuse but adds comparison overhead.
- **Response fidelity**: Stored responses must be complete. If your response includes dynamic data (e.g., current timestamps), replayed responses will show stale values.

## Further Reading

- [Stripe — Idempotent Requests](https://stripe.com/docs/api/idempotent_requests)
- [Designing Robust and Predictable APIs with Idempotency — Brandur](https://brandur.org/idempotency-keys)
- [IETF — The Idempotency-Key HTTP Header Field](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/)
- [AWS — Making Retries Safe with Idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)
