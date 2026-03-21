---
title: Use Domain Services for Cross-Entity Logic
impact: HIGH
impactDescription: prevents entity coupling, keeps multi-aggregate logic in the domain layer
tags: entity, domain-service, ddd, orchestration
---

## Use Domain Services for Cross-Entity Logic

A Domain Service handles domain logic that naturally does not belong inside a single entity or value object — typically logic involving multiple aggregates. Domain services have no infrastructure dependencies. They receive entities, perform logic, and return results.

**Incorrect (cross-entity logic inside one entity):**

```typescript
// domain/entities/Order.ts
class Order {
  transferTo(newCustomer: Customer): void {
    // Order shouldn't know about Customer internals
    newCustomer.addToHistory(this);  // Order coupled to Customer
    this.customerId = newCustomer.id;
  }
}
```

**Correct (domain service receives entities, performs logic):**

```typescript
// domain/services/OrderTransferService.ts
class OrderTransferService {
  canTransfer(order: Order, fromCustomer: Customer, toCustomer: Customer): boolean {
    return order.status === 'pending'
      && fromCustomer.hasOrder(order.id)
      && toCustomer.isVerified();
  }

  transfer(
    order: Order,
    fromCustomer: Customer,
    toCustomer: Customer
  ): Result<void, 'TransferNotAllowed'> {
    if (!this.canTransfer(order, fromCustomer, toCustomer)) {
      return { ok: false, error: 'TransferNotAllowed' };
    }
    fromCustomer.removeOrder(order.id);
    toCustomer.addOrder(order.id);
    return { ok: true, value: undefined };
  }
}

// application/usecases/TransferOrderUseCase.ts
// Application service loads aggregates, calls domain service
class TransferOrderUseCase {
  constructor(
    private readonly orders: OrderRepository,
    private readonly customers: CustomerRepository,
  ) {}

  async execute(cmd: TransferOrderCommand): Promise<Result<void, TransferError>> {
    const [order, from, to] = await Promise.all([
      this.orders.findById(cmd.orderId),
      this.customers.findById(cmd.fromCustomerId),
      this.customers.findById(cmd.toCustomerId),
    ]);
    if (!order || !from || !to) return { ok: false, error: 'NotFound' };

    const service = new OrderTransferService();
    return service.transfer(order, from, to);
  }
}
```

**When NOT to use this pattern:**
- Logic belongs to a single entity — put it on that entity instead
- Logic requires infrastructure (DB, API calls) — that belongs in application services
- Simple delegation that an entity method can handle directly

**Benefits:**
- Entities stay focused on their own invariants
- Multi-aggregate business logic stays in the domain layer, not application layer
- Domain services are pure functions — trivially testable without mocks
- Clear distinction between domain orchestration and infrastructure orchestration

Reference: [Domain-Driven Design — Eric Evans, Ch. 5: Domain Services](https://www.domainlanguage.com/ddd/)
