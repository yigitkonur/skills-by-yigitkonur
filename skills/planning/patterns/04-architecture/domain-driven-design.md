# Domain-Driven Design (DDD)

**Model software around the business domain using a shared language between developers and domain experts.**

---

## Origin

Domain-Driven Design was formalized by Eric Evans in his seminal book *"Domain-Driven Design: Tackling Complexity in the Heart of Software"* (2003). Evans drew on decades of object-oriented design thinking, particularly the work of Martin Fowler (*Patterns of Enterprise Application Architecture*, 2002), Ward Cunningham, and the Smalltalk community. Vaughn Vernon extended the concepts in *"Implementing Domain-Driven Design"* (2013), providing more practical guidance. The DDD community has since grown into a major movement with conferences (DDD Europe, Explore DDD) and a rich body of pattern literature.

---

## The Problem It Solves

Most software projects fail not because of technology but because of a disconnect between what the business needs and what the software does. Developers use technical terms ("entities," "controllers," "services") while domain experts use business terms ("claim," "underwriting," "settlement"). This translation gap leads to software that technically works but does not accurately model the business — rules are misunderstood, edge cases are missed, and every new requirement requires extensive rework because the code structure does not match the domain structure.

---

## The Principle Explained

DDD provides both strategic and tactical patterns. At the strategic level, **Bounded Contexts** divide a large system into distinct areas, each with its own model. The word "Account" means something different in the Billing context (payment method, invoices) than in the Identity context (username, permissions). Rather than forcing a single model, DDD acknowledges these differences and draws explicit boundaries.

**Ubiquitous Language** is the practice of using the same terminology in code, documentation, and conversation. If domain experts say "policy" rather than "contract," the code should have a `Policy` class, not a `Contract` class. This shared language eliminates translation errors and makes the code readable to non-developers.

At the tactical level, DDD introduces building blocks: **Aggregates** (consistency boundaries around a cluster of entities), **Value Objects** (immutable objects defined by their attributes, not identity), **Domain Events** (significant occurrences in the domain), **Repositories** (abstractions for retrieving aggregates), and **Domain Services** (operations that do not belong to a single entity). These patterns organize code so that business rules are explicit, invariants are enforced, and the model evolves alongside the business.

---

## Code Examples

### BAD: Anemic domain model — logic scattered across services

```typescript
// Entity is just a data bag
interface Order {
  id: string;
  customerId: string;
  items: Array<{ productId: string; quantity: number; price: number }>;
  status: string;
  total: number;
  discountCode?: string;
  discountAmount: number;
}

// All logic lives in a service — the "anemic domain model" anti-pattern
class OrderService {
  async applyDiscount(orderId: string, code: string): Promise<void> {
    const order = await this.db.orders.findOne(orderId);
    const discount = await this.db.discounts.findOne(code);

    // Business rules scattered across service methods
    if (order.status !== "draft") {
      throw new Error("Cannot apply discount to non-draft order");
    }

    if (discount.minOrderTotal && order.total < discount.minOrderTotal) {
      throw new Error("Order total too low for this discount");
    }

    if (discount.type === "percentage") {
      order.discountAmount = order.total * (discount.value / 100);
    } else {
      order.discountAmount = discount.value;
    }

    order.discountCode = code;
    order.total = order.total - order.discountAmount;

    // Direct database call — no aggregate boundary
    await this.db.orders.update(orderId, order);
  }

  async addItem(orderId: string, productId: string, qty: number): Promise<void> {
    const order = await this.db.orders.findOne(orderId);
    const product = await this.db.products.findOne(productId);

    // More scattered business logic
    if (order.status !== "draft") throw new Error("Cannot modify non-draft order");
    if (order.items.length >= 50) throw new Error("Too many items");

    order.items.push({ productId, quantity: qty, price: product.price });
    order.total = order.items.reduce((sum, i) => sum + i.price * i.quantity, 0);

    await this.db.orders.update(orderId, order);
  }
}
```

### GOOD: Rich domain model with DDD tactical patterns

```typescript
// ============================================
// VALUE OBJECTS — immutable, identity-less
// ============================================
class Money {
  private constructor(
    readonly amount: number,
    readonly currency: string
  ) {
    if (amount < 0) throw new Error("Money amount cannot be negative");
  }

  static of(amount: number, currency: string): Money {
    return new Money(Math.round(amount * 100) / 100, currency);
  }

  add(other: Money): Money {
    this.ensureSameCurrency(other);
    return Money.of(this.amount + other.amount, this.currency);
  }

  subtract(other: Money): Money {
    this.ensureSameCurrency(other);
    return Money.of(this.amount - other.amount, this.currency);
  }

  multiplyBy(factor: number): Money {
    return Money.of(this.amount * factor, this.currency);
  }

  isGreaterThanOrEqual(other: Money): boolean {
    this.ensureSameCurrency(other);
    return this.amount >= other.amount;
  }

  private ensureSameCurrency(other: Money): void {
    if (this.currency !== other.currency) {
      throw new Error(`Currency mismatch: ${this.currency} vs ${other.currency}`);
    }
  }
}

class Discount {
  private constructor(
    readonly code: string,
    private readonly type: "percentage" | "fixed",
    private readonly value: number,
    private readonly minOrderTotal: Money | null
  ) {}

  static percentage(code: string, percent: number, minTotal?: Money): Discount {
    if (percent <= 0 || percent > 100) throw new Error("Invalid percentage");
    return new Discount(code, "percentage", percent, minTotal ?? null);
  }

  static fixed(code: string, amount: Money, minTotal?: Money): Discount {
    return new Discount(code, "fixed", amount.amount, minTotal ?? null);
  }

  calculateDiscount(orderTotal: Money): Money {
    if (this.type === "percentage") {
      return orderTotal.multiplyBy(this.value / 100);
    }
    return Money.of(this.value, orderTotal.currency);
  }

  isApplicableTo(orderTotal: Money): boolean {
    if (!this.minOrderTotal) return true;
    return orderTotal.isGreaterThanOrEqual(this.minOrderTotal);
  }
}

// ============================================
// AGGREGATE — consistency boundary
// ============================================
class OrderItem {
  constructor(
    readonly productId: string,
    readonly quantity: number,
    readonly unitPrice: Money
  ) {}

  get lineTotal(): Money {
    return this.unitPrice.multiplyBy(this.quantity);
  }
}

// Domain events
interface DomainEvent {
  readonly occurredAt: Date;
}

class OrderPlacedEvent implements DomainEvent {
  readonly occurredAt = new Date();
  constructor(
    readonly orderId: string,
    readonly customerId: string,
    readonly total: Money
  ) {}
}

class DiscountAppliedEvent implements DomainEvent {
  readonly occurredAt = new Date();
  constructor(
    readonly orderId: string,
    readonly discountCode: string,
    readonly discountAmount: Money
  ) {}
}

// The Order AGGREGATE ROOT — all business rules enforced here
class Order {
  private items: OrderItem[] = [];
  private discount: Discount | null = null;
  private discountAmount: Money;
  private domainEvents: DomainEvent[] = [];

  private static readonly MAX_ITEMS = 50;

  constructor(
    readonly id: string,
    readonly customerId: string,
    private status: "draft" | "placed" | "cancelled",
    private readonly currency: string
  ) {
    this.discountAmount = Money.of(0, currency);
  }

  addItem(productId: string, quantity: number, unitPrice: Money): void {
    this.ensureDraft();
    if (this.items.length >= Order.MAX_ITEMS) {
      throw new OrderLimitExceededError(this.id, Order.MAX_ITEMS);
    }
    this.items.push(new OrderItem(productId, quantity, unitPrice));
  }

  applyDiscount(discount: Discount): void {
    this.ensureDraft();
    const subtotal = this.calculateSubtotal();

    if (!discount.isApplicableTo(subtotal)) {
      throw new DiscountNotApplicableError(discount.code, subtotal);
    }

    this.discount = discount;
    this.discountAmount = discount.calculateDiscount(subtotal);
    this.domainEvents.push(
      new DiscountAppliedEvent(this.id, discount.code, this.discountAmount)
    );
  }

  place(): void {
    this.ensureDraft();
    if (this.items.length === 0) {
      throw new EmptyOrderError(this.id);
    }
    this.status = "placed";
    this.domainEvents.push(
      new OrderPlacedEvent(this.id, this.customerId, this.total)
    );
  }

  get total(): Money {
    return this.calculateSubtotal().subtract(this.discountAmount);
  }

  pullDomainEvents(): DomainEvent[] {
    const events = [...this.domainEvents];
    this.domainEvents = [];
    return events;
  }

  private calculateSubtotal(): Money {
    return this.items.reduce(
      (sum, item) => sum.add(item.lineTotal),
      Money.of(0, this.currency)
    );
  }

  private ensureDraft(): void {
    if (this.status !== "draft") {
      throw new InvalidOrderStateError(this.id, this.status, "draft");
    }
  }
}

// ============================================
// REPOSITORY — port for aggregate persistence
// ============================================
interface OrderRepository {
  findById(id: string): Promise<Order | null>;
  save(order: Order): Promise<void>;
}

// ============================================
// APPLICATION SERVICE — thin orchestration layer
// ============================================
class PlaceOrderUseCase {
  constructor(
    private readonly orders: OrderRepository,
    private readonly eventBus: EventBus
  ) {}

  async execute(orderId: string): Promise<void> {
    const order = await this.orders.findById(orderId);
    if (!order) throw new Error(`Order not found: ${orderId}`);

    order.place(); // All business rules inside the aggregate

    await this.orders.save(order);
    for (const event of order.pullDomainEvents()) {
      await this.eventBus.publish(event);
    }
  }
}
```

---

## Alternatives & Related Principles

| Approach | Relationship |
|---|---|
| **CRUD-Based Design** | No domain model — application is a thin layer over database operations. Appropriate for simple data-entry apps. Breaks down when business rules emerge. |
| **Transaction Script** | Business logic is organized as procedures, each handling a single request. Simpler than DDD but leads to duplication as complexity grows. |
| **Table Module** | One class per database table, containing all business logic for that table. A middle ground between Transaction Script and DDD. |
| **Active Record** | Objects map directly to database rows and include both data and behavior. Works for simple domains but conflates persistence with business logic. |
| **Event Sourcing** | Stores domain events instead of current state. Natural extension of DDD's domain events concept. |

---

## When NOT to Apply

- **Simple CRUD applications**: If the business logic is "save data, retrieve data, maybe validate some fields," DDD's aggregate/value object ceremony adds no value.
- **Data-pipeline / ETL systems**: These systems transform data; they do not model a domain. Functional patterns (map, filter, reduce) are more appropriate.
- **When domain experts are unavailable**: DDD requires collaboration with domain experts to build the Ubiquitous Language. Without them, developers invent a model that may not match reality.
- **Early-stage startups**: When the domain itself is unclear and pivoting frequently, investing in a rich domain model may be premature. Start with simpler patterns and refactor toward DDD as the domain stabilizes.

---

## Tensions & Trade-offs

- **Model purity vs. performance**: Aggregates enforce consistency boundaries, but loading an entire aggregate for a simple read is wasteful. CQRS is the common resolution.
- **Bounded Context boundaries**: Drawing the wrong boundaries is expensive. Too many contexts create integration overhead; too few create model pollution.
- **Learning curve**: DDD has a steep learning curve. The tactical patterns (aggregates, value objects, domain events) require experience to apply correctly.
- **Ubiquitous Language maintenance**: Language evolves. Keeping code terminology in sync with business terminology requires ongoing effort.

---

## Real-World Consequences

**Adherence example**: The British government's digital services (GDS) applied DDD to modernize immigration processing. By modeling the domain with domain experts and using bounded contexts (Visa Applications, Border Control, Settlement), they replaced a monolithic system with independently deployable services. Processing times dropped from weeks to days.

**Misapplication example**: A startup applied full DDD to a todo-list application — aggregates, value objects, domain events, bounded contexts. The team spent three months building infrastructure that a simple CRUD API could have delivered in two weeks. The startup ran out of runway.

---

## Key Quotes

> "The heart of software is its ability to solve domain-related problems for its user." — Eric Evans, *Domain-Driven Design*

> "Any fool can write code that a computer can understand. Good programmers write code that humans can understand." — Martin Fowler

> "When you model domain concepts in software, the model acts as a Ubiquitous Language to facilitate communication between software developers and domain experts." — Vaughn Vernon

---

## Further Reading

- Evans, E. — *Domain-Driven Design: Tackling Complexity in the Heart of Software* (2003)
- Vernon, V. — *Implementing Domain-Driven Design* (2013)
- Vernon, V. — *Domain-Driven Design Distilled* (2016)
- Fowler, M. — *Patterns of Enterprise Application Architecture* (2002)
- Brandolini, A. — *Introducing EventStorming* (2021)
- [ddd-crew/bounded-context-canvas](https://github.com/ddd-crew/bounded-context-canvas) — tool for designing bounded contexts
