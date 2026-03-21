---
title: Implement Repository Pattern with TypeScript Generic Interfaces
impact: MEDIUM
impactDescription: decouples persistence from business logic, enables instant test doubles
tags: pattern, repository, persistence, generics
---

## Implement Repository Pattern with TypeScript Generic Interfaces

Define a generic `Repository<T, ID>` interface in the application layer. Implement it in infrastructure with ORM or database specifics. Use cases depend on the interface, never on the concrete implementation — making persistence swappable and testing trivial.

**Incorrect (use case directly importing and calling Prisma):**

```typescript
// application/usecases/CreateOrderUseCase.ts
import { PrismaClient } from '@prisma/client';  // Application depends on infrastructure

class CreateOrderUseCase {
  private prisma = new PrismaClient();  // Concrete dependency, not injectable

  async execute(dto: CreateOrderDto): Promise<Order> {
    // Prisma-specific API leaks into business logic
    const order = await this.prisma.order.create({
      data: { customerId: dto.customerId, status: 'PENDING',
        items: { create: dto.items.map(i => ({
          productId: i.productId, quantity: i.quantity, price: i.price,
        }))},
      },
      include: { items: true },  // ORM-specific query shape
    });
    return order;  // Returns Prisma model, not domain entity
  }
}
```

**Correct (repository interface in application, implementation in infrastructure):**

```typescript
// application/ports/Repository.ts
interface Repository<T, ID> {
  findById(id: ID): Promise<T | null>;
  save(entity: T): Promise<void>;
  delete(id: ID): Promise<void>;
}

// application/ports/IOrderRepository.ts
interface IOrderRepository extends Repository<Order, OrderId> {
  findByCustomer(customerId: CustomerId): Promise<Order[]>;
  findPending(): Promise<Order[]>;
}

// application/usecases/CreateOrderUseCase.ts
class CreateOrderUseCase {
  constructor(private readonly orderRepo: IOrderRepository) {}  // Depends on port

  async execute(command: CreateOrderCommand): Promise<Result<OrderId>> {
    const order = Order.create(
      command.customerId,
      command.items.map(i => OrderItem.create(i.productId, i.quantity, i.price)),
    );

    await this.orderRepo.save(order);  // Pure domain operation
    return Result.ok(order.id);
  }
}

// infrastructure/persistence/PrismaOrderRepository.ts
import { PrismaClient } from '@prisma/client';

class PrismaOrderRepository implements IOrderRepository {
  constructor(private readonly prisma: PrismaClient) {}

  async findById(id: OrderId): Promise<Order | null> {
    const rec = await this.prisma.order.findUnique({ where: { id: id.value }, include: { items: true } });
    return rec ? this.toDomain(rec) : null;
  }

  async save(order: Order): Promise<void> {
    const data = this.toPersistence(order);
    await this.prisma.order.upsert({ where: { id: order.id.value }, create: data, update: data });
  }

  async delete(id: OrderId): Promise<void> {
    await this.prisma.order.delete({ where: { id: id.value } });
  }

  async findByCustomer(cid: CustomerId): Promise<Order[]> {
    const recs = await this.prisma.order.findMany({ where: { customerId: cid.value }, include: { items: true } });
    return recs.map(r => this.toDomain(r));
  }

  async findPending(): Promise<Order[]> {
    const recs = await this.prisma.order.findMany({ where: { status: 'PENDING' }, include: { items: true } });
    return recs.map(r => this.toDomain(r));
  }

  private toDomain(record: any): Order { /* map DB record → entity */ }
  private toPersistence(order: Order): any { /* map entity → DB shape */ }
}

// infrastructure/persistence/InMemoryOrderRepository.ts
class InMemoryOrderRepository implements IOrderRepository {
  private store = new Map<string, Order>();

  async findById(id: OrderId): Promise<Order | null> { return this.store.get(id.value) ?? null; }
  async save(order: Order): Promise<void> { this.store.set(order.id.value, order); }
  async delete(id: OrderId): Promise<void> { this.store.delete(id.value); }
  async findByCustomer(cid: CustomerId): Promise<Order[]> {
    return [...this.store.values()].filter(o => o.customerId.equals(cid));
  }
  async findPending(): Promise<Order[]> {
    return [...this.store.values()].filter(o => o.isPending());
  }
}
```

**When NOT to use this pattern:**
- Throwaway scripts or one-off data migrations
- When the ORM is unlikely to change and testing against a real database is acceptable
- Extremely simple apps where a single `db.query()` call suffices

**Benefits:**
- Use cases are testable in milliseconds with `InMemoryRepository` — no database needed
- Switching from Prisma to TypeORM or raw SQL changes only the infrastructure layer
- Domain entities stay free of ORM decorators and persistence concerns
- Generic base interface eliminates boilerplate across multiple aggregates

Reference: [Repository - Martin Fowler](https://martinfowler.com/eaaCatalog/repository.html)
