# Async/Await Patterns

**Write asynchronous code that reads like synchronous code, while understanding the pitfalls that lurk beneath the syntactic sugar.**

---

## Origin / History

JavaScript's concurrency story evolved through four eras. Callbacks (Node.js 2009) enabled non-blocking I/O but created "callback hell" — deeply nested, error-prone pyramids of anonymous functions. Promises (ES2015) flattened callbacks into chainable `.then()` calls. Async/await (ES2017) provided syntactic sugar over Promises, making asynchronous code read like sequential code. Most recently, top-level await (ES2022) extended async/await to module scope.

The async/await pattern itself was not invented by JavaScript. C# introduced `async`/`await` in 2012 (Anders Hejlsberg). Python added it in 3.5 (2015). Rust, Kotlin, Swift, and Dart all adopted the pattern. The core idea traces back to coroutines (Melvin Conway, 1958) — functions that can suspend and resume execution.

---

## The Problem It Solves

Asynchronous code is inherently harder to reason about than synchronous code. Operations complete in unpredictable order, errors occur at unpredictable times, and shared state can be modified between suspension points. Without good patterns, async code becomes a tangle of race conditions, unhandled rejections, resource leaks, and mysterious timing bugs.

Async/await solves the readability problem: code reads top-to-bottom like synchronous code. But it introduces new problems: developers forget that `await` is a suspension point (other code can run), accidentally serialize operations that should be concurrent, or create floating promises that swallow errors silently.

---

## The Principle Explained

`async` marks a function as returning a Promise. `await` pauses execution of the async function until the awaited Promise settles, then resumes with the resolved value (or throws the rejection reason). The key mental model is that `await` is a suspension point — the function yields control to the event loop, and other code may execute before it resumes.

Sequential vs. concurrent await is the most important distinction. `await a(); await b();` runs `a` then `b` sequentially — total time is `time(a) + time(b)`. `await Promise.all([a(), b()])` runs them concurrently — total time is `max(time(a), time(b))`. Choosing the wrong pattern is one of the most common performance bugs in async code.

Error handling in async code requires deliberate patterns. `try/catch` works around `await`, but unhandled promise rejections (from floating promises or missing `.catch()`) crash Node.js processes. `Promise.allSettled` handles partial failures gracefully. Understanding these patterns is the difference between robust async code and code that fails silently.

---

## Code Examples

### BAD: Sequential awaits that should be concurrent

```typescript
// Each await blocks the next — total time is sum of all fetches
async function getUserDashboard(userId: string): Promise<Dashboard> {
  const user = await fetchUser(userId);
  const orders = await fetchOrders(userId);        // Waits for user to finish
  const recommendations = await fetchRecommendations(userId); // Waits for orders
  const notifications = await fetchNotifications(userId);     // Waits for recs

  // If each takes 200ms, total is 800ms — but they are independent!
  return { user, orders, recommendations, notifications };
}
```

### GOOD: Concurrent awaits with Promise.all

```typescript
// Independent operations run concurrently — total time is max of all fetches
async function getUserDashboard(userId: string): Promise<Dashboard> {
  const [user, orders, recommendations, notifications] = await Promise.all([
    fetchUser(userId),
    fetchOrders(userId),
    fetchRecommendations(userId),
    fetchNotifications(userId),
  ]);

  // If each takes 200ms, total is ~200ms
  return { user, orders, recommendations, notifications };
}
```

### Promise.all vs. Promise.allSettled — handling partial failures

```typescript
// Promise.all: fails fast — if ANY promise rejects, all results are lost
async function fetchAllOrNothing(userIds: string[]): Promise<User[]> {
  try {
    return await Promise.all(userIds.map(fetchUser));
  } catch (error) {
    // One failure means we get NONE of the results
    // Even the successful fetches are discarded
    throw new Error("Failed to fetch all users");
  }
}

// Promise.allSettled: get all results, handle failures individually
async function fetchWithGracefulDegradation(
  userIds: string[],
): Promise<{ users: User[]; errors: Array<{ id: string; error: unknown }> }> {
  const results = await Promise.allSettled(
    userIds.map((id) => fetchUser(id).then((user) => ({ id, user }))),
  );

  const users: User[] = [];
  const errors: Array<{ id: string; error: unknown }> = [];

  for (const result of results) {
    if (result.status === "fulfilled") {
      users.push(result.value.user);
    } else {
      errors.push({ id: "unknown", error: result.reason });
    }
  }

  return { users, errors };
}
```

### BAD: Floating promises — silent error swallowing

```typescript
async function processWebhook(event: WebhookEvent): Promise<void> {
  // DANGER: These promises float — errors are silently swallowed
  updateAnalytics(event);          // No await, no .catch()
  notifySubscribers(event);        // Fire-and-forget with no error handling
  syncToExternalService(event);    // If this fails, nobody knows

  // The function returns "successfully" even if all three fail
}
```

### GOOD: Explicit handling of fire-and-forget operations

```typescript
async function processWebhook(event: WebhookEvent): Promise<void> {
  // Critical path — await these
  await validateEvent(event);
  await persistEvent(event);

  // Non-critical — fire-and-forget with explicit error handling
  void updateAnalytics(event).catch((error) =>
    logger.warn("Analytics update failed", { error, eventId: event.id }),
  );

  // Or collect non-critical operations
  Promise.allSettled([
    notifySubscribers(event),
    syncToExternalService(event),
  ]).then((results) => {
    const failures = results.filter((r) => r.status === "rejected");
    if (failures.length > 0) {
      logger.warn("Non-critical webhook tasks failed", { failures });
    }
  });
}
```

### Controlled concurrency — limiting parallel operations

```typescript
// Process items with bounded concurrency (e.g., max 5 at a time)
async function mapWithConcurrency<T, R>(
  items: readonly T[],
  concurrency: number,
  fn: (item: T) => Promise<R>,
): Promise<R[]> {
  const results: R[] = new Array(items.length);
  let nextIndex = 0;

  async function worker(): Promise<void> {
    while (nextIndex < items.length) {
      const index = nextIndex++;
      results[index] = await fn(items[index]);
    }
  }

  const workers = Array.from({ length: Math.min(concurrency, items.length) }, worker);
  await Promise.all(workers);
  return results;
}

// Usage: process 1000 items, max 10 concurrent requests
const users = await mapWithConcurrency(userIds, 10, fetchUser);
```

### Async iteration with for-await-of

```typescript
// Process a stream of data as it arrives
async function processLargeDataset(
  stream: AsyncIterable<DataChunk>,
): Promise<ProcessingResult> {
  let totalProcessed = 0;
  const errors: Error[] = [];

  for await (const chunk of stream) {
    try {
      await processChunk(chunk);
      totalProcessed += chunk.size;
    } catch (error) {
      errors.push(error instanceof Error ? error : new Error(String(error)));
      // Continue processing remaining chunks
    }
  }

  return { totalProcessed, errors };
}
```

---

## Alternatives & Related Approaches

| Approach | Trade-off |
|---|---|
| **Callbacks** | No library/syntax needed. But nesting, error propagation, and cancellation are manual and error-prone. |
| **RxJS Observables** | Powerful for streams, cancellation, and complex async flows (debounce, retry, merge). But steep learning curve and overkill for simple request/response. |
| **Generators (function*)** | Can model async flows with co-routines (via libraries like `co`). Largely superseded by async/await. |
| **Event emitters** | Good for pub/sub patterns. Bad for request/response flows where you need the result. |
| **Worker threads** | True parallelism for CPU-bound work. Communication overhead makes them unsuitable for I/O-bound work that async/await handles well. |

---

## When NOT to Apply

- **CPU-bound computation**: Async/await does not make computation faster. A CPU-intensive loop with `await` between iterations still blocks the event loop during each iteration. Use worker threads instead.
- **Simple synchronous operations**: Do not make a function async if it does not await anything. An async function always returns a Promise, adding unnecessary overhead and complexity.
- **Hot paths with sub-millisecond latency requirements**: Each `await` creates a microtask. In extremely hot paths, the microtask overhead matters. Use synchronous code.
- **When you need cancellation**: Native Promises cannot be cancelled. If cancellation is important, consider AbortController or RxJS.

---

## Tensions & Trade-offs

- **Readability vs. Performance**: Sequential `await` reads naturally but serializes independent operations. Concurrent `Promise.all` is faster but harder to read and reason about error handling.
- **Simplicity vs. Robustness**: try/catch around `await` is simple. But comprehensive error handling (timeouts, retries, partial failures, cleanup) requires significantly more code.
- **Fire-and-forget vs. Observability**: Sometimes you do not want to wait for a result. But unobserved promise rejections are the async equivalent of swallowed exceptions.
- **Async everywhere vs. Sync core**: Making everything async "just in case" creates unnecessary overhead. But mixing sync and async code at boundaries requires careful attention.

---

## Real-World Consequences

**Unhandled promise rejections crashing production**: Node.js 15+ crashes on unhandled promise rejections by default. A single floating promise in a request handler can take down the entire process. Companies that enforced the ESLint rule `no-floating-promises` (via typescript-eslint) eliminated this class of crashes entirely.

**Sequential await in API handlers**: A major e-commerce company discovered their product page API handler took 1.2 seconds because it sequentially awaited six independent database queries. Switching to `Promise.all` reduced response time to 250ms — the time of the single slowest query.

**Promise.all failure cascade**: A microservices team used `Promise.all` to fetch data from five services. When one service went down, all requests failed — even though four services were healthy. Switching to `Promise.allSettled` with graceful degradation let the page render with partial data instead of showing an error.

---

## Further Reading

- [MDN — Async Functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)
- [JavaScript.info — Async/Await](https://javascript.info/async-await)
- [Node.js — Don't Block the Event Loop](https://nodejs.org/en/docs/guides/dont-block-the-event-loop)
- [typescript-eslint — no-floating-promises Rule](https://typescript-eslint.io/rules/no-floating-promises/)
- [Dr. Axel Rauschmayer — JavaScript for Impatient Programmers (Async chapters)](https://exploringjs.com/impatient-js/)
