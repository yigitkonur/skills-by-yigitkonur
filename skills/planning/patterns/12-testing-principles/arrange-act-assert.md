# Arrange-Act-Assert (AAA)

**Structure every test in three distinct phases: set up the preconditions, execute the behavior, and verify the outcome.**

---

## Origin / History

The Arrange-Act-Assert pattern was popularized by Bill Wake in 2001 and became the standard structure for unit tests across languages. The BDD community independently developed the equivalent Given-When-Then format, attributed to Dan North's work on Behavior-Driven Development (2006). JUnit, NUnit, and virtually every test framework implicitly encourage this structure. The pattern is so fundamental that it is often taught as "the first thing to learn about writing tests."

## The Problem It Solves

Without a consistent structure, tests become hard to read, hard to maintain, and easy to write incorrectly. Common problems include: mixing setup and assertion on the same line, testing multiple behaviors in one test, forgetting to assert at all (a test that never fails), and burying the relevant setup in helper methods that obscure the test's intent. AAA provides a visual rhythm that makes tests self-documenting: you can glance at any test and immediately see what it sets up, what it does, and what it checks.

## The Principle Explained

**Arrange:** Set up the preconditions. Create objects, seed data, configure mocks, establish the starting state. This section answers: "Given these conditions..."

**Act:** Execute the single behavior being tested. Call the function, make the HTTP request, trigger the event. This section should be one or two lines. If it is more, you are probably testing multiple things. This section answers: "When this happens..."

**Assert:** Verify the outcome. Check return values, verify side effects, inspect state changes. This section answers: "Then this should be true." Multiple assertions are fine if they all verify aspects of the same behavior.

The BDD equivalent — Given-When-Then — uses natural language and is designed to be readable by non-developers:

```
Given a shopping cart with two items
When the user applies a 10% discount code
Then the total should reflect the discount
And the discount should appear as a line item
```

Both formats enforce the same discipline: separate setup, action, and verification.

## Code Examples

### GOOD: Clean AAA structure with descriptive naming

```typescript
describe("OrderService.placeOrder", () => {
  it("creates an order with the correct total after applying discount", async () => {
    // Arrange
    const customer = buildCustomer({ tier: "gold" });
    const items = [
      buildCartItem({ productId: "P1", price: 50, quantity: 2 }),
      buildCartItem({ productId: "P2", price: 30, quantity: 1 }),
    ];
    const discount = buildDiscount({ type: "percentage", value: 10 });

    const orderService = new OrderService(
      new InMemoryOrderRepository(),
      new InMemoryProductCatalog(items.map((i) => i.product)),
      new StubPaymentGateway({ alwaysSucceeds: true })
    );

    // Act
    const order = await orderService.placeOrder(customer, items, discount);

    // Assert
    expect(order.status).toBe("confirmed");
    expect(order.subtotal).toBe(130); // (50*2) + (30*1)
    expect(order.discountAmount).toBe(13); // 10% of 130
    expect(order.total).toBe(117);
    expect(order.customerId).toBe(customer.id);
  });

  it("rejects order when payment fails", async () => {
    // Arrange
    const customer = buildCustomer();
    const items = [buildCartItem({ price: 100, quantity: 1 })];
    const failingPayment = new StubPaymentGateway({ alwaysFails: true });
    const orderService = new OrderService(
      new InMemoryOrderRepository(),
      new InMemoryProductCatalog([items[0].product]),
      failingPayment
    );

    // Act & Assert (for expected exceptions, combine act and assert)
    await expect(
      orderService.placeOrder(customer, items, null)
    ).rejects.toThrow(PaymentFailedError);
  });
});

// Test builders: reusable, readable, with sensible defaults
function buildCustomer(overrides: Partial<Customer> = {}): Customer {
  return {
    id: "cust-1",
    name: "Jane Doe",
    email: "jane@example.com",
    tier: "standard",
    ...overrides,
  };
}

function buildCartItem(overrides: Partial<CartItemInput> = {}): CartItemInput {
  const productId = overrides.productId ?? "prod-default";
  return {
    productId,
    product: { id: productId, name: "Test Product", price: overrides.price ?? 10 },
    price: 10,
    quantity: 1,
    ...overrides,
  };
}

function buildDiscount(overrides: Partial<Discount> = {}): Discount {
  return {
    code: "TEST10",
    type: "percentage",
    value: 10,
    expiresAt: new Date("2099-12-31"),
    ...overrides,
  };
}
```

### BAD: Muddled test with no clear phases

```typescript
describe("OrderService", () => {
  it("works", async () => {
    // Setup, action, and assertions are mixed together.
    // What is this test actually verifying?
    const service = new OrderService(realDb, realCatalog, realPayment);
    const c = await realDb.query("INSERT INTO customers ...");

    // First behavior: placing an order
    const order = await service.placeOrder(c, [{ pid: "1", qty: 1 }], null);
    expect(order).toBeTruthy(); // vague assertion
    const dbOrder = await realDb.query("SELECT * FROM orders WHERE id = $1", [order.id]);
    expect(dbOrder.status).toBe("confirmed");

    // Second behavior: cancelling — this is a different test!
    await service.cancelOrder(order.id);
    const cancelled = await realDb.query("SELECT * FROM orders WHERE id = $1", [order.id]);
    expect(cancelled.status).toBe("cancelled");

    // Third behavior: refund — yet another test!
    const refund = await service.refundOrder(order.id);
    expect(refund.amount).toBe(order.total);
    // One "test" covering three behaviors. If cancel breaks,
    // refund is never tested. Failure messages are confusing.
  });
});
```

## Alternatives & Related Approaches

| Approach | When to prefer it |
|---|---|
| **Table-driven tests** | When testing the same behavior with many input/output combinations |
| **Property-based testing** | When the input space is large and you want to test invariants, not specific examples |
| **Given-When-Then (BDD)** | When non-technical stakeholders need to read test scenarios |
| **Approval/snapshot testing** | When the output is complex (large objects, rendered HTML) and easier to review as a snapshot |

Table-driven tests work well within the AAA framework:

```typescript
describe("calculateShipping", () => {
  const cases = [
    { weight: 0.5, zone: "domestic", expected: 5.99 },
    { weight: 2.0, zone: "domestic", expected: 8.99 },
    { weight: 0.5, zone: "international", expected: 15.99 },
    { weight: 5.0, zone: "international", expected: 35.99 },
  ];

  it.each(cases)(
    "charges $expected for ${weight}kg to $zone",
    ({ weight, zone, expected }) => {
      // Arrange (inline — the table IS the arrangement)
      const parcel = { weight, zone };

      // Act
      const cost = calculateShipping(parcel);

      // Assert
      expect(cost).toBe(expected);
    }
  );
});
```

## When NOT to Apply

- **Do not force AAA when the test is genuinely one line.** `expect(add(2, 3)).toBe(5)` does not need three labeled sections.
- **Do not use AAA comments in every test.** The pattern should be visible from the structure (blank lines between phases). Comments like `// Arrange` are training wheels — useful for beginners, unnecessary in experienced teams.
- **Do not separate Act and Assert when testing exceptions.** `expect(() => fn()).toThrow()` naturally combines the two phases. That is fine.

## Tensions & Trade-offs

- **Arrange duplication:** When many tests need the same setup, you are tempted to move Arrange into `beforeEach`. This hides context from the test, making it harder to read. Prefer test builder functions over shared setup.
- **One assertion per test vs. multiple assertions:** Purists say one assertion per test. Pragmatists say: multiple assertions verifying the same behavior are fine. One test for "order is created" can assert status, total, and customer ID. But do not assert on unrelated behaviors.
- **Fixture complexity:** Complex Arrange sections indicate either a complex domain (acceptable) or a design problem (the system under test has too many dependencies). If Arrange is 20 lines and Act is 1 line, consider whether the design needs simplification.

## Real-World Consequences

Teams that adopt AAA consistently report that new developers can read and understand tests within days of joining the project. The structure is universal — once you learn it in one codebase, you recognize it in every other.

A common failure mode: tests that do not have a clear Act phase. The Arrange section creates objects and calls methods, and the Assert section checks state — but it is unclear which specific action is being tested. AAA forces you to identify the one thing the test is about.

## Further Reading

- [Bill Wake: Arrange, Act, Assert](https://xp123.com/articles/3a-arrange-act-assert/)
- [Martin Fowler: Given When Then](https://martinfowler.com/bliki/GivenWhenThen.html)
- *xUnit Test Patterns* by Gerard Meszaros — comprehensive test structure patterns
- [Dan North: Introducing BDD](https://dannorth.net/introducing-bdd/)
