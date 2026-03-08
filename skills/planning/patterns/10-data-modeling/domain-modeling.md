# Domain Modeling — Aggregates, Entities, and Value Objects

## Origin

Domain modeling as a discipline was formalized by Eric Evans in his 2003 book "Domain-Driven Design: Tackling Complexity in the Heart of Software." The concepts of aggregates, entities, and value objects provide a framework for mapping business concepts to code structures with clear rules about identity, equality, and consistency boundaries. These patterns address a fundamental question: where do you draw the line around data that must be consistent together?

## Explanation

### Entities

Objects with a persistent identity that matters. Two entities with the same attributes but different IDs are different objects. An `Order` with ID `order-123` is always that specific order, even if its status changes.

- Have a unique identifier
- Are mutable (state changes over their lifecycle)
- Equality is based on identity, not attributes

### Value Objects

Objects defined entirely by their attributes. Two value objects with the same attributes are interchangeable. A `Money` value of `{ amount: 1000, currency: "USD" }` is equal to any other `Money` with the same values. They have no identity.

- No unique identifier
- Immutable (create a new one instead of modifying)
- Equality is based on all attributes

### Aggregates

A cluster of entities and value objects with a single root entity (the aggregate root). The aggregate defines a consistency boundary: all invariants within the aggregate are enforced synchronously. Cross-aggregate consistency is eventual.

**Rules**:
1. External objects can only reference the aggregate root, never internal entities.
2. Changes to the aggregate go through the root.
3. One transaction modifies one aggregate.
4. Inter-aggregate references use IDs, not object references.

### Consistency Boundaries

The aggregate boundary answers: "What data must be consistent together in a single transaction?" An `Order` and its `OrderItems` must be consistent (you cannot add an item to a non-existent order). But an `Order` and a `Product` can be eventually consistent (the product price may change after the order is placed).

## TypeScript Code Examples

### Bad: No Consistency Boundaries

```typescript
// BAD: Everything is a flat data bag with no invariant protection
interface Order {
  id: string;
  customerId: string;
  items: OrderItem[];
  status: string;
  total: number;
}

// Anyone can mutate anything — no invariants enforced
async function addItem(order: Order, item: OrderItem): Promise<void> {
  order.items.push(item); // What if the order is already shipped?
  order.total += item.price * item.quantity; // Can total go negative?
  await db.orders.update(order); // Entire object saved, no validation
}

// Separate transaction modifies the same order — race condition
async function cancelOrder(orderId: string): Promise<void> {
  await db.query("UPDATE orders SET status = 'cancelled' WHERE id = $1", [orderId]);
  // Items are not cleaned up. Total is stale. No invariant checked.
}
```

### Good: Value Objects

```typescript
// GOOD: Value objects are immutable, equality by attributes
class Money {
  private constructor(
    readonly cents: number,
    readonly currency: string
  ) {
    if (cents < 0) throw new Error("Money cannot be negative");
    if (!currency || currency.length !== 3) throw new Error("Invalid currency code");
  }

  static of(cents: number, currency: string): Money {
    return new Money(cents, currency);
  }

  add(other: Money): Money {
    if (this.currency !== other.currency) {
      throw new Error(`Cannot add ${this.currency} and ${other.currency}`);
    }
    return Money.of(this.cents + other.cents, this.currency);
  }

  multiply(factor: number): Money {
    return Money.of(Math.round(this.cents * factor), this.currency);
  }

  equals(other: Money): boolean {
    return this.cents === other.cents && this.currency === other.currency;
  }

  toString(): string {
    return `${(this.cents / 100).toFixed(2)} ${this.currency}`;
  }
}

class Address {
  private constructor(
    readonly street: string,
    readonly city: string,
    readonly state: string,
    readonly postalCode: string,
    readonly country: string
  ) {}

  static create(input: AddressInput): Address {
    if (!input.street) throw new Error("Street is required");
    if (!input.postalCode) throw new Error("Postal code is required");
    return new Address(input.street, input.city, input.state, input.postalCode, input.country);
  }

  equals(other: Address): boolean {
    return (
      this.street === other.street &&
      this.city === other.city &&
      this.state === other.state &&
      this.postalCode === other.postalCode &&
      this.country === other.country
    );
  }
}
```

### Good: Entity with Identity

```typescript
// GOOD: Entity — identity matters, mutable state with lifecycle
class OrderItem {
  constructor(
    readonly id: string,
    readonly productId: string,
    readonly productName: string,
    private _quantity: number,
    readonly unitPrice: Money
  ) {
    if (_quantity <= 0) throw new Error("Quantity must be positive");
  }

  get quantity(): number {
    return this._quantity;
  }

  get lineTotal(): Money {
    return this.unitPrice.multiply(this._quantity);
  }

  updateQuantity(newQuantity: number): void {
    if (newQuantity <= 0) throw new Error("Quantity must be positive");
    this._quantity = newQuantity;
  }
}
```

### Good: Aggregate Root with Invariant Protection

```typescript
// GOOD: Order as aggregate root — all mutations go through it
type OrderStatus = "draft" | "placed" | "confirmed" | "shipped" | "delivered" | "cancelled";

class Order {
  private _items: OrderItem[] = [];
  private _status: OrderStatus = "draft";

  constructor(
    readonly id: string,
    readonly customerId: string,
    private _shippingAddress: Address
  ) {}

  get status(): OrderStatus {
    return this._status;
  }

  get items(): ReadonlyArray<OrderItem> {
    return this._items;
  }

  get total(): Money {
    return this._items.reduce(
      (sum, item) => sum.add(item.lineTotal),
      Money.of(0, "USD")
    );
  }

  // All mutations go through the aggregate root
  addItem(productId: string, productName: string, quantity: number, unitPrice: Money): void {
    this.assertModifiable();

    const existing = this._items.find((i) => i.productId === productId);
    if (existing) {
      existing.updateQuantity(existing.quantity + quantity);
    } else {
      this._items.push(
        new OrderItem(generateId(), productId, productName, quantity, unitPrice)
      );
    }
  }

  removeItem(itemId: string): void {
    this.assertModifiable();
    const index = this._items.findIndex((i) => i.id === itemId);
    if (index === -1) throw new Error(`Item ${itemId} not found in order`);
    this._items.splice(index, 1);
  }

  place(): void {
    if (this._items.length === 0) {
      throw new Error("Cannot place an order with no items");
    }
    if (this._status !== "draft") {
      throw new Error(`Cannot place order in status: ${this._status}`);
    }
    this._status = "placed";
  }

  confirm(): void {
    if (this._status !== "placed") {
      throw new Error(`Cannot confirm order in status: ${this._status}`);
    }
    this._status = "confirmed";
  }

  cancel(reason: string): void {
    if (this._status === "shipped" || this._status === "delivered") {
      throw new Error("Cannot cancel a shipped or delivered order");
    }
    this._status = "cancelled";
  }

  updateShippingAddress(address: Address): void {
    if (this._status !== "draft" && this._status !== "placed") {
      throw new Error("Cannot change address after order is confirmed");
    }
    this._shippingAddress = address;
  }

  private assertModifiable(): void {
    if (this._status !== "draft") {
      throw new Error(`Cannot modify order in status: ${this._status}`);
    }
  }
}
```

### Good: Repository for Aggregate Persistence

```typescript
// GOOD: Repository loads and saves the entire aggregate
interface OrderRepository {
  findById(id: string): Promise<Order | null>;
  save(order: Order): Promise<void>;
}

class PostgresOrderRepository implements OrderRepository {
  async findById(id: string): Promise<Order | null> {
    const orderRow = await db.query("SELECT * FROM orders WHERE id = $1", [id]);
    if (orderRow.rows.length === 0) return null;

    const itemRows = await db.query(
      "SELECT * FROM order_items WHERE order_id = $1",
      [id]
    );

    return reconstituteOrder(orderRow.rows[0], itemRows.rows);
  }

  async save(order: Order): Promise<void> {
    await db.transaction(async (tx) => {
      // Save aggregate root
      await tx.query(
        `INSERT INTO orders (id, customer_id, status, total_cents)
         VALUES ($1, $2, $3, $4)
         ON CONFLICT (id) DO UPDATE SET status = $3, total_cents = $4`,
        [order.id, order.customerId, order.status, order.total.cents]
      );

      // Replace all items (simplest approach for aggregate consistency)
      await tx.query("DELETE FROM order_items WHERE order_id = $1", [order.id]);
      for (const item of order.items) {
        await tx.query(
          `INSERT INTO order_items (id, order_id, product_id, product_name, quantity, unit_price_cents)
           VALUES ($1, $2, $3, $4, $5, $6)`,
          [item.id, order.id, item.productId, item.productName, item.quantity, item.unitPrice.cents]
        );
      }
    });
  }
}
```

## Alternatives

| Approach | Best For | Trade-off |
|----------|----------|-----------|
| **Anemic domain model** | Simple CRUD with little business logic | Business rules scattered across services |
| **Active Record** | Rapid prototyping, thin domain logic | Entity coupled to persistence |
| **Table Module** | Report-heavy, set-based operations | Less natural for complex behaviors |
| **Functional domain modeling** | Immutable-first architectures | Less familiar to OOP-trained teams |

## When NOT to Apply

- **CRUD-heavy applications with trivial business rules**: If your domain logic is "save this, read that, list those," full DDD modeling adds ceremony with no benefit. Use simple data transfer objects.
- **Reporting and analytics**: Aggregates are for transactional consistency. Reporting queries naturally cross aggregate boundaries. Use denormalized read models instead.
- **When the team is not invested**: Domain modeling requires the entire team to understand and respect aggregate boundaries. Without buy-in, boundaries erode and the model becomes a confusing wrapper around CRUD.

## Trade-offs

- **Encapsulation vs. simplicity**: Aggregate roots protect invariants but add layers of indirection. For a simple entity, the ceremony may not be justified.
- **Single-aggregate transactions vs. performance**: One transaction per aggregate is the ideal, but sometimes you need to update two aggregates atomically. Options: eventual consistency via events, saga pattern, or pragmatic multi-aggregate transactions (acknowledging the trade-off).
- **Aggregate size**: Too large and transactions become contention points. Too small and you lose consistency guarantees. Size aggregates based on what must be immediately consistent, not on conceptual grouping.
- **Reference by ID vs. object reference**: Inter-aggregate references by ID prevent unintended transactional coupling but make navigation less convenient. This is intentional friction.

## Further Reading

- [Eric Evans — Domain-Driven Design (2003)](https://www.domainlanguage.com/ddd/)
- [Vaughn Vernon — Implementing Domain-Driven Design (2013)](https://www.informit.com/store/implementing-domain-driven-design-9780321834577)
- [Vaughn Vernon — Effective Aggregate Design (3-part series)](https://www.dddcommunity.org/library/vernon_2011/)
- [Martin Fowler — DDD Aggregate](https://martinfowler.com/bliki/DDD_Aggregate.html)
