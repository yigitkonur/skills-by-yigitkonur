# 12 — Testing Principles

**Principles and patterns for building test suites that provide confidence, run fast, and survive refactoring.**

---

## Why Testing Principles Matter

Tests are not a tax. They are a design tool, a safety net, and a living specification. A good test suite lets you refactor with confidence, deploy on Friday, and onboard new developers in days. A bad test suite — slow, flaky, brittle, or misleading — is worse than no tests because it creates false confidence and punishes change.

## Principle Index

| Principle | Summary | Key Question |
|---|---|---|
| [Test Pyramid](./test-pyramid.md) | Balance unit, integration, and E2E tests | "How should I distribute my testing effort?" |
| [Test-Driven Development](./test-driven-development.md) | Red-Green-Refactor: tests drive design | "Should I write tests before or after code?" |
| [Arrange-Act-Assert](./arrange-act-assert.md) | Structure every test in three clear phases | "How should I structure a single test?" |
| [Test Doubles](./test-doubles.md) | Mocks, stubs, fakes, spies, dummies | "How should I handle dependencies in tests?" |
| [Property-Based Testing](./property-based-testing.md) | Test invariants with generated inputs | "How do I find edge cases I cannot think of?" |
| [Contract Testing](./contract-testing.md) | Verify API agreements between services | "How do I test microservice integration?" |
| [Mutation Testing](./mutation-testing.md) | Test your tests by injecting code changes | "Are my tests actually catching bugs?" |
| [Testing Anti-Patterns](./testing-anti-patterns.md) | Common mistakes and how to fix them | "Why is my test suite slow/flaky/useless?" |

## Flowchart: What Kind of Test Should I Write?

```
START: What am I testing?
│
├── Pure logic (calculations, transformations, validation)?
│   └── Write a UNIT TEST
│       ├── Few inputs? → Example-based test (AAA pattern)
│       └── Large input space? → Property-based test
│
├── A component with its dependencies (API handler + DB, React component + hooks)?
│   └── Write an INTEGRATION TEST
│       ├── Own database? → Use test containers or in-memory DB
│       └── External API? → Use contract test (Pact) or recorded responses
│
├── A critical user journey (signup, checkout, payment)?
│   └── Write an E2E TEST (sparingly)
│       └── Use Playwright or Cypress for browser-based flows
│
├── An API contract between two services?
│   └── Write a CONTRACT TEST (Pact, Spring Cloud Contract)
│
├── "Are my existing tests good enough?"
│   └── Run MUTATION TESTING (Stryker, PIT)
│       └── Fix surviving mutants by adding stronger assertions
│
└── Not sure?
    └── Start with an integration test.
        Kent C. Dodds says: "Write tests. Not too many. Mostly integration."
```

## Testing Strategy by Application Type

### Backend API (Node.js/Express/Fastify)
```
60% Unit tests      — business logic, validation, calculations
30% Integration     — API handlers with real DB, middleware chains
 5% Contract tests  — consumer-driven contracts for each API consumer
 5% E2E tests       — critical API workflows (auth flow, payment flow)
```

### Frontend SPA (React/Vue/Svelte)
```
20% Unit tests      — utility functions, state reducers, formatters
50% Integration     — components with hooks/context, form interactions
20% E2E tests       — critical user journeys
10% Visual tests    — snapshot/visual regression for UI components
```

### Microservice System (10+ services)
```
40% Unit tests      — per-service business logic
30% Integration     — per-service with own database/queue
20% Contract tests  — consumer-driven contracts between services
10% E2E tests       — critical cross-service workflows
```

### Data Pipeline (ETL/batch processing)
```
30% Unit tests      — transformation logic, parsing, validation
50% Integration     — pipeline stages with real data samples
10% Property tests  — data invariants (no rows lost, types preserved)
10% E2E tests       — full pipeline runs with known datasets
```

## Core Testing Heuristics

1. **Test behavior, not implementation.** If you can refactor the internals without changing behavior and the tests break, the tests are testing the wrong thing.

2. **One reason to fail.** Each test should fail for one reason. If a test can fail because of a discount calculation bug OR a database connection issue, split it into two tests.

3. **Tests are documentation.** A new developer should be able to read your tests and understand what the system does. Name tests as behaviors: "rejects expired discount codes" not "test_discount_3".

4. **Fast feedback loop.** The primary test suite (unit + integration) should run in under 5 minutes. If developers cannot run tests before pushing, they will not.

5. **Deterministic always.** Tests must produce the same result regardless of time of day, execution order, or machine. Use fake clocks, seeded random, and isolated state.

6. **Fix flaky tests immediately.** A test that fails 5% of the time will fail in every CI pipeline of 20+ tests. Quarantine, fix, or delete — never ignore.

7. **Coverage is a floor, not a goal.** Use code coverage to find untested code. Use mutation testing to find untested behavior. Never optimize for the coverage number itself.

8. **Delete tests that do not earn their keep.** A test that breaks on every refactor, takes 30 seconds, and tests trivial behavior is a liability. Delete it.

## Key Libraries (TypeScript/Node.js)

| Category | Library | Purpose |
|---|---|---|
| Test runner | [Vitest](https://vitest.dev/) | Fast, Vite-native, Jest-compatible |
| Test runner | [Jest](https://jestjs.io/) | Established, large ecosystem |
| E2E | [Playwright](https://playwright.dev/) | Cross-browser E2E testing |
| Contract | [Pact](https://docs.pact.io/) | Consumer-driven contract testing |
| Property | [fast-check](https://fast-check.dev/) | Property-based testing |
| Mutation | [Stryker](https://stryker-mutator.io/) | Mutation testing |
| Containers | [Testcontainers](https://testcontainers.com/) | Docker-based test dependencies |
| HTTP mocking | [MSW](https://mswjs.io/) | Mock Service Worker for API mocking |

## Further Reading

- *Test-Driven Development: By Example* by Kent Beck
- *xUnit Test Patterns* by Gerard Meszaros
- *Growing Object-Oriented Software, Guided by Tests* by Freeman & Pryce
- *Working Effectively with Legacy Code* by Michael Feathers
- [Kent C. Dodds: Write Tests. Not Too Many. Mostly Integration.](https://kentcdodds.com/blog/write-tests)
- [Google Testing Blog](https://testing.googleblog.com/)
- [Martin Fowler: Testing Articles](https://martinfowler.com/testing/)
