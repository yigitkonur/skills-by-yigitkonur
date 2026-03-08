# Composition Over Inheritance

**Favor assembling objects from smaller, focused components rather than building deep class hierarchies. Achieve code reuse through "has-a" relationships instead of "is-a" relationships.**

---

## Origin

Formalized by the **Gang of Four (Gamma, Helm, Johnson, Vlissides)** in *Design Patterns: Elements of Reusable Object-Oriented Software* (1994). The second principle stated in the book's introduction: "Favor object composition over class inheritance." The insight came from observing that the most flexible and maintainable designs they studied used composition, while the most brittle used deep inheritance hierarchies.

---

## The Problem It Solves

Inheritance creates the tightest form of coupling in object-oriented programming. A subclass depends on every implementation detail of its parent -- method signatures, field layout, internal algorithms, even the order of method calls. Change a base class, and every subclass might break (the "fragile base class problem"). Worse, inheritance hierarchies tend to grow over time as developers wedge new behaviors into the wrong places, leading to god classes at the top and bizarre workarounds at the leaves. The classic example: `Stack extends Vector` in Java's standard library, which meant stacks exposed methods like `insertElementAt()` that violate stack semantics.

---

## The Principle Explained

Composition means building complex behavior by combining simple, focused objects. Instead of a `Bird` inheriting from `FlyingAnimal` which inherits from `Animal`, a `Bird` *has* a `FlightBehavior` and a `SoundBehavior` that can be swapped, configured, and tested independently. The bird doesn't inherit flying -- it delegates to a flying component.

The advantages compound. Composition supports mixing behaviors freely (a duck can fly and swim; with inheritance, you'd need `FlyingSwimmingAnimal`). Components can be tested in isolation. Behavior can be changed at runtime. Dependencies are explicit -- you can see exactly what a class uses by looking at its constructor parameters, rather than tracing up a hierarchy of `super` calls.

This doesn't mean inheritance is always wrong. Inheritance is appropriate when there's a genuine "is-a" relationship with substitutability (Liskov Substitution Principle), the hierarchy is shallow (1-2 levels), and the base class is designed for extension. `FileInputStream extends InputStream` is reasonable. `AdminUser extends User extends Person extends Entity` is a maintenance nightmare.

---

## Code Examples

### BAD: Deep inheritance hierarchy

```typescript
class Entity {
  id: string = crypto.randomUUID();
  createdAt: Date = new Date();
  updatedAt: Date = new Date();

  save(): Promise<void> { /* ... */ return Promise.resolve(); }
  delete(): Promise<void> { /* ... */ return Promise.resolve(); }
}

class User extends Entity {
  constructor(public name: string, public email: string) { super(); }

  sendEmail(subject: string, body: string): Promise<void> {
    return Promise.resolve(); // Email sending coupled to domain entity
  }
}

class AdminUser extends User {
  permissions: string[] = ["all"];

  // Inherits save(), delete(), sendEmail() -- and their bugs
  grantPermission(userId: string, permission: string): Promise<void> {
    return Promise.resolve();
  }
}

class SuperAdminUser extends AdminUser {
  // Three levels deep. Changing Entity.save() could break this.
  // SuperAdminUser "is-a" AdminUser "is-a" User "is-a" Entity
  // What if we need a SuperAdmin that ISN'T a User? (e.g., a system account)
  override grantPermission(userId: string, permission: string): Promise<void> {
    // Overrides parent but still calls super -- fragile chain
    return super.grantPermission(userId, permission);
  }
}

// The Diamond Problem in action:
// What if we need a "ReadOnlyAdminUser" that can grant permissions
// but NOT save/delete? Inheritance can't express this cleanly.
```

### GOOD: Composition with focused components

```typescript
// --- Small, focused interfaces ---
interface Identifiable {
  readonly id: string;
  readonly createdAt: Date;
}

interface Persistable {
  save(): Promise<void>;
  delete(): Promise<void>;
}

interface PermissionGranter {
  grantPermission(userId: string, permission: string): Promise<void>;
}

// --- Reusable implementations ---
function createIdentity(): Identifiable {
  return {
    id: crypto.randomUUID(),
    createdAt: new Date(),
  };
}

function createPersistence(tableName: string, db: Database): Persistable {
  return {
    async save() { await db.upsert(tableName, this); },
    async delete() { await db.remove(tableName, this); },
  };
}

function createPermissionManager(permissionRepo: PermissionRepo): PermissionGranter {
  return {
    async grantPermission(userId: string, permission: string) {
      await permissionRepo.grant(userId, permission);
    },
  };
}

// --- Composed types ---
interface User extends Identifiable {
  name: string;
  email: string;
}

function createUser(name: string, email: string, db: Database): User & Persistable {
  return {
    ...createIdentity(),
    ...createPersistence("users", db),
    name,
    email,
  };
}

function createAdmin(
  name: string,
  email: string,
  db: Database,
  permissionRepo: PermissionRepo
): User & Persistable & PermissionGranter {
  return {
    ...createUser(name, email, db),
    ...createPermissionManager(permissionRepo),
  };
}

// Easy to create a ReadOnlyAdmin: just don't compose Persistable
// Easy to create a SystemAccount with permissions but no User fields
// Each piece is independently testable
```

### BAD: Inheritance for code reuse

```typescript
// Using inheritance just to share a logging method
class BaseService {
  protected log(message: string): void {
    console.log(`[${this.constructor.name}] ${message}`);
  }

  protected async withRetry<T>(fn: () => Promise<T>, retries = 3): Promise<T> {
    for (let i = 0; i < retries; i++) {
      try { return await fn(); }
      catch (e) { if (i === retries - 1) throw e; }
    }
    throw new Error("Unreachable");
  }
}

class UserService extends BaseService {
  async getUser(id: string): Promise<User> {
    this.log(`Fetching user ${id}`);
    return this.withRetry(() => this.db.findUser(id));
  }
}

class OrderService extends BaseService {
  async getOrder(id: string): Promise<Order> {
    this.log(`Fetching order ${id}`);
    return this.withRetry(() => this.db.findOrder(id));
  }
}
// Every service inherits BaseService for two utility methods.
// Now every service is coupled to BaseService. Can't use a different
// logger without changing the base class. Can't test the retry logic
// without instantiating a service.
```

### GOOD: Inject composed dependencies

```typescript
interface Logger {
  log(message: string): void;
}

interface RetryPolicy {
  execute<T>(fn: () => Promise<T>): Promise<T>;
}

class UserService {
  constructor(
    private readonly db: Database,
    private readonly logger: Logger,
    private readonly retry: RetryPolicy,
  ) {}

  async getUser(id: string): Promise<User> {
    this.logger.log(`Fetching user ${id}`);
    return this.retry.execute(() => this.db.findUser(id));
  }
}

// Logger and RetryPolicy are independently testable, swappable, configurable.
// UserService declares exactly what it needs -- no hidden inherited behavior.
```

---

## Alternatives & Related Principles

| Principle | Relationship |
|-----------|-------------|
| **Mixins** | A middle ground. Mixins compose behavior into classes without deep hierarchies. TypeScript supports them via intersection types and helper functions. Less flexible than composition but more ergonomic for certain patterns. |
| **Traits** | Similar to mixins but with explicit conflict resolution (found in Rust, Scala, PHP). Traits provide implementation reuse without inheritance, with clear rules for when two traits define the same method. |
| **Protocol-Oriented Programming** | Swift's approach. Define behavior contracts (protocols/interfaces) and provide default implementations through protocol extensions. Composition through conformance rather than inheritance. |
| **Entity-Component-System (ECS)** | The game development pattern. Entities are just IDs. Components are pure data. Systems process entities with specific component combinations. Pure composition, no inheritance at all. |

---

## When NOT to Apply

- **When there's a genuine, stable "is-a" relationship.** `HttpError extends Error` is fine. The hierarchy is shallow, the contract is stable, and substitutability holds.
- **When the framework demands it.** Some frameworks (older Angular, some Java frameworks) are built around inheritance. Fighting the framework is worse than accepting its patterns.
- **When composition introduces too much boilerplate.** If every composed class requires 15 constructor parameters for its components, the cure is worse than the disease. Consider a factory or builder.
- **Abstract base classes for template methods.** When subclasses override specific steps in a well-defined algorithm, the Template Method pattern (inheritance-based) can be cleaner than the equivalent composition.

---

## Tensions & Trade-offs

- **Composition vs. Discoverability**: With inheritance, IDE autocomplete shows you everything a class can do. With composition, you need to know which interface to look at. Good type definitions and documentation mitigate this.
- **Composition vs. Boilerplate**: Composition often requires more code -- constructor parameters, delegation methods, type declarations. TypeScript's structural typing and utility types help, but composition is inherently more verbose than `extends`.
- **Composition vs. Polymorphism**: Inheritance gives you polymorphism for free. With composition, you need explicit interfaces. In TypeScript, structural typing makes this less painful than in Java.
- **Composition vs. DRY**: Composition can lead to duplication if many classes compose the same set of behaviors. Factories and builder functions help, but the boilerplate is real.

---

## Real-World Consequences

The Java standard library's `Stack extends Vector` decision (made in 1996) has been a textbook example of inheritance misuse for three decades. Because `Stack` inherits from `Vector`, you can call `stack.insertElementAt(0, element)` -- inserting at the bottom of a "stack." You can call `stack.remove(index)` to pull elements from the middle. The stack contract is completely violated by its own API. The Java team acknowledged this was a mistake but can't fix it without breaking backward compatibility. Every Java developer has had to learn to use `Deque` instead, but `Stack` remains in the standard library -- a permanent monument to the wrong abstraction choice.

---

## Key Quotes

> "Favor object composition over class inheritance."
> -- Gang of Four, *Design Patterns*

> "Inheritance is not for code reuse. Inheritance is for polymorphism."
> -- Sandi Metz (paraphrased)

> "The problem with object-oriented languages is they've got all this implicit environment that they carry around with them. You wanted a banana but what you got was a gorilla holding the banana and the entire jungle."
> -- Joe Armstrong

> "Prefer composition over inheritance as it is more malleable / easy to modify later, but do not use a compose-always approach."
> -- Go language FAQ

---

## Further Reading

- *Design Patterns: Elements of Reusable Object-Oriented Software* -- Gamma, Helm, Johnson, Vlissides (1994)
- *Effective Java* (3rd Edition) -- Joshua Bloch (2018), Item 18: "Favor composition over inheritance"
- ["Composition vs Inheritance"](https://www.youtube.com/watch?v=wfMtDGfHWpA) -- Fun Fun Function (video)
- *Practical Object-Oriented Design* -- Sandi Metz (2018, 2nd Edition)
- *Head First Design Patterns* -- Freeman & Robson (2004)
