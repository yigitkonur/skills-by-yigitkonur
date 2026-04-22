---
title: Aggregate Roots Are the Only Entry Point to Entity Clusters
impact: CRITICAL
impactDescription: prevents invariant bypass, enforces transactional consistency boundaries
tags: entity, aggregate, ddd, boundaries
---

## Aggregate Roots Are the Only Entry Point to Entity Clusters

An Aggregate Root is the single entry point to a cluster of domain objects. External code references only the root — never internal entities. Transactions must not span multiple aggregates. Cross-aggregate references use IDs, never object references.

**Incorrect (external code bypasses aggregate root):**

```typescript
// domain/entities/Order.ts
class Order {
  lines: OrderLine[] = [];
}

// domain/entities/OrderLine.ts
class OrderLine {
  productId: string;
  quantity: number;
  unitPrice: number;
}

// application/usecases/UpdateLineUseCase.ts
class UpdateLineUseCase {
  async execute(lineId: string, newQty: number): Promise<void> {
    // Bypasses Order aggregate — no invariant check on max items
    const line = await this.lineRepo.findById(lineId);
    line.quantity = newQty;
    await this.lineRepo.save(line);
  }
}

// Repository exposes internal entity directly
interface OrderLineRepository {
  findById(id: string): Promise<OrderLine | null>;
  save(line: OrderLine): Promise<void>;
}
```

**Correct (all mutations go through aggregate root):**

```typescript
// domain/entities/Order.ts — Aggregate Root
class Order {
  readonly #id: OrderId;
  readonly #customerId: CustomerId;  // Cross-aggregate ref by ID only
  #lines: OrderLine[];
  #domainEvents: DomainEvent[] = [];

  get lines(): ReadonlyArray<OrderLine> { return this.#lines; }

  addLine(product: Product, quantity: number): Result<void, 'ExceedsMax'> {
    if (this.#lines.length >= 10) return { ok: false, error: 'ExceedsMax' };
    this.#lines.push(OrderLine.create(product, quantity));
    return { ok: true, value: undefined };
  }

  updateLineQuantity(lineId: OrderLineId, quantity: number): Result<void, 'LineNotFound'> {
    const line = this.#lines.find(l => l.id === lineId);
    if (!line) return { ok: false, error: 'LineNotFound' };
    line.updateQuantity(quantity);
    return { ok: true, value: undefined };
  }

  pullDomainEvents(): ReadonlyArray<DomainEvent> {
    const events = [...this.#domainEvents];
    this.#domainEvents = [];
    return events;
  }
}

// Repository works ONLY with aggregate roots
interface OrderRepository {
  save(order: Order): Promise<void>;
  findById(id: OrderId): Promise<Order | null>;
  // NEVER: findLineById(lineId: OrderLineId) — bypasses aggregate
}

// Use case operates through the root
class UpdateLineUseCase {
  constructor(private readonly orders: OrderRepository) {}

  async execute(orderId: OrderId, lineId: OrderLineId, qty: number): Promise<Result<void, UpdateLineError>> {
    const order = await this.orders.findById(orderId);
    if (!order) return { ok: false, error: 'OrderNotFound' };

    const result = order.updateLineQuantity(lineId, qty);
    if (!result.ok) return result;

    await this.orders.save(order);
    return { ok: true, value: undefined };
  }
}
```

**When NOT to use this pattern:**
- Simple CRUD without invariants spanning multiple entities
- When aggregate size causes performance issues — split into smaller aggregates
- Read-side queries in CQRS — query handlers bypass aggregates entirely

**Benefits:**
- All invariants checked on every mutation — impossible to bypass
- Clear transactional consistency boundary — one aggregate per transaction
- Internal entities can be refactored without affecting external code
- Repository surface stays small — only aggregate root CRUD

Reference: [Domain-Driven Design — Eric Evans](https://www.domainlanguage.com/ddd/) | [Implementing DDD — Vaughn Vernon](https://www.oreilly.com/library/view/implementing-domain-driven-design/9780133039900/)
