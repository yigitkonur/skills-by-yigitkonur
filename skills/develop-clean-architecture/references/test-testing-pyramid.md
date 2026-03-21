---
title: Follow the Testing Pyramid Aligned to Architecture Layers
impact: MEDIUM-HIGH
impactDescription: optimizes test suite speed and coverage by matching test types to layer responsibilities
tags: test, pyramid, layers, integration
---

## Follow the Testing Pyramid Aligned to Architecture Layers

Each architectural layer has a corresponding test type. Domain tests are pure and fast (bulk of tests). Use case tests mock ports. Adapter tests use real infrastructure. E2E tests verify wiring. This alignment maximizes confidence per test-dollar spent.

**The architecture-aligned testing pyramid:**

```text
         [E2E Tests — ~5-10%]           Full wiring, happy path
         [Integration Tests — ~15-20%]   Adapters + real DB (Testcontainers)
         [Use Case Tests — ~30-40%]      Mocked ports, orchestration logic
         [Domain Tests — ~40-50%]        Pure functions, zero mocks — cheapest
```

**Incorrect (all tests are integration tests — slow, brittle):**

```typescript
describe('PlaceOrder', () => {
  it('should place order', async () => {
    // Requires running DB, payment service, email server...
    const res = await request(app).post('/orders').send({ /* ... */ });
    expect(res.status).toBe(201);
  });
});
```

**Correct (each layer tested at appropriate level):**

```typescript
// DOMAIN UNIT TEST — zero mocks, pure
describe('Order entity', () => {
  it('rejects shipping a draft order', () => {
    const order = Order.create('cust_1' as CustomerId, [mockLine]);
    assert(order.ok);
    const result = order.value.ship('TRACK123');
    expect(result.ok).toBe(false);
    expect(result.error).toBe('NotConfirmed');
  });
});

// USE CASE TEST — mock all ports
describe('PlaceOrderHandler', () => {
  const mockOrders: jest.Mocked<OrderRepository> = {
    save: jest.fn().mockResolvedValue(undefined),
    findById: jest.fn(),
  };
  const mockPayments: jest.Mocked<PaymentGateway> = {
    charge: jest.fn().mockResolvedValue({ ok: true, value: 'txn_123' }),
  };
  const handler = new PlaceOrderHandler(mockOrders, mockPayments);

  it('does not save order if payment fails', async () => {
    mockPayments.charge.mockResolvedValue({ ok: false, error: new InsufficientFundsError() });
    const result = await handler.execute(cmd);
    expect(result.ok).toBe(false);
    expect(mockOrders.save).not.toHaveBeenCalled();
  });
});

// ADAPTER INTEGRATION TEST — real DB
describe('PrismaOrderRepository', () => {
  let container: StartedPostgreSqlContainer;
  let repo: PrismaOrderRepository;

  beforeAll(async () => {
    container = await new PostgreSqlContainer().start();
    // ... setup
  });

  it('saves and retrieves an order', async () => {
    const order = Order.create('cust_1' as CustomerId, [mockLine]);
    assert(order.ok);
    await repo.save(order.value);
    const found = await repo.findById(order.value.id);
    expect(found?.id).toBe(order.value.id);
  });
});
```

**Key rule: never mock domain entities in tests.** They are pure functions — mocking defeats the purpose. Test them directly.

**When NOT to use this pattern:**
- Tiny projects where a few E2E tests cover everything adequately
- Prototypes where test infrastructure overhead is not justified

**Benefits:**
- Domain tests run in milliseconds — fast feedback loop
- Use case tests verify orchestration without infrastructure startup time
- Integration tests catch real DB/API issues that mocks would miss
- E2E tests are few but verify the wiring is correct

Reference: [Test Pyramid — Martin Fowler](https://martinfowler.com/articles/practical-test-pyramid.html)
