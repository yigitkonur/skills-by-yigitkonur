# The Event Loop

**Node.js processes everything on a single thread via an event loop that dispatches callbacks. Understanding its phases is essential for avoiding performance pitfalls and mysterious bugs.**

---

## Origin / History

Event-driven programming predates Node.js by decades. The X Window System (1984), Tcl/Tk (1988), and GUI frameworks like Win32's message pump all used event loops. Nginx (2004) proved that event-driven architecture could outperform thread-per-request servers for I/O-heavy workloads.

Node.js (Ryan Dahl, 2009) brought the event loop to server-side JavaScript, building on libuv — a cross-platform asynchronous I/O library. The key insight was that most server workloads are I/O-bound (waiting for databases, network, disk), not CPU-bound. A single-threaded event loop with non-blocking I/O can handle tens of thousands of concurrent connections with minimal memory overhead, whereas a thread-per-request model (Java, PHP) allocates a stack per connection.

The event loop model was refined in browser JavaScript engines (V8's microtask queue, 2014) and standardized in the HTML spec. Node.js added worker threads in v10 (2018) for CPU-bound work, and the event loop phases were documented in detail to help developers avoid common pitfalls.

---

## The Problem It Solves

Thread-per-request models have a fundamental scaling problem: each thread consumes 1-8MB of stack memory. At 10,000 concurrent connections, that is 10-80GB of memory just for stacks — before any work is done. Context switching between threads adds CPU overhead. Java application servers historically capped at a few thousand concurrent connections.

Conversely, a naive single-threaded model cannot handle concurrency at all — one slow operation blocks everything. The event loop solves both problems: it uses a single thread for JavaScript execution (minimal memory overhead) but delegates I/O operations to the operating system's async facilities (epoll, kqueue, IOCP). When I/O completes, a callback is queued for the event loop to execute. The result: high concurrency with low resource usage.

The problem the event loop creates is more subtle: any synchronous CPU-intensive work blocks the loop, stalling all concurrent operations. Understanding the event loop's phases and when your code runs is the difference between a responsive server and one that intermittently freezes.

---

## The Principle Explained

The Node.js event loop has six phases, executed in order on each "tick": (1) Timers — execute `setTimeout` and `setInterval` callbacks whose threshold has elapsed. (2) Pending callbacks — execute I/O callbacks deferred to the next iteration. (3) Idle/prepare — internal use. (4) Poll — retrieve new I/O events and execute their callbacks. (5) Check — execute `setImmediate` callbacks. (6) Close callbacks — execute close event callbacks (e.g., `socket.on('close')`).

Between each phase, Node.js processes the microtask queue: resolved Promises (`.then` callbacks) and `process.nextTick` callbacks. Microtasks run to completion before the event loop proceeds to the next phase. This means a recursive chain of microtasks can starve the event loop — no timers fire, no I/O callbacks run, and the process appears frozen.

The practical implications are: (1) never block the event loop with synchronous computation — use worker threads for CPU-bound work, (2) understand that `await` creates a microtask boundary — other code can run between your suspension points, (3) avoid `process.nextTick` in hot paths because it starves I/O, and (4) use `setImmediate` when you need to yield to the event loop between iterations of a long computation.

---

## Code Examples

### BAD: Blocking the event loop with synchronous computation

```typescript
import express from "express";

const app = express();

app.get("/api/hash", (req, res) => {
  const input = req.query.input as string;

  // CPU-intensive: blocks the event loop for seconds
  // ALL other requests wait — the entire server is frozen
  const result = computeExpensiveHash(input); // 2 seconds of CPU work

  res.json({ hash: result });
});

app.get("/api/health", (_req, res) => {
  // This "instant" endpoint takes 2+ seconds to respond
  // because the event loop is blocked by /api/hash
  res.json({ status: "ok" });
});

function computeExpensiveHash(input: string): string {
  // Simulates CPU-intensive work
  let hash = input;
  for (let i = 0; i < 100_000_000; i++) {
    hash = hash.split("").reverse().join(""); // Blocks the event loop
  }
  return hash;
}
```

### GOOD: Offloading CPU work to a worker thread

```typescript
import { Worker, isMainThread, parentPort, workerData } from "node:worker_threads";
import express from "express";

// Main thread: handles I/O, delegates CPU work
if (isMainThread) {
  const app = express();

  function runInWorker<T>(task: string, data: unknown): Promise<T> {
    return new Promise((resolve, reject) => {
      const worker = new Worker(__filename, { workerData: { task, data } });
      worker.on("message", resolve);
      worker.on("error", reject);
      worker.on("exit", (code) => {
        if (code !== 0) reject(new Error(`Worker exited with code ${code}`));
      });
    });
  }

  app.get("/api/hash", async (req, res) => {
    const input = req.query.input as string;
    // CPU work runs in a separate thread — event loop stays free
    const result = await runInWorker<string>("hash", input);
    res.json({ hash: result });
  });

  app.get("/api/health", (_req, res) => {
    // Responds instantly even while hash is computing
    res.json({ status: "ok" });
  });

  app.listen(3000);
}

// Worker thread: CPU-intensive work in isolation
if (!isMainThread) {
  const { task, data } = workerData;
  if (task === "hash") {
    const result = computeExpensiveHash(data as string);
    parentPort!.postMessage(result);
  }
}
```

### Understanding microtasks vs. macrotasks

```typescript
// Execution order demonstration
console.log("1: Synchronous");

setTimeout(() => console.log("2: setTimeout (macrotask - timers phase)"), 0);

setImmediate(() => console.log("3: setImmediate (check phase)"));

Promise.resolve().then(() => console.log("4: Promise.then (microtask)"));

process.nextTick(() => console.log("5: process.nextTick (microtask, high priority)"));

console.log("6: Synchronous");

// Output order:
// 1: Synchronous
// 6: Synchronous
// 5: process.nextTick (microtask, high priority)
// 4: Promise.then (microtask)
// 2: setTimeout (macrotask - timers phase)  -- order of 2/3 can vary
// 3: setImmediate (check phase)
```

### BAD: Microtask starvation — recursive nextTick blocks everything

```typescript
// This starves the event loop — timers and I/O never execute
function recursiveNextTick(): void {
  process.nextTick(() => {
    // This runs before ANY macrotask — forever
    doSomeWork();
    recursiveNextTick(); // Queue another microtask immediately
  });
}

recursiveNextTick();
// setTimeout callbacks, I/O callbacks, setImmediate — NONE of these ever run
```

### GOOD: Yielding to the event loop during long computations

```typescript
// Process a large array without blocking the event loop
async function processLargeArray<T>(
  items: readonly T[],
  processor: (item: T) => void,
  batchSize: number = 100,
): Promise<void> {
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    batch.forEach(processor);

    // Yield to the event loop after each batch
    // This lets timers, I/O, and other callbacks run
    if (i + batchSize < items.length) {
      await new Promise<void>((resolve) => setImmediate(resolve));
    }
  }
}

// Usage: process 1M items without blocking
await processLargeArray(millionItems, processItem, 1000);
```

### Monitoring event loop lag

```typescript
// Detect when the event loop is falling behind
function monitorEventLoopLag(
  thresholdMs: number = 100,
  intervalMs: number = 1000,
): NodeJS.Timeout {
  let lastCheck = process.hrtime.bigint();

  return setInterval(() => {
    const now = process.hrtime.bigint();
    const elapsed = Number(now - lastCheck) / 1_000_000; // Convert to ms
    const lag = elapsed - intervalMs;

    if (lag > thresholdMs) {
      console.warn(`Event loop lag: ${lag.toFixed(1)}ms (threshold: ${thresholdMs}ms)`);
      // Alert, emit metric, etc.
    }

    lastCheck = now;
  }, intervalMs);
}
```

---

## Alternatives & Related Approaches

| Approach | Trade-off |
|---|---|
| **Thread-per-request (Java Servlets, PHP)** | Simple mental model. But high memory overhead per connection and context-switching costs limit concurrency. |
| **Coroutines (Go goroutines, Kotlin coroutines)** | Lightweight cooperative threads scheduled by the runtime. Similar concurrency to event loop, but with a synchronous-looking API and no single-thread bottleneck. |
| **Multi-process (Python multiprocessing, PM2 cluster)** | Fork multiple processes, each with its own event loop. Scales across CPU cores but requires IPC for shared state. |
| **Async I/O with thread pool (Rust tokio, Java NIO)** | Event loop for I/O multiplexing with a thread pool for CPU work. Best of both worlds, but more complex runtime. |
| **Reactive streams (RxJS, Project Reactor)** | Declarative async composition with built-in backpressure. Powerful for complex event processing, steep learning curve. |

---

## When NOT to Apply

- **CPU-bound applications**: Image processing, machine learning inference, video encoding — these need thread pools or separate processes, not an event loop.
- **When you need true parallelism**: The event loop is concurrent (interleaved) but not parallel (simultaneous). For parallel computation, use worker threads, a cluster, or a different runtime.
- **Real-time systems with strict latency guarantees**: The event loop's non-deterministic scheduling (microtask queues, GC pauses) makes it unsuitable for hard real-time requirements.

---

## Tensions & Trade-offs

- **Simplicity vs. Performance**: Single-threaded execution eliminates races and locks, but caps CPU utilization at one core. Cluster mode or workers add complexity.
- **Non-blocking vs. Ecosystem**: Some npm packages use synchronous I/O (fs.readFileSync, crypto.pbkdf2Sync). One call blocks the entire server. Auditing dependencies for blocking calls is essential but tedious.
- **Microtask priority vs. Fairness**: Microtasks (Promises, nextTick) run before macrotasks. Heavy Promise chains can starve timers and I/O.
- **Abstraction vs. Understanding**: async/await hides the event loop. Developers who do not understand the underlying model write code that accidentally blocks or starves the loop.

---

## Real-World Consequences

**LinkedIn's Node.js migration**: LinkedIn migrated from Ruby on Rails to Node.js and reduced their server count from 30 to 3 — because the event loop handled the same concurrent connections with far less memory overhead. But they had to learn the hard way that synchronous JSON parsing of large payloads blocked the event loop.

**Event loop blocking in production**: A SaaS company's API intermittently spiked to 10-second response times. The cause: a scheduled task ran a CPU-intensive data aggregation on the main thread every 60 seconds. During the 2-second computation, all HTTP requests queued. Moving the aggregation to a worker thread eliminated the spikes.

**DNS resolution blocking**: Node.js `dns.lookup()` (the default for HTTP requests) uses the libuv thread pool, which defaults to 4 threads. Under high concurrency, DNS lookups queue, causing mysterious latency spikes. The fix: increase `UV_THREADPOOL_SIZE` or use `dns.resolve()` which uses non-blocking c-ares.

---

## Further Reading

- [Node.js — The Event Loop, Timers, and process.nextTick()](https://nodejs.org/en/docs/guides/event-loop-timers-and-nexttick)
- [Node.js — Don't Block the Event Loop](https://nodejs.org/en/docs/guides/dont-block-the-event-loop)
- [Philip Roberts — What the heck is the event loop anyway? (JSConf EU 2014)](https://www.youtube.com/watch?v=8aGhZQkoFbQ)
- [Jake Archibald — Tasks, Microtasks, Queues and Schedules](https://jakearchibald.com/2015/tasks-microtasks-queues-and-schedules/)
- [libuv Design Overview](https://docs.libuv.org/en/v1.x/design.html)
