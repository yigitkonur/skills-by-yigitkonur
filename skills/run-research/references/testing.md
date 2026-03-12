# Testing Strategy Research Guide

## Quick Reference: Which Tools For Which Testing Problem

| Use Case | Primary Tool | Secondary Tool | Key Signal |
|---|---|---|---|
| 01. Test Framework Selection | `deep_research` | `search_reddit` | Structured decision framework with migration cost |
| 02. Mocking & Stubbing Strategy | `deep_research` | `search_google` | Architecture-aware mock boundary decisions |
| 03. End-to-End Testing Setup | `deep_research` | `search_google` | Integrated strategy: framework + CI + flakiness |
| 04. Load & Stress Testing | `deep_research` | `search_google` | Scenario design + result interpretation methodology |
| 05. Property-Based Testing | `deep_research` | `search_google` | Property pattern taxonomy and generator design |

---

## 01. Test Framework Selection

### Recommended Tools
- **deep_research**: Produces weighted comparison tables accounting for your constraints (monorepo size, CI environment, team familiarity) with migration cost estimates.
- **search_reddit**: Unfiltered practitioner opinions, migration regret stories, and plugin ecosystem gaps.
- **search_google**: Latest benchmarks, migration guides, and feature comparison tables.

### Query Templates
```python
# deep_research
"Decision framework for Vitest vs Jest vs Mocha for large TypeScript monorepo (200+ packages,
~15,000 tests). Realistic speed improvement for Jest->Vitest? Jest features with no Vitest
equivalent? Migration effort in developer-weeks? Hybrid approaches during migration?"

# search_google
keywords = ["vitest vs jest benchmark 2025 performance comparison",
            "vitest migration from jest guide breaking changes"]

# search_reddit
queries = ["vitest vs jest which do you use 2025",
           "vitest problems issues flaky",
           "jest slow large project workaround"]
```

### Best Practices
- Include your specific context: monorepo size, test count, CI provider, team size.
- Ask about **migration cost separately** from feature comparison -- different research domains.
- Search for problems, not just comparisons: "jest slow" or "vitest flaky" reveals post-honeymoon reality.
- Include the current year to filter out stale advice.
- On Reddit, look for "switched from" queries to find migration experience reports.
- Attach your current test config file for dramatically more specific migration guidance.

---

## 02. Mocking & Stubbing Strategy

### Recommended Tools
- **deep_research**: Synthesizes testing philosophy ("mockist vs classicist", "testing trophy") with concrete patterns into a coherent decision framework.
- **search_google**: Foundational articles (Martin Fowler's "Mocks Aren't Stubs", Kent C. Dodds' "Testing Trophy") and framework-specific docs.
- **search_reddit**: Real pain points with over-mocking, brittle tests, and practical boundary decisions.

### Query Templates
```python
# deep_research
"Best practices for deciding what to mock vs real implementations in TypeScript backend
with PostgreSQL, Redis, and three external APIs. 400+ mocks but bugs reach production.
Mockist vs classicist consensus? When to use testcontainers vs mock DB? Contract testing
for external APIs? Testing trophy for our architecture?"

# search_google
keywords = ["when to mock vs integration test backend service 2025",
            "testcontainers vs mock database testing strategy",
            "Martin Fowler mocks stubs fakes test doubles"]
```

### Best Practices
- **Attach your actual test files** -- mocking advice is useless without seeing current patterns.
- Describe your **architecture** (hexagonal, layered, microservices) -- mock boundaries depend on it.
- Ask about **anti-patterns explicitly**: "What are we probably doing wrong?" yields more actionable advice.
- Separate language-specific questions -- Rust mocking (trait-based) is fundamentally different from JavaScript (monkey-patching).
- Include your pain points: "tests pass but bugs reach production" gives concrete problems to solve.
- Decision framework: mock at **architectural boundaries** (HTTP client interface, not axios directly).

---

## 03. End-to-End Testing Setup

### Recommended Tools
- **deep_research**: Integrated E2E strategy covering framework selection, CI pipeline design, flakiness reduction, and test organization as one coherent plan.
- **search_google**: Official CI integration guides, flakiness reduction articles, and framework benchmarks.
- **search_reddit**: Real flakiness struggles, CI configuration problems, and team adoption experiences.

### Query Templates
```python
# deep_research (use 2 questions)
"Q1: Complete E2E testing strategy for React SPA with 15 critical flows on GitHub Actions.
Playwright test structure (page objects vs fixtures)? Optimal CI config for parallel execution?
OAuth login handling in E2E? Flakiness prevention from day one? ROI inflection point?"
"Q2: Reduce E2E test flakiness from 25% to under 5%. Top 5 flakiness causes in Playwright?
Test data isolation (factory vs seeded DB vs API setup)? Retry vs auto-wait patterns?
Automatic flaky test detection and quarantine in CI?"

# search_google
keywords = ["playwright vs cypress vs selenium 2025 comparison benchmark",
            "reduce e2e test flakiness playwright best practices"]
```

### Best Practices
- **Describe your app's features** -- OAuth, WebSockets, file uploads each need specific E2E patterns.
- Mention your CI provider -- GitHub Actions, GitLab CI, CircleCI have different optimal Playwright configs.
- Include your current flake rate if reducing flakiness -- calibrates aggressiveness of changes.
- Search for "flaky" and "flakiness" explicitly -- the dominant pain point with the most dedicated content.
- Ask about **test organization separately** from framework selection.
- Key pattern: test data isolation per test prevents the majority of flaky failures.

---

## 04. Load & Stress Testing

### Recommended Tools
- **deep_research**: Methodology design (scenario types), result interpretation framework, and bottleneck isolation techniques.
- **search_google**: Official tool documentation (k6, Locust, Gatling), distributed execution guides, and visualization integrations.
- **search_reddit**: Real load testing stories with diagnostic processes and before/after metrics.

### Query Templates
```python
# deep_research (use 2 questions)
"Q1: Load testing strategy for 12 microservices (REST + gRPC, PostgreSQL + Redis, Kubernetes).
Tool for mixed REST+gRPC? Scenario design (ramp, sustained, spike, soak). Metrics beyond
latency. Bottleneck isolation across 12 services. Realistic zero-to-ready timeline."
"Q2: Interpreting load test results. p50=45ms, p95=120ms, p99=890ms at 2000 VUs, error rate
jumps to 5%. What does large p95-p99 gap indicate? Correlating k6 results with server metrics?
Most common bottlenecks at 2000+ concurrent? Targeted tests to isolate DB vs network vs compute?"

# search_google
keywords = ["k6 vs locust vs gatling vs artillery comparison 2025",
            "interpreting load test results percentile latency throughput"]
```

### Best Practices
- Include your **actual metrics** ("p50=45ms, p99=890ms at 2000 VUs") for specific analysis.
- Describe your architecture -- microservices, databases, caches all affect bottleneck location.
- Ask about **interpretation separately from tool selection** -- different expertise.
- Specify your target metrics ("10K users, p99 < 200ms") to focus on strategies hitting specific goals.
- Four scenario types to design: **ramp-up** (find breaking point), **sustained** (steady state), **spike** (burst handling), **soak** (memory leaks, connection exhaustion).

---

## 05. Property-Based Testing

### Recommended Tools
- **deep_research**: Property pattern taxonomy (round-trip, invariant, oracle, metamorphic), generator design principles, and adoption strategy.
- **search_google**: Library documentation (fast-check, proptest), pattern catalogs, and real-world case studies.
- **search_reddit**: Adoption experiences, practical benefits vs example-based tests, and domain-specific property examples.

### Query Templates
```python
# deep_research (use 2 questions)
"Q1: Practical guide to adopting property-based testing in TypeScript + Rust. Most common
property patterns (round-trip, invariant, oracle, metamorphic)? Which functions benefit most
from PBT? Generator design for domain types (email, URL, JSON)? Shrinking mechanics?
Realistic test runtime expectations?"
"Q2: Advanced proptest in Rust: custom strategies, stateful testing, type system integration.
Stateful property testing (command sequences). Custom strategies for complex domain types.
Shrinking control for meaningful minimal examples. CI integration and regression files."

# search_google
keywords = ["property based testing patterns round trip invariant oracle",
            "fast-check advanced generators domain specific types"]
```

### Best Practices
- Include your **domain** ("parser, serializer, validator") for domain-specific property pattern suggestions.
- Separate the "what is PBT" conceptual question from "how to use proptest/fast-check" practical question.
- Ask about **property patterns explicitly** -- formulating good properties is the hardest part.
- Mention your language -- fast-check (TS) and proptest (Rust) have very different APIs and idioms.
- Search for "real world examples" or "production" alongside PBT to filter out toy demonstrations.
- Five core property patterns to learn:
  1. **Round-trip**: encode then decode returns original (`deserialize(serialize(x)) == x`)
  2. **Invariant**: property always holds (`sorted list is always non-decreasing`)
  3. **Oracle**: compare with trusted reference implementation
  4. **Metamorphic**: related inputs produce related outputs
  5. **Idempotent**: applying operation twice equals applying once

## Steering notes

1. **Weight 6+ month experience** over new-project enthusiasm in framework comparisons.
2. **GitHub for real configs:** `site:github.com jest.config` or `vitest.config`.
3. **r/ExperiencedDevs** for senior testing philosophy.
4. **"What not to test"** is valuable: `"over-testing"`, `"test maintenance burden"`.
5. **Chaos/contract/mutation testing:** research these for resilience, API contracts, and test quality assessment.
