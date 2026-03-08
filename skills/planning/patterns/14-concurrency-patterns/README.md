# 14 - Concurrency Patterns

Concurrency is about dealing with many things at once. Parallelism is about doing many things at once. These patterns address both — how to structure code that handles multiple operations, how to coordinate shared resources, and how to avoid the bugs that make concurrent systems notoriously difficult.

---

## Contents

| # | Pattern | Summary | File |
|---|---------|---------|------|
| 1 | [Async/Await Patterns](./async-await-patterns.md) | Sequential vs. concurrent await, Promise.all vs. allSettled, error handling, floating promises, controlled concurrency. |
| 2 | [Actor Model](./actor-model.md) | Isolated actors communicating via message passing. No shared state, no locks. Supervision and fault tolerance. |
| 3 | [Producer-Consumer](./producer-consumer.md) | Decouple work production from consumption via queues. Backpressure, bounded buffers, message queues. |
| 4 | [Event Loop](./event-loop.md) | Node.js single-threaded execution model. Phases, microtasks vs. macrotasks, blocking prevention, worker threads. |
| 5 | [Optimistic vs. Pessimistic Locking](./optimistic-vs-pessimistic-locking.md) | Version-based conflict detection vs. exclusive locks. ETags, CAS, SELECT FOR UPDATE. |
| 6 | [Pub/Sub](./pub-sub.md) | Publisher/subscriber decoupling via topics. Fan-out, event buses, Kafka, Redis Pub/Sub. |
| 7 | [Thread Safety](./thread-safety.md) | Race conditions, deadlocks, atomicity. JavaScript's single-threaded advantage. SharedArrayBuffer and Atomics. |

---

## Decision Flowchart

Use this flowchart when choosing a concurrency pattern for your problem:

```
START: What kind of concurrent problem are you solving?
│
├─ "I need to run multiple I/O operations"
│  │
│  ├─ Are they independent of each other?
│  │  ├─ YES → Promise.all() or Promise.allSettled()
│  │  │         (See: async-await-patterns.md)
│  │  └─ NO → Sequential await with error handling
│  │           (See: async-await-patterns.md)
│  │
│  └─ Do I need to limit how many run at once?
│     └─ YES → Bounded concurrency / semaphore pattern
│              (See: async-await-patterns.md, producer-consumer.md)
│
├─ "I need to process a stream of work items"
│  │
│  ├─ Should each item go to ONE processor?
│  │  └─ YES → Producer-Consumer with queue
│  │           (See: producer-consumer.md)
│  │
│  └─ Should each item go to ALL interested parties?
│     └─ YES → Pub/Sub with topics
│              (See: pub-sub.md)
│
├─ "Multiple things are reading/writing the same data"
│  │
│  ├─ Is conflict rare (many resources, few writers)?
│  │  └─ YES → Optimistic locking (version numbers, ETags)
│  │           (See: optimistic-vs-pessimistic-locking.md)
│  │
│  ├─ Is conflict frequent (single resource, many writers)?
│  │  └─ YES → Pessimistic locking (mutex, SELECT FOR UPDATE)
│  │           (See: optimistic-vs-pessimistic-locking.md)
│  │
│  └─ Can you eliminate shared state entirely?
│     └─ YES → Actor model or immutability
│              (See: actor-model.md, thread-safety.md)
│
├─ "I need CPU-intensive work without blocking"
│  │
│  └─ In Node.js?
│     ├─ YES → Worker threads (do NOT block the event loop)
│     │        (See: event-loop.md)
│     └─ NO → Thread pool or process pool
│
├─ "I need fault-tolerant, self-healing concurrency"
│  │
│  └─ Actor model with supervision trees
│     (See: actor-model.md)
│
└─ "I'm not sure what kind of problem this is"
   │
   └─ Start with: Is your code single-threaded (Node.js)?
      ├─ YES → Most concurrency issues are async race conditions.
      │        Read: event-loop.md, async-await-patterns.md, thread-safety.md
      └─ NO → You likely need locks or actors.
              Read: thread-safety.md, actor-model.md
```

---

## Key Relationships Between Patterns

```
Event Loop ──underpins──→ Async/Await (all async code runs on the event loop)
     │
     └──constrains──→ Thread Safety (single thread = safe by default,
                                      unless SharedArrayBuffer)

Producer-Consumer ──uses──→ Backpressure (bounded queues)
        │
        └──related to──→ Pub/Sub (one-to-one vs one-to-many delivery)

Actor Model ──alternative to──→ Locks / Thread Safety
      │
      └──uses──→ Message Passing (a form of Producer-Consumer)

Optimistic Locking ──tension──→ Pessimistic Locking
         │                              │
         └──both solve──→ Concurrent write conflicts
```

---

## Common Mistakes

1. **Awaiting sequentially when operations are independent** — the single most common performance bug in async TypeScript code.
2. **Forgetting that `await` is a suspension point** — shared state can change between two awaits, even in single-threaded Node.js.
3. **Blocking the event loop with synchronous computation** — freezes the entire server for all concurrent requests.
4. **Fire-and-forget promises without error handling** — floating promises that swallow errors silently.
5. **Using unbounded queues** — deferred out-of-memory crashes under load.
6. **Optimistic locking without retry limits** — retry storms under high contention.
7. **Adding locks where immutability would suffice** — unnecessary complexity.

---

## Key Takeaway

In Node.js, you get thread safety for free — the event loop is single-threaded. But you do NOT get concurrency safety for free. Async race conditions (shared state modified across await boundaries) are just as real as thread-based race conditions. Understanding the event loop, choosing the right async pattern, and being deliberate about shared state are the skills that separate reliable concurrent systems from fragile ones.
