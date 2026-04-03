---
title: Wire All Dependencies in a Single Composition Root
impact: HIGH
impactDescription: centralizes all concrete-type knowledge in one file — the only place that knows everything
tags: bound, composition-root, di, wiring
---

## Wire All Dependencies in a Single Composition Root

The Composition Root (`main.ts`) is the ONLY file that knows about all concrete implementations. It instantiates infrastructure, wires dependencies, and starts the application. No other file should import concrete implementations from other layers. Prefer manual DI for projects with fewer than 30 dependencies.

**Incorrect (dependencies wired ad-hoc across multiple files):**

```typescript
// application/usecases/PlaceOrder.ts — imports concrete infrastructure
import { PrismaOrderRepository } from '../../infrastructure/persistence/PrismaOrderRepo';
import { StripePaymentGateway } from '../../infrastructure/gateways/StripePaymentGateway';

class PlaceOrderHandler {
  private orders = new PrismaOrderRepository();  // Hardwired — untestable
  private payments = new StripePaymentGateway();  // Hardwired — can't swap
}
```

**Correct (single Composition Root wires everything):**

```typescript
// src/main.ts — the Composition Root ("Dirty Main")
// This is the ONLY file that knows about ALL concrete implementations

import { PrismaClient } from '@prisma/client';
import { PrismaOrderRepository } from './infrastructure/persistence/PrismaOrderRepository';
import { StripePaymentGateway } from './infrastructure/gateways/StripePaymentGateway';
import { InMemoryDomainEventBus } from './infrastructure/events/InMemoryDomainEventBus';
import { PlaceOrderHandler } from './application/commands/PlaceOrderHandler';
import { GetOrderSummaryHandler } from './application/queries/GetOrderSummaryHandler';
import { OrderController } from './adapters/http/OrderController';
import { createExpressApp } from './infrastructure/http/server';

// Instantiate infrastructure
const prisma = new PrismaClient();
const eventBus = new InMemoryDomainEventBus();

// Wire dependencies explicitly — type-safe, no magic
const orderRepo = new PrismaOrderRepository(prisma);
const paymentGW = new StripePaymentGateway(process.env.STRIPE_SECRET!);

// Wire use case handlers with their port implementations
const placeHandler = new PlaceOrderHandler(orderRepo, paymentGW, eventBus);
const summaryHandler = new GetOrderSummaryHandler(prisma);

// Wire adapters
const controller = new OrderController(placeHandler, summaryHandler);
const app = createExpressApp(controller);

app.listen(3000, () => console.log('Server running'));
```

**When to consider a DI container instead of manual wiring:**

| Criteria | Manual DI | DI Container (tsyringe/InversifyJS) |
|---|---|---|
| Dependencies | < 30 | 30+ |
| Type safety | Perfect | Good (symbol-based) |
| Bundle size | 0KB | 15-35KB |
| `erasableSyntaxOnly` | Compatible | Incompatible (decorators) |

**When NOT to use this pattern:**
- Lambda functions or serverless where each function has 1-2 dependencies
- When a DI container is already established and working well

**Benefits:**
- Single place to understand the entire wiring of the application
- All other files depend on abstractions (ports) not concretions
- Swapping implementations (e.g., Prisma to DynamoDB) requires changing only main.ts
- Tests create their own mini composition roots with test doubles
- No decorator magic — pure constructor injection is debuggable

Reference: [Composition Root — Mark Seemann](https://blog.ploeh.dk/2011/07/28/CompositionRoot/) | [Clean Architecture — Robert C. Martin, Ch. 26: The Main Component](https://www.oreilly.com/library/view/clean-architecture-a/9780134494272/)
