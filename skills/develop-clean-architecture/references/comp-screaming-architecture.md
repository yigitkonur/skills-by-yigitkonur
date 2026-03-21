---
title: Structure Should Scream the Domain Not the Framework
impact: HIGH
impactDescription: enables understanding at a glance, reveals intent
tags: comp, screaming-architecture, structure, domain
---

## Structure Should Scream the Domain Not the Framework

The folder structure should communicate what the system does, not what framework it uses. Looking at the top-level directories should reveal the business domain. Prefer package-by-component (each bounded context has its own layers) over package-by-layer (all entities in one folder, all services in another).

**Incorrect (framework-oriented structure):**

```text
src/
├── controllers/
│   ├── UserController.ts
│   ├── OrderController.ts
│   └── ProductController.ts
├── services/
│   ├── UserService.ts
│   ├── OrderService.ts
│   └── ProductService.ts
├── repositories/
│   ├── UserRepository.ts
│   ├── OrderRepository.ts
│   └── ProductRepository.ts
├── models/
│   ├── User.ts
│   ├── Order.ts
│   └── Product.ts
└── utils/
    └── helpers.ts

# This screams "MVC framework" not "e-commerce system"
```

**Correct (domain-oriented structure with package-by-component):**

```text
src/
├── ordering/                        ← Bounded context 1
│   ├── domain/
│   │   ├── Order.ts                 ← Aggregate Root
│   │   ├── OrderLine.ts             ← Internal entity
│   │   ├── value-objects/
│   │   │   ├── Money.ts
│   │   │   └── CouponCode.ts
│   │   ├── events/
│   │   │   ├── OrderPlaced.ts
│   │   │   └── OrderCancelled.ts
│   │   ├── services/
│   │   │   └── OrderTransferService.ts
│   │   └── ports/
│   │       └── OrderRepository.ts
│   ├── application/
│   │   ├── commands/
│   │   │   ├── PlaceOrder.command.ts
│   │   │   └── PlaceOrder.handler.ts
│   │   ├── queries/
│   │   │   └── GetOrderSummary.handler.ts
│   │   └── ports/
│   │       ├── PaymentGateway.ts
│   │       └── DomainEventBus.ts
│   ├── adapters/
│   │   ├── http/
│   │   │   ├── OrderController.ts
│   │   │   └── schemas/PlaceOrder.schema.ts
│   │   └── presenters/
│   │       └── OrderPresenter.ts
│   └── infrastructure/
│       ├── persistence/
│       │   ├── PrismaOrderRepository.ts
│       │   └── mappers/OrderMapper.ts
│       └── gateways/
│           └── StripePaymentGateway.ts
├── customers/                       ← Bounded context 2
│   ├── domain/
│   ├── application/
│   ├── adapters/
│   └── infrastructure/
├── shared/                          ← Shared Kernel (keep MINIMAL)
│   ├── domain/
│   │   ├── Result.ts
│   │   ├── DomainEvent.ts
│   │   └── ValueObject.ts
│   └── infrastructure/
│       └── IdGenerator.ts
└── main.ts                          ← Composition Root
```

**Package-by-layer vs Package-by-component:**

| Dimension | Package-by-layer | Package-by-component |
|---|---|---|
| Top-level screams | "MVC framework" | "E-commerce system" |
| Team ownership | Teams own layers (everyone touches domain) | Teams own bounded contexts |
| Feature delivery | Changes span all layer folders | Changes stay within one component folder |
| Best for | Small apps, learning exercises | Large teams, long-lived systems |

**Benefits:**
- New developers understand the domain immediately
- Related code lives together, enabling focused changes
- Frameworks become implementation details, not organizing principles

Reference: [Screaming Architecture](https://blog.cleancoder.com/uncle-bob/2011/09/30/Screaming-Architecture.html)
