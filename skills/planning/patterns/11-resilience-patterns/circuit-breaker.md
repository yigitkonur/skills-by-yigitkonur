# Circuit Breaker

**Prevent cascading failures by failing fast when a downstream dependency is unhealthy.**

---

## Origin / History

Michael Nygard introduced the Circuit Breaker pattern in his 2007 book *Release It!*, drawing an analogy from electrical circuit breakers that trip to prevent house fires. The pattern gained massive adoption through Netflix's Hystrix library (2012), which brought resilience engineering into mainstream microservice architecture. Today it lives in libraries like Polly (.NET), resilience4j (Java), opossum (Node.js), and cockatiel (TypeScript).

## The Problem It Solves

When a downstream service becomes slow or unavailable, callers pile up waiting for responses. Each waiting request holds a thread, a connection, and memory. Within seconds, the caller itself becomes unresponsive — not because it is broken, but because it is waiting on something broken. This cascade propagates upstream until the entire system collapses. A single failing database can take down dozens of services that have nothing to do with each other.

## The Principle Explained

A circuit breaker wraps calls to an external dependency and monitors failures. It operates in three states:

**Closed (normal operation):** Requests flow through. The breaker counts consecutive failures or failures within a time window. Everything works as if the breaker is not there.

**Open (tripped):** Once failures exceed a configured threshold, the breaker trips open. All subsequent calls fail immediately with a known error — no network call is made. This protects the caller from wasting resources and gives the downstream service breathing room to recover. The breaker stays open for a configured timeout period.

**Half-Open (probing):** After the timeout expires, the breaker allows a single probe request through. If it succeeds, the breaker resets to Closed. If it fails, the breaker returns to Open and the timeout resets. Some implementations allow a configurable number of probe requests rather than just one.

The key insight is that failing fast is better than failing slow. A 5ms rejection is infinitely better than a 30-second timeout when you know the dependency is down.

## Code Examples

### GOOD: Well-configured circuit breaker with monitoring

```typescript
interface CircuitBreakerOptions {
  failureThreshold: number;
  resetTimeoutMs: number;
  halfOpenMaxAttempts: number;
  monitoringWindow: number;
}

type CircuitState = "closed" | "open" | "half-open";

class CircuitBreaker<T> {
  private state: CircuitState = "closed";
  private failureCount = 0;
  private lastFailureTime = 0;
  private halfOpenAttempts = 0;
  private successCount = 0;

  constructor(
    private readonly action: () => Promise<T>,
    private readonly options: CircuitBreakerOptions,
    private readonly onStateChange?: (from: CircuitState, to: CircuitState) => void
  ) {}

  async execute(): Promise<T> {
    if (this.state === "open") {
      if (Date.now() - this.lastFailureTime >= this.options.resetTimeoutMs) {
        this.transitionTo("half-open");
      } else {
        throw new CircuitOpenError(
          `Circuit is open. Retry after ${this.remainingCooldownMs()}ms`
        );
      }
    }

    if (this.state === "half-open" && this.halfOpenAttempts >= this.options.halfOpenMaxAttempts) {
      throw new CircuitOpenError("Half-open probe limit reached");
    }

    try {
      const result = await this.action();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    if (this.state === "half-open") {
      this.successCount++;
      if (this.successCount >= this.options.halfOpenMaxAttempts) {
        this.transitionTo("closed");
      }
    }
    this.failureCount = 0;
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.state === "half-open") {
      this.transitionTo("open");
    } else if (this.failureCount >= this.options.failureThreshold) {
      this.transitionTo("open");
    }
  }

  private transitionTo(newState: CircuitState): void {
    const oldState = this.state;
    this.state = newState;
    this.halfOpenAttempts = 0;
    this.successCount = 0;
    if (newState === "closed") this.failureCount = 0;
    this.onStateChange?.(oldState, newState);
  }

  private remainingCooldownMs(): number {
    return Math.max(
      0,
      this.options.resetTimeoutMs - (Date.now() - this.lastFailureTime)
    );
  }
}

class CircuitOpenError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CircuitOpenError";
  }
}

// Usage with monitoring
const paymentBreaker = new CircuitBreaker(
  () => paymentGateway.charge(order),
  {
    failureThreshold: 5,
    resetTimeoutMs: 30_000,
    halfOpenMaxAttempts: 3,
    monitoringWindow: 60_000,
  },
  (from, to) => {
    metrics.recordStateChange("payment-gateway", from, to);
    if (to === "open") {
      alerting.notify(`Payment gateway circuit opened after failures`);
    }
  }
);
```

### BAD: No protection — cascading failure waiting to happen

```typescript
// Every request blocks for up to 30 seconds when the service is down.
// 100 concurrent requests = 100 threads/connections held hostage.
async function chargePayment(order: Order): Promise<PaymentResult> {
  try {
    const response = await fetch("https://payments.example.com/charge", {
      method: "POST",
      body: JSON.stringify(order),
      // 30-second timeout is generous... and deadly
    });
    return response.json();
  } catch (error) {
    // Log and rethrow — the next caller will try again and wait 30 seconds too
    console.error("Payment failed:", error);
    throw error;
  }
}
```

## Alternatives & Related Approaches

| Approach | When to prefer it |
|---|---|
| **Retry-only** | Transient failures with quick recovery (DNS blips, momentary overload) |
| **Bulkhead** | Isolate failures to prevent resource exhaustion across unrelated calls |
| **Queue-based load leveling** | When the downstream can catch up if given time; requests can be deferred |
| **Timeout + fallback** | Simpler cases where you have a reasonable default/cached response |

Circuit breakers combine well with all of the above. Retry inside the closed state, bulkhead to limit concurrent calls, timeout to bound individual attempts.

## When NOT to Apply

- **In-process function calls** that cannot fail independently (no network boundary).
- **Fire-and-forget operations** where you do not need a response.
- **Batch processing** where you control the pace and can handle individual item failures.
- **When the "dependency" is a local cache or in-memory store** — the overhead is not worth it.
- **When you have no fallback behavior** — tripping the breaker just gives users a different error message, not a better experience.

## Tensions & Trade-offs

- **Sensitivity vs. stability:** A low failure threshold trips the breaker quickly (protecting resources) but may trip on transient blips. A high threshold tolerates more failures but delays protection. There is no universal right answer.
- **Timeout duration:** Too short and you never give the dependency time to recover. Too long and you waste time in the open state after the dependency has healed.
- **Shared vs. per-instance breakers:** A shared breaker (via a distributed store) prevents all instances from hammering a recovering service. A per-instance breaker is simpler but means N instances still send N probe requests.
- **Monitoring cost:** Circuit breakers produce state-change events that need dashboards, alerts, and runbooks. Without observability, a tripped breaker is invisible.

## Real-World Consequences

Netflix discovered that a single failing dependency could take out their entire API gateway. Hystrix circuit breakers allowed them to serve degraded but functional pages (missing recommendations, missing ratings) instead of a full outage. When they open-sourced Hystrix, it became the canonical implementation and influenced every resilience library that followed.

AWS's 2017 S3 outage cascaded across services because health-check systems depended on S3 — a circular dependency that no circuit breaker could fix. The lesson: circuit breakers help, but they cannot save you from architectural dependency loops.

## Further Reading

- *Release It!* by Michael Nygard — the original source
- [Martin Fowler: Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Microsoft: Circuit Breaker Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)
- [resilience4j documentation](https://resilience4j.readme.io/docs/circuitbreaker)
- [Netflix Hystrix Wiki (archived)](https://github.com/Netflix/Hystrix/wiki)
