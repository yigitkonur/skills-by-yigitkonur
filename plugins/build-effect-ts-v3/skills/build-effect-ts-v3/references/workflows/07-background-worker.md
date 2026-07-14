# Background Worker
Build an Effect v3 background worker with queues, bounded concurrency, schedules, graceful shutdown, and test overrides.

Use this for jobs, ingestion, notification delivery, or polling loops. Model the worker as a scoped layer or main Effect so interruption drains resources predictably.

## Primitive index

| Primitive | Read first |
|---|---|
| queues, producer-consumer, shutdown | [queue-pubsub](../queue-pubsub/02-bounded-queue.md), [queue-pubsub](../queue-pubsub/06-producer-consumer.md), [queue-pubsub](../queue-pubsub/07-graceful-shutdown.md) |
| fibers, interruption, bounded concurrency | [concurrency](../concurrency/02-fork-types.md), [concurrency](../concurrency/07-bounded-parallelism.md), [concurrency](../concurrency/11-interruption.md) |
| scheduling and retry | [scheduling](../scheduling/02-built-in-schedules.md), [scheduling](../scheduling/06-effect-retry.md), [scheduling](../scheduling/09-effect-delay.md) |
| streams and backpressure | [streams](../streams/03-stream-from-queue-pubsub.md), [streams](../streams/14-backpressure.md), [streams](../streams/10-stream-consumption.md) |
| services, observability, tests | [services-layers](../services-layers/03-effect-service.md), [observability](../observability/08-metrics-counter-gauge.md), [testing](../testing/13-testing-concurrency.md) |

## 1. Package setup

```typescript
{
  "type": "module",
  "scripts": {
    "dev": "tsx src/main.ts",
    "build": "tsc -p tsconfig.json",
    "test": "vitest"
  },
  "dependencies": {
    "@effect/platform-node": "^0.90.0",
    "effect": "^3.21.2"
  },
  "devDependencies": {
    "@effect/vitest": "^0.28.0",
    "tsx": "^4.20.0",
    "typescript": "^5.9.0",
    "vitest": "^4.0.0"
  }
}
```

## 2. Entry point

`src/main.ts` runs the worker forever until interrupted.

```typescript
import { NodeRuntime } from "@effect/platform-node"
import { Effect } from "effect"
import { Worker } from "./worker.js"

Worker.run.pipe(
  Effect.provide(Worker.Default),
  NodeRuntime.runMain
)
```

If the worker is only one part of a service, expose it as a layer and use `Layer.launch`. Do not leave detached fibers unowned.

## 3. Main Effect orchestration

`src/worker.ts` creates a bounded queue, starts producers, and processes with explicit concurrency.

```typescript
import { Effect, Metric, Queue, Schedule, Schema } from "effect"

export class Job extends Schema.Class<Job>("Job")({
  id: Schema.String,
  payload: Schema.String
}) {}

const processed = Metric.counter("jobs_processed")

export class Worker extends Effect.Service<Worker>()("app/Worker", {
  effect: Effect.gen(function*() {
    const queue = yield* Queue.bounded<Job>(100)

    const enqueue = (job: Job) => Queue.offer(queue, job)

    const poll = Effect.gen(function*() {
      const job = new Job({ id: `job-${Date.now()}`, payload: "sync" })
      yield* enqueue(job)
    }).pipe(Effect.repeat(Schedule.spaced("10 seconds")))

    const handle = (job: Job) =>
      Effect.gen(function*() {
        yield* Effect.logInfo("processing job", { id: job.id })
        yield* Metric.increment(processed)
      }).pipe(
        Effect.retry(Schedule.exponential("100 millis").pipe(Schedule.compose(Schedule.recurs(3))))
      )

    const consume = Queue.take(queue).pipe(
      Effect.flatMap(handle),
      Effect.forever
    )

    const run = Effect.gen(function*() {
      yield* Effect.logInfo("worker starting")
      yield* Effect.all([poll, consume, consume, consume], { concurrency: 4 })
    })

    return { enqueue, run } as const
  })
}) {}
```

The queue is bounded so producers backpressure instead of growing memory without limit. Add a dead-letter service before adding broad retries.

## 4. Per-feature service definitions

Split external effects into services as soon as jobs touch real systems.

```typescript
import { Effect, Schema } from "effect"

export class Notification extends Schema.Class<Notification>("Notification")({
  recipient: Schema.String,
  body: Schema.String
}) {}

export class Notifier extends Effect.Service<Notifier>()("app/Notifier", {
  effect: Effect.succeed({
    send: (notification: Notification) =>
      Effect.logInfo("notification sent", { recipient: notification.recipient })
  })
}) {}
```

Then have `Worker` depend on `Notifier` and call `notifier.send` from `handle`. This keeps queue mechanics separate from job effects.

## 5. Layer wiring

```typescript
import { Layer } from "effect"
import { Notifier } from "./notifier.js"
import { Worker } from "./worker.js"

export const WorkerLayer = Worker.Default.pipe(
  Layer.provide(Notifier.Default)
)
```

If the worker uses SQL, HTTP clients, or caches, provide those at the same edge. Keep lifetime-sensitive dependencies scoped.

## 6. Test layer override

Use a test notifier and `TestClock` for schedules. This avoids waiting for wall-clock time.

```typescript
import { it } from "@effect/vitest"
import { Effect, Layer } from "effect"
import { Notifier } from "../src/notifier.js"
import { Job, Worker } from "../src/worker.js"

const NotifierTest = Layer.succeed(Notifier, {
  send: () => Effect.void
})

it.effect("enqueues a job", () =>
  Effect.gen(function*() {
    const worker = yield* Worker
    const accepted = yield* worker.enqueue(new Job({ id: "j1", payload: "test" }))
    expect(accepted).toBe(true)
  }).pipe(Effect.provide(Worker.Default), Effect.provide(NotifierTest))
)
```

For concurrent workers, assert bounded parallelism with controlled latches or semaphores. See [Latch](../concurrency/10-latch.md) and [Semaphore](../concurrency/08-semaphore.md).

## Workflow checklist

1. Use a bounded queue.
2. Choose worker concurrency explicitly.
3. Own every fiber through the main Effect or a layer.
4. Use schedules for polling.
5. Use retries around idempotent work only.
6. Add shutdown tests before deploying.
7. Keep external systems behind services.
8. Record job metrics at the handler boundary.

## 7. Deployment

Run background workers as separate processes from HTTP APIs unless the platform guarantees graceful shutdown for both. Give the process a termination grace period long enough for in-flight jobs to finish or requeue. In distributed deployments, move the queue to durable infrastructure and keep the same `Worker` service shape.

## Cross-references

See also: [microservice](06-microservice.md), [greenfield CLI](01-greenfield-cli.md), [MCP server](08-mcp-server.md), [queue overview](../queue-pubsub/01-overview.md).
