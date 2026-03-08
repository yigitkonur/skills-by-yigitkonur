# Command-Query Separation (CQS)

**Every method should either be a command that performs an action, or a query that returns data -- but never both.**

---

## Origin

Formalized by **Bertrand Meyer** in his 1988 book *Object-Oriented Software Construction*. Meyer developed CQS while designing the Eiffel programming language, where he used it as a fundamental design discipline. The idea has older roots in the mathematical distinction between functions (which compute values) and procedures (which produce effects), but Meyer gave it a name, a rigorous formulation, and made it a design principle.

---

## The Problem It Solves

When methods both change state and return values, reasoning about code becomes treacherous. Consider a `stack.pop()` that removes the top element AND returns it. You can't inspect the top element without modifying the stack. You can't retry a failed operation without losing data. Testing becomes order-dependent. Debugging requires tracking both what was returned and what was mutated, simultaneously. In concurrent systems, combining mutation with observation creates race conditions: between checking a condition and acting on it, another thread may have changed the state.

---

## The Principle Explained

CQS divides all operations into two categories. **Queries** return a value and have no observable side effects -- calling a query twice in a row yields the same result (assuming no intervening commands) and does not change the system's state. **Commands** modify state and return nothing (void). This division gives you a powerful guarantee: you can call any query as often as you want, in any order, without affecting the system. Queries become safe to call in assertions, logging, debugging, and retries.

The practical benefit is profound: when reading code, if a method returns a value, you immediately know it's safe -- it doesn't change anything. If a method returns void, you know it has effects and you should be careful about when and how often you call it. This simple convention dramatically reduces the cognitive load of reading and reasoning about code.

Meyer allowed one pragmatic exception: methods that both mutate and return are acceptable when separation would be awkward or unsafe. Iterator `next()` methods, atomic operations like `compareAndSwap()`, and resource allocation like `malloc()` are classic cases where combining command and query is the lesser evil. The principle is a guideline for clear design, not a straitjacket.

---

## Code Examples

### BAD: Methods that both query and command

```typescript
class ShoppingCart {
  private items: CartItem[] = [];

  // Violates CQS: modifies state AND returns data
  addItem(product: Product, quantity: number): CartItem[] {
    this.items.push({ product, quantity, addedAt: new Date() });
    return this.items; // Why does adding return the full list?
  }

  // Violates CQS: removes AND returns
  checkout(): Order {
    if (this.items.length === 0) throw new Error("Empty cart");
    const order = createOrder(this.items);
    this.items = []; // Side effect: empties the cart
    return order;    // Also returns data
    // Can't review the order without emptying the cart
    // Can't retry on failure -- items are gone
  }

  // Violates CQS: query with side effects
  getTotal(): number {
    this.lastAccessedAt = new Date(); // Hidden side effect!
    return this.items.reduce((sum, item) => sum + item.product.price * item.quantity, 0);
  }
}
```

### GOOD: Clear separation of commands and queries

```typescript
class ShoppingCart {
  private items: CartItem[] = [];

  // --- COMMANDS (return void, modify state) ---

  addItem(product: Product, quantity: number): void {
    this.items.push({ product, quantity, addedAt: new Date() });
  }

  removeItem(productId: string): void {
    this.items = this.items.filter((item) => item.product.id !== productId);
  }

  clear(): void {
    this.items = [];
  }

  // --- QUERIES (return data, no side effects) ---

  getItems(): readonly CartItem[] {
    return [...this.items]; // Defensive copy
  }

  getTotal(): number {
    return this.items.reduce(
      (sum, item) => sum + item.product.price * item.quantity,
      0
    );
  }

  isEmpty(): boolean {
    return this.items.length === 0;
  }

  getItemCount(): number {
    return this.items.length;
  }
}

// Checkout is now a separate service that orchestrates commands and queries
class CheckoutService {
  async checkout(cart: ShoppingCart): Promise<Order> {
    // Query: inspect state without modifying it
    if (cart.isEmpty()) throw new Error("Empty cart");
    const items = cart.getItems();
    const total = cart.getTotal();

    // Command: create the order (external effect)
    const order = await this.orderRepo.create({ items, total });

    // Command: clear the cart only after success
    cart.clear();

    return order;
  }
}
```

### BAD: Service methods with hidden mutations

```typescript
class UserService {
  // Returns user but also logs the access, increments a counter,
  // and refreshes the cache -- all hidden behind a "get"
  async getUser(id: string): Promise<User> {
    this.accessLog.record(id, new Date());    // Side effect
    this.metrics.increment("user.fetched");    // Side effect
    const user = await this.cache.getOrFetch(  // Mutation: updates cache
      id,
      () => this.db.findUser(id)
    );
    return user;
  }
}
```

### GOOD: Explicit separation of observation and effects

```typescript
class UserService {
  // Pure query -- no side effects
  async getUser(id: string): Promise<User | null> {
    return this.db.findUser(id);
  }

  // Explicit command for recording access
  recordAccess(userId: string): void {
    this.accessLog.record(userId, new Date());
    this.metrics.increment("user.fetched");
  }
}

// The caller decides whether to record access
const user = await userService.getUser(id);
if (user) {
  userService.recordAccess(id); // Explicit, visible, optional
}
```

### Pragmatic exception: atomic operations

```typescript
// This is one of Meyer's accepted exceptions.
// Separating the check-and-set into two operations creates a race condition.
class AtomicCounter {
  // CQS exception: returns the old value AND increments
  // Separation would be unsafe in concurrent contexts
  incrementAndGet(): number {
    return Atomics.add(this.buffer, 0, 1) + 1;
  }
}

// Similarly, Map.delete() returning boolean is a pragmatic CQS violation:
// it tells you whether something was there AND removes it atomically.
```

---

## Alternatives & Related Principles

| Principle | Relationship |
|-----------|-------------|
| **CQRS (Command Query Responsibility Segregation)** | Greg Young's architectural extension of CQS. Instead of separating methods, separate entire *models* -- one model optimized for writes (commands), another for reads (queries). Used with Event Sourcing in complex domains. |
| **Event Sourcing** | Often paired with CQRS. Instead of storing current state, store the sequence of events (commands) that produced it. Queries are served from projections (read models) built from the event stream. |
| **Functional Purity** | Pure functions are the ultimate queries -- no side effects, same input always yields same output. FP takes CQS further by making purity the default and effects explicit. |
| **Tell, Don't Ask** | Can tension with CQS. "Tell, Don't Ask" says objects should perform operations, not expose data for callers to act on. This can push toward command-and-query-combined methods. |

---

## When NOT to Apply

- **Atomic operations in concurrent code.** `compareAndSwap`, `getAndIncrement`, `pop` from a concurrent queue -- separating these into query + command introduces race conditions.
- **Builder/fluent APIs.** Returning `this` from a mutating method enables chaining. Technically a CQS violation, but the return value isn't "data" -- it's the same object for ergonomics.
- **Interactive user interfaces.** `window.prompt()` displays a dialog (side effect) and returns user input (query). Separating these would create terrible UX.
- **Performance-critical paths.** When the overhead of two separate calls (one to check, one to act) is unacceptable.

---

## Tensions & Trade-offs

- **CQS vs. Convenience**: `array.pop()` is convenient precisely because it combines command and query. A CQS-pure version (inspect last, then remove last) is verbose and error-prone in concurrent contexts.
- **CQS vs. Tell Don't Ask**: Tell Don't Ask discourages querying an object's state to make decisions externally. But CQS encourages queries. The resolution: objects should offer meaningful queries (not raw data exposure) and meaningful commands (not low-level mutations).
- **CQS vs. Error Handling**: A command that returns an error code violates strict CQS. The pragmatic solution: throw exceptions from commands instead of returning error codes.
- **CQS at Scale**: At the architectural level (CQRS), separating read and write models adds significant complexity -- eventual consistency, read model synchronization, and operational overhead. Most applications don't need this.

---

## Real-World Consequences

A payment processing system had a `processPayment()` method that charged the customer AND returned the receipt. When a network timeout occurred after the charge but before the receipt was received, the client retried -- double-charging the customer. A CQS design would have separated `chargeCustomer()` (command, idempotent with a transaction ID) from `getReceipt(transactionId)` (query, safe to retry any number of times). The retry would only repeat the query, not the charge.

---

## Key Quotes

> "Asking a question should not change the answer."
> -- Bertrand Meyer

> "The really fundamental thing about CQS is that it's a way of making the code easier to reason about. If calling a function can't change anything, you can call it in a debugger, in a test, in an assertion, without worrying."
> -- Martin Fowler

> "CQRS is simply the creation of two objects where there was previously one."
> -- Greg Young

---

## Further Reading

- *Object-Oriented Software Construction* -- Bertrand Meyer (1988, 2nd Edition 1997)
- ["CommandQuerySeparation"](https://martinfowler.com/bliki/CommandQuerySeparation.html) -- Martin Fowler
- ["CQRS"](https://martinfowler.com/bliki/CQRS.html) -- Martin Fowler
- ["CQRS Documents"](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf) -- Greg Young
- *Domain-Driven Design* -- Eric Evans (2003), especially bounded contexts
