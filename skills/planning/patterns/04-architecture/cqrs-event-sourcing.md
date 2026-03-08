# CQRS and Event Sourcing

**Separate read and write models for optimized handling of commands and queries, optionally storing events as the source of truth.**

---

## Origin

CQRS (Command Query Responsibility Segregation) was formalized by Greg Young around 2010, building on Bertrand Meyer's Command-Query Separation (CQS) principle from *"Object-Oriented Software Construction"* (1988). Meyer's CQS states that a method should either change state (command) or return data (query), never both. Young elevated this from method-level to architecture-level: separate the write model (commands) from the read model (queries) entirely.

Event Sourcing, often paired with CQRS, has roots in accounting (ledgers are event-sourced by nature) and was formalized in the DDD community by Greg Young and Martin Fowler. The idea is to store every state change as an immutable event rather than storing only the current state. The current state is derived by replaying events.

---

## The Problem It Solves

In a traditional CRUD application, the same data model serves both reads and writes. This creates tension: the write model needs normalization, validation, and invariant enforcement; the read model needs denormalization, joins, and query optimization. You end up with a model that is a compromise — not ideal for either purpose. Complex queries require expensive joins across normalized tables, while writes must update denormalized views to keep reads fast. As the system grows, these competing concerns become irreconcilable.

---

## The Principle Explained

**CQRS** splits the application into two sides. The **command side** handles writes: it validates input, enforces business rules, and persists state changes. The **query side** handles reads: it serves pre-computed, denormalized views optimized for specific use cases. The two sides can use different data stores, different models, and different scaling strategies.

**Event Sourcing** replaces the traditional "store current state" approach with "store the sequence of events that led to the current state." Instead of an `orders` table with a `status` column that gets updated, you store events: `OrderCreated`, `ItemAdded`, `OrderPaid`, `OrderShipped`. The current state is a projection — a materialized view built by replaying events.

The two patterns are independent but complementary. You can use CQRS without Event Sourcing (separate read/write databases, both storing current state). You can use Event Sourcing without CQRS (single model, events as storage). Together, they are powerful: events are written to an append-only event store (command side), and projections read those events to build optimized query models (query side).

---

## Code Examples

### BAD: Single model struggling with competing read/write concerns

```typescript
// One model tries to serve both reads and writes — compromise everywhere
class OrderRepository {
  // Write: needs validation, invariants, transactional integrity
  async updateOrderStatus(orderId: string, status: string): Promise<void> {
    // But how do we know what transitions are valid?
    // The "status" column has lost the history of transitions
    await this.db.query(
      "UPDATE orders SET status = $1, updated_at = NOW() WHERE id = $2",
      [status, orderId]
    );
  }

  // Read: needs denormalized data — joins are expensive at scale
  async getOrderDashboard(customerId: string): Promise<DashboardData> {
    // This query joins 5 tables and is slow at scale
    const result = await this.db.query(`
      SELECT o.*, c.name as customer_name,
             array_agg(oi.product_name) as products,
             p.status as payment_status,
             s.tracking_number
      FROM orders o
      JOIN customers c ON o.customer_id = c.id
      JOIN order_items oi ON o.id = oi.order_id
      LEFT JOIN payments p ON o.id = p.order_id
      LEFT JOIN shipments s ON o.id = s.order_id
      WHERE o.customer_id = $1
      GROUP BY o.id, c.name, p.status, s.tracking_number
      ORDER BY o.created_at DESC
    `, [customerId]);
    return result.rows;
  }
}

// Problem: to make reads fast, we denormalize — but then writes must
// update multiple denormalized views, creating consistency issues.
// Problem: we lost the audit trail — we cannot answer "when was this
// order shipped?" without a separate audit table.
```

### GOOD: CQRS with Event Sourcing

```typescript
// ============================================
// COMMAND SIDE — write model, enforces business rules
// ============================================

// Events — immutable facts
interface OrderEvent {
  readonly eventId: string;
  readonly orderId: string;
  readonly occurredAt: Date;
  readonly type: string;
}

class OrderCreated implements OrderEvent {
  readonly type = "OrderCreated";
  constructor(
    readonly eventId: string,
    readonly orderId: string,
    readonly customerId: string,
    readonly occurredAt: Date
  ) {}
}

class ItemAdded implements OrderEvent {
  readonly type = "ItemAdded";
  constructor(
    readonly eventId: string,
    readonly orderId: string,
    readonly productId: string,
    readonly quantity: number,
    readonly unitPrice: number,
    readonly occurredAt: Date
  ) {}
}

class OrderConfirmed implements OrderEvent {
  readonly type = "OrderConfirmed";
  constructor(
    readonly eventId: string,
    readonly orderId: string,
    readonly total: number,
    readonly occurredAt: Date
  ) {}
}

class OrderShipped implements OrderEvent {
  readonly type = "OrderShipped";
  constructor(
    readonly eventId: string,
    readonly orderId: string,
    readonly trackingNumber: string,
    readonly occurredAt: Date
  ) {}
}

// Aggregate — rebuilt from events, enforces invariants
class OrderAggregate {
  private id: string = "";
  private customerId: string = "";
  private items: Array<{ productId: string; quantity: number; unitPrice: number }> = [];
  private status: "draft" | "confirmed" | "shipped" | "cancelled" = "draft";
  private uncommittedEvents: OrderEvent[] = [];

  // Rebuild state from historical events
  static fromEvents(events: OrderEvent[]): OrderAggregate {
    const order = new OrderAggregate();
    for (const event of events) {
      order.apply(event, false);
    }
    return order;
  }

  // Command: business logic + event production
  static create(orderId: string, customerId: string): OrderAggregate {
    const order = new OrderAggregate();
    order.apply(
      new OrderCreated(generateId(), orderId, customerId, new Date()),
      true
    );
    return order;
  }

  addItem(productId: string, quantity: number, unitPrice: number): void {
    if (this.status !== "draft") {
      throw new Error("Cannot add items to a non-draft order");
    }
    if (this.items.length >= 50) {
      throw new Error("Maximum 50 items per order");
    }
    this.apply(
      new ItemAdded(generateId(), this.id, productId, quantity, unitPrice, new Date()),
      true
    );
  }

  confirm(): void {
    if (this.status !== "draft") throw new Error("Order is not in draft status");
    if (this.items.length === 0) throw new Error("Cannot confirm an empty order");
    const total = this.items.reduce((sum, i) => sum + i.quantity * i.unitPrice, 0);
    this.apply(new OrderConfirmed(generateId(), this.id, total, new Date()), true);
  }

  ship(trackingNumber: string): void {
    if (this.status !== "confirmed") throw new Error("Order must be confirmed first");
    this.apply(new OrderShipped(generateId(), this.id, trackingNumber, new Date()), true);
  }

  getUncommittedEvents(): OrderEvent[] {
    return [...this.uncommittedEvents];
  }

  clearUncommittedEvents(): void {
    this.uncommittedEvents = [];
  }

  // Apply event to internal state
  private apply(event: OrderEvent, isNew: boolean): void {
    switch (event.type) {
      case "OrderCreated": {
        const e = event as OrderCreated;
        this.id = e.orderId;
        this.customerId = e.customerId;
        this.status = "draft";
        break;
      }
      case "ItemAdded": {
        const e = event as ItemAdded;
        this.items.push({
          productId: e.productId,
          quantity: e.quantity,
          unitPrice: e.unitPrice,
        });
        break;
      }
      case "OrderConfirmed":
        this.status = "confirmed";
        break;
      case "OrderShipped":
        this.status = "shipped";
        break;
    }
    if (isNew) {
      this.uncommittedEvents.push(event);
    }
  }
}

// Event Store — append-only persistence
interface EventStore {
  loadEvents(aggregateId: string): Promise<OrderEvent[]>;
  saveEvents(aggregateId: string, events: OrderEvent[], expectedVersion: number): Promise<void>;
}

// ============================================
// QUERY SIDE — read model, optimized for specific views
// ============================================

// Projection: builds a denormalized read model from events
class OrderDashboardProjection {
  constructor(private readonly readDb: ReadDatabase) {}

  // Subscribes to event stream and updates read model
  async handleEvent(event: OrderEvent): Promise<void> {
    switch (event.type) {
      case "OrderCreated": {
        const e = event as OrderCreated;
        await this.readDb.upsert("order_dashboard", {
          orderId: e.orderId,
          customerId: e.customerId,
          status: "draft",
          itemCount: 0,
          total: 0,
          createdAt: e.occurredAt,
        });
        break;
      }
      case "ItemAdded": {
        const e = event as ItemAdded;
        await this.readDb.increment("order_dashboard", e.orderId, "itemCount", 1);
        await this.readDb.increment("order_dashboard", e.orderId, "total", e.quantity * e.unitPrice);
        break;
      }
      case "OrderConfirmed":
        await this.readDb.update("order_dashboard", event.orderId, { status: "confirmed" });
        break;
      case "OrderShipped": {
        const e = event as OrderShipped;
        await this.readDb.update("order_dashboard", e.orderId, {
          status: "shipped",
          trackingNumber: e.trackingNumber,
        });
        break;
      }
    }
  }
}

// Query service — reads from the optimized read model
class OrderQueryService {
  constructor(private readonly readDb: ReadDatabase) {}

  // Fast: single table read, no joins
  async getDashboard(customerId: string): Promise<OrderDashboardItem[]> {
    return this.readDb.find("order_dashboard", { customerId });
  }

  // Bonus: complete audit trail for free
  async getOrderHistory(orderId: string, eventStore: EventStore): Promise<OrderEvent[]> {
    return eventStore.loadEvents(orderId);
  }
}
```

---

## Alternatives & Related Principles

| Approach | Relationship |
|---|---|
| **Single Model CRUD** | The default. One model, one database. Sufficient for most applications. Choose CQRS/ES only when the read/write asymmetry justifies the complexity. |
| **Materialized Views** | A lightweight alternative to full CQRS. Create database views or cached projections for read optimization without a separate write model. |
| **Change Data Capture (CDC)** | Captures database changes as events (Debezium). Achieves some Event Sourcing benefits without changing the application's write model. |
| **Audit Tables / Temporal Tables** | Store change history alongside current state. Provides audit trail without full Event Sourcing. SQL Server and PostgreSQL support temporal tables natively. |

---

## When NOT to Apply

- **Simple CRUD domains**: If reads and writes have similar shapes and volumes, CQRS adds complexity for no benefit. Most web applications are CRUD.
- **Low-volume systems**: If you have hundreds of reads per day, optimizing with separate read models is premature.
- **When eventual consistency is unacceptable**: The read model lags behind the write model. If the business cannot tolerate "the data you see might be 2 seconds old," CQRS's eventual consistency is a problem.
- **Small teams without event store expertise**: Event Sourcing requires understanding event versioning, projection rebuilds, snapshots, and eventual consistency. The learning curve is steep.
- **When the domain is not well understood**: Event Sourcing bakes domain events into the permanent record. If you get the event model wrong early, correcting it is painful (event upcasting, migration events).

---

## Tensions & Trade-offs

- **Complexity**: CQRS/ES is significantly more complex than CRUD. You maintain two models, event-to-state mapping, projections, and eventual consistency.
- **Eventual consistency**: Read models lag. Users may not see their own writes immediately. Patterns like "read-your-own-writes" add complexity.
- **Event versioning**: Events are immutable. When the schema changes, you need upcasters (transformations applied when loading old events) or new event types.
- **Projection rebuilds**: If a projection has a bug, you must replay all events to rebuild it. For large event stores, this can take hours or days.
- **Debugging**: "Why does the read model show X?" requires tracing through events and projection logic. It is not a simple database query.

---

## Real-World Consequences

**Adherence example**: A banking system used Event Sourcing for transaction processing. Every debit, credit, and transfer was stored as an event. When regulators requested a complete audit trail for the past 5 years, the data was already there — no additional work needed. When they discovered a projection bug that miscalculated balances for a specific account type, they fixed the projection and replayed events to correct all affected balances.

**Over-application example**: A team implemented full CQRS/ES for a content management system. Articles were stored as events (ArticleCreated, TitleChanged, BodyUpdated, TagAdded). Replaying 50,000 events to rebuild an article's current state took 3 seconds. They added snapshotting, which helped but introduced another layer of complexity. A simple PostgreSQL table with `updated_at` timestamps would have served the use case perfectly.

---

## Key Quotes

> "CQRS is simply the creation of two objects where there was previously only one." — Greg Young

> "Event Sourcing ensures that all changes to application state are stored as a sequence of events." — Martin Fowler

> "If you are not building a system that has genuinely different read and write requirements, CQRS is over-engineering." — common pragmatic advice

> "The event log is the truth. Everything else is a cached view." — Pat Helland (paraphrased)

---

## Further Reading

- Young, G. — [CQRS Documents](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf) (2010)
- Fowler, M. — [CQRS](https://martinfowler.com/bliki/CQRS.html) and [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
- Meyer, B. — *Object-Oriented Software Construction* (1988), Command-Query Separation
- Kleppmann, M. — *Designing Data-Intensive Applications* (2017), on event logs and stream processing
- Betts, D. et al. — *Exploring CQRS and Event Sourcing* (Microsoft patterns & practices, 2012)
- EventStore documentation — [eventstore.com/docs](https://www.eventstore.com/docs/) (reference implementation)
