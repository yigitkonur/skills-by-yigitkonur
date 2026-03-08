# Immutability and Side Effects

**One-line summary:** Pure functions and immutable data structures eliminate entire categories of bugs by making state changes explicit, predictable, and traceable.

---

## Origin

The intellectual roots trace to Alonzo Church's lambda calculus (1930s) and the functional programming tradition. Haskell (1990) made purity and immutability the default. Rich Hickey's Clojure (2007) brought persistent immutable data structures to the JVM mainstream, arguing that "state is the root of all evil in concurrent programming." Eric Meijer, Erik Elliott, and others have evangelized these ideas in the JavaScript/TypeScript ecosystem. The React library (2013) popularized immutable state management in frontend development through its unidirectional data flow model.

---

## The Problem It Solves

Mutable shared state is the primary source of concurrency bugs, temporal coupling, and "spooky action at a distance" in software. When an object can be changed by any code that holds a reference, you cannot reason about its value without tracing every possible execution path. A function that mutates its input silently couples the caller to the mutation, creating invisible dependencies. Tests become unreliable because the order of execution matters. Debugging becomes forensic work: "who changed this value, and when?" Immutability eliminates these problems by making it impossible for values to change after creation.

---

## The Principle Explained

**Pure functions** take inputs and produce outputs with no side effects. Given the same arguments, they always return the same result (referential transparency). They do not read from or write to external state -- no database queries, no file I/O, no global variable access, no mutation of inputs. Pure functions are trivially testable (no mocks needed), trivially parallelizable (no shared state), and trivially cacheable (same input = same output, so you can memoize).

**Immutable data structures** cannot be changed after creation. Instead of modifying an object in place, you create a new object with the desired changes. This sounds expensive, but structural sharing (used by persistent data structures) means that the new object reuses most of the old one's memory. The benefits are profound: you can safely pass data to any function without defensive copying; you can compare previous and current state trivially (reference equality); and you get an automatic audit trail by keeping old versions.

**Side effect isolation** acknowledges that real programs must have side effects -- they must read from databases, write to files, send HTTP requests. The discipline is not to eliminate side effects but to push them to the edges of the system. The core business logic is pure; the outer shell handles I/O. This "functional core, imperative shell" pattern (coined by Gary Bernhardt) makes the hardest-to-test code (I/O) thin and the most important code (logic) easy to test.

---

## Code Examples

### BAD: Mutable State and Hidden Side Effects

```typescript
// Mutable shared state: any code can change these at any time
let discountRate = 0.1;
let orderCount = 0;

interface MutableOrder {
  items: { name: string; price: number; quantity: number }[];
  total: number;
  status: string;
  appliedDiscount: number;
}

// Impure function: mutates input, reads global state, has side effects
function processOrder(order: MutableOrder): void {
  // Side effect: reads mutable global
  order.appliedDiscount = discountRate;

  // Mutates the input object -- callers may not expect this
  order.total = 0;
  for (const item of order.items) {
    item.price = item.price * (1 - discountRate); // mutates nested objects!
    order.total += item.price * item.quantity;
  }

  // Side effect: modifies global state
  orderCount++;
  order.status = "PROCESSED";

  // Side effect: I/O mixed with logic
  console.log(`Order processed. Total: ${order.total}`);
  sendEmail(`Order #${orderCount} processed`);
}

// Caller has no idea their order object was modified
const order: MutableOrder = {
  items: [{ name: "Widget", price: 100, quantity: 2 }],
  total: 0,
  status: "NEW",
  appliedDiscount: 0,
};
processOrder(order);
// order.items[0].price is now 90, not 100!
// order.status is "PROCESSED" -- was the caller expecting that?
```

### GOOD: Immutable Data and Pure Functions

```typescript
// Immutable types using readonly throughout
interface OrderItem {
  readonly name: string;
  readonly unitPrice: number;
  readonly quantity: number;
}

interface Order {
  readonly items: readonly OrderItem[];
  readonly discountRate: number;
  readonly status: "NEW" | "PROCESSED" | "SHIPPED";
}

interface ProcessedOrder extends Order {
  readonly status: "PROCESSED";
  readonly subtotal: number;
  readonly discountAmount: number;
  readonly total: number;
}

// Pure function: no side effects, returns new value
function calculateSubtotal(items: readonly OrderItem[]): number {
  return items.reduce((sum, item) => sum + item.unitPrice * item.quantity, 0);
}

// Pure function: derives discount from inputs only
function calculateDiscount(subtotal: number, rate: number): number {
  return subtotal * rate;
}

// Pure function: transforms input into output without mutation
function processOrder(order: Order): ProcessedOrder {
  const subtotal = calculateSubtotal(order.items);
  const discountAmount = calculateDiscount(subtotal, order.discountRate);
  const total = subtotal - discountAmount;

  // Returns a new object -- original order is unchanged
  return {
    ...order,
    status: "PROCESSED",
    subtotal,
    discountAmount,
    total,
  };
}

// Functional Core, Imperative Shell pattern
// Shell: handles I/O, orchestrates side effects
async function handleOrderRequest(rawOrder: unknown): Promise<void> {
  // Imperative shell: I/O at the edges
  const order = parseOrder(rawOrder);          // I/O: parse external input
  const processed = processOrder(order);       // Pure: no I/O
  await saveOrder(processed);                  // I/O: database write
  await sendConfirmation(processed);           // I/O: email
}

// Original order is never modified
const myOrder: Order = {
  items: [{ name: "Widget", unitPrice: 100, quantity: 2 }],
  discountRate: 0.1,
  status: "NEW",
};
const result = processOrder(myOrder);
// myOrder.status is still "NEW"
// myOrder.items[0].unitPrice is still 100
// result is a completely new object
```

### GOOD: Immutable Collection Operations

```typescript
// Instead of mutating arrays, create new ones

// BAD: mutation
function addItemMutable(cart: CartItem[], item: CartItem): void {
  cart.push(item); // mutates the array
}

// GOOD: immutable -- returns a new array
function addItem(cart: readonly CartItem[], item: CartItem): readonly CartItem[] {
  return [...cart, item];
}

// BAD: mutation
function removeItemMutable(cart: CartItem[], index: number): void {
  cart.splice(index, 1);
}

// GOOD: immutable -- returns a new array
function removeItem(cart: readonly CartItem[], index: number): readonly CartItem[] {
  return [...cart.slice(0, index), ...cart.slice(index + 1)];
}

// BAD: mutation
function updateQuantityMutable(cart: CartItem[], index: number, qty: number): void {
  cart[index].quantity = qty;
}

// GOOD: immutable -- returns new array with new item at index
function updateQuantity(
  cart: readonly CartItem[],
  index: number,
  quantity: number
): readonly CartItem[] {
  return cart.map((item, i) => (i === index ? { ...item, quantity } : item));
}
```

---

## Alternatives & Related Approaches

| Approach | Philosophy | Trade-off |
|---|---|---|
| **Mutable state with discipline** | Use mutation but follow conventions (no shared mutation) | Faster writes, requires vigilance |
| **Copy-on-write (COW)** | Share data until a write occurs, then copy | Good performance for read-heavy workloads |
| **Persistent data structures** | Structural sharing for efficient immutable updates | O(log n) updates instead of O(1), but safe |
| **Immer (TypeScript)** | Write mutations that produce immutable updates via proxy | Familiar syntax, adds runtime dependency |
| **Freezing objects** | `Object.freeze()` to enforce immutability at runtime | Shallow freeze only; runtime cost; no structural sharing |
| **Lens libraries** | Composable accessors for deeply nested immutable updates | Powerful but adds conceptual overhead |

---

## When NOT to Apply

- **Performance-critical tight loops.** Allocating a new array on every iteration of a hot loop is wasteful. Use mutable local state within a function, return an immutable result.
- **Large data transformations.** Copying a 100MB dataset on every transformation is impractical. Use streaming or mutable buffers internally, expose immutable interfaces externally.
- **Inherently stateful domains.** A game engine's physics simulation or a real-time audio processor needs mutable state for performance. Isolate mutation behind clear interfaces.
- **Simple scripts.** A 20-line utility script does not need persistent data structures.

---

## Tensions & Trade-offs

- **Immutability vs. performance:** Naive immutability (copy everything) can be slow. Structural sharing and careful allocation mitigate this, but add complexity.
- **Purity vs. pragmatism:** Real programs need I/O. The goal is not 100% pure functions but maximum separation of pure logic from impure I/O.
- **Readability of immutable updates:** Deeply nested immutable updates (`{ ...obj, nested: { ...obj.nested, deep: { ...obj.nested.deep, value: 42 } } }`) are harder to read than `obj.nested.deep.value = 42`. Libraries like Immer address this.
- **TypeScript's `readonly` limitations:** TypeScript's `readonly` is a compile-time check only. There is no runtime enforcement. Discipline is still required.

---

## Real-World Consequences

- **React's rendering model** depends on immutability for efficient re-renders. Mutating state directly bypasses React's change detection, causing bugs that are notoriously difficult to diagnose.
- **Redux** requires immutable state updates. Accidental mutation is the #1 cause of Redux bugs, which led to the creation of Redux Toolkit with Immer built in.
- **Git** is built on immutable data structures. Every commit is an immutable snapshot. Branches are just pointers. This design enables every feature: branching, merging, rebasing, and the reflog safety net.
- **Kafka** treats messages as immutable append-only logs, enabling replay, reprocessing, and decoupled consumers.

---

## Key Quotes

> "State is the root of all evil. In particular, mutable state." -- Rich Hickey

> "It is better to have 100 functions operate on one data structure than 10 functions on 10 data structures." -- Alan Perlis

> "An immutable object is an object whose state cannot be modified after it is created. There's no way to get it wrong." -- Joshua Bloch

> "Functional Core, Imperative Shell -- push side effects to the boundary." -- Gary Bernhardt

---

## Further Reading

- "Boundaries" talk by Gary Bernhardt (2012, destroyallsoftware.com) -- Functional Core, Imperative Shell
- *Effective Java* by Joshua Bloch (2018) -- Item 17: Minimize mutability
- "Are We There Yet?" talk by Rich Hickey (2009) -- Identity, state, and immutability
- *Grokking Simplicity* by Eric Normand (2021) -- Practical functional thinking for working programmers
- Immer documentation (immerjs.github.io) -- Practical immutable updates in TypeScript/JavaScript
