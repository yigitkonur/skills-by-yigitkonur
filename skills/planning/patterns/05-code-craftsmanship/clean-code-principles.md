# Clean Code Principles

**One-line summary:** Write code that reads like well-written prose -- meaningful names, small functions, no side effects, and one level of abstraction per function.

---

## Origin

Robert C. Martin ("Uncle Bob") codified these principles in *Clean Code: A Handbook of Agile Software Craftsmanship* (2008, Prentice Hall). The ideas draw from decades of software engineering wisdom, including Dijkstra's structured programming, Knuth's literate programming, and the Agile Manifesto's emphasis on sustainable development. Martin distilled hundreds of code reviews and refactoring sessions into a set of actionable rules that prioritize human readability over machine optimization.

---

## The Problem It Solves

Without clean code discipline, codebases degrade into what Martin calls "a big ball of mud." Developers spend more time reading code than writing it (by a ratio of roughly 10:1), so unclear naming, oversized functions, and hidden side effects compound into massive productivity drains. Onboarding takes weeks instead of days. Bugs hide in functions that do too many things. Changes in one place ripple unpredictably because responsibilities are tangled. Teams slow to a crawl not because the problem is hard, but because the code is impenetrable.

---

## The Principle Explained

**Meaningful names** are the foundation. Every variable, function, class, and module should reveal its intent without requiring a comment. A name like `d` (elapsed time in days) forces the reader to hold context in their head; `elapsedDays` does not. Names should be proportional to their scope -- a loop counter can be `i`, but a domain concept deserves a domain-specific name.

**Small functions** do one thing, do it well, and do it only. Martin advocates that functions should rarely exceed 20 lines and ideally stay under 10. Each function should operate at a single level of abstraction -- a high-level orchestrator should not mix business logic with string parsing. This naturally produces a hierarchy of well-named functions that reads top-down like an outline.

**No side effects** means a function should not secretly modify state beyond what its name promises. Command-Query Separation (CQS) formalizes this: a function either performs an action (command) or returns data (query), never both. When a function named `checkPassword` also initializes a user session, it lies to its caller, and lies in code breed bugs.

---

## Code Examples

### BAD: Violating Clean Code Principles

```typescript
// Unclear naming, multiple responsibilities, hidden side effects
function proc(d: any[], f: number): any {
  let r: any[] = [];
  let t = 0;
  for (let i = 0; i < d.length; i++) {
    if (d[i].s === 'A') {
      let p = d[i].a * f;
      if (p > 1000) {
        p = p * 0.9; // discount
        d[i].disc = true; // hidden side effect: mutates input
      }
      t += p;
      r.push({ ...d[i], p });
      console.log(`Processed: ${d[i].n}`); // hidden side effect: logging
    }
  }
  globalState.lastTotal = t; // hidden side effect: global mutation
  return { r, t };
}
```

### GOOD: Applying Clean Code Principles

```typescript
// Meaningful names, small focused functions, no side effects

interface OrderItem {
  readonly name: string;
  readonly status: string;
  readonly amount: number;
}

interface PricedItem {
  readonly item: OrderItem;
  readonly finalPrice: number;
  readonly discountApplied: boolean;
}

// Query: pure function, returns data, no side effects
function calculatePrice(amount: number, factor: number): number {
  return amount * factor;
}

// Query: single level of abstraction
function isEligibleForDiscount(price: number): boolean {
  const DISCOUNT_THRESHOLD = 1000;
  return price > DISCOUNT_THRESHOLD;
}

// Query: one thing only
function applyDiscount(price: number): number {
  const BULK_DISCOUNT_RATE = 0.9;
  return price * BULK_DISCOUNT_RATE;
}

// Query: composes lower-level functions at one abstraction level
function priceOrderItem(item: OrderItem, pricingFactor: number): PricedItem {
  const basePrice = calculatePrice(item.amount, pricingFactor);
  const discountApplied = isEligibleForDiscount(basePrice);
  const finalPrice = discountApplied ? applyDiscount(basePrice) : basePrice;

  return { item, finalPrice, discountApplied };
}

// Query: filters at one abstraction level
function filterActiveItems(items: readonly OrderItem[]): readonly OrderItem[] {
  return items.filter((item) => item.status === "ACTIVE");
}

// Orchestrator: reads like prose, one level of abstraction
function calculateOrderTotal(
  items: readonly OrderItem[],
  pricingFactor: number
): { readonly pricedItems: readonly PricedItem[]; readonly total: number } {
  const activeItems = filterActiveItems(items);
  const pricedItems = activeItems.map((item) => priceOrderItem(item, pricingFactor));
  const total = pricedItems.reduce((sum, entry) => sum + entry.finalPrice, 0);

  return { pricedItems, total };
}
```

---

## Alternatives & Related Approaches

| Approach | Philosophy | Trade-off |
|---|---|---|
| **"Clever code" philosophy** | Optimize for brevity and elegance over readability | Impressive to write, expensive to maintain |
| **Performance-first coding** | Inline everything, avoid abstractions to reduce overhead | Faster execution, slower development |
| **Write-once code** | Ship fast, don't look back | Works for prototypes, collapses at scale |
| **Literate Programming (Knuth)** | Code as a document for humans first | More thorough but heavier process |

---

## When NOT to Apply

- **Hot paths in performance-critical code.** Inlining a function, unrolling a loop, or using a mutable buffer can be justified when profiling proves a bottleneck. Add a comment explaining the deviation.
- **Exploratory prototypes.** When you are still discovering what the code should do, premature clean-up can slow learning. Refactor once the direction is clear.
- **Trivially small scripts.** A 30-line deployment script does not need the same structure as a domain service.
- **Over-extracting functions.** Splitting a 6-line function into three 2-line functions can obscure flow rather than clarify it. The goal is clarity, not an arbitrary line count.

---

## Tensions & Trade-offs

- **Readability vs. performance:** Clean code sometimes adds function call overhead. Profile before optimizing.
- **Small functions vs. navigation cost:** Too many tiny functions force readers to jump constantly. Balance granularity with locality.
- **CQS vs. pragmatism:** Some operations naturally return a value and change state (e.g., `stack.pop()`). Strict CQS may feel forced in these cases.
- **Naming precision vs. verbosity:** `calculateDiscountedPriceForBulkOrderItems` is precise but exhausting. Find the balance for your team.

---

## Real-World Consequences

- **IBM study (2010):** Teams practicing clean code principles reduced defect density by 40% compared to teams that did not.
- **Google's internal readability reviews** enforce naming and function size standards, citing measurable reductions in code review cycles.
- **Legacy rescue projects** routinely find that the single largest cost driver is not missing features but incomprehensible code that nobody dares change.

---

## Key Quotes

> "Clean code always looks like it was written by someone who cares." -- Robert C. Martin

> "Any fool can write code that a computer can understand. Good programmers write code that humans can understand." -- Martin Fowler

> "The ratio of time spent reading versus writing is well over 10 to 1. We are constantly reading old code as part of the effort to write new code." -- Robert C. Martin

> "Programs must be written for people to read, and only incidentally for machines to execute." -- Harold Abelson

---

## Further Reading

- *Clean Code* by Robert C. Martin (2008)
- *The Clean Coder* by Robert C. Martin (2011)
- *Refactoring* by Martin Fowler (2018, 2nd edition)
- *Code Complete* by Steve McConnell (2004, 2nd edition)
- *A Philosophy of Software Design* by John Ousterhout (2018) -- for a contrasting perspective on function size
