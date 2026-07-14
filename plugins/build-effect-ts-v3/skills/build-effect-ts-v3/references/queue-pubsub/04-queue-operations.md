# Queue Operations
Use Queue operations to enqueue, dequeue, inspect, and shut down fiber-safe work queues.

## Core Operations

The common Queue operations are:

| Operation | Effect | Suspends when |
|---|---|---|
| `Queue.offer` | enqueue one value | bounded queue is full |
| `Queue.offerAll` | enqueue many values | bounded queue is full |
| `Queue.take` | dequeue one value | queue is empty |
| `Queue.takeAll` | dequeue everything currently buffered | never for emptiness |
| `Queue.takeUpTo` | dequeue up to a maximum | never for emptiness |
| `Queue.takeBetween` | dequeue between min and max | fewer than min available |
| `Queue.poll` | try to dequeue one value | never for emptiness |
| `Queue.shutdown` | interrupt waiters and close queue | never |

`Queue.Dequeue<A>` also extends `Effect.Effect<A>`, so yielding a dequeue value
directly is equivalent to taking one item. Prefer `Queue.take(queue)` in examples
and shared code because it is more explicit.

## Offer

```typescript
import { Effect, Queue } from "effect"

interface Job {
  readonly id: string
}

const enqueue = (queue: Queue.Enqueue<Job>, job: Job) =>
  Queue.offer(queue, job)

const program = Effect.gen(function* () {
  const queue = yield* Queue.bounded<Job>(16)

  const accepted = yield* enqueue(queue, { id: "job-1" })

  yield* Effect.logInfo(`accepted: ${accepted}`)
})
```

The meaning of `accepted` depends on the strategy. Bounded and sliding queues
normally return `true`; dropping queues return `false` when the new item is
dropped.

## Offer All

```typescript
import { Effect, Queue } from "effect"

const program = Effect.gen(function* () {
  const queue = yield* Queue.bounded<number>(4)

  yield* Queue.offerAll(queue, [1, 2, 3])

  const first = yield* Queue.take(queue)

  yield* Effect.logInfo(`first: ${first}`)
})
```

Use `offerAll` for a finite batch. For large dynamic collections, prefer a
bounded producer loop so backpressure is applied between items.

## Take

`Queue.take(queue)` suspends when the queue is empty and resumes when a producer
offers an item.

```typescript
import { Effect, Queue } from "effect"

const worker = (queue: Queue.Dequeue<string>) =>
  Effect.gen(function* () {
    const item = yield* Queue.take(queue)
    yield* Effect.logInfo(`received ${item}`)
  })
```

This is the primitive behind long-running workers. Wrap it in `Effect.forever`
only when the surrounding scope owns worker lifetime.

## Take All

`Queue.takeAll(queue)` drains the currently buffered values and returns an empty
chunk when the queue is empty.

```typescript
import { Chunk, Effect, Queue } from "effect"

const drainNow = (queue: Queue.Dequeue<string>) =>
  Effect.gen(function* () {
    const items = yield* Queue.takeAll(queue)

    yield* Effect.logInfo(`drained ${Chunk.size(items)} items`)
  })
```

Use `takeAll` for opportunistic draining. It does not wait for future values.

## Take Up To

`Queue.takeUpTo(queue, max)` takes up to `max` currently available values. It can
return fewer than `max`, including zero.

```typescript
import { Chunk, Effect, Queue } from "effect"

const takeBatch = (queue: Queue.Dequeue<string>) =>
  Effect.gen(function* () {
    const batch = yield* Queue.takeUpTo(queue, 100)

    yield* Effect.logInfo(`batch size: ${Chunk.size(batch)}`)
  })
```

Use this for non-blocking batch pulls after a worker has already taken at least
one item or on a periodic flush loop.

## Take Between

Use `takeBetween` when a batch should wait for a minimum size but can process
less than the maximum.

```typescript
import { Chunk, Effect, Queue } from "effect"

const takeUsefulBatch = (queue: Queue.Dequeue<string>) =>
  Effect.gen(function* () {
    const batch = yield* Queue.takeBetween(queue, 5, 50)

    yield* Effect.logInfo(`useful batch: ${Chunk.size(batch)}`)
  })
```

## Poll

`Queue.poll(queue)` returns `Option.Option<A>` and never suspends for emptiness.

```typescript
import { Effect, Option, Queue } from "effect"

const pollOnce = (queue: Queue.Dequeue<string>) =>
  Effect.gen(function* () {
    const maybeItem = yield* Queue.poll(queue)

    yield* Option.match(maybeItem, {
      onNone: () => Effect.logInfo("no item available"),
      onSome: (item) => Effect.logInfo(`polled ${item}`)
    })
  })
```

Use `poll` when the caller has useful work to do if the queue is empty. Use
`take` when the caller should wait.

## Inspection

`Queue.size`, `Queue.isEmpty`, `Queue.isFull`, and `Queue.capacity` are useful
for diagnostics. Do not use them as a correctness check before `offer` or `take`;
the state can change between inspection and action.

`Queue.size` may be negative when fibers are suspended waiting for elements, so
use it for reporting rather than admission control.

## Shutdown

```typescript
import { Effect, Queue } from "effect"

const closeQueue = (queue: Queue.Queue<string>) =>
  Effect.gen(function* () {
    yield* Queue.shutdown(queue)
    yield* Queue.awaitShutdown(queue)
  })
```

After shutdown, pending and future offers or takes are interrupted. Use shutdown
to stop queue users; use worker joins or other coordination to prove processing
finished.

## Cross-references

See also:

- [02-bounded-queue.md](02-bounded-queue.md)
- [03-dropping-sliding-queue.md](03-dropping-sliding-queue.md)
- [06-producer-consumer.md](06-producer-consumer.md)
- [07-graceful-shutdown.md](07-graceful-shutdown.md)
