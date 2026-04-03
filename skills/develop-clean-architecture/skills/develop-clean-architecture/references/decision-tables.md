---
title: Decision Tables, Anti-Patterns, and Conflict Resolution
impact: REFERENCE
impactDescription: comprehensive lookup tables for architecture decisions, anti-pattern recognition, and tension resolution
tags: reference, decisions, anti-patterns, conflicts
---

## Architecture Selector — When to Apply What

```
Is this a new project?
|
+-- YES: What is the domain complexity?
|  |
|  +-- LOW (CRUD, simple rules, startup MVP)
|  |  -> Vertical Slices + Zod + Result types
|  |  -> Add domain layer only when rules emerge
|  |
|  +-- MEDIUM (some business rules, 2-5 bounded contexts)
|  |  -> Clean Architecture per component
|  |  -> Rich domain model, no events yet
|  |  -> CQRS for read-heavy features
|  |
|  +-- HIGH (complex invariants, many contexts, event-driven)
|     -> Full Explicit Architecture
|     -> DDD tactical patterns (aggregates, domain events)
|     -> CQRS + Event Sourcing where appropriate
|
+-- NO: Existing codebase -- where is the pain?
   |
   +-- Tests are slow / hard to write -> Extract domain layer first
   +-- Business rules scattered everywhere -> Introduce rich domain model
   +-- DB changes break everything -> Add repository abstraction
   +-- Slow build times -> Remove barrel files
   +-- Type errors at runtime -> Add strict + noUncheckedIndexedAccess
```

**The "Rule of Three" Before Abstracting:** Wait until you have three similar implementations before extracting a shared abstraction. Premature abstraction increases cognitive overhead and creates false DRY.

---

## Anti-Pattern Recognition Table

| Anti-Pattern | Symptoms | Layer Violated | Fix |
|---|---|---|---|
| Anemic Domain Model | Entities are data bags; services have all logic | Domain | Move business logic into entities |
| Fat Use Case | Use case > 50 lines; mixes orchestration with computation | Application | Extract domain logic to entities/domain services |
| Leaked Prisma Types | `Prisma.User` used in use case or domain | Application/Domain | Create mapper; use domain types inward |
| God Controller | Controller contains business rules | Adapters | Move logic to use case |
| Missing reconstitute factory | `Entity.create()` called when loading from DB | Domain | Add `Entity.reconstitute()` — no events, no invariant re-check |
| Event published before commit | Domain events dispatched inside `save()` | Infrastructure | Pull events after save; dispatch in use case |
| Barrel file cascade | Slow build; 11k modules loaded; circular deps | All | Replace with direct imports |
| Flag argument | `getUser(id, includeDeleted)` | Any | Split into two functions |
| Validation in domain | `if (!email.includes('@')) throw` in use case | Application | Parse at adapter boundary with Zod |
| Cross-aggregate direct reference | `order.customer.email` — Order holds Customer object | Domain | Reference by ID only: `order.customerId` |
| Tests mocking domain entities | `jest.spyOn(order, 'calculateTotal')` | Test | Test the real entity — it's pure |

---

## Conflict & Tension Resolution

Clean Code and Clean Architecture occasionally conflict. This table documents known tensions and their resolutions.

| # | Clean Code Says | Clean Architecture Says | Type | Resolution |
|:---:|---|---|:---:|---|
| 1 | DRY — don't repeat yourself | Each layer needs own DTOs/models | Conflict | Accept cross-layer duplication. Each model serves a different master |
| 2 | Functions <= 20 lines | Use cases orchestrate many steps | Tension | Apply SRP by reason to change, not line count |
| 3 | Avoid comments | Adapters need boundary contracts documented | Tension | JSDoc on ports and adapters only |
| 4 | No side effects | Domain events, persistence are side effects | Tension | Push to injected ports; dispatch events post-commit |
| 5 | Max 3 function arguments | Use case functions inject 3-5 ports | Tension | Group ports into `deps` object or use class-based handlers |
| 6 | Unit test every class | Test Interactors, not every tiny class | Conflict | Test use cases + domain entities; adapter tests = integration |
| 7 | Small classes | Rich domain entities grow large | Tension | Entity size = domain complexity, not a Clean Code violation |
| 8 | Avoid duplicate code | CQRS read side duplicates domain shape in DTOs | Tension | Query DTOs serve a fundamentally different purpose |
| 9 | Throw exceptions for errors | Typed Result returns for domain errors | Tension | Two-error-type model: Result for expected; throw for defects |
| 10 | Flat structure | Clean Architecture mandates 4+ layers | Conflict | Applies only to large, long-lived, rule-heavy codebases |
| 11 | Barrel file exports | Module boundary enforcement needs direct imports | Conflict | Avoid barrels in app code; use only for published library APIs |

---

## Layer Responsibility Cheatsheet

| Layer | Owns | May Import | Must Never Import | TypeScript Patterns |
|---|---|---|---|---|
| **Domain** | Entities, VOs, Aggregates, Domain Services, Domain Events, Port interfaces | `shared/domain` only | Application, Adapters, Infrastructure, any framework | `class`, branded `type`, discriminated unions, `#` private fields |
| **Application** | Use Cases, Command/Query Handlers, Application Events, Output Port interfaces | Domain layer | Adapters, Infrastructure, Express, Prisma | `async function`, `Result<T,E>`, `interface` for ports |
| **Adapters** | Controllers, Presenters, Input validation schemas | Application, Domain (types only) | Infrastructure internals | `implements`, Zod schemas, mapping functions |
| **Infrastructure** | Concrete repo impls, Gateway impls, ORM config, DB migrations | Adapters, Application ports | Domain logic | `implements` port interfaces, ORM types |
| **main.ts** | Wiring only | Everything | Nothing — it wires everything | `new`, DI container registration |

---

## Do This, Not That

| Do This | Not That | Rule |
|---------|----------|------|
| Define interface in use case layer | Define interface next to implementation | dep-interface-ownership |
| Return `Result<User, CreateUserError>` | Return `User \| null` or throw generic Error | ts-result-type |
| Use branded `UserId` type | Pass raw `string` for IDs | ts-branded-types |
| Separate `GetUserQuery` + `UpdateUserCommand` | One `UserService` with get + update | pattern-cqrs-separation |
| Entity emits `OrderCompleted` event | Use case calls `emailService.notify()` directly | pattern-domain-events |
| Domain-oriented folder: `src/ordering/domain/` | Technical folders: `src/models/`, `src/services/` | comp-screaming-architecture |
| Parse with Zod at HTTP boundary | Validate inside use case or domain | code-parse-dont-validate |
| `Order.create()` for new + `Order.reconstitute()` for DB load | Same constructor for both | entity-create-reconstitute |
| Per-layer DTOs (domain, API, DB) | One shared type everywhere | dep-dry-vs-duplication |
| Direct file imports | Barrel `index.ts` re-exports | comp-barrel-file-discipline |
| `import type { Order }` | `import { Order }` for type-only use | ts-verbatim-module-syntax |
| `#privateField` on entities | `private` keyword (compile-time only) | entity-rich-not-anemic |
| Wire in `main.ts` composition root | Hardwire deps inside use cases | bound-composition-root |
| `interface extends A, B, C {}` | `type X = A & B & C` | ts-lsp-performance |
