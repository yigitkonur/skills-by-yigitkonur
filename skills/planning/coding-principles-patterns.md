# Coding Principles & Patterns for Building New Software

A comprehensive reference of software engineering principles, organized as actionable patterns for creating new systems, features, and code.

---

## 1. Core Design Principles

The foundational rules that apply to virtually every coding decision.

### DRY - Don't Repeat Yourself
**Origin:** Andy Hunt & Dave Thomas, *The Pragmatic Programmer* (1999)

> Every piece of knowledge must have a single, unambiguous representation in a system.

- **Apply:** Extract common validation logic into a shared method used by multiple classes
- **Violate:** Copy-pasting the same database query across 5 controllers
- **Nuance:** Use the *Rule of Three* — duplicate up to 2-3 times before generalizing. Premature abstraction is worse than a little duplication.

### YAGNI - You Ain't Gonna Need It
**Origin:** Kent Beck, Extreme Programming (late 1990s)

> Implement only what is needed now. Avoid speculative features.

- **Apply:** Build a simple list endpoint without pagination until actually requested
- **Violate:** Adding a full plugin system before any plugins exist
- **Nuance:** Conflicts with Open-Closed Principle if needed flexibility emerges later. Balance with architectural foresight.

### KISS - Keep It Simple, Stupid
**Origin:** Cleve Moler (1970s), widely adopted

> Favor simple designs over complex ones. Complexity is the enemy.

- **Apply:** Use an if-else chain instead of the Strategy pattern when there are only 3 cases
- **Violate:** Over-engineering authentication with microservices for a monolith app

### SoC - Separation of Concerns
**Origin:** Edsger Dijkstra (1974)

> Divide a system into distinct sections where each addresses a separate concern.

- **Apply:** MVC — Model handles data, View handles UI, Controller handles logic
- **Violate:** A monolithic class mixing UI rendering, business logic, and database persistence

### CQS - Command-Query Separation
**Origin:** Bertrand Meyer (1980s)

> Methods either query (return value, no side effects) or command (produce side effects, no return value) — never both.

- **Apply:** `getBalance()` returns a value; `withdraw(amount)` changes state
- **Violate:** `getNext()` that advances an iterator while returning a value

---

## 2. SOLID Principles

The five pillars of object-oriented design, formulated by Robert C. Martin.

### S - Single Responsibility Principle (SRP)
> A class should have one, and only one, reason to change.

- **Apply:** `UserService` handles authentication only; a separate `EmailService` handles notifications
- **Violate:** A `User` class that handles auth, persistence, and UI rendering

### O - Open-Closed Principle (OCP)
> Software entities should be open for extension but closed for modification.

- **Apply:** Abstract `PaymentProcessor` base; add new payment types by creating new subclasses
- **Violate:** Modifying the core `PaymentHandler` class every time a new payment method is added

### L - Liskov Substitution Principle (LSP)
**Origin:** Barbara Liskov (1987)

> Subtypes must be substitutable for their base types without altering correctness.

- **Apply:** A `Rectangle` subclass behaves as a `Rectangle` — `setWidth` and `setHeight` are independent
- **Violate:** A `Square` subclass where `setWidth` also changes height, breaking expectations

### I - Interface Segregation Principle (ISP)
> Clients should not be forced to depend on interfaces they do not use.

- **Apply:** Separate `IPrinter` and `IScanner` interfaces instead of one fat `IDevice`
- **Violate:** A single interface with `print()`, `scan()`, and `fax()` forcing all implementations to stub unused methods

### D - Dependency Inversion Principle (DIP)
> Depend on abstractions, not concretions.

- **Apply:** Inject an `ILogger` abstraction into a class, not a concrete `ConsoleLogger`
- **Violate:** `new ConsoleLogger()` hardwired inside a class constructor

---

## 3. Behavioral Principles

Rules governing how code components interact with each other.

### Law of Demeter (Don't Talk to Strangers)
**Origin:** Ian Holland (1987)

> An object should only talk to its immediate friends, not reach through chains.

- **Bad:** `user.getAccount().getTransactions()[0].getAmount()`
- **Good:** `user.getAccountBalance()` — the user object delegates internally

### POLA - Principle of Least Astonishment
> Software should behave as expected by a knowledgeable user.

- **Apply:** A `sort()` method returns a new sorted list and does not mutate the original
- **Violate:** A function named `getUser()` that silently deletes expired sessions as a side effect

### Hollywood Principle (Don't Call Us, We'll Call You)
**Origin:** Gang of Four (1994)

> High-level components define the flow; low-level components plug into it.

- **Apply:** Register event listeners; the framework invokes them when events occur
- **Violate:** Application code polling the framework for updates in a loop

### Fail Fast
> Detect errors at the earliest possible moment and fail immediately.

- **Apply:** Validate inputs at method entry and throw exceptions on invalid state
- **Violate:** Silently swallowing malformed data and corrupting downstream state

### Postel's Law (Robustness Principle)
**Origin:** Jon Postel, TCP/IP (1980s)

> Be conservative in what you send, liberal in what you accept.

- **Apply:** Accept flexible date formats as input, but always output strict ISO 8601
- **Violate:** Rejecting requests over minor version mismatches

### Convention over Configuration (CoC)
**Origin:** David Heinemeier Hansson, Rails (2004)

> Use sensible defaults and naming conventions to reduce boilerplate configuration.

- **Apply:** Rails assumes `id` as primary key, plural table names by convention
- **Violate:** Requiring explicit configuration for every default setting

---

## 4. Architecture Patterns

Principles that guide how to structure systems at scale.

### Hexagonal Architecture (Ports and Adapters)
> Place core business logic at the center. External concerns (DB, UI, APIs) connect via ports (interfaces) and adapters (implementations).

**When to apply:** Applications needing testability and technology independence; microservices or modular monoliths.

### Domain-Driven Design Bounded Contexts
> Define explicit boundaries around domain models. Each context has its own model and ubiquitous language.

**When to apply:** Complex domains with multiple subdomains; large-scale systems.

### Strangler Fig Pattern
> Incrementally replace a legacy system by growing new code around it, routing traffic from old to new.

**When to apply:** Migrating monoliths to microservices without a big-bang rewrite.

### Polyglot Persistence
> Choose the right database per workload — SQL for transactions, document stores for flexible schemas, time-series DBs for metrics.

**When to apply:** Microservices with varied data access patterns.

---

## 5. API Design Principles

| Principle | Description | When to Apply |
|-----------|-------------|---------------|
| **Postel's Law** | Conservative output, liberal input acceptance | Public APIs handling diverse clients |
| **Principle of Least Power** | Use the least powerful format sufficient for the task | Minimizing client complexity and lock-in |
| **HATEOAS** | APIs return links for next actions, not hardcoded URLs | RESTful services needing discoverability |
| **Versioning Stability** | Stable endpoints; version only for breaking changes | Evolving public APIs without breaking clients |
| **Idempotency Keys** | Ensure operations are safe to retry without duplication | APIs over unreliable networks |

---

## 6. Data Modeling Principles

| Principle | Description | When to Apply |
|-----------|-------------|---------------|
| **Normalize (1NF-3NF)** | Eliminate redundancy; depend on keys only | Transactional OLTP systems |
| **Denormalize for reads** | Intentionally add redundancy for query speed | Read-heavy OLAP or high-scale apps |
| **Domain Model Alignment** | Model data structures matching business language | Bounded contexts in DDD |
| **Schema Evolution** | Add columns without breaking; use views or defaults | Evolving schemas in production |

---

## 7. Error Handling & Resilience

| Pattern | Description | When to Apply |
|---------|-------------|---------------|
| **Fail Fast** | Detect and fail on invalid state immediately | Input validation, system startup |
| **Circuit Breaker** | Halt calls to failing services; fallback after cooldown | Distributed service calls |
| **Bulkhead** | Isolate resources (threads, connections) per service | Preventing cascading failures |
| **Graceful Degradation** | Provide reduced functionality on failure | User-facing services |
| **Retry with Exponential Backoff** | Retry transient failures with increasing delays | Idempotent operations |

---

## 8. Code Craftsmanship

### From Clean Code (Robert C. Martin)

- **Meaningful names:** `daysSinceCreation` not `dsc`
- **Small functions:** 20 lines max, do one thing, max 3 arguments
- **No side effects:** Functions should not produce hidden changes
- **Exceptions over error codes:** Throw exceptions for abnormal cases, don't return null
- **FIRST tests:** Fast, Independent, Repeatable, Self-Validating, Timely

### From A Philosophy of Software Design (John Ousterhout)

- **Deep modules:** Few public APIs that hide significant internal complexity
- **Minimize abstraction layers:** Each layer has a cognitive cost — combine when possible
- **Avoid tactical programming:** Don't patch complexity with more code; redesign for simplicity
- **Strategic design:** Plan interfaces early — good design pays compound interest

### Refactoring Signals (Code Smells)

| Smell | Signal | Refactor Action |
|-------|--------|-----------------|
| Long Method | > 20 lines | Extract Method |
| Large Class | > 10 fields | Extract Class |
| Long Parameter List | > 3 args | Introduce Parameter Object |
| Switch Statements | Duplicated branching | Replace with Polymorphism |
| Divergent Change | Class changes for multiple reasons | Extract Class |
| Shotgun Surgery | One change touches many classes | Move Method / Inline Class |

### The Boy Scout Rule
> Always leave the code cleaner than you found it. Small improvements compound over time.

---

## 9. Testing Principles

- **Arrange-Act-Assert (AAA):** Setup state, perform action, verify outcome
- **Test Pyramid:** 70% unit, 20% integration, 10% E2E
- **One assert per test:** Keep tests focused and diagnostic
- **Test behavior, not implementation:** Avoid fragile tests coupled to internals
- **Rule of thumb:** If you can't test it, the design needs improvement

---

## 10. Modern Practices

### DevOps & Deployment
- **Infrastructure as Code (IaC):** Automate provisioning for reproducibility
- **Immutable Infrastructure:** Replace servers, don't patch them
- **Progressive Delivery:** Canary releases and feature flags to minimize blast radius
- **Config as Code:** Store config externally, not in the binary (12-Factor App)
- **Stateless Processes:** Design for fast start/stop, horizontal scaling
- **SLOs and Error Budgets:** Balance reliability with shipping velocity

### Security by Design
- **Least Privilege:** Grant minimal permissions required
- **Defense in Depth:** Multiple layered controls (identity, data, network, application)
- **Zero Trust:** Verify every request regardless of origin
- **Secrets Management:** Store credentials externally, never in code
- **Shift-Left Security:** Automate security checks in CI/CD pipelines

### Observability
- **Structured Logging:** Machine-readable JSON event streams
- **Correlation IDs:** Propagate across services for distributed tracing
- **Four Golden Signals:** Monitor latency, traffic, errors, saturation
- **Alerts on SLOs:** Alert on objectives, not symptoms

### Performance
- **Measure Before Optimizing:** "Premature optimization is the root of all evil" — Knuth
- **Amdahl's Law:** Speedup is bounded by the serial fraction of the workload
- **Cache Aggressively:** At edge and application layers
- **Right-Size Resources:** Auto-scale to match demand

---

## 11. Software Laws & Aphorisms

Named laws encoding hard-won engineering wisdom.

| Law | What It Says | Practical Takeaway |
|-----|-------------|-------------------|
| **Conway's Law** | Systems mirror org communication structures | Align team boundaries with module boundaries |
| **Brooks's Law** | Adding people to a late project makes it later | Reduce complexity, don't add headcount |
| **Hyrum's Law** | With enough users, every observable behavior becomes a dependency | Treat public APIs as immutable; version for changes |
| **Goodhart's Law** | When a measure becomes a target, it ceases to be good | Don't game code coverage or velocity metrics |
| **Hofstadter's Law** | It always takes longer, even accounting for this law | Plan for overruns; time-box aggressively |
| **Parkinson's Law** | Work expands to fill available time | Use deadlines and time-boxing |
| **Zawinski's Law** | Every program expands until it reads mail | Fight feature creep with strict scoping |
| **Linus's Law** | Given enough eyeballs, all bugs are shallow | Leverage code review and open collaboration |
| **Sturgeon's Law** | 90% of everything is crud | Curate libraries and dependencies ruthlessly |
| **Lehman's Laws** | Evolving systems grow more complex unless restructured | Schedule periodic refactoring |
| **Cunningham's Law** | The best way to get the right answer is to post the wrong one | Share drafts publicly for fast feedback |

### Numbered Rules

| Rule | Description |
|------|-------------|
| **Rule of Three** | Duplicate up to 3 times before abstracting |
| **Zero-One-Infinity** | Allow 0, 1, or unbounded instances — avoid arbitrary limits like 2-N |
| **Rule of Least Power** | Use the least powerful tool sufficient for the task |

### Key Anti-Patterns to Avoid

| Anti-Pattern | What Goes Wrong | Prevention |
|--------------|----------------|------------|
| **God Object** | One class does everything | Apply Single Responsibility Principle |
| **Lava Flow** | Dead code too risky to remove | Migrate incrementally; deprecate before delete |
| **Second System Effect** | Over-engineered sequel to a simple system | Prototype simply; iterate conservatively |
| **Analysis Paralysis** | Endless planning, no action | Time-box decisions; ship an MVP |
| **Vendor Lock-in** | Dependency on a specific provider | Use abstractions and standards for portability |

---

## 12. Principle Relationships

Understanding how principles reinforce or tension against each other:

```
KISS <--reinforces--> YAGNI <--tempered by--> Rule of Three <--enables--> DRY
  |                                                                        |
  +--reinforces--> POLA                                                    |
                                                                           v
SoC --underpins--> SRP --enables--> ISP                              Abstraction
                    |                                                      ^
                    v                                                      |
                   OCP <--supports--> LSP                                  |
                    |                                                      |
                    v                                                      |
                   DIP <--complements--> Law of Demeter -------> Loose Coupling
                    |
                    v
              Hollywood Principle (Inversion of Control)
```

**Key tensions:**
- **DRY vs YAGNI:** Don't abstract too early (YAGNI), but don't repeat yourself (DRY). The Rule of Three resolves this.
- **OCP vs KISS:** Making everything extensible adds complexity. Only apply OCP where change is likely.
- **Postel's Law vs Fail Fast:** Be liberal in acceptance, but also detect errors early. Apply Postel's at system boundaries, Fail Fast internally.
- **CoC vs POLA:** Conventions speed development but may surprise newcomers. Document conventions well.

---

## Quick Decision Framework

When building something new, ask in order:

1. **Do I need this now?** (YAGNI)
2. **Is there a simpler way?** (KISS)
3. **Does this have one clear responsibility?** (SRP / SoC)
4. **Am I duplicating knowledge?** (DRY, but check Rule of Three)
5. **Can I test this easily?** (If not, redesign)
6. **Would this surprise another developer?** (POLA)
7. **Am I depending on concretions?** (DIP)
8. **Am I reaching through object chains?** (Law of Demeter)
9. **Have I measured before optimizing?** (Avoid premature optimization)
10. **Is security built in, not bolted on?** (Least Privilege, Defense in Depth)
