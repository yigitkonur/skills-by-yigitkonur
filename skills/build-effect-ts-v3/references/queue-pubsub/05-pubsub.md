# PubSub
Use `PubSub` when each active subscriber should receive each published message.

## What PubSub Is

`PubSub<A>` is an asynchronous message hub. Publishers add messages with
`publish` or `publishAll`. Subscribers call `subscribe` to receive a scoped
`Queue.Dequeue<A>`.

Unlike `Queue`, PubSub is broadcast. A published message is retained until it has
been taken by all subscribers that should receive it, subject to the chosen
overflow strategy.

Use PubSub for notifications, invalidation, event fan-out, and subscription
feeds. Do not use it for work queues unless every worker must perform every item.

## Constructors

```typescript
import { PubSub } from "effect"

const bounded = PubSub.bounded<string>(64)
const dropping = PubSub.dropping<string>(64)
const sliding = PubSub.sliding<string>(64)
const unbounded = PubSub.unbounded<string>()
```

Constructor behavior:

| Constructor | Overflow behavior |
|---|---|
| `PubSub.bounded` | applies backpressure to publishers when full |
| `PubSub.dropping` | drops new messages when full |
| `PubSub.sliding` | drops old messages when full |
| `PubSub.unbounded` | grows without capacity backpressure |

For bounded, dropping, and sliding PubSubs, capacities that are powers of two are
preferred for performance.

## Subscriptions Are Scoped

`PubSub.subscribe(pubsub)` has `Scope.Scope` in its requirements. The
subscription must be acquired inside a scope and is automatically unsubscribed
when the scope closes.

```typescript
import { Effect, PubSub, Queue } from "effect"

const program = Effect.gen(function* () {
  const bus = yield* PubSub.bounded<string>(16)

  yield* Effect.scoped(
    Effect.gen(function* () {
      const subscription = yield* PubSub.subscribe(bus)

      yield* PubSub.publish(bus, "ready")

      const message = yield* Queue.take(subscription)

      yield* Effect.logInfo(`subscriber received ${message}`)
    })
  )
})
```

Do not store a subscription beyond the scope that created it. When the scope
closes, that subscription is no longer active.

## Publish

`PubSub.publish(pubsub, value)` returns `Effect<boolean>`.

```typescript
import { Effect, PubSub } from "effect"

const notify = (bus: PubSub.PubSub<string>, message: string) =>
  Effect.gen(function* () {
    const published = yield* PubSub.publish(bus, message)

    yield* Effect.logInfo(`published: ${published}`)
  })
```

For dropping PubSub, `false` means the new message was dropped. For bounded
PubSub, publishing waits when the hub is at capacity. For sliding PubSub, newer
messages can evict older messages.

## Publish All

```typescript
import { Effect, PubSub } from "effect"

const publishBatch = (
  bus: PubSub.PubSub<string>,
  messages: ReadonlyArray<string>
) =>
  Effect.gen(function* () {
    const published = yield* PubSub.publishAll(bus, messages)

    yield* Effect.logInfo(`batch published: ${published}`)
  })
```

Use `publishAll` for finite batches. Keep the same overflow discipline you would
use for queues: dropping can reject, sliding can evict, bounded can suspend.

## Two Subscribers

Each subscriber has its own dequeue. One subscriber taking a message does not
remove that message from another subscriber.

```typescript
import { Effect, PubSub, Queue } from "effect"

const program = Effect.gen(function* () {
  const bus = yield* PubSub.bounded<string>(16)

  yield* Effect.scoped(
    Effect.gen(function* () {
      const first = yield* PubSub.subscribe(bus)
      const second = yield* PubSub.subscribe(bus)

      yield* PubSub.publish(bus, "changed")

      const firstMessage = yield* Queue.take(first)
      const secondMessage = yield* Queue.take(second)

      yield* Effect.logInfo(`first: ${firstMessage}`)
      yield* Effect.logInfo(`second: ${secondMessage}`)
    })
  )
})
```

This is the defining difference from `Queue`: both subscribers receive the same
message.

## Scoped Subscriber Fiber

Use `Effect.forkScoped` for subscriber loops owned by the same scope as the
subscription.

```typescript
import { Effect, PubSub, Queue } from "effect"

const subscriber = (bus: PubSub.PubSub<string>) =>
  Effect.scoped(
    Effect.gen(function* () {
      const subscription = yield* PubSub.subscribe(bus)

      yield* Effect.forkScoped(
        Effect.forever(
          Effect.gen(function* () {
            const message = yield* Queue.take(subscription)
            yield* Effect.logInfo(`event: ${message}`)
          })
        )
      )

      yield* PubSub.publish(bus, "started")
      yield* Effect.sleep("100 millis")
    })
  )
```

When the scoped effect completes, the forked subscriber is interrupted and the
subscription is unsubscribed.

## Replay Option

PubSub constructors accept an options object with `capacity` and optional
`replay` for bounded variants, or optional `replay` for unbounded.

```typescript
import { PubSub } from "effect"

const bus = PubSub.bounded<string>({ capacity: 64, replay: 1 })
```

Use replay deliberately. Replaying stale operational events can create confusing
behavior for new subscribers. It is most useful when the latest retained value is
part of the subscription contract.

## Shutdown and Inspection

PubSub supports queue-like inspection and shutdown operations:

```typescript
import { Effect, PubSub } from "effect"

const close = (bus: PubSub.PubSub<string>) =>
  Effect.gen(function* () {
    const size = yield* PubSub.size(bus)
    const full = yield* PubSub.isFull(bus)

    yield* Effect.logInfo(`pubsub size: ${size}, full: ${full}`)

    yield* PubSub.shutdown(bus)
    yield* PubSub.awaitShutdown(bus)
  })
```

Shutdown interrupts suspended publishers and subscribers. Scope closure
unsubscribes a subscription; PubSub shutdown closes the hub.

## Queue vs PubSub Mistakes

Do not use PubSub to distribute jobs to a worker pool. Every subscriber can see
the same job, so work can be duplicated.

Do not use Queue when every listener must observe every event. Queue consumers
compete for values.

Do not forget `Effect.scoped` around `PubSub.subscribe`. Without a scope, there
is no correct lifetime for the subscription.

## Cross-references

See also:

- [01-overview.md](01-overview.md)
- [04-queue-operations.md](04-queue-operations.md)
- [06-producer-consumer.md](06-producer-consumer.md)
- [07-graceful-shutdown.md](07-graceful-shutdown.md)
