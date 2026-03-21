---
title: Consider Vertical Slice Architecture for Feature-Oriented Organization
impact: MEDIUM
impactDescription: reduces cross-feature coupling, enables team-per-feature ownership
tags: pattern, vertical-slices, feature-organization, alternative
---

## Consider Vertical Slice Architecture for Feature-Oriented Organization

Vertical Slice Architecture (VSA) organizes code by feature rather than by technical layer. Each slice contains all code for one feature — validation, business logic, persistence, and HTTP binding. VSA and Clean Architecture are not mutually exclusive; combine them for complex slices.

**Incorrect (layered organization scatters feature code across 4+ folders):**

```text
src/
├── controllers/OrderController.ts    ← Feature code in 4 places
├── services/OrderService.ts
├── repositories/OrderRepository.ts
├── models/Order.ts
```

**Correct (vertical slice — all feature code in one folder):**

```text
src/features/
├── place-order/
│   ├── PlaceOrder.schema.ts        ← Zod validation
│   ├── PlaceOrder.handler.ts       ← Business logic
│   ├── PlaceOrder.repository.ts    ← Data access
│   ├── PlaceOrder.route.ts         ← HTTP binding
│   └── PlaceOrder.test.ts          ← All tests
├── cancel-order/
│   ├── CancelOrder.schema.ts
│   ├── CancelOrder.handler.ts
│   └── CancelOrder.test.ts
└── get-order-summary/
    ├── GetOrderSummary.handler.ts
    └── GetOrderSummary.test.ts
```

**Hybrid approach (VSA + Clean Architecture within complex slices):**

```text
src/
├── ordering/                        ← Complex feature → inner layers
│   ├── domain/
│   │   ├── Order.ts
│   │   └── OrderLine.ts
│   ├── application/
│   │   ├── PlaceOrder.handler.ts
│   │   └── ports/OrderRepository.ts
│   └── infrastructure/
│       └── PrismaOrderRepository.ts
├── notifications/                   ← Simple feature → flat slice
│   ├── SendConfirmation.handler.ts
│   └── SendConfirmation.test.ts
└── shared/
    └── Result.ts
```

**When to use VSA over layered Clean Architecture:**
- CRUD-heavy applications with simple business rules
- Microservice codebases where each service is small
- Fast feature delivery with independent team ownership
- When most features have identical structural needs

**When to use Clean Architecture over VSA:**
- Complex domain logic with rich invariants
- Many cross-cutting business rules
- Long-lived applications where domain complexity will grow
- When domain entities are shared across many features

**Benefits:**
- All code for a feature is in one folder — no hunting across layers
- Features can be added/removed without affecting other features
- Each team owns complete features, not horizontal layers
- Start flat; introduce inner layers only when complexity warrants it

Reference: [Vertical Slice Architecture — Jimmy Bogard](https://www.jimmybogard.com/vertical-slice-architecture/) | [Milan Jovanovic — VSA + Clean Architecture](https://www.milanjovanovic.tech/)
