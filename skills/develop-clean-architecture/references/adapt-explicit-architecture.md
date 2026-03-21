---
title: Distinguish Primary and Secondary Ports in Explicit Architecture
impact: HIGH
impactDescription: clarifies driving vs driven adapters, prevents port direction confusion
tags: adapt, explicit-architecture, ports, hexagonal
---

## Distinguish Primary and Secondary Ports in Explicit Architecture

Herberto Graca's Explicit Architecture extends hexagonal/Clean Architecture with a critical distinction: ports come in two directions. Primary (Input) Ports are called BY adapters to drive the application. Secondary (Output) Ports are called BY the application, implemented by infrastructure.

**Incorrect (all ports treated the same — direction is unclear):**

```typescript
// application/ports/OrderService.ts — is this called or implemented?
interface OrderService {
  placeOrder(cmd: PlaceOrderCommand): Promise<Result<OrderId, OrderError>>;
  findById(id: OrderId): Promise<Order | null>;
  save(order: Order): Promise<void>;
  sendNotification(orderId: OrderId): Promise<void>;
}

// One class implements everything — no separation of concerns
class OrderServiceImpl implements OrderService {
  async placeOrder(cmd: PlaceOrderCommand) { /* ... */ }
  async findById(id: OrderId) { /* ... */ }
  async save(order: Order) { /* ... */ }
  async sendNotification(orderId: OrderId) { /* ... */ }
}
```

**Correct (explicit primary/secondary port separation):**

```typescript
// ── PRIMARY (INPUT) PORTS — interfaces called BY adapters ──────────
// Defined in application layer, implemented by use case handlers

// application/ports/input/IPlaceOrderUseCase.ts
interface IPlaceOrderUseCase {
  execute(cmd: PlaceOrderCommand): Promise<Result<OrderId, OrderError>>;
}

// application/ports/input/IGetOrderSummaryQuery.ts
interface IGetOrderSummaryQuery {
  execute(query: GetOrderSummaryQuery): Promise<OrderSummaryDTO | null>;
}

// ── SECONDARY (OUTPUT) PORTS — interfaces the app calls outward ────
// Defined in application/domain layer, implemented by infrastructure

// domain/ports/output/OrderRepository.ts
interface OrderRepository {
  save(order: Order): Promise<void>;
  findById(id: OrderId): Promise<Order | null>;
}

// application/ports/output/PaymentGateway.ts
interface PaymentGateway {
  charge(customerId: CustomerId, amount: Money): Promise<Result<TransactionId, PaymentError>>;
}

// application/ports/output/DomainEventBus.ts
interface DomainEventBus {
  publish(events: ReadonlyArray<DomainEvent>): Promise<void>;
}

// ── PRIMARY (DRIVING) ADAPTERS — call input ports ──────────────────
// adapters/http/OrderController.ts
class OrderController {
  constructor(
    private readonly placeOrder: IPlaceOrderUseCase,  // primary port
    private readonly getOrder: IGetOrderSummaryQuery,  // primary port
  ) {}

  async create(req: Request, res: Response): Promise<void> {
    const result = await this.placeOrder.execute(req.body);
    // ...
  }
}

// ── SECONDARY (DRIVEN) ADAPTERS — implement output ports ───────────
// infrastructure/persistence/PrismaOrderRepository.ts
class PrismaOrderRepository implements OrderRepository {
  async save(order: Order): Promise<void> { /* Prisma impl */ }
  async findById(id: OrderId): Promise<Order | null> { /* Prisma impl */ }
}
```

**The full architecture map:**

```text
[Primary Adapters]  →  [Input Ports]  →  [Application Core]  →  [Output Ports]  →  [Secondary Adapters]
CLI, REST, gRPC        IPlaceOrder        Use Cases, Domain       OrderRepository    Prisma, Stripe, S3
                       IGetOrder          Entities, Events        PaymentGateway
```

**When NOT to use this pattern:**
- Small applications with 1-2 adapters where the distinction adds no clarity
- Vertical slice features where ports are implicit in the handler signatures

**Benefits:**
- Direction of every port is unambiguous — driving vs. driven
- Primary adapters are independently swappable (REST today, gRPC tomorrow)
- Secondary adapters are independently swappable (Prisma today, DynamoDB tomorrow)
- Testing: primary ports are the test entry points; secondary ports are the mocked boundaries

Reference: [Explicit Architecture — Herberto Graca](https://herbertograca.com/2017/11/16/explicit-architecture-01-ddd-hexagonal-onion-clean-cqrs-how-i-put-it-all-together/)
