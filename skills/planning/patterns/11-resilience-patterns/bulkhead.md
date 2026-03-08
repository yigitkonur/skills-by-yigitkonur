# Bulkhead

**Isolate resources so that a failure in one area cannot drain resources from another.**

---

## Origin / History

The bulkhead pattern takes its name from the watertight compartments in ship hulls. When the RMS Titanic struck an iceberg in 1912, water flooded six compartments — one more than the ship was designed to survive. The bulkheads were not tall enough; water spilled over the tops from one compartment to the next. The engineering lesson is clear: isolation only works if the boundaries are truly sealed. In software, Michael Nygard popularized the pattern in *Release It!* (2007), and it became a core feature of Netflix Hystrix's thread pool isolation.

## The Problem It Solves

In a typical application server, all requests share the same thread pool, connection pool, and memory. If one downstream dependency becomes slow, requests to it consume threads while waiting. Eventually the shared pool is exhausted, and even requests to perfectly healthy endpoints are rejected — not because those endpoints are broken, but because a different dependency stole all the resources. This is the software equivalent of water flooding from one compartment to the next.

## The Principle Explained

The bulkhead pattern partitions resources into isolated pools. Each downstream dependency (or group of related operations) gets its own limited set of resources. When one pool is exhausted, only the operations that depend on that pool are affected. Everything else continues operating normally.

There are three common isolation strategies. **Thread pool isolation** gives each dependency its own thread pool with a fixed size. This is the strongest form of isolation but adds overhead from context switching and thread management. **Semaphore isolation** uses counting semaphores to limit concurrent access without dedicated threads — lighter weight but without timeout protection on individual calls. **Process isolation** runs different workloads in separate processes or containers, providing OS-level resource boundaries. Microservice architecture is, in a sense, a bulkhead pattern applied at the deployment level.

The critical design decision is sizing the pools. Too large and the bulkhead provides no real protection. Too small and you artificially throttle healthy operations. The right size depends on the expected concurrency, the acceptable queuing delay, and the failure characteristics of each dependency.

## Code Examples

### GOOD: Semaphore-based bulkhead with per-dependency isolation

```typescript
class Bulkhead {
  private active = 0;
  private readonly queue: Array<{
    resolve: () => void;
    reject: (err: Error) => void;
    timer: ReturnType<typeof setTimeout>;
  }> = [];

  constructor(
    private readonly name: string,
    private readonly maxConcurrent: number,
    private readonly maxQueue: number,
    private readonly queueTimeoutMs: number
  ) {}

  async execute<T>(action: () => Promise<T>): Promise<T> {
    if (this.active < this.maxConcurrent) {
      return this.run(action);
    }

    if (this.queue.length >= this.maxQueue) {
      throw new BulkheadRejectedError(
        `${this.name}: max concurrent (${this.maxConcurrent}) and queue (${this.maxQueue}) both full`
      );
    }

    await this.waitForSlot();
    return this.run(action);
  }

  private async run<T>(action: () => Promise<T>): Promise<T> {
    this.active++;
    try {
      return await action();
    } finally {
      this.active--;
      this.dequeueNext();
    }
  }

  private waitForSlot(): Promise<void> {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        const idx = this.queue.findIndex((item) => item.resolve === resolve);
        if (idx !== -1) this.queue.splice(idx, 1);
        reject(new BulkheadRejectedError(`${this.name}: queue timeout after ${this.queueTimeoutMs}ms`));
      }, this.queueTimeoutMs);

      this.queue.push({ resolve, reject, timer });
    });
  }

  private dequeueNext(): void {
    const next = this.queue.shift();
    if (next) {
      clearTimeout(next.timer);
      next.resolve();
    }
  }

  getMetrics() {
    return {
      name: this.name,
      active: this.active,
      queued: this.queue.length,
      availableSlots: Math.max(0, this.maxConcurrent - this.active),
    };
  }
}

class BulkheadRejectedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "BulkheadRejectedError";
  }
}

// Each dependency gets its own isolated pool
const bulkheads = {
  paymentGateway: new Bulkhead("payment-gateway", 10, 5, 2000),
  inventoryService: new Bulkhead("inventory-service", 20, 10, 1000),
  emailService: new Bulkhead("email-service", 5, 50, 5000),
};

// Payment gateway being slow does NOT affect inventory lookups
async function processOrder(order: Order): Promise<void> {
  const [payment, stock] = await Promise.all([
    bulkheads.paymentGateway.execute(() => chargeCustomer(order)),
    bulkheads.inventoryService.execute(() => reserveStock(order.items)),
  ]);

  // Email is fire-and-forget with its own pool
  bulkheads.emailService
    .execute(() => sendConfirmation(order))
    .catch((err) => logger.warn("Email bulkhead rejected", err));
}
```

### BAD: Shared resource pool — one slow dependency kills everything

```typescript
// All HTTP calls share the same connection pool (typically the default).
// If the payment gateway starts responding in 25 seconds instead of 200ms,
// all 50 connections fill up waiting for payment responses.
// Now inventory checks, email sends, and health checks all fail.

import axios from "axios";

// Single global instance — no isolation whatsoever
const httpClient = axios.create({
  timeout: 30_000,
  maxSockets: 50, // Shared across ALL downstream services
});

async function processOrder(order: Order): Promise<void> {
  // Both calls compete for the same 50 sockets
  const payment = await httpClient.post("https://payments.slow.com/charge", order);
  const stock = await httpClient.post("https://inventory.healthy.com/reserve", order.items);
  await httpClient.post("https://email.healthy.com/send", { orderId: order.id });
}
```

## Alternatives & Related Approaches

| Approach | When to prefer it |
|---|---|
| **Circuit breaker** | When you want to stop calling a failing dependency entirely rather than just limiting concurrency |
| **Rate limiting** | When the concern is protecting the downstream service from overload, not isolating the caller |
| **Process/container isolation** | When you need OS-level guarantees (memory limits, CPU quotas) — stronger than in-process bulkheads |
| **Queue-based decoupling** | When work can be deferred and processed asynchronously |

Bulkheads and circuit breakers are complementary. The bulkhead limits how many resources a dependency can consume. The circuit breaker stops calling the dependency when it is clearly broken. Use both.

## When NOT to Apply

- **Simple applications with a single dependency** — the overhead of multiple pools adds complexity for no benefit.
- **CPU-bound workloads** — bulkheads help with I/O-bound waiting (network, disk), not with CPU contention. Use worker threads or process-level isolation for CPU work.
- **When all dependencies share a fate** — if service A and service B both hit the same database, separate bulkheads give a false sense of isolation.
- **Serverless functions** — each invocation is already isolated by the platform. Bulkheads within a single function execution are meaningless.

## Tensions & Trade-offs

- **Pool sizing is hard.** Under-provision and you reject valid requests. Over-provision and you defeat the purpose of isolation. Adaptive sizing (adjusting based on latency and error rates) helps but adds complexity.
- **Thread pool isolation vs. semaphore isolation:** Thread pools provide timeout protection per call but waste memory on idle threads. Semaphores are lightweight but cannot enforce per-call timeouts. Node.js/TypeScript applications typically use semaphore-style isolation since they are single-threaded with async I/O.
- **Total resource budget:** The sum of all bulkhead sizes must not exceed the system's capacity. If you have 10 bulkheads of 20 concurrent each, you need to handle 200 concurrent connections at full load.
- **Observability overhead:** Each bulkhead needs its own metrics (active count, queue depth, rejection rate). Without dashboards, teams cannot tune pool sizes.

## Real-World Consequences

Netflix used Hystrix thread pool isolation in production for years. When their recommendation service degraded, only recommendation-related requests queued up. The homepage still loaded (without recommendations), search still worked, and playback was unaffected. This is the bulkhead pattern working exactly as intended.

Amazon's architecture takes bulkheading to the organizational level: each service team owns its own infrastructure. A failure in the retail product catalog does not affect AWS S3 because they share nothing — not even the same AWS accounts.

## Further Reading

- *Release It!* by Michael Nygard — Chapter 5: Stability Patterns
- [Microsoft: Bulkhead Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead)
- [resilience4j: Bulkhead](https://resilience4j.readme.io/docs/bulkhead)
- [Netflix Hystrix: How It Works (Thread Pools)](https://github.com/Netflix/Hystrix/wiki/How-it-Works#isolation)
