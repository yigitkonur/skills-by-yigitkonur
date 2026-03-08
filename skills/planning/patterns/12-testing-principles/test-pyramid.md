# Test Pyramid

**Structure your test suite with many fast unit tests at the base, fewer integration tests in the middle, and a thin layer of end-to-end tests at the top.**

---

## Origin / History

Mike Cohn introduced the Test Pyramid in his 2009 book *Succeeding with Agile*. The idea was simple: the higher you go in the pyramid, the slower, more brittle, and more expensive tests become. Therefore, invest heavily in the base (unit tests) and sparingly at the top (E2E tests). In 2018, Kent C. Dodds proposed the "Testing Trophy" as an alternative, arguing that integration tests provide the best return on investment for frontend applications. The debate continues with Martin Fowler's "Testing Diamond" and various context-specific variations. The core question remains: where should you concentrate your testing effort?

## The Problem It Solves

Without a deliberate testing strategy, teams either write too few tests (shipping bugs) or write tests at the wrong level (slow suites that break constantly). A common anti-pattern is the "Ice Cream Cone" or inverted pyramid: many E2E tests, few unit tests, and almost no integration tests. This creates test suites that take 45 minutes to run, fail intermittently due to timing issues, and are so expensive to maintain that developers stop running them.

## The Principle Explained

**The Original Pyramid (Mike Cohn):**

```
        /  E2E  \          Few, slow, expensive
       /----------\
      / Integration \       Moderate number, moderate speed
     /----------------\
    /    Unit Tests     \   Many, fast, cheap
   /--------------------\
```

Unit tests form the foundation. They test individual functions, classes, or modules in isolation. They are fast (milliseconds), deterministic, and cheap to write and maintain. A large codebase might have thousands.

Integration tests verify that components work together: a service with its database, an API handler with its middleware, a React component with its state management. They are slower (seconds) and require more setup, but they catch the bugs that unit tests miss — the ones at the boundaries.

E2E tests simulate real user workflows through the entire stack. They are slow (minutes), brittle (sensitive to UI changes, network timing, test data), and expensive to maintain. They should cover critical user journeys, not every feature.

**The Testing Trophy (Kent C. Dodds):**

```
         /  E2E  \
        /----------\
       / Integration \     ← Most tests here
      /----------------\
     /    Unit Tests     \
    /--------------------\
   /    Static Analysis    \   ← TypeScript, ESLint
  /-------------------------\
```

Dodds argues that for frontend/fullstack applications, integration tests give the best confidence-to-cost ratio. Testing a React component with its hooks, context, and child components catches more real bugs than testing each piece in isolation. Static analysis (TypeScript, linting) catches an entire class of errors that unit tests would otherwise cover.

**The Testing Diamond:**

Emphasizes integration tests as the widest layer, with thinner unit and E2E layers. Common in microservice architectures where the interesting behavior is at the integration points (database queries, API calls, message handling).

## Code Examples

### GOOD: Balanced pyramid with appropriate test levels

```typescript
// UNIT TEST: Pure logic, no dependencies, runs in <1ms
// Tests the discount calculation in isolation
describe("calculateDiscount", () => {
  it("applies percentage discount to subtotal", () => {
    const result = calculateDiscount({
      subtotal: 100,
      discountType: "percentage",
      discountValue: 15,
    });
    expect(result).toBe(15);
  });

  it("caps absolute discount at subtotal", () => {
    const result = calculateDiscount({
      subtotal: 10,
      discountType: "absolute",
      discountValue: 25,
    });
    expect(result).toBe(10); // Cannot discount more than subtotal
  });

  it("returns zero for expired discount codes", () => {
    const result = calculateDiscount({
      subtotal: 100,
      discountType: "percentage",
      discountValue: 15,
      expiresAt: new Date("2020-01-01"),
    });
    expect(result).toBe(0);
  });
});

// INTEGRATION TEST: Tests the API handler with real middleware
// and a real database (via test container or in-memory DB)
describe("POST /api/orders", () => {
  let app: Express;
  let db: TestDatabase;

  beforeAll(async () => {
    db = await TestDatabase.create();
    app = createApp({ database: db.connection });
  });

  afterAll(() => db.destroy());

  it("creates an order and applies discount", async () => {
    await db.seed({
      products: [{ id: "P1", name: "Widget", price: 50 }],
      discounts: [{ code: "SAVE10", type: "percentage", value: 10 }],
    });

    const response = await request(app)
      .post("/api/orders")
      .send({
        items: [{ productId: "P1", quantity: 2 }],
        discountCode: "SAVE10",
      })
      .expect(201);

    expect(response.body.total).toBe(90); // 100 - 10%
    expect(response.body.discount).toBe(10);

    // Verify the database state
    const order = await db.query("SELECT * FROM orders WHERE id = $1", [response.body.id]);
    expect(order.status).toBe("pending");
  });
});

// E2E TEST: Critical user journey through the real UI
// Run sparingly — only for the most important flows
describe("checkout flow", () => {
  it("completes purchase with discount code", async () => {
    await page.goto("/products/widget");
    await page.click("[data-testid='add-to-cart']");
    await page.goto("/cart");
    await page.fill("[data-testid='discount-code']", "SAVE10");
    await page.click("[data-testid='apply-discount']");
    await expect(page.locator("[data-testid='total']")).toHaveText("$90.00");
    await page.click("[data-testid='checkout']");
    await page.fill("[data-testid='card-number']", "4242424242424242");
    await page.click("[data-testid='pay']");
    await expect(page.locator("[data-testid='confirmation']")).toBeVisible();
  });
});
```

### BAD: Inverted pyramid — mostly E2E tests

```typescript
// The team wrote 200 E2E tests and 10 unit tests.
// Test suite takes 45 minutes. 15% of runs fail due to flakiness.
// Developers stop running tests locally. CI becomes a bottleneck.

describe("discount feature", () => {
  // E2E test for something that should be a unit test
  it("calculates percentage discount", async () => {
    await page.goto("/products/widget");
    await page.click("[data-testid='add-to-cart']");
    await page.goto("/cart");
    await page.fill("[data-testid='discount-code']", "SAVE10");
    await page.click("[data-testid='apply-discount']");
    // Wait 3 seconds for the UI to update (fragile!)
    await page.waitForTimeout(3000);
    await expect(page.locator("[data-testid='total']")).toHaveText("$90.00");
  });

  // Another E2E test for expired discount — same 30-second setup
  it("rejects expired discount", async () => {
    await page.goto("/products/widget");
    await page.click("[data-testid='add-to-cart']");
    await page.goto("/cart");
    await page.fill("[data-testid='discount-code']", "EXPIRED");
    await page.click("[data-testid='apply-discount']");
    await page.waitForTimeout(3000);
    await expect(page.locator("[data-testid='error']")).toHaveText("Discount expired");
  });
  // 50 more E2E tests like this...
});
```

## Alternatives & Related Approaches

| Approach | When to prefer it |
|---|---|
| **No tests (move fast and break things)** | Prototype/hackathon only. Never for production code with users. |
| **Only E2E tests** | When the codebase is tiny, the team is small, and speed of feedback does not matter |
| **Contract testing** | In microservice architectures where integration points are the primary risk |
| **Testing Trophy** | Frontend-heavy applications where component integration tests give the best ROI |
| **Snapshot testing** | UI components where visual regression is the primary concern |

## When NOT to Apply

- **Do not follow the pyramid blindly for all architectures.** A data pipeline with no UI benefits from heavy integration tests (data in, data out) and few unit tests of internal transformations.
- **Do not optimize for the wrong metric.** A "balanced" pyramid with 1,000 unit tests that test getters/setters is worse than 50 integration tests that cover real behavior.
- **Do not avoid E2E tests entirely.** The pyramid says "fewer," not "zero." Critical user journeys (signup, checkout, payment) need E2E coverage.

## Tensions & Trade-offs

- **Speed vs. confidence:** Unit tests are fast but test in isolation. E2E tests are slow but test the real system. The pyramid optimizes for speed; the trophy optimizes for confidence.
- **Maintenance cost:** E2E tests break when UI changes. Unit tests break when you refactor internals. Integration tests break when contracts change. Each level has a different maintenance trigger.
- **Where are YOUR bugs?** If most production bugs come from component integration issues, shift investment toward integration tests. If most come from logic errors, invest in unit tests. Let your bug history guide the shape of your pyramid.
- **TypeScript changes the equation.** Strong static typing eliminates entire categories of bugs that unit tests would catch in JavaScript. This is one reason the Testing Trophy adds "Static Analysis" as the foundation layer.

## Real-World Consequences

Google maintains a rough ratio of 70% unit / 20% integration / 10% E2E and enforces it through code review norms. Their test suites run in minutes, not hours, enabling their rapid deployment pace.

A fintech startup wrote 800 Cypress E2E tests and 50 unit tests. Their CI pipeline took 90 minutes. Developers pushed code and went to lunch. A single CSS change broke 200 tests. They eventually deleted 600 E2E tests and replaced the coverage with 400 integration tests and 1,000 unit tests. CI dropped to 8 minutes.

## Further Reading

- *Succeeding with Agile* by Mike Cohn — the original test pyramid
- [Kent C. Dodds: Write Tests. Not Too Many. Mostly Integration.](https://kentcdodds.com/blog/write-tests)
- [Martin Fowler: Test Pyramid](https://martinfowler.com/bliki/TestPyramid.html)
- [Ham Vocke: The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- [Google Testing Blog: Just Say No to More End-to-End Tests](https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html)
