# Graceful Shutdown
Use queue shutdown to stop waiters, then coordinate worker completion explicitly.

## What Shutdown Does

`Queue.shutdown(queue)` interrupts fibers suspended on `offer` or `take`.
`Queue.awaitShutdown(queue)` waits until shutdown has happened.

Shutdown closes the communication primitive. It does not prove that every item
already taken by a worker has finished processing.

```typescript
import { Effect, Queue } from "effect"

const closeQueue = (queue: Queue.Queue<string>) =>
  Effect.gen(function* () {
    yield* Queue.shutdown(queue)
    yield* Queue.awaitShutdown(queue)
  })
```

Use shutdown to release blocked producers and consumers during service teardown.

## Interrupting Takers

A worker blocked on `Queue.take` is interrupted when the queue shuts down.

```typescript
import { Effect, Queue } from "effect"

const program = Effect.gen(function* () {
  const queue = yield* Queue.bounded<string>(1)

  const worker = yield* Effect.fork(
    Effect.forever(
      Effect.gen(function* () {
        const item = yield* Queue.take(queue)
        yield* Effect.logInfo(`received ${item}`)
      })
    )
  )

  yield* Queue.shutdown(queue)
  yield* Queue.awaitShutdown(queue)
  yield* worker.await
})
```

The worker does not need a sentinel value just to escape a blocked take. Queue
shutdown is the stop signal for waiters.

## Interrupting Offers

A producer blocked because a bounded queue is full is also interrupted by
shutdown.

```typescript
import { Effect, Queue } from "effect"

const program = Effect.gen(function* () {
  const queue = yield* Queue.bounded<string>(1)

  yield* Queue.offer(queue, "first")

  const producer = yield* Effect.fork(Queue.offer(queue, "second"))

  yield* Queue.shutdown(queue)
  yield* Queue.awaitShutdown(queue)
  yield* producer.await
})
```

This matters for bounded queues because they are the only queues that
backpressure producers on capacity.

## Drain Before Shutdown

If you need to stop accepting new work but finish buffered work, use an
application-level gate before queue shutdown. Queue shutdown is abrupt for
blocked queue operations.

```typescript
import { Chunk, Effect, Queue } from "effect"

const drainBuffered = (queue: Queue.Dequeue<string>) =>
  Effect.gen(function* () {
    const remaining = yield* Queue.takeAll(queue)

    yield* Effect.logInfo(`remaining items: ${Chunk.size(remaining)}`)
  })
```

Draining only sees values still buffered. Items already taken by workers are no
longer in the queue.

## PubSub Shutdown

PubSub has the same shutdown shape:

```typescript
import { Effect, PubSub } from "effect"

const closePubSub = (bus: PubSub.PubSub<string>) =>
  Effect.gen(function* () {
    yield* PubSub.shutdown(bus)
    yield* PubSub.awaitShutdown(bus)
  })
```

Use PubSub shutdown to close the hub. Use scope closure to unsubscribe an
individual subscription.

## Scoped Subscription Lifetime

PubSub subscriptions must be scoped, and scope closure unsubscribes them.

```typescript
import { Effect, PubSub, Queue } from "effect"

const useSubscription = (bus: PubSub.PubSub<string>) =>
  Effect.scoped(
    Effect.gen(function* () {
      const subscription = yield* PubSub.subscribe(bus)

      yield* PubSub.publish(bus, "hello")

      const message = yield* Queue.take(subscription)

      yield* Effect.logInfo(message)
    })
  )
```

After `Effect.scoped` completes, the subscription is removed even if the PubSub
itself remains active.

## Shutdown Checklist

Use this order for required work:

1. Stop accepting new external requests.
2. Let producers finish or interrupt them deliberately.
3. Wait for workers that already took work if processing completion matters.
4. Drain buffered items only if your domain has a safe place to put them.
5. Shut down the Queue or PubSub to release blocked waiters.
6. Await shutdown before releasing dependent resources.

Do not treat queue shutdown as a graceful drain by itself.

## Cross-references

See also:

- [02-bounded-queue.md](02-bounded-queue.md)
- [04-queue-operations.md](04-queue-operations.md)
- [05-pubsub.md](05-pubsub.md)
- [06-producer-consumer.md](06-producer-consumer.md)
