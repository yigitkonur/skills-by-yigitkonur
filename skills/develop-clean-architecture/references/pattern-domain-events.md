---
title: Publish Domain Events to Decouple Side Effects from Core Logic
impact: HIGH
impactDescription: eliminates hidden coupling between domain actions and side effects, 3-5× easier to add new reactions
tags: pattern, events, domain, decoupling
---

## Publish Domain Events to Decouple Side Effects from Core Logic

Entities and aggregates collect domain events during state changes. The use case pulls events AFTER persistence succeeds, then dispatches them. Event handlers trigger side effects — emails, notifications, projections — without polluting domain logic. Events MUST be dispatched after the DB transaction commits to avoid inconsistency.

**Incorrect (side effects coupled directly in domain logic):**

```typescript
// domain/entities/Order.ts
class Order {
  constructor(
    private readonly emailService: IEmailService,       // Domain depends on infra
    private readonly inventoryService: IInventoryService,
  ) {}

  complete(): void {
    this.status = OrderStatus.Completed;
    this.completedAt = new Date();
    this.emailService.sendOrderConfirmation(this);   // What if email fails?
    this.inventoryService.decrementStock(this.items); // Every new reaction = more deps
  }
}
```

**Correct (domain events decouple side effects):**

```typescript
// domain/events/DomainEvent.ts
interface DomainEvent {
  readonly eventType: string;
  readonly occurredAt: Date;
  readonly aggregateId: string;
}

interface OrderCompletedEvent extends DomainEvent {
  readonly eventType: 'OrderCompleted';
  readonly orderId: string;
  readonly customerId: string;
  readonly totalAmount: number;
}

// domain/entities/AggregateRoot.ts
abstract class AggregateRoot {
  private _events: DomainEvent[] = [];
  protected addEvent(event: DomainEvent): void { this._events.push(event); }
  pullEvents(): DomainEvent[] { const e = [...this._events]; this._events = []; return e; }
}

// domain/entities/Order.ts
class Order extends AggregateRoot {
  complete(): void {
    if (this.status === OrderStatus.Completed) {
      throw new OrderAlreadyCompletedError(this.id);
    }

    this.status = OrderStatus.Completed;
    this.completedAt = new Date();

    // Record what happened — no side effects, no infrastructure
    this.addEvent({
      eventType: 'OrderCompleted', occurredAt: this.completedAt,
      aggregateId: this.id, orderId: this.id,
      customerId: this.customerId, totalAmount: this.totalAmount,
    });
  }
}

// application/ports/EventBus.ts
interface IEventBus {
  publish(events: DomainEvent[]): Promise<void>;
  subscribe<E extends DomainEvent>(eventType: string, handler: EventHandler<E>): void;
}

interface EventHandler<E extends DomainEvent> {
  handle(event: E): Promise<void>;
}

// application/usecases/CompleteOrderUseCase.ts
class CompleteOrderUseCase {
  constructor(
    private readonly orderRepo: IOrderRepository,
    private readonly eventBus: IEventBus,
  ) {}

  async execute(orderId: string): Promise<Result<void>> {
    const order = await this.orderRepo.findById(orderId);
    if (!order) return Result.fail('Order not found');

    order.complete();
    await this.orderRepo.save(order);              // 1. Persist first
    const events = order.pullEvents();              // 2. Pull events after save
    await this.eventBus.publish(events);            // 3. Dispatch after commit

    return Result.ok();
  }
}

// infrastructure/events/InMemoryEventBus.ts — implements IEventBus
class InMemoryEventBus implements IEventBus {
  private handlers = new Map<string, EventHandler<any>[]>();

  async publish(events: DomainEvent[]): Promise<void> {
    for (const event of events) {
      const list = this.handlers.get(event.eventType) ?? [];
      await Promise.all(list.map(h => h.handle(event)));
    }
  }

  subscribe<E extends DomainEvent>(type: string, handler: EventHandler<E>): void {
    this.handlers.set(type, [...(this.handlers.get(type) ?? []), handler]);
  }
}

// Subscriber in another subdomain — decoupled without direct coupling
// Notifications subdomain reacts to OrderCompleted
// eventBus.subscribe<OrderCompletedEvent>('OrderCompleted', async (event) => {
//   await emailService.sendOrderConfirmation(event.customerId, event.totalAmount);
// });
```

**When NOT to use this pattern:**
- Simple CRUD with no meaningful side effects to decouple
- When strict synchronous consistency is required across all reactions
- Extremely small domains where the indirection adds more complexity than it removes

**Benefits:**
- Adding new reactions (analytics, webhooks) requires zero changes to domain entities
- Entity is testable without any infrastructure — just assert on collected events
- Event handlers are independently deployable and replaceable
- Natural audit trail of everything that happened in the domain

**Critical warning:** Events MUST be dispatched AFTER the DB transaction commits. Dispatching before commit means: event published, but DB rolled back — inconsistency. The correct order is always: persist -> pull events -> dispatch.

**Tension with Clean Code's "no side effects" rule:** Domain events ARE side effects — but intentional, explicit ones. The reconciliation: push all side effects behind port interfaces and dispatch them from use cases only after persistence.

Reference: [Implementing Domain-Driven Design - Vaughn Vernon](https://www.oreilly.com/library/view/implementing-domain-driven-design/9780133039900/)
