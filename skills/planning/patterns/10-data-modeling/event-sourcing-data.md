# Event Sourcing as a Data Model

## Origin

Event sourcing was articulated by Martin Fowler and further popularized by Greg Young in the late 2000s within the CQRS/DDD community. The core insight comes from accounting: ledgers record every transaction, and the current balance is derived from the history. Version control systems (Git) are another manifestation — the repository state is the sum of all commits. Event sourcing applies this principle to application data: store every state change as an immutable event, and derive current state by replaying events.

## Explanation

### Core Concepts

**Events as source of truth**: Instead of storing the current state of an entity, you store every event that ever happened to it. The current state is a derived projection.

**Event store**: An append-only log of events. Events are immutable — you never update or delete them. Each event has a type, a timestamp, and a payload.

**Projections (Read Models)**: Materialized views built by processing events. You can have multiple projections optimized for different query patterns, rebuilt from scratch at any time.

**Snapshots**: Periodic captures of projected state to avoid replaying the entire event history. A performance optimization, not a fundamental concept.

### Event Sourcing vs. CRUD

| CRUD | Event Sourcing |
|------|---------------|
| Current state stored | Full history stored |
| UPDATE overwrites | Append-only, immutable |
| "What is the state?" | "What happened and why?" |
| Single data shape | Multiple projections |
| Simple to implement | Complex to implement |

## TypeScript Code Examples

### Bad: Losing History with CRUD Updates

```typescript
// BAD: Each update overwrites previous state — history is lost
async function updateOrderStatus(orderId: string, status: string): Promise<void> {
  await db.query("UPDATE orders SET status = $1 WHERE id = $2", [status, orderId]);
  // Question: What was the previous status? When did it change? Who changed it?
  // Answer: Nobody knows. The data is gone.
}
```

### Good: Event-Sourced Order Aggregate

```typescript
// GOOD: Every state change is an immutable event
// Event definitions
type OrderEvent =
  | { type: "OrderPlaced"; orderId: string; customerId: string; items: OrderItem[]; occurredAt: Date }
  | { type: "OrderConfirmed"; orderId: string; confirmedBy: string; occurredAt: Date }
  | { type: "PaymentReceived"; orderId: string; amountCents: number; paymentId: string; occurredAt: Date }
  | { type: "OrderShipped"; orderId: string; trackingNumber: string; occurredAt: Date }
  | { type: "OrderCancelled"; orderId: string; reason: string; cancelledBy: string; occurredAt: Date };

// Current state derived from events
interface OrderState {
  id: string;
  customerId: string;
  items: OrderItem[];
  status: "placed" | "confirmed" | "paid" | "shipped" | "cancelled";
  totalCents: number;
  trackingNumber: string | null;
}

// Left fold: replay events to build current state
function buildOrderState(events: OrderEvent[]): OrderState | null {
  if (events.length === 0) return null;

  let state: OrderState | null = null;

  for (const event of events) {
    switch (event.type) {
      case "OrderPlaced":
        state = {
          id: event.orderId,
          customerId: event.customerId,
          items: event.items,
          status: "placed",
          totalCents: event.items.reduce((sum, i) => sum + i.priceCents * i.quantity, 0),
          trackingNumber: null,
        };
        break;

      case "OrderConfirmed":
        if (state) state.status = "confirmed";
        break;

      case "PaymentReceived":
        if (state) state.status = "paid";
        break;

      case "OrderShipped":
        if (state) {
          state.status = "shipped";
          state.trackingNumber = event.trackingNumber;
        }
        break;

      case "OrderCancelled":
        if (state) state.status = "cancelled";
        break;
    }
  }

  return state;
}
```

### Good: Event Store Implementation

```typescript
// GOOD: Append-only event store with optimistic concurrency
const eventStoreSchema = `
  CREATE TABLE events (
    id BIGSERIAL PRIMARY KEY,
    stream_id TEXT NOT NULL,
    stream_version INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (stream_id, stream_version)
  );

  CREATE INDEX idx_events_stream ON events(stream_id, stream_version);
  CREATE INDEX idx_events_type ON events(event_type);
`;

async function appendEvents(
  streamId: string,
  expectedVersion: number,
  events: OrderEvent[]
): Promise<void> {
  await db.transaction(async (tx) => {
    // Optimistic concurrency check
    const current = await tx.query(
      "SELECT MAX(stream_version) as version FROM events WHERE stream_id = $1",
      [streamId]
    );
    const currentVersion = current.rows[0]?.version ?? 0;

    if (currentVersion !== expectedVersion) {
      throw new ConcurrencyError(
        `Expected version ${expectedVersion}, but stream is at ${currentVersion}`
      );
    }

    // Append events
    for (let i = 0; i < events.length; i++) {
      const event = events[i];
      await tx.query(
        `INSERT INTO events (stream_id, stream_version, event_type, payload, occurred_at)
         VALUES ($1, $2, $3, $4, $5)`,
        [streamId, expectedVersion + i + 1, event.type, event, event.occurredAt]
      );
    }
  });
}

async function loadEvents(streamId: string): Promise<OrderEvent[]> {
  const result = await db.query(
    "SELECT payload FROM events WHERE stream_id = $1 ORDER BY stream_version ASC",
    [streamId]
  );
  return result.rows.map((row) => row.payload as OrderEvent);
}
```

### Good: Projection and Snapshot

```typescript
// GOOD: Projection builds a read-optimized view from events
async function projectOrderToReadModel(streamId: string): Promise<void> {
  const events = await loadEvents(streamId);
  const state = buildOrderState(events);

  if (!state) return;

  await db.query(
    `INSERT INTO order_read_model (id, customer_id, status, total_cents, tracking_number, updated_at)
     VALUES ($1, $2, $3, $4, $5, NOW())
     ON CONFLICT (id) DO UPDATE SET
       status = EXCLUDED.status,
       total_cents = EXCLUDED.total_cents,
       tracking_number = EXCLUDED.tracking_number,
       updated_at = NOW()`,
    [state.id, state.customerId, state.status, state.totalCents, state.trackingNumber]
  );
}

// GOOD: Snapshot to avoid replaying thousands of events
interface Snapshot<T> {
  streamId: string;
  version: number;
  state: T;
  createdAt: Date;
}

async function loadWithSnapshot(streamId: string): Promise<OrderState | null> {
  // Try loading from snapshot first
  const snapshot = await db.query(
    "SELECT version, state FROM snapshots WHERE stream_id = $1 ORDER BY version DESC LIMIT 1",
    [streamId]
  );

  let startVersion = 0;
  let state: OrderState | null = null;

  if (snapshot.rows.length > 0) {
    startVersion = snapshot.rows[0].version;
    state = snapshot.rows[0].state as OrderState;
  }

  // Replay only events after the snapshot
  const result = await db.query(
    "SELECT payload FROM events WHERE stream_id = $1 AND stream_version > $2 ORDER BY stream_version ASC",
    [streamId, startVersion]
  );

  const newEvents = result.rows.map((r) => r.payload as OrderEvent);

  if (state && newEvents.length > 0) {
    // Continue building from snapshot state
    for (const event of newEvents) {
      state = applyEvent(state, event);
    }
  } else if (!state) {
    state = buildOrderState(newEvents);
  }

  return state;
}
```

## Alternatives

| Approach | Best For | Trade-off |
|----------|----------|-----------|
| **CRUD with audit log** | Adding history to existing systems | Audit log is secondary, can diverge |
| **Change Data Capture (Debezium)** | Streaming changes from existing databases | Relies on database internals |
| **Temporal tables** (SQL:2011) | Built-in history in supported databases | Limited query flexibility |
| **Git-style versioning** | Document versioning (CMS, wikis) | Not suited for transactional data |

## When NOT to Apply

- **Simple CRUD applications**: A blog, a task manager, a contact list. Event sourcing adds enormous complexity for entities where the history has no business value.
- **When you only need an audit log**: An audit log table alongside CRUD is 10x simpler and serves 90% of "I need history" requirements.
- **High-frequency, low-value events**: Storing every mouse click or page view as an event will overwhelm your event store. Use analytics pipelines instead.
- **Teams without DDD experience**: Event sourcing is deeply intertwined with domain-driven design. Without aggregates and bounded contexts, event sourcing becomes a formless append-only table.
- **When eventual consistency is unacceptable**: Projections are eventually consistent with the event store. If your domain requires strong consistency for reads, event sourcing creates friction.

## Trade-offs

- **Complete audit trail vs. complexity**: You get a perfect history of everything that happened, but the implementation is significantly more complex than CRUD.
- **Projection flexibility vs. rebuild time**: You can create any read model from events, but rebuilding projections from scratch on a large event store can take hours.
- **Storage growth**: Events accumulate forever. Snapshots reduce read cost but the event store itself grows indefinitely. Plan for archival and compaction strategies.
- **Schema evolution of events**: Events are immutable, but their schema must evolve. You need upcasters that transform old event shapes into new ones during replay.
- **Debugging difficulty**: Instead of looking at a row and seeing current state, you must replay events to understand how the system reached a particular state.

## Further Reading

- [Martin Fowler — Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
- [Greg Young — CQRS and Event Sourcing](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf)
- [EventStoreDB — Event Sourcing Database](https://www.eventstore.com/)
- [Marten — Event Sourcing for .NET/PostgreSQL](https://martendb.io/)
- [Axon Framework — Event Sourcing for Java/Kotlin](https://www.axoniq.io/)
