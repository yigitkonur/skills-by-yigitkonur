# Pure Functions

**No side effects, same input produces same output, every time.**

---

## Origin / History

The concept of pure functions originates from mathematical function theory and lambda calculus, formalized by Alonzo Church in the 1930s. In programming, the idea was carried forward by functional languages like Lisp (1958), ML (1973), and Haskell (1990). Haskell famously enforces purity at the language level, pushing all side effects into the type system via monads. The term "referential transparency" — the property that an expression can be replaced with its value without changing program behavior — became a cornerstone of functional programming philosophy.

In the JavaScript and TypeScript ecosystem, the push toward pure functions gained momentum with Redux (2015), which mandated pure reducer functions, and the broader React community's shift toward functional components and hooks.

---

## The Problem It Solves

Impure functions create hidden dependencies. A function that reads from a database, mutates global state, or depends on the current time is unpredictable. You cannot reason about it in isolation. You cannot test it without setting up the world around it. You cannot cache its results. You cannot safely run it in parallel.

When a codebase is riddled with impure functions, every change carries risk. A function that "usually" returns the right answer but sometimes does not — because of some ambient state — is the source of the most insidious bugs: the ones that only appear in production, under load, on Tuesdays.

Pure functions eliminate this entire category of problems by making functions self-contained units of logic.

---

## The Principle Explained

A pure function satisfies two properties: (1) given the same inputs, it always returns the same output (determinism), and (2) it produces no observable side effects — no mutation of external state, no I/O, no writing to disk, no network calls.

Referential transparency is the consequence of purity. If `add(2, 3)` always returns `5`, then anywhere you see `add(2, 3)` in your code, you can replace it with `5` and the program behaves identically. This makes reasoning about code dramatically simpler. Compilers and runtimes can exploit this for optimization — memoization, lazy evaluation, and automatic parallelization all become safe.

The practical implication is architectural: push impurity to the edges of your system. The core business logic should be pure functions that transform data. I/O, database access, and user interaction live at the boundary, calling into the pure core. This pattern — sometimes called "Functional Core, Imperative Shell" — gives you the best of both worlds: testable, composable logic at the center, and practical interaction with the messy world at the perimeter.

---

## Code Examples

### BAD: Impure function with hidden dependencies and side effects

```typescript
// Global mutable state
let taxRate = 0.08;
const orderLog: string[] = [];

function calculateTotal(items: { price: number; qty: number }[]): number {
  let total = 0;
  for (const item of items) {
    total += item.price * item.qty;
  }
  // Side effect: depends on external mutable state
  total += total * taxRate;
  // Side effect: mutates external state
  orderLog.push(`Order total: ${total} at ${new Date().toISOString()}`);
  return total;
}

// Problems:
// - Changing taxRate anywhere changes this function's behavior
// - Cannot test without inspecting orderLog
// - Cannot memoize (depends on taxRate and Date)
// - Cannot run in parallel safely (shared orderLog)
```

### GOOD: Pure function with explicit inputs and no side effects

```typescript
interface LineItem {
  readonly price: number;
  readonly qty: number;
}

interface TaxConfig {
  readonly rate: number;
}

function calculateSubtotal(items: readonly LineItem[]): number {
  return items.reduce((sum, item) => sum + item.price * item.qty, 0);
}

function applyTax(subtotal: number, tax: TaxConfig): number {
  return subtotal + subtotal * tax.rate;
}

function calculateTotal(items: readonly LineItem[], tax: TaxConfig): number {
  return applyTax(calculateSubtotal(items), tax);
}

// Side effects are pushed to the caller:
function processOrder(items: readonly LineItem[], tax: TaxConfig): void {
  const total = calculateTotal(items, tax);   // Pure
  console.log(`Order total: ${total}`);        // Impure, at the edge
  saveToDatabase(total);                       // Impure, at the edge
}

// Benefits:
// - calculateTotal is trivially testable
// - Safe to memoize: same items + tax = same result
// - Safe to parallelize: no shared state
// - Easy to reason about: all inputs are explicit
```

### Memoization — only safe with pure functions

```typescript
function memoize<A extends unknown[], R>(fn: (...args: A) => R): (...args: A) => R {
  const cache = new Map<string, R>();
  return (...args: A): R => {
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key)!;
    const result = fn(...args);
    cache.set(key, result);
    return result;
  };
}

const memoizedTotal = memoize(calculateTotal);
// Safe because calculateTotal is pure — cache will never be stale
```

---

## Alternatives & Related Approaches

| Approach | Trade-off |
|---|---|
| **Imperative mutation with discipline** | Team conventions instead of language enforcement. Works in small teams but scales poorly. |
| **Effect systems (Effect-TS, fp-ts)** | Encode side effects in the type system. Purity is enforced structurally, not just by convention. Steeper learning curve. |
| **Immutable data + encapsulated mutation** | Use classes with private mutable state that present a pure external interface. Pragmatic but leaks if not careful. |
| **Command/Query Separation** | Separate state-changing operations from queries. A lighter-weight discipline than full purity. |

---

## When NOT to Apply

- **Performance-critical inner loops**: Sometimes in-place mutation of a large array is orders of magnitude faster than creating new arrays. Profile first, then decide.
- **I/O by nature**: Functions whose entire purpose is a side effect (writing to a file, sending a network request) cannot be pure. Wrap them; do not fight them.
- **Prototyping and scripts**: When you are exploring, enforcing purity everywhere slows you down for little benefit. Clean it up when the code matures.
- **Legacy codebases**: Refactoring an entire impure codebase to pure functions is risky. Introduce purity incrementally at module boundaries.

---

## Tensions & Trade-offs

- **Purity vs. Performance**: Creating new data structures instead of mutating can increase GC pressure. Persistent data structures (structural sharing) mitigate this but add complexity.
- **Purity vs. Pragmatism**: Strictly pure code requires threading every dependency through function arguments. This can lead to long parameter lists or the need for Reader-monad-like patterns.
- **Purity vs. Familiarity**: Most developers learn imperative programming first. Pure functional style has a learning curve that affects team velocity initially.
- **Purity vs. Debugging**: Impure code with logging is sometimes easier to debug in development. Pure code requires structured approaches to observability.

---

## Real-World Consequences

**Redux reducers**: Redux mandates pure reducers. This made time-travel debugging possible — you can replay actions and always reach the same state. Teams that broke purity (mutating state in reducers) experienced mysterious UI bugs that were nearly impossible to reproduce.

**React rendering**: React assumes render functions are pure. Components that perform side effects during render cause double-rendering bugs in StrictMode, stale closure issues, and broken concurrent rendering.

**Financial calculations**: A payments company discovered that an impure pricing function (which read a cached exchange rate from a global variable) returned different totals during the same request when the cache refreshed mid-calculation. A pure function taking the exchange rate as a parameter would have prevented the inconsistency entirely.

---

## Further Reading

- [Mostly Adequate Guide to Functional Programming — Chapter 3: Pure Happiness with Pure Functions](https://github.com/MostlyAdequate/mostly-adequate-guide)
- [Mark Seemann — Functional Core, Imperative Shell](https://blog.ploeh.dk/2020/03/02/impureim-sandwich/)
- [Haskell Wiki — Referential Transparency](https://wiki.haskell.org/Referential_transparency)
- [Redux Documentation — Reducers Must Be Pure](https://redux.js.org/tutorials/fundamentals/part-3-state-actions-reducers)
- [Eric Normand — Grokking Simplicity (Manning, 2021)](https://www.manning.com/books/grokking-simplicity)
