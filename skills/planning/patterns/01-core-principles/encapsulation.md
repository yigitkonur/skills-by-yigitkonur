# Encapsulation (Information Hiding)

**Bundle data with the methods that operate on it, and restrict direct access to an object's internals. Expose a stable interface; hide the volatile implementation details.**

---

## Origin

The concept was introduced by **David Parnas** in his 1972 paper "On the Criteria To Be Used in Decomposing Systems into Modules." Parnas argued that modules should be designed to hide design decisions that are likely to change. The term "encapsulation" became widespread through **Bjarne Stroustrup**'s work on C++ and **Alan Kay**'s Smalltalk, though each emphasized different aspects. Parnas focused on *information hiding* (what you conceal), while OOP traditions focused on *encapsulation* (how you bundle data and behavior). They're complementary views of the same idea.

---

## The Problem It Solves

When an object's internal data is exposed, every piece of code that touches that data becomes coupled to the internal representation. Change the data structure, and you break all consumers. Add a validation rule, and you can't enforce it -- callers can bypass it by writing directly. Debugging becomes a nightmare: when data is in a bad state, the mutation could have come from anywhere. In large codebases, exposed internals create a web of implicit dependencies that makes refactoring dangerous and expensive.

---

## The Principle Explained

Encapsulation has two facets. The first is **bundling**: keeping data and the operations on that data together in a single unit (class, module, closure). This ensures that the code most likely to change together lives together. The second is **access control**: hiding implementation details behind a public interface. Callers interact with the interface, not the internals.

The key insight is that the interface is a *contract* and the implementation is a *secret*. The contract should be stable -- callers can rely on it. The secret should be free to change -- you can optimize, restructure, or completely replace the implementation without affecting callers. This is why proper encapsulation isn't just slapping `private` on fields. It's about designing an interface that exposes *what* the object does, not *how* it does it.

Good encapsulation also enables **invariant protection**. If an `Account` object must never have a negative balance, and the `balance` field is public, every piece of code that modifies it must remember to check. One forgets, and you have corruption. If `balance` is private and only modifiable through a `withdraw()` method that enforces the rule, the invariant is guaranteed by design.

---

## Code Examples

### BAD: Exposed internals, no encapsulation

```typescript
class UserProfile {
  // All internals exposed -- anyone can modify anything
  name: string;
  email: string;
  passwordHash: string;   // Security disaster: exposed hash
  loginAttempts: number;   // Anyone can reset this
  isLocked: boolean;       // Anyone can unlock
  lastLoginAt: Date | null;
  preferences: Map<string, string>;

  constructor(name: string, email: string, passwordHash: string) {
    this.name = name;
    this.email = email;
    this.passwordHash = passwordHash;
    this.loginAttempts = 0;
    this.isLocked = false;
    this.lastLoginAt = null;
    this.preferences = new Map();
  }
}

// Callers reach into internals and manipulate state directly
function handleLogin(profile: UserProfile, passwordHash: string): boolean {
  if (profile.isLocked) return false;

  if (profile.passwordHash !== passwordHash) {
    profile.loginAttempts++;
    // BUG: forgot to check if attempts exceeded threshold
    // Another file locks at 5, this one doesn't lock at all
    return false;
  }

  profile.loginAttempts = 0;
  profile.lastLoginAt = new Date();
  return true;
}

// Somewhere else in the codebase...
profile.isLocked = false;      // Bypass security
profile.loginAttempts = 0;     // Reset without authorization
profile.passwordHash = "abc";  // Change password without validation
```

### GOOD: Proper encapsulation with enforced invariants

```typescript
class UserProfile {
  private passwordHash: string;
  private loginAttempts: number = 0;
  private locked: boolean = false;
  private lastLoginAt: Date | null = null;
  private readonly preferences: Map<string, string> = new Map();

  private static readonly MAX_LOGIN_ATTEMPTS = 5;

  constructor(
    private name: string,
    private email: string,
    passwordHash: string,
  ) {
    this.passwordHash = passwordHash;
  }

  // --- Public interface: exposes behavior, not data ---

  attemptLogin(candidateHash: string): LoginResult {
    if (this.locked) {
      return { success: false, reason: "account_locked" };
    }

    if (this.passwordHash !== candidateHash) {
      this.loginAttempts++;
      if (this.loginAttempts >= UserProfile.MAX_LOGIN_ATTEMPTS) {
        this.locked = true;
      }
      return { success: false, reason: "invalid_credentials" };
    }

    this.loginAttempts = 0;
    this.lastLoginAt = new Date();
    return { success: true };
  }

  unlock(adminAuthorization: AdminToken): void {
    if (!adminAuthorization.isValid()) {
      throw new UnauthorizedError("Invalid admin token");
    }
    this.locked = false;
    this.loginAttempts = 0;
  }

  changePassword(currentHash: string, newHash: string): void {
    if (this.passwordHash !== currentHash) {
      throw new InvalidCredentialsError();
    }
    this.passwordHash = newHash;
  }

  getDisplayName(): string {
    return this.name;
  }

  getEmail(): string {
    return this.email;
  }

  isAccountLocked(): boolean {
    return this.locked;
  }

  // Preferences exposed through controlled interface
  setPreference(key: string, value: string): void {
    if (key.length > 100) throw new ValidationError("Key too long");
    this.preferences.set(key, value);
  }

  getPreference(key: string): string | undefined {
    return this.preferences.get(key);
  }
}

// The invariant (lock after 5 attempts) is GUARANTEED.
// No external code can bypass it. No duplication of the rule.
// passwordHash is never exposed outside the class.
```

### BAD: "Encapsulation" that's just getters and setters

```typescript
// This is NOT encapsulation -- it's exposed fields with extra steps
class Order {
  private items: OrderItem[] = [];
  private status: OrderStatus = "draft";
  private total: number = 0;

  getItems(): OrderItem[] { return this.items; }         // Returns mutable reference!
  setItems(items: OrderItem[]): void { this.items = items; } // No validation
  getStatus(): OrderStatus { return this.status; }
  setStatus(s: OrderStatus): void { this.status = s; }   // Can set any status from any status
  getTotal(): number { return this.total; }
  setTotal(t: number): void { this.total = t; }          // Can set total independent of items
}

// Callers still control the internals
const order = new Order();
order.setStatus("shipped"); // Ship an empty order?
order.setTotal(-500);       // Negative total?
order.getItems().push(item); // Mutate through the getter!
```

### GOOD: Behavior-rich interface that protects invariants

```typescript
class Order {
  private readonly items: OrderItem[] = [];
  private status: OrderStatus = "draft";

  addItem(product: Product, quantity: number): void {
    if (this.status !== "draft") {
      throw new InvalidOperationError("Cannot modify a submitted order");
    }
    if (quantity <= 0) {
      throw new ValidationError("Quantity must be positive");
    }
    this.items.push({ product, quantity });
  }

  submit(): void {
    if (this.items.length === 0) {
      throw new InvalidOperationError("Cannot submit empty order");
    }
    if (this.status !== "draft") {
      throw new InvalidOperationError("Order already submitted");
    }
    this.status = "submitted";
  }

  ship(trackingNumber: string): void {
    if (this.status !== "submitted") {
      throw new InvalidOperationError("Only submitted orders can be shipped");
    }
    this.status = "shipped";
  }

  getTotal(): number {
    return this.items.reduce(
      (sum, item) => sum + item.product.price * item.quantity,
      0,
    );
  }

  // Return a read-only view of items
  getItems(): readonly OrderItem[] {
    return this.items;
  }

  getStatus(): OrderStatus {
    return this.status;
  }
}

// State transitions are enforced. You can't ship a draft.
// Total is always derived from items -- can't be set independently.
// Items can't be modified after submission.
```

---

## Alternatives & Related Principles

| Principle | Relationship |
|-----------|-------------|
| **Open Data / Transparent Types** | Some paradigms (functional programming, data-oriented design) advocate for plain data without behavior. Data is immutable and public; functions operate on it externally. Encapsulation through immutability rather than access control. |
| **Records/DTOs** | Data Transfer Objects intentionally have no encapsulation -- they're bags of public fields for moving data between layers. Not every type needs encapsulation; some are just data. |
| **Module-Level Encapsulation** | In TypeScript/JavaScript, you can encapsulate at the module level using non-exported functions and variables, rather than class-level `private`. Often more natural in functional codebases. |
| **Closure-Based Encapsulation** | JavaScript's original encapsulation mechanism. Variables captured in a closure are truly private -- no reflection hack can access them, unlike class `private` in many languages. |

---

## When NOT to Apply

- **Data Transfer Objects (DTOs).** DTOs exist to carry data between boundaries. They should be simple, serializable, and transparent. Adding behavior to a DTO defeats its purpose.
- **Immutable value objects.** If an object is immutable, exposing its fields is safe -- no one can corrupt the state. A `Point { readonly x: number; readonly y: number }` doesn't need getters.
- **Configuration objects.** Plain objects with public fields are often the clearest representation of configuration.
- **When it leads to getter/setter bloat.** If every private field has a public getter and setter with no additional logic, you have the overhead of encapsulation with none of the benefits. Either add real behavior or use a plain data structure.
- **Prototyping.** During exploration, encapsulation overhead slows you down. Make things public, find the right design, then encapsulate.

---

## Tensions & Trade-offs

- **Encapsulation vs. Testability**: Strict encapsulation can make testing harder. You can't inspect internal state to verify a command worked correctly. Resolution: test through the public interface (behavioral testing), not by inspecting internals.
- **Encapsulation vs. Serialization**: Serialization frameworks often need access to private fields. This creates a tension between encapsulation and infrastructure concerns. Solutions: serialization-specific constructors, builder patterns, or dedicated serialization adapters.
- **Encapsulation vs. Debugging**: Hidden state is harder to debug. You can't just log the object's fields. Solution: implement `toString()` or `toJSON()` methods that expose a debug-safe representation.
- **Encapsulation vs. Performance**: Accessor methods add function call overhead. In hot loops processing millions of records, direct field access may be necessary. Modern JIT compilers usually inline trivial accessors, but measure before assuming.

---

## Real-World Consequences

A social media platform exposed its `Post` object's `viewCount` field publicly. A bug in the recommendation engine accidentally set `viewCount = 0` on popular posts during a batch update. Because no encapsulation existed, there was no audit trail, no validation, and no way to detect the corruption until users reported that trending posts showed zero views. With encapsulation, the `incrementViewCount()` method would have been the only way to modify the count, the batch job couldn't have zeroed it, and the system could have logged every modification.

---

## Key Quotes

> "We propose instead that one begins with a list of difficult design decisions or design decisions which are likely to change. Each module is then designed to hide such a decision from the others."
> -- David Parnas

> "The purpose of encapsulation isn't to prevent access to internal data. It's to ensure that the invariants of the object are always maintained."
> -- Eric Evans (paraphrased)

> "Don't ask for the information you need to do the work; ask the object that has the information to do the work for you."
> -- Allen Holub

> "A class is a mechanism for information hiding, not a mechanism for making structs with methods."
> -- John Ousterhout (paraphrased)

---

## Further Reading

- ["On the Criteria To Be Used in Decomposing Systems into Modules"](https://www.win.tue.nl/~wstomv/edu/2ip30/references/criteria_for_modularization.pdf) -- David Parnas (1972)
- *Object-Oriented Software Construction* -- Bertrand Meyer (1997)
- *A Philosophy of Software Design* -- John Ousterhout (2018)
- *Domain-Driven Design* -- Eric Evans (2003), especially Value Objects and Entities
- *Effective Java* (3rd Edition) -- Joshua Bloch (2018), Item 16: "In public classes, use accessor methods, not public fields"
