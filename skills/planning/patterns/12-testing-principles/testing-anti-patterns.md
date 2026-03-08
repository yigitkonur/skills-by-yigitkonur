# Testing Anti-Patterns

**Recognize and fix the most common testing mistakes that make test suites slow, brittle, and untrustworthy.**

---

## Origin / History

Testing anti-patterns have been documented across decades of software engineering literature. Gerard Meszaros catalogued many in *xUnit Test Patterns* (2007). The software craftsmanship movement of the 2010s refined the list through blog posts, conference talks, and hard-won experience. These anti-patterns are universal — they appear in every language, every framework, and every team. The consequences are also universal: developers stop trusting the tests, stop running the tests, and eventually stop writing tests.

## The Problem It Solves

A test suite is only valuable if developers trust it and run it. Anti-patterns erode trust in predictable ways: flaky tests make developers ignore failures ("it's probably just flaky"), slow suites make developers skip them locally, and brittle tests make developers dread refactoring. Recognizing and fixing these patterns is the difference between a test suite that accelerates development and one that slows it down.

## The Anti-Patterns

### 1. Flaky Tests

**The problem:** Tests that pass sometimes and fail sometimes with no code change. Common causes: timing dependencies, shared mutable state, test ordering, network calls, date/time sensitivity.

**The fix:**

```typescript
// BAD: Timing-dependent test
it("debounces search input", async () => {
  fireEvent.change(input, { target: { value: "hello" } });
  await new Promise((r) => setTimeout(r, 500)); // Hope 500ms is enough
  expect(mockSearch).toHaveBeenCalledTimes(1);
});

// GOOD: Use fake timers, not real time
it("debounces search input", () => {
  vi.useFakeTimers();
  fireEvent.change(input, { target: { value: "hello" } });
  vi.advanceTimersByTime(300); // Exact control
  expect(mockSearch).toHaveBeenCalledTimes(1);
  vi.useRealTimers();
});
```

**Rule:** If a test fails on CI but passes locally (or vice versa), it is flaky. Fix it immediately or delete it. A flaky test is worse than no test — it teaches the team to ignore failures.

### 2. Testing Implementation Details

**The problem:** Tests that assert on internal structure (private methods, internal state, specific function calls) instead of observable behavior. These break on every refactor even when behavior is unchanged.

**The fix:**

```typescript
// BAD: Testing how the code works
it("uses the cache", () => {
  const spy = vi.spyOn(cache, "get");
  service.getUserProfile(123);
  expect(spy).toHaveBeenCalledWith("user:123"); // Internal detail
});

// GOOD: Testing what the code does
it("returns the user profile", async () => {
  await seedUser({ id: 123, name: "Jane" });
  const profile = await service.getUserProfile(123);
  expect(profile.name).toBe("Jane"); // Observable behavior
});

// GOOD: If caching behavior IS the requirement, test the observable effect
it("returns the same result without hitting the database twice", async () => {
  await seedUser({ id: 123, name: "Jane" });
  const dbSpy = vi.spyOn(db, "query");

  await service.getUserProfile(123);
  await service.getUserProfile(123);

  expect(dbSpy).toHaveBeenCalledTimes(1); // Caching is an observable optimization
});
```

### 3. Excessive Mocking

**The problem:** Tests that mock everything become mirrors of the implementation. They pass when the code is wrong and fail when the code is refactored. They provide zero confidence.

**The fix:**

```typescript
// BAD: Mock everything
it("sends welcome email", async () => {
  const mockRepo = { save: vi.fn() };
  const mockEmail = { send: vi.fn() };
  const mockLogger = { info: vi.fn() };
  const mockMetrics = { increment: vi.fn() };

  const service = new UserService(mockRepo, mockEmail, mockLogger, mockMetrics);
  await service.register({ name: "Jane", email: "jane@test.com" });

  expect(mockRepo.save).toHaveBeenCalled();
  expect(mockEmail.send).toHaveBeenCalledWith("jane@test.com", expect.any(String));
  expect(mockLogger.info).toHaveBeenCalled();
  expect(mockMetrics.increment).toHaveBeenCalledWith("user.registered");
  // This test is just the implementation rewritten as expectations.
});

// GOOD: Use real collaborators where practical, fake only infrastructure
it("sends welcome email on registration", async () => {
  const emailSpy = new SpyEmailService();
  const service = new UserService(
    new InMemoryUserRepository(),
    emailSpy,
    realLogger,      // Let it log — no need to mock
    realMetrics      // Let it record — or use a no-op
  );

  await service.register({ name: "Jane", email: "jane@test.com" });

  expect(emailSpy.sentEmails).toContainEqual(
    expect.objectContaining({ to: "jane@test.com" })
  );
});
```

### 4. Slow Test Suites

**The problem:** Test suites that take more than a few minutes make developers skip running them locally. Slow tests pile up. CI becomes a 30-minute bottleneck.

**The fix:**
- Move slow tests (database, network, browser) to integration suites that run separately.
- Use in-memory fakes instead of real databases for unit tests.
- Parallelize test execution (`vitest --pool=threads`).
- Avoid unnecessary setup/teardown per test (use `beforeAll` for shared read-only fixtures).
- Profile your test suite — often 80% of the time is spent in 20% of the tests.

### 5. Test Interdependence

**The problem:** Tests that depend on the execution order or shared state of other tests. Test A creates a user; test B assumes it exists. Reorder the tests and B fails.

**The fix:**

```typescript
// BAD: Tests share state
describe("user management", () => {
  it("creates a user", async () => {
    await service.createUser({ id: 1, name: "Jane" });
    // state leaks to the next test
  });

  it("finds the user", async () => {
    // DEPENDS on the previous test having run first
    const user = await service.findUser(1);
    expect(user.name).toBe("Jane");
  });
});

// GOOD: Each test is self-contained
describe("user management", () => {
  let repo: InMemoryUserRepository;
  let service: UserService;

  beforeEach(() => {
    repo = new InMemoryUserRepository(); // Fresh state per test
    service = new UserService(repo);
  });

  it("creates and retrieves a user", async () => {
    await service.createUser({ id: 1, name: "Jane" });
    const user = await service.findUser(1);
    expect(user.name).toBe("Jane");
  });
});
```

### 6. Testing Private Methods

**The problem:** Reaching into a class to test private methods indicates either the private method is complex enough to deserve its own class/function, or you are testing implementation instead of behavior.

**The fix:**

```typescript
// BAD: Bypassing access control to test internals
it("validates email format", () => {
  const service = new UserService();
  // @ts-ignore or (service as any) to access private method
  expect((service as any).isValidEmail("test@example.com")).toBe(true);
});

// GOOD Option 1: Test through the public API
it("rejects registration with invalid email", async () => {
  await expect(
    service.register({ name: "Jane", email: "not-an-email" })
  ).rejects.toThrow(InvalidEmailError);
});

// GOOD Option 2: Extract and test as a standalone function
// If the logic is complex enough to test directly, it deserves to be public
import { isValidEmail } from "./validation";
it("validates email format", () => {
  expect(isValidEmail("test@example.com")).toBe(true);
  expect(isValidEmail("not-an-email")).toBe(false);
});
```

### 7. The 100% Coverage Obsession

**The problem:** Treating code coverage as a target leads to meaningless tests written to satisfy a metric. Developers write `expect(result).toBeDefined()` to cover a line without testing behavior. Getters, setters, and error messages get "tested" to hit 100%.

**The fix:**
- Use coverage as a floor (e.g., "no file below 70%"), not a ceiling to strive toward.
- Use mutation testing to evaluate test quality instead of coverage.
- Accept that some code (configuration, boilerplate, framework glue) does not need unit tests.
- Measure what matters: "Does the test suite catch bugs?" not "Does it touch every line?"

### 8. The Giant Test Setup

**The problem:** 50 lines of setup for 1 line of action and 1 line of assertion. The test is unreadable because the important parts are buried.

**The fix:** Use test builders with sensible defaults.

```typescript
// BAD: 30 lines of setup noise
it("applies senior discount", async () => {
  const customer = {
    id: "c1",
    name: "Jane",
    email: "jane@test.com",
    phone: "555-0100",
    address: { street: "123 Main", city: "Anytown", zip: "12345", country: "US" },
    tier: "senior",
    createdAt: new Date(),
    updatedAt: new Date(),
    preferences: { notifications: true, marketing: false },
  };
  // ... 20 more lines of irrelevant setup ...

  const result = await service.calculateDiscount(customer, cart);
  expect(result.discountPercent).toBe(15);
});

// GOOD: Builder highlights only what matters
it("applies senior discount", async () => {
  const customer = buildCustomer({ tier: "senior" });
  const result = await service.calculateDiscount(customer, buildCart());
  expect(result.discountPercent).toBe(15);
});
```

## Alternatives & Related Approaches

| Anti-pattern | Better approach |
|---|---|
| Flaky tests | Fake timers, deterministic data, isolated state |
| Testing implementation | Test observable behavior and public APIs |
| Excessive mocking | Fakes, in-memory implementations, integration tests |
| Slow suites | Parallel execution, in-memory dependencies, test sharding |
| Test interdependence | Fresh state per test, self-contained tests |
| Testing private methods | Test through public API or extract to a public module |
| 100% coverage | Mutation testing, coverage floors (not targets) |
| Giant setup | Test builders with sensible defaults |

## When NOT to Apply (These Fixes)

- **Mocking is sometimes correct.** External APIs, payment gateways, and email services should be mocked. The anti-pattern is mocking *everything*, not mocking *anything*.
- **Shared setup is sometimes fine.** Read-only test fixtures (reference data, static config) can be shared via `beforeAll` without causing interdependence.
- **100% coverage might be required.** Safety-critical software (medical devices, aviation) may mandate 100% coverage by regulation. In that context, the "obsession" is justified.

## Tensions & Trade-offs

- **Speed vs. realism:** Replacing real dependencies with fakes makes tests fast but less realistic. Every fake is a simplification that might miss real bugs.
- **Isolation vs. readability:** Self-contained tests duplicate setup. Shared fixtures reduce duplication but create implicit dependencies. Test builders strike a balance.
- **Strictness vs. pragmatism:** Demanding zero flaky tests, zero mocks, and 85% mutation score is admirable but impractical for many teams. Start by fixing the worst offenders and raise the bar incrementally.

## Real-World Consequences

Spotify published an internal study showing that flaky tests cost them thousands of engineering hours per year. Developers retried CI pipelines, investigated false failures, and lost trust in the test suite. They invested in a "flaky test quarantine" system that automatically disabled consistently flaky tests and created tickets to fix them.

A team at a large bank had 100% code coverage. They also had a production incident every two weeks. Their tests were full of `toBeDefined()`, `toBeInstanceOf()`, and `not.toThrow()` assertions that covered lines without testing logic. After introducing mutation testing, their mutation score was 35%. They spent three months replacing weak assertions with behavior-verifying tests. Production incidents dropped to one per quarter.

## Further Reading

- *xUnit Test Patterns* by Gerard Meszaros — the comprehensive catalog
- [Google Testing Blog: Flaky Tests at Google](https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html)
- [Kent C. Dodds: Testing Implementation Details](https://kentcdodds.com/blog/testing-implementation-details)
- [Martin Fowler: Eradicating Non-Determinism in Tests](https://martinfowler.com/articles/nonDeterminism.html)
- [Spotify: Flaky Test Handling](https://engineering.atspotify.com/)
