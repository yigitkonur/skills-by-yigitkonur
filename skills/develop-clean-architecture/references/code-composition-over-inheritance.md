---
title: Prefer Composition Over Inheritance — Implement Focused Interfaces
impact: HIGH
impactDescription: prevents fragile base class problem, enables ISP-compliant designs
tags: code, composition, inheritance, isp
---

## Prefer Composition Over Inheritance — Implement Focused Interfaces

Inheritance creates tight coupling between base and derived classes. Composition via focused interfaces lets classes implement only what they need, following the Interface Segregation Principle. Reserve inheritance for shared plumbing (e.g., AggregateRoot event tracking).

**Incorrect (inheritance creates fragile coupling):**

```typescript
abstract class BaseRepository<T> {
  abstract findById(id: string): Promise<T | null>;
  async findOrThrow(id: string): Promise<T> {
    const entity = await this.findById(id);
    if (!entity) throw new Error(`Not found: ${id}`);
    return entity;
  }
  abstract save(entity: T): Promise<void>;
  abstract delete(id: string): Promise<void>;
}

// Forced to implement delete even when orders should never be deleted
class PrismaOrderRepository extends BaseRepository<Order> {
  async findById(id: string): Promise<Order | null> { /* ... */ }
  async save(order: Order): Promise<void> { /* ... */ }
  async delete(id: string): Promise<void> {
    throw new Error('Orders cannot be deleted');  // Dead code
  }
}
```

**Correct (composition via focused interfaces):**

```typescript
interface Findable<T, ID> {
  findById(id: ID): Promise<T | null>;
}

interface Saveable<T> {
  save(entity: T): Promise<void>;
}

interface Deletable<ID> {
  delete(id: ID): Promise<void>;
}

// Implements only what it needs — orders are never deleted
class PrismaOrderRepository implements Findable<Order, OrderId>, Saveable<Order> {
  async findById(id: OrderId): Promise<Order | null> { /* ... */ }
  async save(order: Order): Promise<void> { /* ... */ }
}

// Users support all operations
class PrismaUserRepository implements Findable<User, UserId>, Saveable<User>, Deletable<UserId> {
  async findById(id: UserId): Promise<User | null> { /* ... */ }
  async save(user: User): Promise<void> { /* ... */ }
  async delete(id: UserId): Promise<void> { /* ... */ }
}
```

**When NOT to use this pattern:**
- Shared event-tracking plumbing in AggregateRoot — inheritance is appropriate for this narrow case
- Framework-mandated base classes where you have no choice

**Benefits:**
- No forced implementation of unused methods
- Each interface is independently testable and mockable
- Adding new capabilities does not affect existing implementations
- Classes document exactly which capabilities they support via `implements`

Reference: [Design Patterns — Gamma et al., "Favor composition over inheritance"](https://en.wikipedia.org/wiki/Design_Patterns)
