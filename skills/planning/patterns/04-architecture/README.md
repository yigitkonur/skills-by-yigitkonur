# 04 - Architecture Patterns

**Architectural patterns that define how systems are structured, how components communicate, and how they evolve over time.**

---

## Overview

Architecture patterns operate at the highest level of software design. They determine the shape of the entire system: how code is organized, how services communicate, where data lives, and how the system evolves. Unlike design patterns (which solve recurring problems within a codebase) or principles (which guide individual decisions), architecture patterns define the fundamental structural decisions that constrain all subsequent choices.

Choosing an architecture pattern is not a one-time decision. Real systems combine multiple patterns: a modular monolith with hexagonal architecture internally, using event-driven communication between modules, deployed following twelve-factor principles. The skill is knowing which pattern to apply where and when.

---

## Patterns Index

| # | Pattern | One-Liner | Best For |
|---|---|---|---|
| 1 | [Hexagonal Architecture](./hexagonal-architecture.md) | Ports and Adapters — isolate domain from infrastructure | Systems with complex domain logic and multiple integrations |
| 2 | [Domain-Driven Design](./domain-driven-design.md) | Model software around business domains with shared language | Complex business domains with domain expert access |
| 3 | [Microservices Principles](./microservices-principles.md) | Independently deployable services per business capability | Large teams, high-scale systems, organizational autonomy |
| 4 | [Event-Driven Architecture](./event-driven-architecture.md) | Components communicate through events, not direct calls | Systems needing extensibility, async processing, decoupling |
| 5 | [Strangler Fig](./strangler-fig.md) | Incrementally migrate from legacy to modern systems | Legacy modernization with low risk tolerance |
| 6 | [CQRS & Event Sourcing](./cqrs-event-sourcing.md) | Separate read/write models; store events as truth | High read/write asymmetry, audit requirements |
| 7 | [Layered Architecture](./layered-architecture.md) | Horizontal layers with clear responsibilities | Standard web applications, team onboarding |
| 8 | [Twelve-Factor App](./twelve-factor-app.md) | Cloud-native application design methodology | Any application deployed to cloud platforms |

---

## Architecture Decision Matrix

Use this matrix to help choose the right pattern for your situation. Score each factor for your project (Low / Medium / High) and see which patterns align.

### By Project Characteristics

| Characteristic | Layered | Hexagonal | Microservices | Event-Driven | CQRS/ES |
|---|---|---|---|---|---|
| **Domain complexity** | Low-Med | High | Medium | Any | High |
| **Team size** | 1-10 | 2-15 | 10+ | 5+ | 5+ |
| **Scaling needs** | Low-Med | Medium | High | High | High |
| **Integration count** | Few | Many | Many | Many | Few-Many |
| **Change frequency** | Low-Med | High | High | High | Medium |
| **Infrastructure maturity** | Low | Medium | High | High | High |

### By Quality Attribute Priority

| Quality Attribute | Best Pattern(s) | Avoid |
|---|---|---|
| **Time to market** | Layered, Twelve-Factor | CQRS/ES, Microservices (initially) |
| **Testability** | Hexagonal, DDD | Tightly-coupled Layered |
| **Scalability** | Microservices, Event-Driven | Single-process Monolith |
| **Maintainability** | Hexagonal, DDD, Vertical Slices | Deep Layered without discipline |
| **Auditability** | CQRS/Event Sourcing | CRUD (without audit tables) |
| **Team autonomy** | Microservices | Monolith (shared codebase) |
| **Operational simplicity** | Layered (Monolith) | Microservices |
| **Migration safety** | Strangler Fig | Big Bang Rewrite |

### Common Combinations

These patterns are frequently used together:

| Combination | When to Use |
|---|---|
| **Modular Monolith + Hexagonal + DDD** | Complex domain, small-medium team, not yet ready for microservices. The best starting point for most serious applications. |
| **Microservices + Event-Driven + Twelve-Factor** | Large organization, high scale, independent team velocity required. The "Netflix/Amazon" stack. |
| **Layered + Twelve-Factor** | Standard web application deployed to cloud. Simple, well-understood, gets you to production fast. |
| **Strangler Fig + Event-Driven** | Migrating legacy: new services communicate via events, legacy is gradually replaced. |
| **DDD + CQRS/ES** | Complex domain with audit requirements and high read/write asymmetry (financial, healthcare). |
| **Hexagonal + Microservices** | Each microservice internally uses hexagonal architecture for testability and adapter swappability. |

---

## Decision Flowchart

```
Start: What is your situation?
  |
  +-- Building a new application?
  |     |
  |     +-- Small team (< 8), unclear domain?
  |     |     --> Layered Architecture + Twelve-Factor
  |     |         (ship fast, learn the domain)
  |     |
  |     +-- Complex domain, domain experts available?
  |     |     --> DDD + Hexagonal Architecture
  |     |         (model the domain first, extract services later)
  |     |
  |     +-- Large org (50+ devs), multiple teams?
  |     |     --> Microservices + Event-Driven + Twelve-Factor
  |     |         (but consider Modular Monolith first)
  |     |
  |     +-- Need complete audit trail?
  |           --> CQRS + Event Sourcing
  |               (but only if domain justifies complexity)
  |
  +-- Migrating a legacy system?
  |     |
  |     +-- Can isolate features behind a proxy?
  |     |     --> Strangler Fig Pattern
  |     |
  |     +-- Cannot isolate externally?
  |           --> Branch by Abstraction (internal strangler)
  |
  +-- Scaling an existing system?
        |
        +-- Read/write ratio heavily skewed?
        |     --> CQRS (separate read replicas/models)
        |
        +-- Need to scale specific features independently?
        |     --> Extract to Microservices (selectively)
        |
        +-- Need to decouple components?
              --> Event-Driven Architecture
```

---

## Relationships Between Patterns

```
+------------------+          +-----------------+
| Layered          |  evolves | Hexagonal       |
| Architecture     | -------> | Architecture    |
+------------------+          +--------+--------+
                                       |
                            "with DDD tactical patterns"
                                       |
                              +--------v--------+
                              | Domain-Driven   |
                              | Design          |
                              +--------+--------+
                                       |
                        "extract bounded contexts into"
                                       |
                              +--------v--------+
                              | Microservices   |
                              +--------+--------+
                                       |
                          "communicate via"
                                       |
                              +--------v--------+
                              | Event-Driven    |
                              | Architecture    |
                              +--------+--------+
                                       |
                       "optionally with"
                                       |
                              +--------v--------+
                              | CQRS / Event    |
                              | Sourcing        |
                              +-----------------+

  +------------------+
  | Strangler Fig    |  applies when migrating
  | Pattern          |  between any of the above
  +------------------+

  +------------------+
  | Twelve-Factor    |  cross-cutting: applies to
  | App              |  how any of the above are
  +------------------+  deployed and operated
```

---

## Anti-Pattern Warning Signs

Watch for these signals that your architecture choice is not working:

| Signal | Likely Problem | Consider |
|---|---|---|
| Deploy one service, must deploy three more | Distributed Monolith | Modular Monolith, or fix service boundaries |
| Every feature change touches every layer | Layered Architecture pain | Vertical Slices, Feature Folders |
| Business rules scattered across services | Missing DDD / domain layer | Hexagonal Architecture, Tell Don't Ask |
| Cannot test without full infrastructure | Tight coupling to infra | Hexagonal Architecture (ports/adapters) |
| Adding a new reaction requires modifying producer | Missing Event-Driven | Event-Driven Architecture |
| Read performance degrades as write volume grows | Single model bottleneck | CQRS, Read Replicas |
| Legacy rewrite is "90% done" for 2 years | Big Bang Rewrite failure | Strangler Fig Pattern |

---

## Further Reading

- Richards, M. — *Fundamentals of Software Architecture* (2020)
- Richards, M., Ford, N. — *Software Architecture: The Hard Parts* (2021)
- Newman, S. — *Building Microservices* (2nd ed., 2021)
- Evans, E. — *Domain-Driven Design* (2003)
- Martin, R.C. — *Clean Architecture* (2017)
- Kleppmann, M. — *Designing Data-Intensive Applications* (2017)
- Fowler, M. — [Architecture section on martinfowler.com](https://martinfowler.com/architecture/)
