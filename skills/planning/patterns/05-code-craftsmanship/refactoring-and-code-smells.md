# Refactoring and Code Smells

**One-line summary:** Refactoring is the disciplined technique of restructuring existing code without changing its behavior, guided by recognizing "code smells" -- surface indicators of deeper design problems.

---

## Origin

Martin Fowler formalized the practice in *Refactoring: Improving the Design of Existing Code* (1999, Addison-Wesley; 2nd edition 2018 with JavaScript examples). The "code smell" metaphor was coined by Kent Beck during their collaboration. The refactoring catalog now contains over 60 named transformations. The Boy Scout Rule ("leave the campground cleaner than you found it") was popularized by Robert C. Martin in *Clean Code* (2008), advocating continuous incremental improvement over planned rewrite efforts.

---

## The Problem It Solves

Code degrades over time. Features get bolted on. Quick fixes accumulate. What started as a clean design becomes tangled, duplicated, and brittle. Without a vocabulary for identifying problems (smells) and a catalog of safe transformations (refactorings), teams either tolerate the mess until productivity collapses, or attempt a risky Big Rewrite that frequently fails. Refactoring provides a middle path: continuous, incremental, safe improvement guided by pattern recognition.

---

## The Principle Explained

**Code smells** are not bugs. The code works. But something about its structure suggests a design problem that will cause pain later. Smells are heuristics, not rules -- they point you toward code worth examining, not code that is automatically wrong. A Long Method might be perfectly readable if its steps are sequential and clear. The smell is a prompt to look, not a command to act.

**Refactoring** is behavior-preserving transformation. You change how the code is organized without changing what it does. This requires tests: without automated tests confirming behavior, refactoring is just editing with hope. Each refactoring is a small, named, reversible step -- Extract Method, Inline Variable, Move Function, Replace Conditional with Polymorphism. Small steps reduce risk. You can stop at any point and the code still works.

**The Boy Scout Rule** embeds refactoring into daily work. You do not need a "refactoring sprint." Every time you touch code, leave it slightly better. Rename an unclear variable. Extract a duplicated block. Simplify a conditional. Over weeks and months, these micro-improvements compound into significant quality gains without requiring dedicated refactoring time.

---

## Code Smell Taxonomy with Examples

### BAD: Long Method + Feature Envy + Primitive Obsession

```typescript
// Long Method: does too many things
// Feature Envy: reaches into other objects' data constantly
// Primitive Obsession: uses raw strings and numbers for domain concepts

function processOrder(
  items: { name: string; price: number; qty: number; cat: string }[],
  customerType: string,
  address: string,
  zipCode: string,
  state: string
): { total: number; tax: number; shipping: number; discount: number } {
  let subtotal = 0;
  for (const item of items) {
    subtotal += item.price * item.qty;
  }

  // Feature Envy: this function knows too much about discount rules
  let discount = 0;
  if (customerType === "gold") {
    discount = subtotal * 0.1;
  } else if (customerType === "silver") {
    discount = subtotal * 0.05;
  } else if (customerType === "platinum") {
    discount = subtotal * 0.15;
    if (subtotal > 500) discount += 25;
  }

  // Primitive Obsession: tax logic scattered with raw strings
  let taxRate = 0.08;
  if (state === "OR" || state === "MT" || state === "NH") {
    taxRate = 0;
  } else if (state === "CA") {
    taxRate = 0.0725;
  }
  const tax = (subtotal - discount) * taxRate;

  // Shotgun Surgery: shipping logic repeated in 4 other places
  let shipping = 9.99;
  if (subtotal > 100) shipping = 0;
  if (state === "HI" || state === "AK") shipping += 15;

  return { total: subtotal - discount + tax + shipping, tax, shipping, discount };
}
```

### GOOD: After Refactoring -- Extract Class, Replace Conditional with Polymorphism

```typescript
// Value Object eliminates Primitive Obsession
class Money {
  constructor(readonly cents: number) {}

  static fromDollars(dollars: number): Money {
    return new Money(Math.round(dollars * 100));
  }

  add(other: Money): Money { return new Money(this.cents + other.cents); }
  subtract(other: Money): Money { return new Money(this.cents - other.cents); }
  multiply(factor: number): Money { return new Money(Math.round(this.cents * factor)); }
  get dollars(): number { return this.cents / 100; }
}

// Extract Class: encapsulates line item logic
class OrderItem {
  constructor(
    readonly name: string,
    readonly unitPrice: Money,
    readonly quantity: number,
    readonly category: string
  ) {}

  get lineTotal(): Money { return this.unitPrice.multiply(this.quantity); }
}

// Replace Conditional with Polymorphism: discount strategies
interface DiscountStrategy {
  calculate(subtotal: Money): Money;
}

class GoldDiscount implements DiscountStrategy {
  calculate(subtotal: Money): Money { return subtotal.multiply(0.1); }
}

class PlatinumDiscount implements DiscountStrategy {
  calculate(subtotal: Money): Money {
    const base = subtotal.multiply(0.15);
    const bonus = subtotal.cents > 50000 ? Money.fromDollars(25) : Money.fromDollars(0);
    return base.add(bonus);
  }
}

class NoDiscount implements DiscountStrategy {
  calculate(_subtotal: Money): Money { return Money.fromDollars(0); }
}

// Extract Class: tax calculation is its own responsibility
class TaxCalculator {
  private static readonly NO_TAX_STATES = new Set(["OR", "MT", "NH"]);
  private static readonly SPECIAL_RATES: Record<string, number> = { CA: 0.0725 };
  private static readonly DEFAULT_RATE = 0.08;

  calculateTax(amount: Money, state: string): Money {
    if (TaxCalculator.NO_TAX_STATES.has(state)) return Money.fromDollars(0);
    const rate = TaxCalculator.SPECIAL_RATES[state] ?? TaxCalculator.DEFAULT_RATE;
    return amount.multiply(rate);
  }
}

// Extract Class: shipping is its own responsibility (eliminates Shotgun Surgery)
class ShippingCalculator {
  private static readonly REMOTE_STATES = new Set(["HI", "AK"]);
  private static readonly FREE_SHIPPING_THRESHOLD = 10000; // cents

  calculateShipping(subtotal: Money, state: string): Money {
    let shipping = Money.fromDollars(9.99);
    if (subtotal.cents > ShippingCalculator.FREE_SHIPPING_THRESHOLD) {
      shipping = Money.fromDollars(0);
    }
    if (ShippingCalculator.REMOTE_STATES.has(state)) {
      shipping = shipping.add(Money.fromDollars(15));
    }
    return shipping;
  }
}

// Orchestrator: small, readable, delegates to focused collaborators
function processOrder(
  items: readonly OrderItem[],
  discount: DiscountStrategy,
  state: string
): { total: Money; tax: Money; shipping: Money; discount: Money } {
  const subtotal = items.reduce((sum, item) => sum.add(item.lineTotal), Money.fromDollars(0));
  const discountAmount = discount.calculate(subtotal);
  const taxableAmount = subtotal.subtract(discountAmount);
  const tax = new TaxCalculator().calculateTax(taxableAmount, state);
  const shipping = new ShippingCalculator().calculateShipping(subtotal, state);
  const total = taxableAmount.add(tax).add(shipping);

  return { total, tax, shipping, discount: discountAmount };
}
```

---

## Common Code Smells Reference

| Smell | Signal | Typical Refactoring |
|---|---|---|
| **Long Method** | Function exceeds ~20 lines, multiple concerns | Extract Method |
| **Large Class** | Class has too many fields/methods | Extract Class, Extract Subclass |
| **Feature Envy** | Method uses another object's data more than its own | Move Method |
| **Shotgun Surgery** | One change requires edits in many classes | Move Method, Inline Class |
| **Divergent Change** | One class is changed for many different reasons | Extract Class |
| **Primitive Obsession** | Uses strings/numbers for domain concepts | Replace Primitive with Value Object |
| **Data Clumps** | Same group of fields appears together repeatedly | Extract Class, Introduce Parameter Object |
| **Switch Statements** | Repeated type-checking conditionals | Replace Conditional with Polymorphism |
| **Speculative Generality** | Unused abstractions "just in case" | Collapse Hierarchy, Remove Dead Code |
| **Message Chains** | `a.getB().getC().getD().doThing()` | Hide Delegate, Extract Method |

---

## Alternatives & Related Approaches

| Approach | When to Use | Risk |
|---|---|---|
| **Rewrite from scratch** | When the codebase is truly unsalvageable | High failure rate; "second system effect" |
| **Leave it alone** | When the code is stable and rarely changed | Technical debt accrues silently |
| **Strangler Fig pattern** | Incrementally replace legacy systems | Requires maintaining two systems during transition |
| **Automated code formatters** | For style-level consistency | Solves surface issues, not structural smells |

---

## When NOT to Apply

- **Code that is about to be deleted.** Do not polish what you are removing.
- **Without test coverage.** Refactoring without tests is gambling. Write characterization tests first.
- **Under deadline pressure.** A half-finished refactoring is worse than the original smell. Complete the refactoring or revert it; never commit a partial transformation.
- **Stable, working code nobody reads.** If a module works, is well-tested, and nobody needs to change it, its smells are academic.

---

## Tensions & Trade-offs

- **Refactoring vs. feature delivery:** Teams must balance paying down technical debt with shipping value. The Boy Scout Rule makes this continuous rather than a negotiation.
- **Small steps vs. large redesigns:** Some structural problems (wrong domain model, poor architectural boundaries) cannot be fixed by Extract Method. They require deliberate design effort.
- **Consistency vs. incremental improvement:** Refactoring one module while leaving similar modules untouched creates inconsistency. Plan to propagate patterns.

---

## Real-World Consequences

- **Etsy** credits continuous refactoring practices with enabling their migration from a PHP monolith to a service-oriented architecture without a full rewrite.
- **The Healthcare.gov launch failure (2013)** was partly attributed to code that had become too tangled to test, a consequence of deferred refactoring.
- **Basecamp** practices the Boy Scout Rule explicitly, citing it as a key factor in maintaining a small team on a large, long-lived codebase.

---

## Key Quotes

> "Refactoring is a disciplined technique for restructuring an existing body of code, altering its internal structure without changing its external behavior." -- Martin Fowler

> "A code smell is a surface indication that usually corresponds to a deeper problem in the system." -- Martin Fowler

> "When you feel the need to write a comment, first try to refactor the code so that any comment becomes superfluous." -- Martin Fowler

> "Leave the campground cleaner than you found it." -- Robert C. Martin (The Boy Scout Rule)

---

## Further Reading

- *Refactoring: Improving the Design of Existing Code* by Martin Fowler (2nd edition, 2018)
- *Working Effectively with Legacy Code* by Michael Feathers (2004)
- *Clean Code* by Robert C. Martin (2008) -- Chapter 17: Smells and Heuristics
- refactoring.guru -- Interactive catalog of refactorings and design patterns
- *Refactoring to Patterns* by Joshua Kerievsky (2004)
