# DRY -- Don't Repeat Yourself

**Every piece of knowledge must have a single, unambiguous, authoritative representation within a system.**

---

## Origin

Coined by **Andy Hunt and Dave Thomas** in *The Pragmatic Programmer* (1999). The principle is often misunderstood as "don't duplicate code," but the authors were explicit: DRY is about **knowledge**, not text. Two identical-looking code blocks that represent different domain concepts are not a DRY violation. Two divergent code blocks that encode the same business rule *are*.

---

## The Problem It Solves

Without DRY, a single change in business logic requires hunting through the codebase for every place that logic is expressed. You miss one, and you have a bug. Worse, the system gradually becomes inconsistent -- different parts encode slightly different versions of the same rule, and no one knows which is canonical. Onboarding developers can't figure out where the "truth" lives. Tests verify one copy but not the other. The codebase rots from the inside.

---

## The Principle Explained

DRY targets **knowledge duplication**, not syntactic duplication. If two functions happen to look identical but model different domain concepts (e.g., calculating shipping tax vs. calculating sales tax, which today share the same formula), they are *not* duplicates -- they represent different knowledge that may diverge independently. Forcing them into a shared abstraction couples unrelated concerns.

The real violations are subtler: a validation rule hardcoded in both the frontend form and the backend handler. A business constant defined as a magic number in three services. A database schema that disagrees with the API contract because someone updated one but not the other. These are the duplications that kill projects.

Applying DRY well means asking: "If this knowledge changes, how many places do I need to touch?" If the answer is more than one, you have a DRY violation worth fixing. If two things look the same *today* but could change for different reasons *tomorrow*, leave them alone.

---

## Code Examples

### BAD: Duplicated business logic across layers

```typescript
// --- order-controller.ts ---
function validateOrder(order: Order): string[] {
  const errors: string[] = [];
  if (order.items.length === 0) {
    errors.push("Order must have at least one item");
  }
  if (order.total > 10_000) {
    errors.push("Orders over $10,000 require manager approval");
  }
  if (order.customer.creditScore < 500) {
    errors.push("Customer credit score too low");
  }
  return errors;
}

// --- order-service.ts --- (same rules, subtly different)
function processOrder(order: Order): Result {
  if (order.items.length < 1) {
    return { ok: false, error: "No items in order" };
  }
  // BUG: threshold was updated to 10,000 in the controller
  // but this file still says 5,000
  if (order.total > 5_000) {
    return { ok: false, error: "Needs approval" };
  }
  // Missing the credit score check entirely
  return executeOrder(order);
}
```

### GOOD: Single source of truth for validation rules

```typescript
// --- order-rules.ts ---
interface OrderRule {
  readonly check: (order: Order) => boolean;
  readonly message: string;
}

const ORDER_VALIDATION_RULES: readonly OrderRule[] = [
  {
    check: (o) => o.items.length === 0,
    message: "Order must have at least one item",
  },
  {
    check: (o) => o.total > 10_000,
    message: "Orders over $10,000 require manager approval",
  },
  {
    check: (o) => o.customer.creditScore < 500,
    message: "Customer credit score too low",
  },
] as const;

function validateOrder(order: Order): string[] {
  return ORDER_VALIDATION_RULES
    .filter((rule) => rule.check(order))
    .map((rule) => rule.message);
}

// --- order-controller.ts ---
function handleOrder(order: Order): Response {
  const errors = validateOrder(order);
  if (errors.length > 0) return { status: 400, body: { errors } };
  return orderService.process(order);
}

// --- order-service.ts ---
function processOrder(order: Order): Result {
  const errors = validateOrder(order);
  if (errors.length > 0) return { ok: false, errors };
  return executeOrder(order);
}
```

### BAD: Over-applying DRY -- coupling unrelated concepts

```typescript
// Forced abstraction because the code "looked the same"
function calculateTax(amount: number, type: "sales" | "shipping" | "import"): number {
  // These rates are coincidentally the same TODAY but governed
  // by completely different regulations
  const rate = 0.08;
  return amount * rate;
}
// When shipping tax changes to 0.06, this function becomes a
// mess of conditionals -- or worse, the change is missed.
```

### GOOD: Separate representations for separate knowledge

```typescript
function calculateSalesTax(amount: number): number {
  const SALES_TAX_RATE = 0.08; // Governed by state tax code
  return amount * SALES_TAX_RATE;
}

function calculateShippingTax(amount: number): number {
  const SHIPPING_TAX_RATE = 0.08; // Governed by federal regulation
  return amount * SHIPPING_TAX_RATE;
}
// Yes, the bodies look identical. No, this is NOT duplication.
// These are different pieces of knowledge with different change reasons.
```

---

## Alternatives & Related Principles

| Principle | Relationship |
|-----------|-------------|
| **WET (Write Everything Twice)** | A tongue-in-cheek counter: tolerate *some* duplication until you see a pattern three times. Useful as a brake against premature abstraction. |
| **AHA (Avoid Hasty Abstractions)** | Coined by Kent C. Dodds. Prefer duplication over the wrong abstraction. Wait until you deeply understand the duplication before extracting. |
| **Rule of Three** | Don't abstract until you've seen the same pattern in three distinct places. The first two might be coincidental. |
| **Once and Only Once (OAOO)** | XP's version. More narrowly focused on code duplication rather than knowledge duplication. |

---

## When NOT to Apply

- **When the "duplication" represents different domain concepts.** Two identical-looking functions that model different business rules should stay separate.
- **When the abstraction is worse than the duplication.** If extracting a shared function requires five parameters and a mode flag, you've made things harder to understand.
- **When you're in discovery mode.** During early development, let patterns emerge. Premature DRY leads to premature abstraction, which is harder to undo than duplication.
- **Across service boundaries.** Sharing code between microservices to avoid "duplication" creates coupling that's far more expensive than the duplication it removes.

---

## Tensions & Trade-offs

- **DRY vs. Decoupling**: Eliminating duplication often means creating a shared dependency. That dependency becomes a coupling point. In distributed systems, duplicating a data type across services is often healthier than sharing a library.
- **DRY vs. Readability**: A highly DRY codebase can become a maze of indirection. Readers jump through layers of abstraction to understand a simple flow. Some duplication aids comprehension.
- **DRY vs. YAGNI**: DRY sometimes pushes you to build abstractions before you need them. YAGNI says wait.

---

## Real-World Consequences

A fintech company shared a `MoneyCalculation` utility across their payment, invoicing, and reporting services. When rounding rules changed for payments (regulatory requirement), the shared utility was updated -- breaking invoice calculations that required the old rounding. The "fix" added a flag parameter. Then another flag. Within a year the utility had seven boolean parameters, no one understood it, and all three teams were afraid to touch it. They eventually duplicated the logic into each service -- exactly where it should have been from the start.

---

## Key Quotes

> "Every piece of knowledge must have a single, unambiguous, authoritative representation within a system."
> -- Andy Hunt & Dave Thomas, *The Pragmatic Programmer*

> "Duplication is far cheaper than the wrong abstraction."
> -- Sandi Metz

> "DRY is about knowledge, not code."
> -- Dave Thomas (clarifying years later)

---

## Further Reading

- *The Pragmatic Programmer* -- Andy Hunt & Dave Thomas (1999, 20th Anniversary Edition 2019)
- ["The Wrong Abstraction"](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction) -- Sandi Metz
- ["AHA Programming"](https://kentcdodds.com/blog/aha-programming) -- Kent C. Dodds
- ["Goodbye, Clean Code"](https://overreacted.io/goodbye-clean-code/) -- Dan Abramov
- *Refactoring* -- Martin Fowler (2018, 2nd Edition)
