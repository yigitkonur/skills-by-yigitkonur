# Test Doubles

**Use substitutes for real dependencies in tests — but know the difference between mocks, stubs, fakes, spies, and dummies.**

---

## Origin / History

Gerard Meszaros coined the umbrella term "test double" in *xUnit Test Patterns* (2007), borrowing from the film industry's "stunt double." Martin Fowler further clarified the taxonomy in his influential 2007 article "Mocks Aren't Stubs," distinguishing between state verification (using stubs) and behavior verification (using mocks). The distinction matters because overusing mocks — behavior verification — leads to tests that are tightly coupled to implementation details. The "mockist vs. classicist" debate maps directly to the London vs. Chicago TDD schools.

## The Problem It Solves

Real dependencies make tests slow (databases, APIs), non-deterministic (network, clocks), or impossible to control (third-party services, payment gateways). You need substitutes that give you speed, determinism, and control. But not all substitutes are the same. Using the wrong type of test double leads to either brittle tests that break on every refactor (over-mocking) or unreliable tests that pass when the real integration would fail (over-stubbing).

## The Principle Explained

Martin Fowler's taxonomy defines five types of test doubles:

**Dummy:** An object passed to satisfy a parameter but never actually used. Often `null` or an empty implementation. Use when the code requires a parameter that is irrelevant to the test.

**Stub:** An object that returns predetermined responses. It does not record how it was called. Use when you need to control what a dependency returns so you can test the caller's logic.

**Spy:** A stub that also records how it was called (which methods, with what arguments, how many times). Use when you need to verify that a side effect occurred (email sent, event published) without asserting the exact implementation.

**Mock:** An object with pre-programmed expectations about how it will be called. The test fails if the expected calls do not happen. Use sparingly — mocks tie your test to the implementation, not the behavior.

**Fake:** A working implementation that takes shortcuts. An in-memory database, a local file system instead of S3, a simplified email service that writes to an array. Fakes are the most realistic test doubles but require maintenance.

The practical guideline: **stub queries, mock commands, fake infrastructure.** If a dependency returns data (query), stub it. If a dependency performs an action (command/side effect), use a spy or mock to verify it was called. If a dependency is infrastructure (database, queue), consider a fake.

## Code Examples

### GOOD: Appropriate test doubles for each situation

```typescript
// --- DUMMY: satisfies a parameter that is irrelevant ---
it("logs the error when processing fails", async () => {
  const dummyConfig: AppConfig = {} as AppConfig; // never accessed
  const logger = new SpyLogger();
  const processor = new OrderProcessor(dummyConfig, logger);

  await processor.process(invalidOrder);

  expect(logger.errors).toContainEqual(
    expect.objectContaining({ message: "Invalid order" })
  );
});

// --- STUB: control what a dependency returns ---
it("applies free shipping for orders over $100", async () => {
  const shippingCalculator: ShippingCalculator = {
    // Stub: always returns the same value
    calculate: async () => ({ cost: 9.99, method: "standard" }),
  };

  const service = new CheckoutService(shippingCalculator);
  const result = await service.checkout({
    items: [{ price: 120, quantity: 1 }],
  });

  // We test the CALLER's logic: free shipping applied
  expect(result.shippingCost).toBe(0);
  expect(result.freeShippingApplied).toBe(true);
});

// --- SPY: verify a side effect occurred ---
class SpyEmailService implements EmailService {
  readonly sentEmails: Array<{ to: string; subject: string; body: string }> = [];

  async send(to: string, subject: string, body: string): Promise<void> {
    this.sentEmails.push({ to, subject, body });
  }
}

it("sends confirmation email after successful order", async () => {
  const emailSpy = new SpyEmailService();
  const service = new OrderService(inMemoryRepo, stubPayment, emailSpy);

  await service.placeOrder(customer, items);

  expect(emailSpy.sentEmails).toHaveLength(1);
  expect(emailSpy.sentEmails[0].to).toBe(customer.email);
  expect(emailSpy.sentEmails[0].subject).toContain("Order Confirmation");
});

// --- FAKE: a working in-memory implementation ---
class InMemoryOrderRepository implements OrderRepository {
  private orders = new Map<string, Order>();

  async save(order: Order): Promise<void> {
    this.orders.set(order.id, { ...order });
  }

  async findById(id: string): Promise<Order | null> {
    return this.orders.get(id) ?? null;
  }

  async findByCustomer(customerId: string): Promise<Order[]> {
    return Array.from(this.orders.values()).filter(
      (o) => o.customerId === customerId
    );
  }
}

it("retrieves orders by customer after saving", async () => {
  const repo = new InMemoryOrderRepository();
  const service = new OrderService(repo, stubPayment, stubEmail);

  await service.placeOrder(customerA, itemsA);
  await service.placeOrder(customerA, itemsB);
  await service.placeOrder(customerB, itemsC);

  const ordersA = await repo.findByCustomer(customerA.id);
  expect(ordersA).toHaveLength(2);
});
```

### BAD: Over-mocking — testing implementation, not behavior

```typescript
it("places an order", async () => {
  // Mock EVERYTHING. The test is now a mirror of the implementation.
  const mockRepo = jest.fn();
  const mockPayment = jest.fn();
  const mockEmail = jest.fn();
  const mockLogger = jest.fn();
  const mockMetrics = jest.fn();

  mockPayment.charge = jest.fn().mockResolvedValue({ id: "ch_123" });
  mockRepo.save = jest.fn().mockResolvedValue(undefined);
  mockEmail.send = jest.fn().mockResolvedValue(undefined);
  mockLogger.info = jest.fn();
  mockMetrics.increment = jest.fn();

  const service = new OrderService(
    mockRepo, mockPayment, mockEmail, mockLogger, mockMetrics
  );

  await service.placeOrder(customer, items);

  // These assertions test HOW the code works, not WHAT it does.
  // If you reorder the internal calls, the test breaks.
  // If you add a log line, the test breaks.
  // If you rename an internal variable, nothing catches a real bug.
  expect(mockPayment.charge).toHaveBeenCalledWith({
    amount: 100,
    currency: "usd",
    customerId: customer.id,
  });
  expect(mockRepo.save).toHaveBeenCalledTimes(1);
  expect(mockEmail.send).toHaveBeenCalledWith(
    customer.email,
    expect.stringContaining("Order"),
    expect.any(String)
  );
  expect(mockLogger.info).toHaveBeenCalledWith("Order placed", expect.any(Object));
  expect(mockMetrics.increment).toHaveBeenCalledWith("orders.placed");
});
```

## Alternatives & Related Approaches

| Approach | When to prefer it |
|---|---|
| **Integration tests with real dependencies** | When the integration itself is what you want to test (DB queries, HTTP handlers) |
| **Testcontainers** | When you want a real database/queue/cache in tests but isolated and disposable |
| **In-memory databases (SQLite)** | When you want realistic query behavior without the weight of a full database server |
| **Contract tests** | When you want to verify the interface between services without a live dependency |
| **Recorded HTTP responses (VCR)** | When you want realistic API responses without hitting the real API |

## When NOT to Apply

- **Do not mock what you do not own.** If you mock `fetch` or `axios`, your test passes but the real API might behave differently. Use integration tests or contract tests for external APIs.
- **Do not mock value objects.** If `Money`, `Email`, or `DateRange` are simple value objects, use the real ones. They are fast and deterministic.
- **Do not mock the system under test.** If you are spying on the class you are testing, the test is testing the mock framework, not your code.
- **Do not mock everything just because you can.** A test with 5 mocks and 10 `expect(mock).toHaveBeenCalledWith(...)` assertions is testing the wiring diagram, not the behavior.

## Tensions & Trade-offs

- **Mock fatigue:** Teams that over-mock end up with tests that break on every refactor. The tests pass, the code ships, and production breaks because the mocks do not match reality. This erodes trust in the test suite.
- **Fake maintenance:** Fakes are the most reliable test doubles, but they need to stay in sync with the real implementation. An in-memory repository that does not enforce unique constraints will miss bugs that the real database catches.
- **Test isolation vs. test realism:** Mocks give perfect isolation but zero realism. Fakes give moderate isolation and moderate realism. Integration tests with real dependencies give full realism but shared state and slower execution.
- **Sociable vs. solitary tests:** Classicist TDD uses real collaborators (sociable tests). Mockist TDD replaces all collaborators with mocks (solitary tests). Sociable tests find integration bugs; solitary tests pinpoint failure locations.

## Real-World Consequences

Google's testing guidelines state: "Prefer real implementations over test doubles when practical." They invest heavily in fakes that behave like real services and maintain them alongside the production code. Their Stubby framework (internal RPC) ships with in-memory fakes for every service.

A common failure: a team mocks their database layer with stubs that return hardcoded data. Tests pass. In production, a SQL query returns rows in a different order, causing a subtle bug. The test suite provided false confidence because the stubs did not replicate real database behavior.

## Further Reading

- [Martin Fowler: Mocks Aren't Stubs](https://martinfowler.com/articles/mocksArentStubs.html)
- *xUnit Test Patterns* by Gerard Meszaros — the canonical test double taxonomy
- *Growing Object-Oriented Software, Guided by Tests* by Freeman & Pryce — the mockist perspective
- [Google Testing Blog: Know Your Test Doubles](https://testing.googleblog.com/2013/07/testing-on-toilet-know-your-test-doubles.html)
