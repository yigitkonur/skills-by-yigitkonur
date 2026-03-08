# Property-Based Testing

**Instead of testing specific input-output examples, test that properties (invariants) hold for all generated inputs.**

---

## Origin / History

Property-based testing was introduced by Koen Claessen and John Hughes with QuickCheck for Haskell in 1999. The approach was revolutionary: instead of developers hand-crafting test cases, the framework generates hundreds or thousands of random inputs and verifies that specified properties always hold. When a property violation is found, the framework "shrinks" the failing input to the smallest reproducing case. QuickCheck has since been ported to virtually every language: fast-check (TypeScript/JavaScript), Hypothesis (Python), PropEr (Erlang), ScalaCheck (Scala), and many others. John Hughes co-founded QuviQ, which has used property-based testing to find bugs in automotive protocols, telecom systems, and distributed databases.

## The Problem It Solves

Example-based tests (traditional unit tests) verify behavior for specific inputs chosen by the developer. The developer picks "representative" cases and edge cases they can think of. But developers have blind spots — they test the cases they anticipated, not the ones that cause real bugs. Property-based testing flips this: you describe the rules your code must satisfy, and the framework generates inputs you would never think to try. It finds corner cases, boundary conditions, and interaction effects that hand-written tests miss.

## The Principle Explained

A property-based test has three components:

**Generators** produce random inputs of the required type. A string generator might produce empty strings, strings with Unicode characters, very long strings, and strings with special characters. A number generator covers zero, negative numbers, MAX_SAFE_INTEGER, NaN, and Infinity. You can compose generators for complex types: an "order" generator produces random orders with random line items, quantities, and prices.

**Properties** are invariants that must hold for all generated inputs. Examples: "sorting a list and sorting it again produces the same result" (idempotency), "encoding then decoding returns the original value" (round-trip), "the output list has the same length as the input" (preservation). Good properties describe the essence of what the code does without reimplementing it.

**Shrinking** takes a failing input and systematically simplifies it to find the minimal failing case. If a test fails for a list of 47 elements, the shrinker tries 23 elements, then 12, then 6, until it finds the smallest list that still triggers the failure. This turns an incomprehensible failure into a debuggable one.

## Code Examples

### GOOD: Property-based tests that find real bugs

```typescript
import fc from "fast-check";

// Property: sort is idempotent
describe("sortByPrice", () => {
  it("is idempotent — sorting twice equals sorting once", () => {
    fc.assert(
      fc.property(
        fc.array(fc.record({ name: fc.string(), price: fc.float({ min: 0, max: 10000 }) })),
        (items) => {
          const sortedOnce = sortByPrice(items);
          const sortedTwice = sortByPrice(sortedOnce);
          expect(sortedTwice).toEqual(sortedOnce);
        }
      )
    );
  });

  it("preserves all elements — no items lost or duplicated", () => {
    fc.assert(
      fc.property(
        fc.array(fc.record({ name: fc.string(), price: fc.float({ min: 0, max: 10000 }) })),
        (items) => {
          const sorted = sortByPrice(items);
          expect(sorted.length).toBe(items.length);
          // Every item in the input exists in the output
          for (const item of items) {
            expect(sorted).toContainEqual(item);
          }
        }
      )
    );
  });

  it("output is actually sorted", () => {
    fc.assert(
      fc.property(
        fc.array(fc.record({ name: fc.string(), price: fc.float({ min: 0, max: 10000 }) })),
        (items) => {
          const sorted = sortByPrice(items);
          for (let i = 1; i < sorted.length; i++) {
            expect(sorted[i].price).toBeGreaterThanOrEqual(sorted[i - 1].price);
          }
        }
      )
    );
  });
});

// Property: encode/decode round-trip
describe("URL-safe Base64", () => {
  it("round-trips for any binary data", () => {
    fc.assert(
      fc.property(fc.uint8Array({ minLength: 0, maxLength: 1000 }), (data) => {
        const encoded = toUrlSafeBase64(data);
        const decoded = fromUrlSafeBase64(encoded);
        expect(decoded).toEqual(data);
      })
    );
  });

  it("produces only URL-safe characters", () => {
    fc.assert(
      fc.property(fc.uint8Array({ minLength: 0, maxLength: 1000 }), (data) => {
        const encoded = toUrlSafeBase64(data);
        expect(encoded).toMatch(/^[A-Za-z0-9_-]*=*$/);
      })
    );
  });
});

// Property: discount logic invariants
describe("applyDiscount", () => {
  const orderArb = fc.record({
    subtotal: fc.float({ min: 0.01, max: 100_000, noNaN: true }),
    discountPercent: fc.float({ min: 0, max: 100, noNaN: true }),
  });

  it("discounted total is never negative", () => {
    fc.assert(
      fc.property(orderArb, ({ subtotal, discountPercent }) => {
        const result = applyDiscount(subtotal, discountPercent);
        expect(result.total).toBeGreaterThanOrEqual(0);
      })
    );
  });

  it("discounted total never exceeds subtotal", () => {
    fc.assert(
      fc.property(orderArb, ({ subtotal, discountPercent }) => {
        const result = applyDiscount(subtotal, discountPercent);
        expect(result.total).toBeLessThanOrEqual(subtotal + 0.01); // float tolerance
      })
    );
  });

  it("zero discount returns original subtotal", () => {
    fc.assert(
      fc.property(
        fc.float({ min: 0.01, max: 100_000, noNaN: true }),
        (subtotal) => {
          const result = applyDiscount(subtotal, 0);
          expect(result.total).toBeCloseTo(subtotal);
        }
      )
    );
  });
});

// Custom generator for domain objects
const addressArb = fc.record({
  street: fc.string({ minLength: 1, maxLength: 100 }),
  city: fc.string({ minLength: 1, maxLength: 50 }),
  zip: fc.stringOf(fc.constantFrom("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"), {
    minLength: 5,
    maxLength: 5,
  }),
  country: fc.constantFrom("US", "CA", "UK", "DE", "FR"),
});
```

### BAD: Example-based tests that miss the real bug

```typescript
// The developer tested the cases they thought of.
// They missed that NaN, Infinity, negative zero, and very large floats
// cause applyDiscount to return unexpected results.
describe("applyDiscount", () => {
  it("applies 10% discount", () => {
    expect(applyDiscount(100, 10).total).toBe(90);
  });

  it("applies 50% discount", () => {
    expect(applyDiscount(200, 50).total).toBe(100);
  });

  it("applies 0% discount", () => {
    expect(applyDiscount(100, 0).total).toBe(100);
  });

  // Never tested: discount > 100%, subtotal of 0, floating point
  // edge cases, extremely large values, or negative discounts.
  // A property-based test would find these in seconds.
});
```

## Alternatives & Related Approaches

| Approach | When to prefer it |
|---|---|
| **Example-based tests** | When the domain is small and well-understood, or when you need specific regression tests for known bugs |
| **Fuzzing** | When testing for crashes, hangs, and security vulnerabilities — no property assertion needed |
| **Mutation testing** | When you want to verify that your existing tests (example or property) actually catch bugs |
| **Metamorphic testing** | When you cannot easily define the expected output but can define relationships between inputs and outputs |

Property-based tests and example-based tests complement each other. Use examples for specific regression cases and documentation. Use properties for invariants and edge case discovery.

## When NOT to Apply

- **When the property is just the implementation restated.** If your property for `sort` reimplements sorting to check the result, you are testing nothing. Find a property that does not reimplement the logic (like idempotency or length preservation).
- **When the code has no meaningful invariants.** A function that formats a string for display may not have a useful property beyond "does not throw."
- **When test execution time matters.** Property-based tests run hundreds of cases by default. For slow code (database queries, network calls), this multiplies the cost. Use properties for pure/fast logic.
- **When debugging a specific reported bug.** Write an example-based regression test for the exact failing case. Property-based tests are for discovery, not regression.

## Tensions & Trade-offs

- **Finding good properties is hard.** The biggest barrier to property-based testing is formulating properties that are meaningful without reimplementing the logic. Common property patterns: round-trip (encode/decode), idempotency (f(f(x)) = f(x)), invariants (output.length === input.length), oracle (compare against a simple reference implementation).
- **Shrinking quality varies.** Built-in shrinkers work well for primitive types but may produce confusing minimal cases for complex domain objects. Custom shrinkers help but add maintenance.
- **Non-determinism in CI.** A property test that fails on 1 in 10,000 inputs may pass 99 times and fail once. Use fixed seeds in CI for reproducibility, and log the failing seed so you can reproduce locally.
- **Slow generators.** Generating complex objects (valid JSON schemas, valid SQL queries) requires careful generator composition. Poorly constrained generators spend most of their time generating invalid inputs that are immediately rejected.

## Real-World Consequences

John Hughes' team at QuviQ used property-based testing to find 20+ bugs in Volvo's AUTOSAR implementation — bugs that thousands of hand-written tests had missed. The bugs were in edge cases of the protocol state machine that no developer had thought to test.

The Hypothesis library (Python) found a bug in every major Python date/time library within a week of being applied. The issue: none of the libraries correctly handled the full range of valid timezone transitions. Example-based tests covered common cases; property-based tests found the uncommon ones.

## Further Reading

- [fast-check documentation](https://fast-check.dev/)
- *Property-Based Testing with PropEr, Erlang, and Elixir* by Fred Hebert
- [John Hughes: QuickCheck Testing for Fun and Profit](https://www.cs.tufts.edu/~nr/cs257/archive/john-hughes/quick.pdf)
- [Hypothesis documentation](https://hypothesis.readthedocs.io/) — best-in-class property testing for Python
- [Scott Wlaschin: An Introduction to Property-Based Testing](https://fsharpforfunandprofit.com/posts/property-based-testing/)
