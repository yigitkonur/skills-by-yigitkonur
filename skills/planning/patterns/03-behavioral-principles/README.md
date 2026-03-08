# 03 - Behavioral Principles

**Principles that govern how software components should behave, communicate, and handle the unexpected.**

---

## Overview

Behavioral principles guide the runtime interactions between objects, modules, and systems. Unlike structural design principles (which address how code is organized) or SOLID principles (which address class-level design), behavioral principles focus on how components **act** — how they communicate, how they handle errors, how they respond to unexpected input, and what assumptions they make about their environment.

These principles are language-agnostic but have different weights in different paradigms. Object-oriented codebases lean heavily on Law of Demeter and Tell Don't Ask. Distributed systems rely on Postel's Law and Fail Fast. Framework designers live by the Hollywood Principle and Convention over Configuration.

---

## Principles Index

| # | Principle | One-Liner | Primary Domain |
|---|---|---|---|
| 1 | [Law of Demeter](./law-of-demeter.md) | Don't talk to strangers — only interact with immediate collaborators | OO Design, Coupling |
| 2 | [Principle of Least Astonishment](./principle-of-least-astonishment.md) | Software should behave the way users expect | API Design, UX |
| 3 | [Hollywood Principle](./hollywood-principle.md) | "Don't call us, we'll call you" — Inversion of Control | Frameworks, DI |
| 4 | [Fail Fast](./fail-fast.md) | Detect and report errors at the earliest possible moment | Error Handling, Reliability |
| 5 | [Postel's Law](./postels-law.md) | Be conservative in what you send, liberal in what you accept | Interoperability, Protocols |
| 6 | [Tell, Don't Ask](./tell-dont-ask.md) | Push behavior to the object that owns the data | Domain Modeling, OO Design |
| 7 | [Convention over Configuration](./convention-over-configuration.md) | Provide sensible defaults; only configure deviations | Frameworks, Productivity |
| 8 | [Principle of Least Power](./principle-of-least-power.md) | Use the least powerful tool sufficient for the task | Tool Selection, Security |

---

## Relationship Map

```
                    +--------------------------+
                    | Principle of Least       |
                    | Astonishment (POLA)      |
                    +------------+-------------+
                                 |
                    "conventions should be unsurprising"
                                 |
                    +------------v-------------+
                    | Convention over          |
                    | Configuration            |
                    +------------+-------------+
                                 |
                   "frameworks provide conventions via..."
                                 |
                    +------------v-------------+
                    | Hollywood Principle       |
                    | (Inversion of Control)    |
                    +------------+-------------+
                                 |
              +------------------+------------------+
              |                                     |
   "objects should be told"              "and not expose internals"
              |                                     |
   +----------v----------+              +-----------v-----------+
   | Tell, Don't Ask      |              | Law of Demeter         |
   +-----------+----------+              +-----------+-----------+
               |                                     |
               +------------------+------------------+
                                  |
                    "when things go wrong..."
                                  |
                +--------+--------+--------+
                |                          |
     +----------v----------+    +----------v----------+
     | Fail Fast            |    | Postel's Law         |
     | (within your code)   |    | (at boundaries)      |
     +---------------------+    +---------------------+

     +---------------------+
     | Principle of Least   |   (cross-cutting: applies to
     | Power                |    tool/language selection
     +---------------------+    at every level)
```

---

## When to Apply Which

| Situation | Primary Principle | Supporting Principles |
|---|---|---|
| Designing a public API | Least Astonishment | Postel's Law, Convention over Configuration |
| Building a framework | Hollywood Principle | Convention over Configuration, Least Astonishment |
| Modeling business domains | Tell, Don't Ask | Law of Demeter |
| Handling user input | Fail Fast | Postel's Law (at the edge) |
| Choosing between tools | Principle of Least Power | Convention over Configuration |
| Integrating with external services | Postel's Law | Fail Fast (for internal errors) |
| Reducing coupling between modules | Law of Demeter | Hollywood Principle |
| Setting up project structure | Convention over Configuration | Least Astonishment |

---

## Tensions Between Principles

These principles do not always agree. Understanding the tensions helps you make informed trade-offs:

- **Fail Fast vs. Postel's Law**: Fail fast rejects bad input immediately. Postel's Law accepts reasonable variation. Resolution: Apply Postel's Law at system boundaries (accept extra fields, tolerate format variation) and fail fast within your domain (reject invalid business state).

- **Tell Don't Ask vs. Principle of Least Power**: Tell Don't Ask pushes logic into objects (more powerful). Least Power suggests using declarative approaches (less powerful). Resolution: Use Tell Don't Ask for domain logic; use declarative/less-powerful tools for infrastructure concerns (config, queries, templates).

- **Convention over Configuration vs. Least Astonishment**: Conventions can surprise newcomers. Resolution: Conventions must be well-documented, discoverable, and match industry norms.

- **Hollywood Principle vs. Debuggability**: IoC makes execution flow harder to trace. Resolution: Use IoC at architectural boundaries, direct calls within modules. Invest in observability.

---

## Further Reading

- Hunt, A., Thomas, D. — *The Pragmatic Programmer* (1999)
- Martin, R.C. — *Clean Code* (2008)
- Evans, E. — *Domain-Driven Design* (2003)
- Fowler, M. — [martinfowler.com/bliki](https://martinfowler.com/bliki/) (numerous articles on these principles)
