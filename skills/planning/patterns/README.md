# Coding Principles & Patterns Registry

A comprehensive, deep-dive reference of 100+ software engineering principles, patterns, laws, and best practices.

## How to Use This Registry
- Each principle has its own file with origin, examples, alternatives, and trade-offs
- Use the Quick Decision Framework below when starting new work
- Browse by category or search for specific principles

## Registry Contents

### [01 - Core Principles](./01-core-principles/)
DRY, YAGNI, KISS, Separation of Concerns, CQS, Composition over Inheritance, Encapsulation

### [02 - SOLID Principles](./02-solid/)
SRP, OCP, LSP, ISP, DIP — and how they interrelate

### [03 - Behavioral Principles](./03-behavioral-principles/)
Law of Demeter, POLA, Hollywood Principle, Fail Fast, Postel's Law, Tell Don't Ask, CoC, Least Power

### [04 - Architecture Patterns](./04-architecture/)
Hexagonal, DDD, Microservices, Event-Driven, Strangler Fig, CQRS, Layered, 12-Factor

### [05 - Code Craftsmanship](./05-code-craftsmanship/)
Clean Code, Deep Modules, Refactoring, Naming, Error Handling, Immutability

### [06 - Modern Practices](./06-modern-practices/)
IaC, Security by Design, Observability, Progressive Delivery, DevOps Culture, Shift-Left

### [07 - Laws & Aphorisms](./07-laws-and-aphorisms/)
Conway's, Brooks's, Hyrum's, Goodhart's, Gall's, Lehman's, Kernighan's, and more

### [08 - Anti-Patterns](./08-anti-patterns/)
God Object, Lava Flow, Golden Hammer, Premature Optimization, Cargo Cult, and more

### [09 - API Design](./09-api-design/)
REST, Versioning, Idempotency, Pagination, Error Responses, Contract-First, GraphQL vs REST

### [10 - Data Modeling](./10-data-modeling/)
Normalization, Denormalization, Schema Evolution, Event Sourcing, Polyglot Persistence

### [11 - Resilience Patterns](./11-resilience-patterns/)
Circuit Breaker, Bulkhead, Retry, Timeouts, Graceful Degradation, Chaos Engineering

### [12 - Testing Principles](./12-testing-principles/)
Test Pyramid, TDD, AAA, Test Doubles, Property-Based Testing, Contract Testing, Mutation Testing

### [13 - Functional Principles](./13-functional-principles/)
Pure Functions, Immutability, Higher-Order Functions, Railway-Oriented, ADTs, Composition

### [14 - Concurrency Patterns](./14-concurrency-patterns/)
Async/Await, Actor Model, Producer-Consumer, Event Loop, Locking, Pub/Sub, Thread Safety

## Quick Decision Framework

When building something new, ask in order:

1. **Do I need this now?** → YAGNI
2. **Is there a simpler way?** → KISS
3. **Does this have one clear job?** → SRP / SoC
4. **Am I duplicating knowledge?** → DRY (but check Rule of Three)
5. **Can I test this easily?** → If not, redesign
6. **Would this surprise another developer?** → POLA
7. **Am I depending on concretions?** → DIP
8. **Am I reaching through object chains?** → Law of Demeter
9. **Have I measured before optimizing?** → Avoid premature optimization
10. **Is security built in, not bolted on?** → Least Privilege, Defense in Depth

## Principle Relationships Map

```
KISS ←reinforces→ YAGNI ←tempered by→ Rule of Three ←enables→ DRY
SoC ──underpins──→ SRP ──enables──→ ISP
OCP ←─supports──→ LSP
DIP ←complements→ Law of Demeter ───→ Loose Coupling
Fail Fast ←tension→ Postel's Law
CoC ←tension→ POLA
```

## Stats
- 14 categories
- 100+ individual principle files
- Every principle includes alternatives and trade-offs
