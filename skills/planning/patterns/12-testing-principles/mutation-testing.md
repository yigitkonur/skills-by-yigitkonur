# Mutation Testing

**Test your tests by introducing small code changes (mutants) and checking whether your tests catch them.**

---

## Origin / History

Richard Lipton proposed mutation testing in 1971 as a way to evaluate test suite effectiveness. The idea was ahead of its time — the computational cost of running every test suite against every mutant was prohibitive for decades. Interest revived in the 2010s as hardware became fast enough and tools matured. Stryker (JavaScript/TypeScript, 2016) and PIT/Pitest (Java, 2010) made mutation testing practical for real-world codebases. The fundamental insight remains unchanged: code coverage tells you which lines are executed, but mutation testing tells you whether your tests actually detect changes to those lines.

## The Problem It Solves

Code coverage is the most common metric for test quality, and it is deeply misleading. A test that executes a line of code but does not assert on its behavior gives 100% coverage for that line while providing zero confidence. Consider a function that calculates a discount: a test that calls the function but only asserts that the result is "not undefined" covers every line of the discount calculation but catches no bugs in the calculation itself. Mutation testing reveals this gap by asking: "If I change `price * 0.9` to `price * 0.1`, does any test fail?"

## The Principle Explained

Mutation testing works by systematically modifying your source code and checking whether your test suite catches each modification:

**1. Generate mutants.** The mutation engine applies small, targeted changes called "mutation operators" to your source code. Common operators: replace `>` with `>=`, change `+` to `-`, replace `true` with `false`, remove a function call, change a return value. Each change produces a "mutant" — a slightly altered version of your code.

**2. Run tests against each mutant.** For each mutant, the entire test suite (or relevant subset) runs. If at least one test fails, the mutant is "killed" — your tests detected the change. If all tests pass, the mutant "survived" — your tests did not notice the code change, which means they are not effectively testing that behavior.

**3. Calculate mutation score.** `mutation score = killed mutants / total mutants * 100`. A score of 85% means your tests catch 85% of simulated bugs. Surviving mutants are a prioritized list of test gaps.

The process is computationally expensive because every mutant requires a test suite run. Modern tools use optimizations: only run tests that cover the mutated line, run tests in parallel, skip equivalent mutants (changes that produce functionally identical code), and incrementally test only changed code.

## Code Examples

### GOOD: Tests that kill mutants — testing behavior, not just executing code

```typescript
// Source code
function calculateOrderTotal(
  items: Array<{ price: number; quantity: number }>,
  discountPercent: number,
  taxRate: number
): { subtotal: number; discount: number; tax: number; total: number } {
  const subtotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const discount = subtotal * (discountPercent / 100);
  const taxable = subtotal - discount;
  const tax = taxable * taxRate;
  const total = taxable + tax;

  return { subtotal, discount, tax, total };
}

// Tests that KILL all mutants:
describe("calculateOrderTotal", () => {
  it("calculates subtotal from items", () => {
    const result = calculateOrderTotal(
      [
        { price: 10, quantity: 2 },
        { price: 5, quantity: 3 },
      ],
      0,
      0
    );
    // Kills mutants: price * quantity → price + quantity, + → -, etc.
    expect(result.subtotal).toBe(35);
  });

  it("applies percentage discount to subtotal", () => {
    const result = calculateOrderTotal([{ price: 100, quantity: 1 }], 10, 0);
    // Kills mutants: discountPercent / 100 → discountPercent * 100,
    // subtotal * → subtotal +, etc.
    expect(result.discount).toBe(10);
    expect(result.total).toBe(90);
  });

  it("calculates tax on discounted amount", () => {
    const result = calculateOrderTotal([{ price: 100, quantity: 1 }], 20, 0.1);
    // Kills mutants: subtotal - discount → subtotal + discount,
    // taxable * taxRate → taxable + taxRate, etc.
    expect(result.tax).toBe(8); // (100 - 20) * 0.1
    expect(result.total).toBe(88); // 80 + 8
  });

  it("returns zero total for empty cart", () => {
    const result = calculateOrderTotal([], 10, 0.1);
    // Kills boundary mutants
    expect(result.subtotal).toBe(0);
    expect(result.discount).toBe(0);
    expect(result.tax).toBe(0);
    expect(result.total).toBe(0);
  });

  it("handles 100% discount", () => {
    const result = calculateOrderTotal([{ price: 50, quantity: 2 }], 100, 0.2);
    // Kills mutants around boundary conditions
    expect(result.total).toBe(0);
  });
});
```

### BAD: Tests that let mutants survive — high coverage, low detection

```typescript
// These tests execute every line (100% code coverage!)
// but many mutants survive because assertions are too weak.
describe("calculateOrderTotal", () => {
  it("returns a result", () => {
    const result = calculateOrderTotal([{ price: 10, quantity: 1 }], 10, 0.1);
    // Mutant survives: changing + to - still returns "a result"
    // Mutant survives: changing * to / still returns "a result"
    expect(result).toBeDefined();
  });

  it("result has expected properties", () => {
    const result = calculateOrderTotal([{ price: 10, quantity: 1 }], 10, 0.1);
    // Mutant survives: any numeric change still produces a number
    expect(typeof result.total).toBe("number");
    expect(typeof result.subtotal).toBe("number");
  });

  it("does not throw", () => {
    // Mutant survives: literally any behavior change that does not throw
    expect(() =>
      calculateOrderTotal([{ price: 10, quantity: 1 }], 10, 0.1)
    ).not.toThrow();
  });
});
// Mutation score: ~15%. Stryker reports 30+ surviving mutants.
// Code coverage: 100%. A useless metric here.
```

### Running Stryker (configuration)

```typescript
// stryker.conf.mts
import { defineConfig } from "@stryker-mutator/core";

export default defineConfig({
  mutate: ["src/**/*.ts", "!src/**/*.test.ts", "!src/**/*.d.ts"],
  testRunner: "vitest",
  reporters: ["html", "clear-text", "progress"],
  thresholds: {
    high: 80,
    low: 60,
    break: 50, // CI fails if mutation score drops below 50%
  },
  concurrency: 4,
  timeoutMS: 10_000,
  // Focus on changed files only (incremental mutation testing)
  incremental: true,
  incrementalFile: ".stryker-cache/incremental.json",
});
```

## Alternatives & Related Approaches

| Approach | When to prefer it |
|---|---|
| **Code coverage** | As a minimum bar ("is this code executed at all?") — weaker but much faster |
| **Code review of tests** | When you want human judgment about test quality, not just automated metrics |
| **Property-based testing** | When you want to generate test inputs that find bugs, not evaluate existing tests |
| **Fuzzing** | When you want to find crashes and security vulnerabilities through random inputs |

Mutation testing and property-based testing are complementary. Property-based tests generate diverse inputs to find bugs. Mutation testing evaluates whether your tests (example-based or property-based) actually detect bugs when they exist.

## When NOT to Apply

- **Extremely large codebases without incremental support.** Full mutation testing on a million-line codebase can take hours. Use incremental mutation testing (only mutate changed files) or target high-risk modules.
- **Generated code or boilerplate.** Mutation testing DTOs, configuration files, or auto-generated API clients wastes time. Focus on business logic.
- **When the code is being rapidly rewritten.** Mutation testing rewards stable code with stable tests. In early prototyping, the overhead is not justified.
- **Integration and E2E tests.** Mutation testing works best with fast unit tests. Running an E2E suite against every mutant is prohibitively slow.

## Tensions & Trade-offs

- **Computational cost:** Each mutant requires running a subset of the test suite. A codebase with 1,000 possible mutants and a test suite that takes 10 seconds means ~3 hours of mutation testing. Incremental testing, parallelization, and smart test selection mitigate this.
- **Equivalent mutants:** Some mutations produce code that is functionally identical to the original (e.g., replacing `x >= 0` with `x > -1` for integer `x`). These "equivalent mutants" cannot be killed and lower the mutation score unfairly. Modern tools try to detect and exclude them, but it is not perfect.
- **Mutation score targets:** 100% mutation score is neither practical nor necessary. Equivalent mutants, trivial code (getters), and unreachable branches inflate the denominator. Target 70-85% for business logic.
- **Developer frustration:** Surviving mutants sometimes point to code that is correct regardless of the mutation (e.g., a logging statement). Developers may feel the tool is crying wolf. Configure mutation operators to focus on meaningful changes.

## Real-World Consequences

Google internal research found that code coverage above 80% provided diminishing returns for defect detection — but mutation testing continued to find meaningful test gaps even at 95% coverage. They use mutation testing internally for high-risk code paths.

The Stryker team reports that first-time users typically discover a mutation score of 50-65% even with 80%+ code coverage. The gap represents tests that execute code but do not actually verify its correctness — the most insidious form of false confidence.

PIT (Java mutation testing) found critical test gaps in Apache Commons Math, a heavily tested library with 90%+ coverage. Surviving mutants revealed that several numerical edge cases were executed but not asserted upon.

## Further Reading

- [Stryker Mutator (JavaScript/TypeScript)](https://stryker-mutator.io/)
- [PIT Mutation Testing (Java)](https://pitest.org/)
- [Mutation Testing: An Introduction](https://stryker-mutator.io/docs/General/introduction/)
- [Google: Mutation Testing](https://testing.googleblog.com/2021/04/mutation-testing.html)
- [Filip van Laenen: Mutation Testing in Practice](https://www.infoq.com/articles/mutation-testing/)
