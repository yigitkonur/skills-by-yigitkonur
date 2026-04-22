---
title: Use Conditional and Mapped Types for Layer Contracts
impact: MEDIUM
impactDescription: auto-derives DTOs from entities, enforces handler-command relationships at compile time
tags: ts, conditional-types, mapped-types, contracts
---

## Use Conditional and Mapped Types for Layer Contracts

Conditional types and mapped types derive one type from another — creating compile-time-enforced contracts between layers. Use them to auto-generate DTOs from entities, extract command types from handlers, and enforce repository method signatures.

**Incorrect (manually maintained parallel types drift):**

```typescript
// Must manually keep in sync — they WILL drift
interface Order {
  id: OrderId;
  status: OrderStatus;
  total: Money;
  createdAt: Date;
}

interface OrderDTO {
  id: string;        // manually mapped from OrderId
  status: string;    // manually mapped from OrderStatus
  total: number;     // manually mapped from Money — WRONG, lost currency
  createdAt: string; // manually mapped from Date
}
```

**Correct (auto-derive DTO shape from entity):**

```typescript
// Automatically derive DTO shape from entity — single source of truth
type EntityToDTO<T> = {
  [K in keyof T as T[K] extends Function ? never : K]: T[K] extends Date
    ? string
    : T[K] extends Money
    ? { amount: number; currency: string }
    : T[K];
};

// Infer command type from handler — compiler enforces relationship
type CommandOf<T extends ICommandHandler<any, any>> =
  T extends ICommandHandler<infer C, any> ? C : never;

type ResultOf<T extends ICommandHandler<any, any>> =
  T extends ICommandHandler<any, infer R> ? R : never;

// Usage: compiler enforces handler-command type relationship
type PlaceOrderInput = CommandOf<PlaceOrderHandler>;   // = PlaceOrderCommand
type PlaceOrderOutput = ResultOf<PlaceOrderHandler>;   // = OrderId

// Generate repository find methods from entity shape
type FindMethods<T, Keys extends keyof T> = {
  [K in Keys as `findBy${Capitalize<string & K>}`]: (value: T[K]) => Promise<T | null>;
};

interface UserRepository extends FindMethods<User, 'email' | 'username'> {
  save(user: User): Promise<void>;
  findById(id: UserId): Promise<User | null>;
}
// Auto-generates: findByEmail(email: Email) and findByUsername(username: Username)
```

**When NOT to use this pattern:**
- Deeply nested conditional types (5+ levels) — exponential compile time
- When the derived types need to diverge intentionally from the source
- Small projects where manual type maintenance is trivial

**Benefits:**
- Single source of truth — entity changes automatically propagate to DTOs
- Handler-command relationships enforced by the type system
- Repository interfaces generated from entity shape — no manual sync
- LSP shows the resolved types on hover for debugging

Reference: [TypeScript Handbook — Conditional Types](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html) | [TypeScript Handbook — Mapped Types](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html)
