# Interface Segregation Principle (ISP)

**No client should be forced to depend on methods it does not use.**

---

## Origin

Formulated by **Robert C. Martin** while consulting for Xerox in the early 1990s. The Xerox printer software had a single `Job` class used by multiple subsystems (stapling, printing, faxing). When the printing subsystem needed a change to `Job`, all subsystems had to be recompiled and redeployed -- even those that didn't use the modified methods. Martin proposed splitting the fat interface into role-specific interfaces, each containing only the methods relevant to one client. The principle was published in *Agile Software Development: Principles, Patterns, and Practices* (2003).

---

## The Problem It Solves

Fat interfaces force implementors to provide methods they don't need, and force consumers to depend on methods they don't call. The implementor problem: a class that implements a 20-method interface but only needs 3 must either provide 17 stub methods (usually throwing `NotImplementedError`) or inherit unused implementations. The consumer problem: when any of those 20 methods changes its signature, *all* consumers must be recompiled -- even the ones using only the 3 methods that didn't change. The dependency graph becomes needlessly wide, coupling increases, and changes ripple further than they should.

---

## The Principle Explained

ISP says: split large interfaces into smaller, more focused ones based on the needs of the clients. Instead of one `Printer` interface with `print()`, `scan()`, `fax()`, and `staple()`, create separate interfaces: `Printable`, `Scannable`, `Faxable`, `Stapleable`. A simple desktop printer implements `Printable`. A multifunction device implements all four. Consumers depend only on the interfaces they actually use.

The principle is about **dependency management**. By narrowing the interface a client depends on, you narrow the reasons that client needs to change. If the fax API changes, only fax consumers are affected -- not print consumers. This reduces coupling, makes testing easier (mock a 2-method interface, not a 20-method one), and communicates intent clearly (a function that accepts `Readable` obviously only reads).

In TypeScript, ISP is particularly natural because of structural typing. You don't need to declare a class "implements" an interface -- if it has the right shape, it matches. This means you can define small, focused interfaces and any object that happens to have those methods satisfies them, without modification.

---

## Code Examples

### BAD: Fat interface forcing unnecessary dependencies

```typescript
interface Worker {
  work(): void;
  eat(): void;
  sleep(): void;
  attendMeeting(): void;
  writeReport(): void;
  manageTeam(): void;
}

class Developer implements Worker {
  work(): void { /* writes code */ }
  eat(): void { /* lunch break */ }
  sleep(): void { /* goes home */ }
  attendMeeting(): void { /* reluctantly */ }
  writeReport(): void { /* weekly status */ }
  manageTeam(): void {
    // Developer doesn't manage anyone, but must implement this
    throw new Error("Not a manager");
  }
}

class Intern implements Worker {
  work(): void { /* learns stuff */ }
  eat(): void { /* lunch break */ }
  sleep(): void { /* goes home */ }
  attendMeeting(): void {
    throw new Error("Interns don't attend meetings");
  }
  writeReport(): void {
    throw new Error("Interns don't write reports");
  }
  manageTeam(): void {
    throw new Error("Interns don't manage teams");
  }
}

// Three methods throw errors -- a clear sign the interface is too fat.
// Any function accepting Worker must handle possible NotImplemented errors.
```

### GOOD: Segregated interfaces based on client needs

```typescript
interface Workable {
  work(): void;
}

interface Feedable {
  eat(): void;
}

interface Restable {
  sleep(): void;
}

interface MeetingAttendee {
  attendMeeting(): void;
}

interface ReportWriter {
  writeReport(): void;
}

interface TeamManager {
  manageTeam(): void;
}

class Developer implements Workable, Feedable, Restable, MeetingAttendee, ReportWriter {
  work(): void { /* writes code */ }
  eat(): void { /* lunch break */ }
  sleep(): void { /* goes home */ }
  attendMeeting(): void { /* reluctantly */ }
  writeReport(): void { /* weekly status */ }
}

class Intern implements Workable, Feedable, Restable {
  work(): void { /* learns stuff */ }
  eat(): void { /* lunch break */ }
  sleep(): void { /* goes home */ }
  // No forced implementation of methods they don't need
}

// Functions declare exactly what they need:
function assignTask(worker: Workable): void {
  worker.work();
  // Only depends on work(). Doesn't know or care about eat/sleep/manage.
}

function scheduleLunch(people: Feedable[]): void {
  for (const person of people) person.eat();
  // Works with both Developer and Intern -- they both implement Feedable
}
```

### BAD: Monolithic repository interface

```typescript
interface Repository<T> {
  findById(id: string): Promise<T | null>;
  findAll(): Promise<T[]>;
  findByFilter(filter: Partial<T>): Promise<T[]>;
  create(entity: T): Promise<T>;
  update(id: string, changes: Partial<T>): Promise<T>;
  delete(id: string): Promise<void>;
  count(): Promise<number>;
  exists(id: string): Promise<boolean>;
  createMany(entities: T[]): Promise<T[]>;
  deleteMany(ids: string[]): Promise<void>;
  findWithPagination(page: number, size: number): Promise<PaginatedResult<T>>;
}

// Read-only views (reports, dashboards) are forced to depend on
// create, update, delete methods they will never call.
// The test doubles for read-only consumers mock 11 methods to use 3.
```

### GOOD: Role-based repository interfaces

```typescript
interface ReadRepository<T> {
  findById(id: string): Promise<T | null>;
  findAll(): Promise<T[]>;
}

interface WriteRepository<T> {
  create(entity: T): Promise<T>;
  update(id: string, changes: Partial<T>): Promise<T>;
  delete(id: string): Promise<void>;
}

interface SearchableRepository<T> {
  findByFilter(filter: Partial<T>): Promise<T[]>;
  findWithPagination(page: number, size: number): Promise<PaginatedResult<T>>;
  count(): Promise<number>;
}

interface BatchRepository<T> {
  createMany(entities: T[]): Promise<T[]>;
  deleteMany(ids: string[]): Promise<void>;
}

// Full repository composes all interfaces
class UserRepository implements
  ReadRepository<User>,
  WriteRepository<User>,
  SearchableRepository<User>,
  BatchRepository<User> {
  // Implements all methods
  async findById(id: string): Promise<User | null> { /* ... */ return null; }
  async findAll(): Promise<User[]> { return []; }
  async create(entity: User): Promise<User> { return entity; }
  async update(id: string, changes: Partial<User>): Promise<User> { return {} as User; }
  async delete(id: string): Promise<void> {}
  async findByFilter(filter: Partial<User>): Promise<User[]> { return []; }
  async findWithPagination(page: number, size: number): Promise<PaginatedResult<User>> {
    return { items: [], total: 0, page, size };
  }
  async count(): Promise<number> { return 0; }
  async createMany(entities: User[]): Promise<User[]> { return entities; }
  async deleteMany(ids: string[]): Promise<void> {}
}

// Consumers declare only what they need:
class UserReportService {
  // Only depends on reading -- not writing, not batching
  constructor(private readonly users: ReadRepository<User>) {}

  async generateReport(): Promise<Report> {
    const allUsers = await this.users.findAll();
    // ...
    return {} as Report;
  }
}

// Test double for UserReportService: mock only 2 methods, not 11
```

### TypeScript-native ISP with structural typing

```typescript
// You don't even need to declare interfaces ahead of time in TypeScript

function processReadableStream(input: { read(): Buffer; close(): void }): void {
  const data = input.read();
  input.close();
}

// ANY object with read() and close() works -- no "implements" declaration needed.
// The interface IS the function parameter type. Naturally segregated.

// This works:
const file = { read: () => Buffer.from("data"), close: () => {}, name: "test.txt" };
processReadableStream(file); // Extra 'name' property is fine -- structural typing
```

---

## Alternatives & Related Principles

| Principle | Relationship |
|-----------|-------------|
| **Role Interfaces** | Martin Fowler's term for interfaces designed around a specific client's needs rather than the implementor's capabilities. ISP naturally produces role interfaces. |
| **Fat Interfaces (Anti-Pattern)** | The opposite of ISP. One large interface that every consumer must depend on. Leads to `NotImplementedError` and unnecessary coupling. |
| **Header Interfaces** | An interface that mirrors a class's public methods 1:1. Often created reflexively ("every class needs an interface"). Usually a sign that ISP hasn't been considered -- the interface is shaped by the implementor, not the consumer. |
| **Adapter Pattern** | When you can't modify an existing fat interface, an adapter can present a narrow interface to consumers. A workaround when the source code isn't under your control. |

---

## When NOT to Apply

- **When the interface is naturally cohesive.** An `Iterator<T>` interface with `next()` and `hasNext()` is small and coherent. Splitting it further would be absurd.
- **When all clients use all methods.** If every consumer of an interface uses every method on it, the interface isn't fat -- it's correctly sized.
- **When the overhead of many interfaces exceeds the coupling cost.** Splitting an interface into 15 single-method interfaces creates navigation and comprehension overhead. Find the natural groupings.
- **Internal interfaces with few consumers.** ISP's cost-benefit ratio improves with more consumers. An interface used by one class doesn't need to be segregated.

---

## Tensions & Trade-offs

- **ISP vs. Discoverability**: Many small interfaces are harder to discover than one large one. IDE autocomplete on a fat interface shows you everything. With segregated interfaces, you need to know which interface to look for.
- **ISP vs. DRY**: Segregated interfaces may repeat method signatures across interfaces (e.g., `findById` appears in both `ReadRepository` and `CacheableRepository`). This is acceptable -- interfaces represent *roles*, not shared code.
- **ISP vs. Implementation Complexity**: An implementation that satisfies five interfaces has five contracts to maintain. The implementation class isn't simpler -- the simplicity is in the consumer's view.
- **ISP vs. Tooling**: Some languages/frameworks work better with larger interfaces. Dependency injection containers, serialization frameworks, and ORM tools may expect specific interface shapes.

---

## Real-World Consequences

A SaaS company's `UserService` interface had 40 methods: CRUD operations, authentication, authorization, profile management, notification preferences, billing integration, and audit logging. Every microservice that needed user data depended on this interface -- even if it only called `getUserById()`. When the billing team added a new method, all 12 consuming services needed to update their dependency, regenerate mocks, and redeploy -- even though none of them used billing methods. Deployments took a full day of coordination. After splitting into `UserLookup`, `UserAuth`, `UserBilling`, and `UserPreferences` interfaces, services depended only on what they used. Billing changes deployed in minutes, affecting only billing consumers.

---

## Key Quotes

> "Clients should not be forced to depend on interfaces that they do not use."
> -- Robert C. Martin

> "The lesson here is that depending on something that carries baggage that you don't need can cause you troubles that you didn't expect."
> -- Robert C. Martin

> "Make thin interfaces that are client-specific rather than general purpose."
> -- Robert C. Martin

---

## Further Reading

- *Agile Software Development: Principles, Patterns, and Practices* -- Robert C. Martin (2003)
- *Clean Architecture* -- Robert C. Martin (2017)
- ["RoleInterface"](https://martinfowler.com/bliki/RoleInterface.html) -- Martin Fowler
- ["HeaderInterface"](https://martinfowler.com/bliki/HeaderInterface.html) -- Martin Fowler
- *Patterns of Enterprise Application Architecture* -- Martin Fowler (2002)
