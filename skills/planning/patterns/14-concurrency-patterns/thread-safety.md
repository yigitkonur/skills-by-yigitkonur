# Thread Safety

**Ensuring that shared data and resources are accessed correctly when multiple threads of execution operate concurrently, preventing race conditions, deadlocks, and data corruption.**

---

## Origin / History

Thread safety became a critical concern with the advent of multi-threaded operating systems in the 1960s and 1970s. Dijkstra's semaphore (1965), Hoare's monitor (1974), and Lamport's bakery algorithm (1974) were early solutions to concurrent access problems. The Java language (1995) brought threading to mainstream application development with built-in `synchronized` blocks and the `volatile` keyword. The Java Memory Model (JSR-133, 2004) formalized the rules for when changes made by one thread become visible to another.

JavaScript was designed as single-threaded (Brendan Eich, 1995), which originally made thread safety irrelevant. However, Web Workers (2009), SharedArrayBuffer (2017, re-enabled 2018 after Spectre mitigations), and Node.js worker_threads (2018) introduced shared memory to the JavaScript ecosystem. Atomics operations were added alongside SharedArrayBuffer to provide low-level thread-safe primitives. While most JavaScript developers never need to think about thread safety, those working with shared memory must understand the same principles that have governed concurrent programming for decades.

---

## The Problem It Solves

When multiple threads access shared mutable state without synchronization, three categories of bugs emerge. Race conditions: the outcome depends on the unpredictable timing of thread execution. Thread A reads a counter (value: 5), Thread B reads the same counter (value: 5), both increment and write back 6 — one increment is lost. Deadlocks: Thread A holds Lock 1 and waits for Lock 2, while Thread B holds Lock 2 and waits for Lock 1. Neither can proceed. Data corruption: partial writes (one thread reads while another is mid-write) produce impossible values.

These bugs are uniquely difficult because they are non-deterministic — they depend on timing, load, and hardware. A race condition might occur once per million operations, making it nearly impossible to reproduce in development but inevitable in production.

---

## The Principle Explained

Thread safety means that a piece of code or data structure behaves correctly when accessed from multiple threads simultaneously. There are several strategies to achieve this, each with different trade-offs.

Mutual exclusion (locks/mutexes) ensures only one thread can access a critical section at a time. This is the most common approach but introduces contention (threads wait for locks), deadlock risk (circular lock dependencies), and priority inversion (a low-priority thread holding a lock blocks a high-priority thread). Lock-free programming uses atomic operations (compare-and-swap) to coordinate threads without locks, avoiding deadlocks but requiring expert-level reasoning about memory ordering.

Immutability is the simplest strategy: if data never changes, sharing it is always safe. No locks, no races, no deadlocks. This is why functional programming's emphasis on immutability is directly relevant to thread safety. In JavaScript, the single-threaded event loop provides a similar benefit — most JavaScript code is "thread-safe by default" because there is only one thread. But SharedArrayBuffer breaks this guarantee, and understanding thread safety becomes essential when using it.

The JavaScript-specific concern is the event loop: while JavaScript is single-threaded, concurrent access to shared state can still occur across `await` boundaries. Between two awaits, other callbacks can modify shared state. This is not "thread safety" in the traditional sense, but it produces identical symptoms — race conditions on shared mutable state.

---

## Code Examples

### BAD: Race condition across await boundaries in Node.js

```typescript
// This is NOT thread-safe even in single-threaded Node.js
// The race condition occurs across async boundaries

let availableTickets = 100; // Shared mutable state

async function purchaseTicket(userId: string): Promise<boolean> {
  // Check
  if (availableTickets <= 0) return false;

  // Other async operations can run here!
  await chargePayment(userId);
  // By the time we reach here, another request may have
  // decremented availableTickets to 0

  // Act — but the check is stale
  availableTickets--;
  await createBooking(userId);
  return true;
}

// If 10 requests arrive simultaneously when availableTickets = 1:
// All 10 pass the check (availableTickets > 0)
// All 10 charge payment
// All 10 decrement — availableTickets becomes -9
// Result: 10 tickets sold when only 1 was available
```

### GOOD: Atomic check-and-act with database transaction

```typescript
async function purchaseTicket(userId: string): Promise<boolean> {
  const client = await pool.connect();
  try {
    await client.query("BEGIN");

    // Atomic check-and-decrement in a single statement
    const result = await client.query(
      `UPDATE events
       SET available_tickets = available_tickets - 1
       WHERE id = $1 AND available_tickets > 0
       RETURNING available_tickets`,
      [eventId],
    );

    if (result.rowCount === 0) {
      await client.query("ROLLBACK");
      return false; // No tickets available — atomically checked
    }

    await chargePayment(userId);
    await createBooking(userId);
    await client.query("COMMIT");
    return true;
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
}
```

### In-process mutex for async operations

```typescript
// Mutex that works with async/await — not OS threads, but async interleaving
class AsyncMutex {
  private locked = false;
  private waitQueue: Array<() => void> = [];

  async acquire(): Promise<void> {
    if (!this.locked) {
      this.locked = true;
      return;
    }

    // Wait until the lock is released
    return new Promise<void>((resolve) => {
      this.waitQueue.push(resolve);
    });
  }

  release(): void {
    if (this.waitQueue.length > 0) {
      // Wake the next waiter
      const next = this.waitQueue.shift()!;
      next();
    } else {
      this.locked = false;
    }
  }

  async withLock<T>(fn: () => Promise<T>): Promise<T> {
    await this.acquire();
    try {
      return await fn();
    } finally {
      this.release();
    }
  }
}

// Usage: serialize access to shared resource
const ticketMutex = new AsyncMutex();

async function purchaseTicketSafe(userId: string): Promise<boolean> {
  return ticketMutex.withLock(async () => {
    if (availableTickets <= 0) return false;
    await chargePayment(userId);
    availableTickets--;
    await createBooking(userId);
    return true;
  });
}
```

### SharedArrayBuffer and Atomics — true thread safety in JavaScript

```typescript
// Worker thread communication via shared memory
import { Worker, isMainThread, workerData } from "node:worker_threads";

if (isMainThread) {
  // Shared memory buffer — visible to all worker threads
  const sharedBuffer = new SharedArrayBuffer(4); // 4 bytes = 1 Int32
  const counter = new Int32Array(sharedBuffer);
  counter[0] = 0;

  // Spawn 4 workers, each incrementing the counter 10000 times
  const workers = Array.from({ length: 4 }, () =>
    new Worker(__filename, { workerData: { sharedBuffer } }),
  );

  await Promise.all(
    workers.map((w) => new Promise((resolve) => w.on("exit", resolve))),
  );

  console.log(`Final counter: ${counter[0]}`); // Should be 40000
} else {
  const counter = new Int32Array(workerData.sharedBuffer);

  for (let i = 0; i < 10_000; i++) {
    // BAD: counter[0]++ is NOT atomic — race condition!
    // counter[0]++;

    // GOOD: Atomics.add is atomic — thread-safe
    Atomics.add(counter, 0, 1);
  }
}
```

### Avoiding deadlocks — consistent lock ordering

```typescript
// BAD: Inconsistent lock ordering causes deadlock
async function transferBad(
  from: Account,
  to: Account,
  amount: number,
): Promise<void> {
  // Thread 1: transfer(A, B) — locks A, then tries to lock B
  // Thread 2: transfer(B, A) — locks B, then tries to lock A
  // DEADLOCK: each holds what the other needs
  await from.mutex.acquire();
  await to.mutex.acquire();
  // ...
}

// GOOD: Always lock in consistent order (by ID)
async function transferSafe(
  from: Account,
  to: Account,
  amount: number,
): Promise<void> {
  // Always lock the lower ID first — prevents circular wait
  const [first, second] =
    from.id < to.id ? [from, to] : [to, from];

  await first.mutex.acquire();
  await second.mutex.acquire();
  try {
    if (from.balance < amount) throw new Error("Insufficient funds");
    from.balance -= amount;
    to.balance += amount;
  } finally {
    second.mutex.release();
    first.mutex.release();
  }
}
```

---

## Alternatives & Related Approaches

| Approach | Trade-off |
|---|---|
| **Immutability (avoid the problem)** | If data never changes, it is always safe to share. The most elegant solution when applicable. But some state must change — the question is where to put the mutation boundary. |
| **Actor model** | Isolate state inside actors; communicate via messages. No shared state means no thread safety concerns. Adds message-passing overhead and requires architectural commitment. |
| **CSP (Communicating Sequential Processes)** | Go's goroutines and channels. Share by communicating, not by sharing memory. Structured and safer than raw threads + locks. |
| **Software Transactional Memory** | Treat memory access like database transactions. Optimistic concurrency at the memory level. Available in Haskell and Clojure; limited support elsewhere. |
| **Single-threaded execution** | JavaScript's event loop avoids thread safety by having one thread. Effective but limits CPU utilization to one core. |

---

## When NOT to Apply

- **Standard Node.js applications**: Most Node.js code runs on a single thread. Thread safety is irrelevant unless you use SharedArrayBuffer or worker_threads with shared memory.
- **Stateless request handlers**: If each request handler uses only local variables and talks to a database, there is no shared state to protect. The database handles concurrency.
- **When immutability suffices**: If you can model your problem with immutable data (functional core, imperative shell), you avoid thread safety concerns entirely.
- **Over-synchronization**: Adding locks everywhere "just in case" reduces concurrency and can introduce deadlocks. Only synchronize when there is actual shared mutable state.

---

## Tensions & Trade-offs

- **Safety vs. Performance**: Every lock acquisition has a cost. Fine-grained locking (one lock per field) maximizes concurrency but multiplies overhead and deadlock risk. Coarse-grained locking (one lock per object) is simpler but serializes more operations.
- **Correctness vs. Complexity**: Lock-free algorithms are faster but extraordinarily difficult to implement correctly. Even experts get them wrong. Prefer locks unless profiling proves they are the bottleneck.
- **Single-threaded simplicity vs. Multi-core utilization**: JavaScript's single-threaded model is simple and safe but wastes CPU cores. Adding workers for parallelism brings thread safety concerns.
- **Async race conditions vs. Thread race conditions**: JavaScript developers must understand that async/await introduces race conditions on shared state — not from threads, but from interleaved execution across await points.

---

## Real-World Consequences

**JavaScript's single-threaded advantage**: The decision to make JavaScript single-threaded — often criticized as a limitation — is one of its greatest strengths for correctness. Most Node.js applications have zero thread safety bugs because there is only one thread. This is a conscious trade-off of CPU utilization for safety.

**SharedArrayBuffer and Spectre**: SharedArrayBuffer was disabled in all browsers in January 2018 after the Spectre CPU vulnerability was disclosed. Shared memory between threads could be used as a side-channel timing attack to read arbitrary memory. It was re-enabled with site isolation (COOP/COEP headers), demonstrating that shared memory carries risks beyond application-level bugs.

**Async race condition in production**: A payment processing company had a bug where a customer's balance was occasionally doubled. The cause: two concurrent API requests both read the balance, both added the deposit amount, and both wrote back. With 50ms of async I/O between read and write, the window for the race condition was narrow but consistent at scale. The fix: use a database transaction with `SELECT FOR UPDATE` to serialize balance modifications.

---

## Further Reading

- [MDN — SharedArrayBuffer](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer)
- [MDN — Atomics](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Atomics)
- [Node.js Worker Threads Documentation](https://nodejs.org/api/worker_threads.html)
- [Brian Goetz — Java Concurrency in Practice (Addison-Wesley, 2006)](https://jcip.net/)
- [Leslie Lamport — Time, Clocks, and the Ordering of Events in a Distributed System (1978)](https://lamport.azurewebsites.net/pubs/time-clocks.pdf)
