---
title: Source Dependencies Point Inward Only
impact: CRITICAL
impactDescription: prevents cascade failures across all layers, foundation of Clean Architecture
tags: dep, dependency-rule, layers, architecture, explicit-architecture
---

## Source Dependencies Point Inward Only

The Dependency Rule states that source code dependencies can only point inward toward higher-level policies. Inner circles must never reference outer circles. Ports come in two directions: Primary (Input) Ports are called BY adapters to drive the app; Secondary (Output) Ports are called BY the app, implemented by infrastructure. All dependencies point inward toward Domain.

```text
[Primary Adapters] → [Input Ports] → [Application Core] → [Output Ports] → [Secondary Adapters]
CLI, REST, gRPC      IPlaceOrder      Use Cases, Domain      OrderRepository   Prisma, Stripe, S3
```

**Incorrect (inner layer imports from outer layer):**

```typescript
// domain/entities/Order.ts - ENTITY LAYER
import { OrderRepository } from '../../infrastructure/OrderRepository'
import { EmailService } from '../../infrastructure/EmailService'

export class Order {
  constructor(
    private repo: OrderRepository,  // Changes to repo implementation break Order
    private email: EmailService
  ) {}

  async complete() {
    await this.repo.save(this)
    await this.email.notify(this.customerId)  // Cannot test without email server
  }
}
```

**Correct (application owns the ports, infrastructure implements them):**

```typescript
type Result<T, E> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

// domain/entities/Order.ts - ENTITY LAYER
export class Order {
  #status: 'pending' | 'completed';
  #domainEvents: Array<{ readonly type: 'OrderCompleted'; readonly orderId: OrderId }> = [];

  constructor(
    readonly id: OrderId,
    readonly customerId: CustomerId,
    status: 'pending' | 'completed',
  ) {
    this.#status = status;
  }

  complete(): Result<void, 'OrderAlreadyCompleted'> {
    if (this.#status === 'completed') {
      return { ok: false, error: 'OrderAlreadyCompleted' };
    }

    this.#status = 'completed';
    this.#domainEvents.push({ type: 'OrderCompleted', orderId: this.id });
    return { ok: true, value: undefined };
  }

  pullDomainEvents(): ReadonlyArray<{ readonly type: 'OrderCompleted'; readonly orderId: OrderId }> {
    const events = [...this.#domainEvents];
    this.#domainEvents = [];
    return events;
  }
}

// application/ports/output/OrderRepository.ts - APPLICATION LAYER
export interface OrderRepository {
  findById(id: OrderId): Promise<Order | null>;
  save(order: Order): Promise<void>;
}

export interface DomainEventBus {
  publish(events: ReadonlyArray<{ readonly type: 'OrderCompleted'; readonly orderId: OrderId }>): Promise<void>;
}

// application/usecases/CompleteOrderUseCase.ts - APPLICATION LAYER
export class CompleteOrderUseCase {
  constructor(
    private readonly orders: OrderRepository,
    private readonly eventBus: DomainEventBus,
  ) {}

  async execute(orderId: OrderId): Promise<Result<void, 'OrderNotFound' | 'OrderAlreadyCompleted'>> {
    const order = await this.orders.findById(orderId);
    if (!order) {
      return { ok: false, error: 'OrderNotFound' };
    }

    const completion = order.complete();
    if (!completion.ok) {
      return completion;
    }

    await this.orders.save(order);
    await this.eventBus.publish(order.pullDomainEvents());
    return { ok: true, value: undefined };
  }
}

// infrastructure/OrderRepository.ts - INFRASTRUCTURE LAYER
import type { OrderRepository } from '../application/ports/output/OrderRepository'
import { Order } from '../domain/entities/Order'

export class PrismaOrderRepository implements OrderRepository {
  async findById(id: OrderId): Promise<Order | null> { /* DB implementation */ }
  async save(order: Order): Promise<void> { /* DB implementation */ }
}
```

**Benefits:**
- Inner layers remain stable when outer layers change
- Business rules can be tested without infrastructure
- Domain entities stay focused on business rules instead of persistence mechanics

Reference: [The Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
