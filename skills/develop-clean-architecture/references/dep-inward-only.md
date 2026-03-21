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

**Correct (inner layer defines interface, outer layer implements):**

```typescript
// domain/entities/Order.ts - ENTITY LAYER
export interface OrderPersistence {
  save(order: Order): Promise<void>
}

export interface NotificationPort {
  notify(customerId: string): Promise<void>
}

export class Order {
  constructor(
    private repo: OrderPersistence,
    private email: NotificationPort
  ) {}

  async complete() {
    await this.repo.save(this)
    await this.email.notify(this.customerId)
  }
}

// infrastructure/OrderRepository.ts - INFRASTRUCTURE LAYER
import { Order, OrderPersistence } from '../domain/entities/Order'

export class OrderRepository implements OrderPersistence {
  async save(order: Order): Promise<void> { /* DB implementation */ }
}
```

**Benefits:**
- Inner layers remain stable when outer layers change
- Business rules can be tested without infrastructure
- Infrastructure can be swapped without touching domain code

Reference: [The Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
