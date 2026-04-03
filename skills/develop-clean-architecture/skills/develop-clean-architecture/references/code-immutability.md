---
title: Enforce Immutability at Compile Time
impact: HIGH
impactDescription: prevents accidental mutation, makes domain objects predictable and thread-safe
tags: code, immutability, readonly, domain
---

## Enforce Immutability at Compile Time

Mutable state is the root of many bugs — especially in domain entities and value objects where invariants must hold. TypeScript provides multiple compile-time immutability patterns. Use them aggressively at every layer.

**Incorrect (mutable data allows silent corruption):**

```typescript
interface OrderLine {
  productId: string;
  quantity: number;
  unitPrice: number;
}

class Order {
  lines: OrderLine[] = [];

  getLines(): OrderLine[] {
    return this.lines;  // Caller can push/pop/mutate directly
  }
}

const order = new Order();
order.getLines().push({ productId: 'x', quantity: -1, unitPrice: 0 }); // Bypasses all checks
```

**Correct (compile-time immutability enforcement):**

```typescript
// Pattern 1: readonly on all value object properties
interface OrderLine {
  readonly productId: ProductId;
  readonly quantity: number;
  readonly unitPrice: Money;
}

// Pattern 2: ReadonlyArray prevents push/pop/splice
class Order {
  #lines: OrderLine[];

  constructor(lines: OrderLine[]) {
    this.#lines = [...lines];  // Defensive copy
  }

  get lines(): ReadonlyArray<OrderLine> {
    return this.#lines;  // Caller cannot mutate
  }
}

// Pattern 3: as const for finite domain sets
const ORDER_STATUSES = ['pending', 'confirmed', 'shipped', 'cancelled'] as const;
type OrderStatus = typeof ORDER_STATUSES[number]; // LSP autocompletes all 4

// Pattern 4: Object.freeze for runtime + compile-time constants
const MAX_ORDER_CONSTRAINTS = Object.freeze({
  lineItems: 10,
  quantity: 100,
  totalUsd: 10_000,
} as const);
// MAX_ORDER_CONSTRAINTS.lineItems = 20; // Compile error AND runtime error

// Pattern 5: Readonly<T> utility for derived types
type ReadonlyOrderLine = Readonly<OrderLine>;
```

**When NOT to use this pattern:**
- Internal mutable state within an entity that is mutated through public methods (use `#` private fields)
- Performance-critical hot paths where copying arrays is measurably expensive

**Benefits:**
- Impossible to corrupt domain state from outside the aggregate boundary
- Value objects are always safe to share between contexts
- `as const` gives LSP literal-type autocomplete for domain constants
- ReadonlyArray prevents the most common mutation bugs (push, pop, splice)

Reference: [Clean Code, Ch. 14 — Successive Refinement](https://www.oreilly.com/library/view/clean-code-a/9780136083238/) | [TypeScript Handbook — Readonly](https://www.typescriptlang.org/docs/handbook/2/objects.html#readonly-properties)
