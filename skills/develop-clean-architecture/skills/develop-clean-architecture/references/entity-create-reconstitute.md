---
title: Separate Create and Reconstitute Factories on Entities
impact: HIGH
impactDescription: prevents duplicate event emission and skipped invariants on persistence load
tags: entity, factory, reconstitute, persistence
---

## Separate Create and Reconstitute Factories on Entities

Entities need two distinct factory methods: `create()` enforces creation invariants and emits domain events. `reconstitute()` rebuilds from persisted data — no events, no invariant re-checking. Missing this distinction causes duplicate events on load or skipped validation on creation.

**Incorrect (single constructor for both creation and loading):**

```typescript
class Order {
  constructor(
    readonly id: OrderId,
    readonly customerId: CustomerId,
    private lines: OrderLine[],
    private status: OrderStatus,
  ) {
    // Invariant check runs on EVERY construction — including DB load
    if (lines.length === 0) throw new Error('Order must have lines');
    if (lines.length > 10) throw new Error('Too many lines');
    // Event emitted on EVERY construction — including DB load
    this.domainEvents.push(new OrderCreated(id, customerId));
  }
}

// Loading from DB triggers creation invariants and emits duplicate events
const order = new Order(row.id, row.customerId, row.lines, row.status);
```

**Correct (separate create and reconstitute factories):**

```typescript
class Order {
  #domainEvents: DomainEvent[] = [];

  private constructor(
    readonly id: OrderId,
    readonly customerId: CustomerId,
    private lines: OrderLine[],
    private status: OrderStatus,
  ) {}

  // Factory: enforces creation invariants, emits events
  static create(
    customerId: CustomerId,
    lines: OrderLine[],
  ): Result<Order, 'EmptyOrder' | 'ExceedsMaxItems'> {
    if (lines.length === 0) return { ok: false, error: 'EmptyOrder' };
    if (lines.length > 10) return { ok: false, error: 'ExceedsMaxItems' };

    const order = new Order(generateId() as OrderId, customerId, lines, 'draft');
    order.#domainEvents.push(new OrderCreated(order.id, customerId));
    return { ok: true, value: order };
  }

  // Reconstitution: rebuilds from persistence — no events, no re-validation
  static reconstitute(
    id: OrderId,
    customerId: CustomerId,
    lines: OrderLine[],
    status: OrderStatus,
  ): Order {
    return new Order(id, customerId, lines, status);
  }

  pullDomainEvents(): ReadonlyArray<DomainEvent> {
    const events = [...this.#domainEvents];
    this.#domainEvents = [];
    return events;
  }
}

// infrastructure/mappers/OrderMapper.ts
class OrderMapper {
  static toDomain(row: OrderRecord): Order {
    return Order.reconstitute(
      row.id as OrderId,
      row.customer_id as CustomerId,
      row.lines.map(LineMapper.toDomain),
      row.status as OrderStatus,
    );
  }
}
```

**When NOT to use this pattern:**
- Simple value objects without domain events or complex invariants
- Entities that are always created fresh and never loaded from persistence

**Benefits:**
- Domain events emitted exactly once — at creation time, not on every DB load
- Creation invariants enforced on new entities but not on already-persisted data
- Private constructor prevents accidental direct instantiation
- Mapper layer has a clear, safe way to rebuild entities from raw data

Reference: [Implementing DDD — Vaughn Vernon, Ch. 5: Entities](https://www.oreilly.com/library/view/implementing-domain-driven-design/9780133039900/)
