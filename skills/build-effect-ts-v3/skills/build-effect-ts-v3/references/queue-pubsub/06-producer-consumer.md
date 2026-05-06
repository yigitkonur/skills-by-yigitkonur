# Producer Consumer Patterns
Use bounded queues to connect producers and worker fibers without losing work.

## Default Pattern

For required work, start with a bounded queue and a fixed worker count.

The bounded queue is the pressure boundary. Producers suspend when all workers
fall behind and the queue fills. That is usually better than silently dropping
work or letting memory grow.

## Workers From Bounded Queue

This is the standard workers-from-bounded-queue pattern.

```typescript
import { Deferred, Effect, Fiber, Queue } from "effect"

interface Job {
  readonly id: string
  readonly completed: Deferred.Deferred<void>
}

declare const handleJob: (job: Job) => Effect.Effect<void, "JobFailed">

const worker = (
  workerId: number,
  queue: Queue.Dequeue<Job>
) =>
  Effect.forever(
    Effect.gen(function* () {
      const job = yield* Queue.take(queue)

      yield* Effect.logInfo(`worker ${workerId} processing ${job.id}`)
      yield* handleJob(job)
      yield* Deferred.succeed(job.completed, void 0)
    })
  )

const program = Effect.gen(function* () {
  const queue = yield* Queue.bounded<Job>(64)
  const firstDone = yield* Deferred.make<void>()
  const secondDone = yield* Deferred.make<void>()

  const workers = yield* Effect.all(
    [
      Effect.fork(worker(1, queue)),
      Effect.fork(worker(2, queue)),
      Effect.fork(worker(3, queue)),
      Effect.fork(worker(4, queue))
    ]
  )

  yield* Queue.offer(queue, { id: "job-1", completed: firstDone })
  yield* Queue.offer(queue, { id: "job-2", completed: secondDone })

  yield* Deferred.await(firstDone)
  yield* Deferred.await(secondDone)

  yield* Fiber.interruptAll(workers)
  yield* Queue.shutdown(queue)
})
```

Each job is taken by one worker. The `Deferred` values are just a local proof
that this example waits for both submitted jobs before interrupting workers.
When the queue reaches capacity, producers offering more jobs wait until a
worker takes something.

In production, interrupt workers at service shutdown, not immediately after
submitting jobs. The snippet keeps lifetime visible in one place.

## Producer Function

Expose a narrow enqueue function instead of the whole queue when producers only
need to submit work.

```typescript
import { Effect, Queue } from "effect"

interface Job {
  readonly id: string
}

const makeProducer = (queue: Queue.Enqueue<Job>) =>
  (job: Job) =>
    Effect.gen(function* () {
      const accepted = yield* Queue.offer(queue, job)

      yield* Effect.logInfo(`job accepted: ${accepted}`)
    })
```

Use `Queue.Enqueue<A>` for producer-only access and `Queue.Dequeue<A>` for
consumer-only access. That keeps accidental operations out of callers.

## Batch After First Item

A common batching pattern is to block for the first item, then opportunistically
take more items that are already buffered.

```typescript
import { Chunk, Effect, Queue } from "effect"

interface Job {
  readonly id: string
}

declare const handleBatch: (
  jobs: ReadonlyArray<Job>
) => Effect.Effect<void, "BatchFailed">

const batchWorker = (queue: Queue.Dequeue<Job>) =>
  Effect.forever(
    Effect.gen(function* () {
      const first = yield* Queue.take(queue)
      const rest = yield* Queue.takeUpTo(queue, 49)

      yield* handleBatch([first, ...Chunk.toReadonlyArray(rest)])
    })
  )
```

This avoids spinning on empty queues while still coalescing bursts into batches.

## Fan-out With PubSub

Use PubSub when several independent consumers must all observe the same event.

```typescript
import { Effect, PubSub, Queue } from "effect"

interface Event {
  readonly name: string
}

const subscriber = (
  label: string,
  bus: PubSub.PubSub<Event>
) =>
  Effect.scoped(
    Effect.gen(function* () {
      const subscription = yield* PubSub.subscribe(bus)

      yield* Effect.forkScoped(
        Effect.forever(
          Effect.gen(function* () {
            const event = yield* Queue.take(subscription)
            yield* Effect.logInfo(`${label}: ${event.name}`)
          })
        )
      )

      yield* Effect.sleep("1 second")
    })
  )
```

Do not use PubSub for competing workers unless duplicate processing is intended.

## Producer Backpressure

Backpressure is observable at the producer boundary.

```typescript
import { Effect, Queue } from "effect"

const submitAll = (
  queue: Queue.Enqueue<string>,
  items: ReadonlyArray<string>
) =>
  Effect.gen(function* () {
    for (const item of items) {
      yield* Queue.offer(queue, item)
    }
  })
```

With a bounded queue, this loop naturally slows down when consumers fall behind.
With dropping, sliding, or unbounded queues, it does not.

## Capacity and Worker Count

Tune capacity and worker count together.

| Symptom | Change to consider |
|---|---|
| producers wait too often | add workers or reduce production rate |
| latency too high | reduce queue capacity or speed workers |
| memory grows | replace unbounded with bounded |
| stale state processed | use sliding for state updates, not jobs |

Do not treat capacity as a throughput feature. It stores waiting work; workers
create throughput.

Worker error policy is separate from queue choice. Decide whether a failed job
stops the worker, is retried, or is moved to a dead-letter path.

## Cross-references

See also:

- [01-overview.md](01-overview.md)
- [02-bounded-queue.md](02-bounded-queue.md)
- [05-pubsub.md](05-pubsub.md)
- [07-graceful-shutdown.md](07-graceful-shutdown.md)
