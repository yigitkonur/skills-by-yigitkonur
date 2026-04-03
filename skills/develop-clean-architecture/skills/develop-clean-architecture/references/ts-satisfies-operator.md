---
title: Use satisfies to Validate Shape Without Widening Types
impact: MEDIUM
impactDescription: preserves literal types for LSP autocomplete while validating conformance to port interfaces
tags: ts, satisfies, type-checking, lsp
---

## Use satisfies to Validate Shape Without Widening Types

The `satisfies` operator validates that a value conforms to a type WITHOUT widening the inferred type. This preserves literal types for LSP autocomplete while ensuring structural correctness — ideal for configuration objects and port registries.

**Incorrect (type annotation widens literals):**

```typescript
const dbConfig: Record<string, string | number | boolean> = {
  host: 'localhost',
  port: 5432,
  database: 'myapp',
  ssl: false,
};

dbConfig.host;  // LSP: string | number | boolean — lost 'localhost' literal
dbConfig.port;  // LSP: string | number | boolean — lost 5432 literal
```

**Correct (satisfies preserves literals):**

```typescript
const dbConfig = {
  host: 'localhost',
  port: 5432,
  database: 'myapp',
  ssl: false,
} satisfies Record<string, string | number | boolean>;

dbConfig.host;  // LSP: 'localhost' — literal preserved
dbConfig.port;  // LSP: 5432 — number literal preserved

// Port registry: validates interface conformance AND preserves concrete types
const ports = {
  orders: new PrismaOrderRepository(prisma),
  payments: new StripePaymentGateway(key),
  events: new InMemoryDomainEventBus(),
} satisfies {
  orders: OrderRepository;
  payments: PaymentGateway;
  events: DomainEventBus;
};

// TS validates ports matches the interfaces AND preserves concrete class types
ports.orders;   // LSP: PrismaOrderRepository (not just OrderRepository)
ports.payments;  // LSP: StripePaymentGateway (not just PaymentGateway)
```

**When NOT to use this pattern:**
- When you intentionally want type widening (e.g., a variable that holds different implementations over time)
- Dynamic objects where the shape is not known at compile time

**Benefits:**
- Configuration objects get full literal-type autocomplete in LSP
- Port registries validate against interfaces without losing concrete type information
- Catches typos and missing fields at compile time
- Zero runtime cost — purely a compile-time check

Reference: [TypeScript 4.9 — satisfies operator](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html)
