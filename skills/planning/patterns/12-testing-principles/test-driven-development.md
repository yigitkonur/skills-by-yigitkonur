# Test-Driven Development (TDD)

**Write a failing test first, make it pass with the simplest code possible, then refactor — the Red-Green-Refactor cycle.**

---

## Origin / History

Kent Beck formalized Test-Driven Development in his 2002 book *Test-Driven Development: By Example*, though the practice traces back to NASA's Project Mercury in the 1960s, where tests were written before code for mission-critical software. TDD became a core practice of Extreme Programming (XP) and gained mainstream adoption in the 2000s-2010s. Two distinct schools emerged: the "Chicago/Detroit school" (classicist), which tests behavior through public APIs and uses real collaborators, and the "London school" (mockist), which isolates the unit under test using mocks and verifies interactions. The debate between these schools continues, with most experienced practitioners blending both approaches pragmatically.

## The Problem It Solves

Developers writing tests after the code face three problems. First, they are biased toward testing the code they wrote, not the behavior they need. Second, writing tests after the fact is tedious — the code works, the tests feel like paperwork. Third, the code's design is already fixed, and it may be hard to test (tight coupling, hidden dependencies, side effects). TDD addresses all three by making testability a design driver, not an afterthought.

## The Principle Explained

The TDD cycle has three steps, repeated in tight loops of minutes:

**Red:** Write a test that describes behavior you want but have not implemented. Run it. Watch it fail. The failing test is proof that the test is actually testing something and that the feature does not already exist.

**Green:** Write the minimum amount of code to make the test pass. Do not optimize, do not handle edge cases, do not refactor. The goal is to go from red to green as quickly as possible. This might mean hard-coding a return value. That is fine — the next test will force you to generalize.

**Refactor:** With all tests green, improve the code's design. Remove duplication, extract functions, rename variables, simplify logic. The tests protect you — if they stay green, your refactoring is safe.

**Chicago/Detroit school (classicist TDD)** tests behavior through the public API of the system under test. It uses real collaborators whenever practical and only introduces test doubles for slow or non-deterministic dependencies (databases, APIs, clocks). Tests are resilient to internal refactoring because they only test observable behavior.

**London school (mockist TDD)** isolates the unit under test by mocking all collaborators. It specifies not just what the unit returns but how it interacts with its dependencies. Tests are precise about design but brittle to internal changes.

## Code Examples

### GOOD: TDD cycle for a shopping cart — Red, Green, Refactor

```typescript
// === RED: Start with a failing test ===
describe("ShoppingCart", () => {
  it("starts empty", () => {
    const cart = new ShoppingCart();
    expect(cart.totalItems()).toBe(0);
    expect(cart.totalPrice()).toBe(0);
  });
});
// RUN → FAIL: ShoppingCart is not defined

// === GREEN: Minimum code to pass ===
class ShoppingCart {
  totalItems(): number { return 0; }
  totalPrice(): number { return 0; }
}
// RUN → PASS

// === RED: Next test drives behavior ===
it("adds an item", () => {
  const cart = new ShoppingCart();
  cart.addItem({ id: "A", name: "Widget", price: 25, quantity: 2 });
  expect(cart.totalItems()).toBe(2);
  expect(cart.totalPrice()).toBe(50);
});
// RUN → FAIL: addItem is not defined

// === GREEN: Implement just enough ===
interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

class ShoppingCart {
  private items: CartItem[] = [];

  addItem(item: CartItem): void {
    this.items.push(item);
  }

  totalItems(): number {
    return this.items.reduce((sum, item) => sum + item.quantity, 0);
  }

  totalPrice(): number {
    return this.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  }
}
// RUN → PASS

// === RED: Edge case — adding same item twice should merge ===
it("merges quantities when adding the same item twice", () => {
  const cart = new ShoppingCart();
  cart.addItem({ id: "A", name: "Widget", price: 25, quantity: 1 });
  cart.addItem({ id: "A", name: "Widget", price: 25, quantity: 3 });
  expect(cart.totalItems()).toBe(4);
  expect(cart.totalPrice()).toBe(100);
  expect(cart.lineItemCount()).toBe(1); // one line item, not two
});
// RUN → FAIL: quantities are not merged

// === GREEN: Handle merging ===
class ShoppingCart {
  private items: Map<string, CartItem> = new Map();

  addItem(item: CartItem): void {
    const existing = this.items.get(item.id);
    if (existing) {
      existing.quantity += item.quantity;
    } else {
      this.items.set(item.id, { ...item });
    }
  }

  totalItems(): number {
    let sum = 0;
    for (const item of this.items.values()) sum += item.quantity;
    return sum;
  }

  totalPrice(): number {
    let sum = 0;
    for (const item of this.items.values()) sum += item.price * item.quantity;
    return sum;
  }

  lineItemCount(): number {
    return this.items.size;
  }
}
// RUN → PASS

// === REFACTOR: Extract calculation, improve readability ===
class ShoppingCart {
  private readonly items = new Map<string, CartItem>();

  addItem(item: CartItem): void {
    const existing = this.items.get(item.id);
    if (existing) {
      existing.quantity += item.quantity;
    } else {
      this.items.set(item.id, { ...item });
    }
  }

  totalItems(): number {
    return this.sumOver((item) => item.quantity);
  }

  totalPrice(): number {
    return this.sumOver((item) => item.price * item.quantity);
  }

  lineItemCount(): number {
    return this.items.size;
  }

  private sumOver(fn: (item: CartItem) => number): number {
    return Array.from(this.items.values()).reduce((sum, item) => sum + fn(item), 0);
  }
}
// RUN → ALL PASS. Refactoring is safe because tests cover the behavior.
```

### BAD: Writing tests after the fact

```typescript
// The developer wrote the entire ShoppingCart class first.
// Now they "add tests" as a chore. The tests mirror the implementation
// instead of specifying behavior.
describe("ShoppingCart", () => {
  it("has an items map", () => {
    const cart = new ShoppingCart();
    // Testing internal state, not behavior
    expect((cart as any).items).toBeInstanceOf(Map);
  });

  it("uses reduce to calculate total", () => {
    // Testing HOW it works, not WHAT it does
    const spy = jest.spyOn(Array.prototype, "reduce");
    const cart = new ShoppingCart();
    cart.addItem({ id: "A", name: "Widget", price: 25, quantity: 1 });
    cart.totalPrice();
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });
});
```

## Alternatives & Related Approaches

| Approach | When to prefer it |
|---|---|
| **Behavior-Driven Development (BDD)** | When non-technical stakeholders need to read and validate test scenarios |
| **Test-after** | When exploring a new domain where the design is unclear; spike first, then stabilize with tests |
| **Spike-and-stabilize** | Write throwaway code to explore, then rewrite with TDD once you understand the problem |
| **Type-driven development** | In strongly typed languages, let the type system guide design before writing tests |

## When NOT to Apply

- **Exploratory/spike work.** When you do not know what you are building yet, TDD slows exploration. Spike first, then write tests when the design stabilizes.
- **UI layout/styling.** Writing tests for CSS positioning is painful and brittle. Use visual regression tools instead.
- **Glue code with no logic.** A function that calls three other functions in sequence has no logic to test-drive. Test it at the integration level.
- **Learning a new framework.** When you are still figuring out the API, writing tests first adds frustration without providing design guidance.

## Tensions & Trade-offs

- **Speed of initial development:** TDD is slower for the first iteration. The payoff comes in reduced debugging time, safer refactoring, and fewer regressions — benefits that compound over weeks and months.
- **London vs. Chicago:** The London school produces tests tightly coupled to implementation, which break during refactoring. The Chicago school produces tests coupled to behavior, which are more resilient. Neither is universally better; choose based on the complexity of collaborator interactions.
- **Over-testing:** TDD can lead to testing every trivial function if practiced dogmatically. Apply judgment: test behavior that matters, not every line of code.
- **Legacy code:** TDD is hardest to apply to existing codebases without tests. Michael Feathers' *Working Effectively with Legacy Code* addresses this with the "characterization test" pattern.

## Real-World Consequences

Pivotal Labs (now part of VMware Tanzu) practiced TDD religiously for client projects. Their teams consistently delivered fewer production defects than industry averages, and their codebases remained malleable over multi-year engagements because the test suite made refactoring safe.

A survey by Microsoft Research found that TDD teams produced 40-90% fewer defects compared to non-TDD teams, with a 15-35% increase in initial development time. The net effect was positive: less time spent debugging and fixing production issues.

## Further Reading

- *Test-Driven Development: By Example* by Kent Beck — the definitive TDD book
- *Growing Object-Oriented Software, Guided by Tests* by Freeman & Pryce — the London school perspective
- *Working Effectively with Legacy Code* by Michael Feathers — adding tests to existing code
- [Martin Fowler: Is TDD Dead?](https://martinfowler.com/articles/is-tdd-dead/) — the debate between Kent Beck, Martin Fowler, and David Heinemeier Hansson
