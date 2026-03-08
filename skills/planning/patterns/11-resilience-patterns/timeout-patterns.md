# Timeout Patterns

**Bound the duration of every external call to prevent indefinite blocking and resource exhaustion.**

---

## Origin / History

Timeouts are as old as networking itself. TCP's retransmission timeout (RTO) dates to the original 1981 RFC 793. In application development, timeouts became critical as systems moved from monolithic to distributed architectures. The shift to microservices in the 2010s exposed a new problem: timeout propagation. A single user request might traverse 5-10 services, and without coordinated timeout budgets, individual service timeouts compound into user-visible delays of minutes. Google's gRPC framework popularized deadline propagation, where the original caller's deadline flows through every downstream hop.

## The Problem It Solves

Without timeouts, a slow or unresponsive dependency causes the caller to wait indefinitely. Each waiting request holds resources: a network connection, memory for the pending response, possibly a thread or goroutine. Under load, the system runs out of resources and cannot serve any requests — even those to healthy endpoints. Timeouts are the single most important resilience mechanism because they transform unknown-duration failures into bounded-duration failures.

## The Principle Explained

There are several layers of timeout that must work together:

**Connection timeout** bounds how long you wait to establish a TCP connection. If a server is completely unreachable, you learn within seconds instead of minutes. Typical values: 1-5 seconds.

**Read/response timeout** (also called socket timeout) bounds how long you wait for data after the connection is established. A server might accept the connection but hang during processing. Typical values: 5-30 seconds depending on the operation.

**Overall request timeout** caps the total duration of a logical operation, including retries, redirects, and DNS resolution. This is the timeout users care about. It should be shorter than the sum of connection timeout plus read timeout plus retry delays.

**Deadline propagation** is the advanced pattern for microservices. Instead of each service setting its own independent timeout, the originating request carries a deadline. Each service in the chain subtracts its own processing time and passes the remaining budget downstream. If the budget is exhausted at any point, the call fails immediately. This prevents a common pathology: service A waits 10s for B, B waits 10s for C, C waits 10s for D — the user waits 30s total, even though A's timeout was "only" 10s.

## Code Examples

### GOOD: Layered timeouts with deadline propagation

```typescript
interface RequestContext {
  deadlineMs: number; // absolute time by which this request must complete
  traceId: string;
}

function remainingBudgetMs(ctx: RequestContext): number {
  return Math.max(0, ctx.deadlineMs - Date.now());
}

function childContext(ctx: RequestContext, reserveMs: number): RequestContext {
  return {
    ...ctx,
    deadlineMs: Math.min(ctx.deadlineMs, Date.now() + remainingBudgetMs(ctx) - reserveMs),
  };
}

async function fetchWithTimeout<T>(
  url: string,
  options: RequestInit,
  ctx: RequestContext
): Promise<T> {
  const remaining = remainingBudgetMs(ctx);
  if (remaining <= 0) {
    throw new DeadlineExceededError(`No time budget remaining for ${url}`);
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), remaining);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        ...options.headers,
        "x-deadline-ms": String(ctx.deadlineMs),
        "x-trace-id": ctx.traceId,
      },
    });

    if (!response.ok) {
      throw new HttpError(response.status, `HTTP ${response.status} from ${url}`);
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new DeadlineExceededError(
        `Request to ${url} timed out after ${remaining}ms`
      );
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

class DeadlineExceededError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DeadlineExceededError";
  }
}

class HttpError extends Error {
  constructor(
    public readonly status: number,
    message: string
  ) {
    super(message);
    this.name = "HttpError";
  }
}

// API gateway sets the top-level deadline
async function handleUserRequest(req: IncomingRequest): Promise<Response> {
  const ctx: RequestContext = {
    deadlineMs: Date.now() + 5000, // 5 second budget for the entire request
    traceId: generateTraceId(),
  };

  // Reserve 200ms for our own processing/serialization
  const downstreamCtx = childContext(ctx, 200);

  const [user, recommendations] = await Promise.allSettled([
    fetchWithTimeout<User>("/user-service/profile", {}, downstreamCtx),
    fetchWithTimeout<Recommendation[]>("/rec-service/for-user", {}, downstreamCtx),
  ]);

  // Degrade gracefully: recommendations are optional
  return buildResponse(
    user.status === "fulfilled" ? user.value : null,
    recommendations.status === "fulfilled" ? recommendations.value : []
  );
}
```

### BAD: No timeouts — blocking forever

```typescript
// No connection timeout, no read timeout, no overall timeout.
// If the user service hangs, this function hangs forever.
// If the database connection pool is exhausted, fetch blocks
// indefinitely waiting for a connection.
async function handleUserRequest(req: IncomingRequest): Promise<Response> {
  // fetch has no default timeout in Node.js before v22
  const user = await fetch("/user-service/profile");
  const recs = await fetch("/rec-service/for-user");
  // If either service is slow, the user waits for BOTH sequentially
  // with no upper bound on total wait time.
  return buildResponse(await user.json(), await recs.json());
}
```

## Alternatives & Related Approaches

| Approach | When to prefer it |
|---|---|
| **Async / fire-and-forget** | When the caller does not need the result immediately; enqueue and return |
| **Polling** | When the operation is inherently long-running; return a job ID and poll for completion |
| **Server-Sent Events / WebSockets** | When the server pushes results when ready, eliminating the need for a response timeout |
| **Circuit breaker** | When repeated timeouts indicate systemic failure — stop trying entirely |

Timeouts are the foundation upon which circuit breakers and retries are built. A circuit breaker counts timeout failures. A retry waits and tries again after a timeout. Without timeouts, neither pattern works.

## When NOT to Apply

- **Long-running batch operations** where the expected duration is minutes or hours. Use a job queue with progress tracking instead of a synchronous timeout.
- **WebSocket/streaming connections** that are meant to stay open. Use heartbeat/ping-pong timeouts instead of overall connection timeouts.
- **Database migrations** and schema changes that may take minutes. These should run outside the request path entirely.
- **File uploads** where the duration depends on file size and bandwidth. Use progress-based timeouts (no data received for X seconds) rather than absolute timeouts.

## Tensions & Trade-offs

- **Too short:** Timeouts that are too aggressive cause false failures. A 99th percentile latency of 2s with a 2s timeout means 1% of requests fail under normal conditions.
- **Too long:** Timeouts that are too generous do not protect resources. A 60-second timeout with 100 concurrent connections means you can only handle ~1.7 requests/second during a slowdown.
- **Deadline propagation adds coupling:** Services must agree on the deadline header format and propagation semantics. This is a form of distributed protocol that needs maintenance.
- **Retries multiply the effective timeout:** A 5s timeout with 3 retries means the caller might wait up to 20s (5s + backoff + 5s + backoff + 5s). The user's perceived timeout is the overall budget, not the individual request timeout.
- **Different operations need different timeouts:** A health check should timeout in 1s. A report generation endpoint might need 30s. A single global timeout is always wrong.

## Real-World Consequences

In 2012, a single slow query in a shared database took down an entire microservice platform at a major e-commerce company. The query took 45 seconds. Every service that touched that database had a default 60-second timeout. Threads accumulated, connection pools filled, and services cascaded into failure. The fix was not just adding timeouts — it was implementing per-query timeout budgets in the database driver.

Google's gRPC framework ships with first-class deadline propagation. Every gRPC call carries a deadline that automatically decrements as it passes through services. If you call a gRPC service with a 5-second deadline and it takes 3 seconds of local processing, it passes a 2-second deadline to its downstream call. This single feature prevents the cascading timeout problem by default.

## Further Reading

- [gRPC Deadlines](https://grpc.io/blog/deadlines/)
- [AWS Builder's Library: Timeouts, Retries, and Backoff with Jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
- *Release It!* by Michael Nygard — timeouts as stability patterns
- [Google SRE Book: Handling Overload](https://sre.google/sre-book/handling-overload/)
