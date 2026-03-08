# 11 — Resilience Patterns

**Patterns for building systems that survive and recover from failures in distributed environments.**

---

## Why Resilience Matters

Distributed systems fail. Networks partition, servers crash, disks fill up, dependencies slow down. The question is not *if* your system will encounter failure, but *how* it will behave when failure occurs. Resilience patterns do not prevent failure — they contain it, limit its blast radius, and enable recovery.

## Pattern Index

| Pattern | Summary | Primary Failure Mode |
|---|---|---|
| [Circuit Breaker](./circuit-breaker.md) | Stop calling a failing dependency to prevent cascade | Dependency outage / slowdown |
| [Bulkhead](./bulkhead.md) | Isolate resources so one failure cannot exhaust shared pools | Resource exhaustion / noisy neighbor |
| [Retry with Backoff](./retry-with-backoff.md) | Retry transient failures with increasing delays and jitter | Transient / intermittent errors |
| [Timeout Patterns](./timeout-patterns.md) | Bound the duration of every external call | Slow / hanging dependencies |
| [Graceful Degradation](./graceful-degradation.md) | Serve reduced functionality instead of failing entirely | Partial system failure |
| [Chaos Engineering](./chaos-engineering.md) | Proactively inject failures to validate resilience | Unknown failure modes |
| [Idempotency Patterns](./idempotency-patterns.md) | Ensure repeated operations produce the same result | Duplicate requests / retries |
| [Let It Crash](./let-it-crash.md) | Let processes fail; rely on supervisors to restart cleanly | Corrupted process state |

## Decision Matrix: Which Pattern for Which Failure?

Use this matrix to select the right pattern based on the failure mode you are defending against.

```
FAILURE MODE                          RECOMMENDED PATTERNS
─────────────────────────────────────────────────────────────────────
Dependency is completely down       → Circuit Breaker + Graceful Degradation
Dependency is intermittently slow   → Timeout + Retry with Backoff
Dependency is consistently slow     → Timeout + Circuit Breaker + Bulkhead
Shared resources exhausted          → Bulkhead + Circuit Breaker
Duplicate requests from retries     → Idempotency Patterns
Process has corrupted state         → Let It Crash (supervisor restart)
Partial system failure              → Graceful Degradation + Bulkhead
Unknown / untested failure modes    → Chaos Engineering
Network partition                   → Timeout + Retry + Idempotency
Thundering herd after recovery      → Retry with Backoff (jitter) + Circuit Breaker (half-open)
```

## How Patterns Combine

These patterns are not mutually exclusive. In practice, a robust system layers them:

```
User Request
  │
  ├─ Timeout (overall request deadline: 5s)
  │    │
  │    ├─ Bulkhead (max 20 concurrent calls to payment service)
  │    │    │
  │    │    ├─ Circuit Breaker (trip after 5 failures in 60s)
  │    │    │    │
  │    │    │    ├─ Retry with Backoff (3 retries, full jitter)
  │    │    │    │    │
  │    │    │    │    └─ Actual HTTP call (with idempotency key)
  │    │    │    │
  │    │    │    └─ [OPEN] → Return cached/fallback response
  │    │    │
  │    │    └─ [FULL] → Reject with 503
  │    │
  │    └─ [EXPIRED] → Return partial response (graceful degradation)
  │
  └─ Response (possibly degraded)
```

## Implementation Priority

If you are starting from zero, implement these patterns in this order:

1. **Timeouts** — the single most impactful pattern. Without timeouts, nothing else works.
2. **Retries with backoff and jitter** — handles the most common failure mode (transient errors).
3. **Circuit breakers** — prevents cascading failures when transient becomes persistent.
4. **Idempotency** — makes retries safe, especially for write operations.
5. **Bulkheads** — isolates failures between independent dependencies.
6. **Graceful degradation** — improves user experience during partial failures.
7. **Let it crash** — for long-running processes and worker systems.
8. **Chaos engineering** — validates everything above actually works.

## Key Libraries (TypeScript/Node.js)

| Library | Patterns Covered |
|---|---|
| [cockatiel](https://github.com/connor4312/cockatiel) | Circuit breaker, retry, timeout, bulkhead |
| [opossum](https://github.com/nodeshift/opossum) | Circuit breaker |
| [p-retry](https://github.com/sindresorhus/p-retry) | Retry with backoff |
| [p-limit](https://github.com/sindresorhus/p-limit) | Concurrency limiting (semaphore bulkhead) |
| [p-timeout](https://github.com/sindresorhus/p-timeout) | Timeouts |

## Further Reading

- *Release It!* by Michael Nygard — the canonical reference for resilience patterns
- *Designing Data-Intensive Applications* by Martin Kleppmann — distributed systems fundamentals
- [AWS Builder's Library](https://aws.amazon.com/builders-library/) — production-tested resilience strategies
- [Google SRE Book](https://sre.google/sre-book/table-of-contents/) — site reliability engineering practices
- [Microsoft Azure Architecture Patterns](https://learn.microsoft.com/en-us/azure/architecture/patterns/) — cloud-native resilience patterns
