# Retry with Backoff

**Automatically retry failed operations with increasing delays to handle transient failures without overwhelming the target.**

---

## Origin / History

Retry with exponential backoff originated in early Ethernet networking (the ALOHA protocol and later Ethernet's CSMA/CD), where colliding stations needed to wait random, increasing durations before retransmitting. The pattern was formalized in networking RFCs and later adopted wholesale by distributed systems. AWS's architecture blog popularized the addition of jitter in 2015, demonstrating how correlated retries create thundering herds. Today every major cloud SDK (AWS SDK, Google Cloud Client, Azure SDK) implements retry with jitter by default.

## The Problem It Solves

Transient failures are the norm in distributed systems: a network packet drops, a server briefly overloads, a database connection pool is momentarily exhausted. These failures resolve themselves within seconds. A single immediate retry often succeeds. But naive retry strategies create two catastrophic problems:

First, **retry storms**: if 1,000 clients all retry at the same instant, the server receives 2,000 requests instead of 1,000 — making the overload worse. Second, **resource waste**: retrying without delay ties up client resources (connections, threads, memory) while the server has no time to recover.

## The Principle Explained

Retry with exponential backoff spaces retries further and further apart: 1s, 2s, 4s, 8s, and so on. This gives the failing service time to recover and reduces the load during failure. But exponential backoff alone is not sufficient. If all clients start at the same time and use the same backoff schedule, they all retry at the same time — the thundering herd problem.

**Jitter** solves this by adding randomness to the delay. Full jitter picks a random delay between 0 and the exponential backoff value. Decorrelated jitter uses the previous delay to calculate the next one. AWS's research showed that full jitter provides the best trade-off between total completion time and server load.

A **retry budget** (also called a retry ratio) caps the total number of retries across all requests. Instead of "retry each request 3 times," you say "retry at most 10% of requests." This prevents the entire system from entering a retry spiral during widespread failures.

## Code Examples

### GOOD: Exponential backoff with jitter and retry budget

```typescript
interface RetryOptions {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitter: "full" | "decorrelated" | "none";
  retryableErrors?: (error: unknown) => boolean;
}

class RetryBudget {
  private attempts = 0;
  private retries = 0;
  private readonly window: number[] = [];

  constructor(
    private readonly maxRetryRatio: number,
    private readonly windowMs: number
  ) {}

  recordAttempt(): void {
    this.cleanup();
    this.attempts++;
    this.window.push(Date.now());
  }

  canRetry(): boolean {
    this.cleanup();
    if (this.attempts === 0) return true;
    return this.retries / this.attempts < this.maxRetryRatio;
  }

  recordRetry(): void {
    this.retries++;
  }

  private cleanup(): void {
    const cutoff = Date.now() - this.windowMs;
    while (this.window.length > 0 && this.window[0] < cutoff) {
      this.window.shift();
      this.attempts = Math.max(0, this.attempts - 1);
    }
  }
}

async function retryWithBackoff<T>(
  action: () => Promise<T>,
  options: RetryOptions,
  budget?: RetryBudget
): Promise<T> {
  const { maxRetries, baseDelayMs, maxDelayMs, jitter } = options;
  const isRetryable = options.retryableErrors ?? (() => true);

  let lastDelay = baseDelayMs;
  budget?.recordAttempt();

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await action();
    } catch (error) {
      const isLastAttempt = attempt === maxRetries;
      if (isLastAttempt || !isRetryable(error)) throw error;

      if (budget && !budget.canRetry()) {
        throw new RetryBudgetExhaustedError("Retry budget exceeded");
      }
      budget?.recordRetry();

      const delay = calculateDelay(attempt, baseDelayMs, maxDelayMs, jitter, lastDelay);
      lastDelay = delay;

      console.warn(
        `Attempt ${attempt + 1} failed. Retrying in ${delay}ms...`,
        error instanceof Error ? error.message : error
      );

      await sleep(delay);
    }
  }

  throw new Error("Unreachable");
}

function calculateDelay(
  attempt: number,
  baseMs: number,
  maxMs: number,
  jitter: "full" | "decorrelated" | "none",
  lastDelay: number
): number {
  const exponential = Math.min(maxMs, baseMs * Math.pow(2, attempt));

  switch (jitter) {
    case "none":
      return exponential;
    case "full":
      return Math.random() * exponential;
    case "decorrelated":
      return Math.min(maxMs, Math.random() * (lastDelay * 3 - baseMs) + baseMs);
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

class RetryBudgetExhaustedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "RetryBudgetExhaustedError";
  }
}

// Usage: retry transient HTTP errors with a shared budget
const httpRetryBudget = new RetryBudget(0.1, 60_000); // max 10% retries per minute

async function fetchUserProfile(userId: string): Promise<UserProfile> {
  return retryWithBackoff(
    async () => {
      const res = await fetch(`/api/users/${userId}`);
      if (res.status === 503 || res.status === 429) {
        throw new TransientError(`HTTP ${res.status}`);
      }
      if (!res.ok) throw new PermanentError(`HTTP ${res.status}`);
      return res.json();
    },
    {
      maxRetries: 3,
      baseDelayMs: 500,
      maxDelayMs: 10_000,
      jitter: "full",
      retryableErrors: (err) => err instanceof TransientError,
    },
    httpRetryBudget
  );
}
```

### BAD: Immediate retries in a tight loop — the thundering herd creator

```typescript
// This function creates a thundering herd:
// - No delay between retries
// - No jitter (all clients retry at the same instant)
// - Retries on ALL errors, including 400 Bad Request
// - No retry budget (infinite retries per request during outage)
async function fetchUserProfile(userId: string): Promise<UserProfile> {
  const MAX_RETRIES = 5;
  for (let i = 0; i < MAX_RETRIES; i++) {
    try {
      const res = await fetch(`/api/users/${userId}`);
      return await res.json();
    } catch {
      // Retry immediately. No delay. No discrimination.
      // If 10,000 clients all fail at the same time, the server
      // receives 50,000 rapid-fire requests.
      console.log(`Retry ${i + 1}...`);
    }
  }
  throw new Error("Failed after retries");
}
```

## Alternatives & Related Approaches

| Approach | When to prefer it |
|---|---|
| **Circuit breaker** | When the failure is persistent, not transient. Stop retrying entirely. |
| **Dead letter queues** | When failed operations can be retried later by a background process |
| **Compensating transactions** | When you need to undo partially completed work rather than retry |
| **Hedged requests** | When latency matters more than load — send parallel requests to multiple replicas |
| **Polling with backoff** | When you are waiting for a state change rather than retrying a failure |

## When NOT to Apply

- **Non-transient errors:** A 400 Bad Request or 401 Unauthorized will never succeed on retry. Distinguish retryable from non-retryable errors.
- **Non-idempotent operations without idempotency keys:** Retrying a payment charge without an idempotency key can result in double charges.
- **Real-time user interactions:** A user clicking "submit" should not wait 30 seconds through exponential backoff. Show an error and let them decide.
- **When the failure is in your own process:** Retrying a null pointer exception is pointless.

## Tensions & Trade-offs

- **Retry count vs. user experience:** More retries increase the chance of eventual success but also increase latency. Three retries with exponential backoff can take 15+ seconds.
- **Jitter reduces thundering herds but increases average latency.** Full jitter can produce very short delays that are essentially wasted retries.
- **Retry budgets require shared state** (or at least per-instance state). In serverless environments where each invocation is isolated, a retry budget cannot span requests.
- **Retries amplify load.** Even with backoff, retrying 3 times means the server receives up to 4x the normal load during partial failures. Retry budgets mitigate this but do not eliminate it.

## Real-World Consequences

AWS documented the thundering herd problem in their Builder's Library, showing that during a 2015 incident, a recovering service was kept down for hours because all clients retried at the same exponential intervals without jitter. Adding full jitter to the AWS SDK reduced retry storm load by over 75%.

Stripe processes millions of API calls daily. Their webhook retry system uses exponential backoff over hours (not seconds) — retrying failed webhook deliveries at 1 minute, 5 minutes, 30 minutes, 2 hours, and so on for up to 3 days. This matches the backoff duration to the expected recovery time.

## Further Reading

- [AWS Architecture Blog: Exponential Backoff and Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [Google Cloud: Retry Strategy](https://cloud.google.com/storage/docs/retry-strategy)
- [Marc Brooker: Jitter (AWS Builder's Library)](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
- *Release It!* by Michael Nygard — retry discussion in stability patterns
