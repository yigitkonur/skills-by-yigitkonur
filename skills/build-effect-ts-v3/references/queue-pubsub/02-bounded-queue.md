# Bounded Queue
Use `Queue.bounded` when producers must slow down instead of losing work.

## What Bounded Means

`Queue.bounded<A>(capacity)` creates a queue with fixed capacity and the
back-pressure strategy. When the queue is full, `Queue.offer` and `Queue.offerAll`
wait until consumers make room.

That suspension is the point. It keeps accepted work inside the system and
forces upstream fibers to experience saturation instead of silently discarding
messages or growing memory without bound.

```typescript
import { Effect, Queue } from "effect"

interface EmailJob {
  readonly id: string
  readonly to: string
}

const makeQueue = Queue.bounded<EmailJob>(64)
```

Use powers of two for capacity when practical. Effect's source notes that the
underlying ring buffer has optimized paths for those capacities.

## Backpressure Semantics

Bounded queues are the only Queue constructor that backpressures producers.

```typescript
import { Effect, Queue } from "effect"

const program = Effect.gen(function* () {
  const queue = yield* Queue.bounded<string>(1)

  yield* Queue.offer(queue, "first")

  const producer = Effect.gen(function* () {
    yield* Queue.offer(queue, "second")
    yield* Effect.logInfo("second offer completed")
  })

  const consumer = Effect.gen(function* () {
    yield* Effect.sleep("100 millis")
    const item = yield* Queue.take(queue)
    yield* Effect.logInfo(`took ${item}`)
  })

  yield* Effect.all([producer, consumer], {
    concurrency: 2,
    discard: true
  })
})
```

The second offer cannot complete until the consumer takes the first item. The
producer fiber is suspended; it is not busy-waiting.

## Offer Return Value

`Queue.offer(queue, value)` returns `Effect<boolean>`. For bounded queues, a
normal completed offer returns `true`. If the queue is full, the effect waits
until there is room and then returns `true`.

```typescript
import { Effect, Queue } from "effect"

const program = Effect.gen(function* () {
  const queue = yield* Queue.bounded<number>(2)

  const accepted = yield* Queue.offer(queue, 1)

  yield* Effect.logInfo(`accepted: ${accepted}`)
})
```

Treat a bounded queue offer as a delivery guarantee to the queue, not a guarantee
that processing has finished. Consumers still need to take and process the item.

## Offer All

`Queue.offerAll` follows the same strategy. For bounded queues, it places the
values in the queue and waits when capacity is exhausted.

```typescript
import { Effect, Queue } from "effect"

const program = Effect.gen(function* () {
  const queue = yield* Queue.bounded<string>(3)

  yield* Queue.offerAll(queue, ["a", "b", "c"])

  const first = yield* Queue.take(queue)

  yield* Effect.logInfo(`first item: ${first}`)
})
```

The `offerAll` call cannot complete until all values have been accepted. If the
batch is larger than available capacity and there is no consumer, a bounded
queue can intentionally suspend the producer.

## Capacity Selection

Pick capacity from the slowest downstream boundary, not from a guess.

Small capacities expose overload quickly. Large capacities absorb bursts but
increase latency because work can wait in memory. If the system must preserve
all jobs, increasing capacity is not a substitute for adding consumers or
reducing producer rate.

Good bounded queue candidates:

| Workload | Why bounded fits |
|---|---|
| payment commands | never silently drop |
| email jobs | retry or delay beats loss |
| database writes | protect the database from overload |
| file ingestion | make upstream wait during bursts |

Poor bounded queue candidates:

| Workload | Better strategy |
|---|---|
| live mouse positions | sliding |
| telemetry samples | dropping or sliding |
| cache refresh hints | dropping |

## Boundary Validation

Validate work before placing it on the queue. Once a value enters the queue,
consumers should be able to treat it as a valid command.

```typescript
import { Effect, Queue } from "effect"

interface WorkItem {
  readonly id: string
}

const enqueue = (
  queue: Queue.Enqueue<WorkItem>,
  item: WorkItem
) =>
  item.id.length === 0
    ? Effect.fail("MissingWorkId" as const)
    : Queue.offer(queue, item)
```

Use typed domain errors at the boundary. Do not enqueue partially valid values
and make every worker rediscover the same validation problem.

## Multiple Consumers

A bounded queue with multiple consumers still delivers each item to only one
consumer.

```typescript
import { Effect, Queue } from "effect"

interface Job {
  readonly id: string
}

declare const handleJob: (job: Job) => Effect.Effect<void>

const worker = (queue: Queue.Dequeue<Job>) =>
  Effect.forever(
    Effect.gen(function* () {
      const job = yield* Queue.take(queue)
      yield* handleJob(job)
    })
  )
```

Add workers when processing is parallelizable. Backpressure still applies when
all workers fall behind and the queue fills.

## Shutdown Behavior

`Queue.shutdown(queue)` interrupts fibers suspended on `offer` or `take`.
`Queue.awaitShutdown(queue)` waits until shutdown has happened.

```typescript
import { Effect, Queue } from "effect"

const program = Effect.gen(function* () {
  const queue = yield* Queue.bounded<string>(1)

  yield* Queue.shutdown(queue)
  yield* Queue.awaitShutdown(queue)
})
```

Shutdown is a coordination signal. It does not mean every already-taken item was
processed. Track worker completion separately when processing completion matters.

## Anti-patterns

Do not replace bounded queues with unbounded queues to make tests stop hanging.
That hides a real producer or consumer coordination problem.

Do not use dropping or sliding queues for required work and then ignore the
return value. The queue strategy says whether data loss is acceptable.

Do not use bounded queues for broadcast. A queue distributes work to one taker;
PubSub broadcasts messages to subscribers.

## Cross-references

See also:

- [01-overview.md](01-overview.md)
- [03-dropping-sliding-queue.md](03-dropping-sliding-queue.md)
- [04-queue-operations.md](04-queue-operations.md)
- [07-graceful-shutdown.md](07-graceful-shutdown.md)
