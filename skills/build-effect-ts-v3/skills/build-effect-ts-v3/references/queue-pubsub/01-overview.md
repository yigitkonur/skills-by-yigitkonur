# Queue and PubSub Overview
Use `Queue` for work distribution and `PubSub` for broadcast between fibers.

## Mental Model

`Queue<A>` is a fiber-safe asynchronous queue. Producers `offer` values and
consumers `take` values. A value taken by one consumer is removed from the
queue, so queues are the right primitive for work distribution.

`PubSub<A>` is a fiber-safe asynchronous hub. Publishers `publish` values and
each active subscriber receives the published values through its own
subscription queue. PubSub is the right primitive for broadcast.

The biggest design choice is overflow behavior. Bounded queues backpressure.
Dropping, sliding, and unbounded queues do not backpressure. They trade delivery
guarantees or memory safety for producer progress.

## Decision Tree

Use this before choosing a constructor:

```text
Need every item processed?
  yes -> need producer backpressure when full?
    yes -> Queue.bounded
    no  -> Queue.unbounded, only for controlled input size
  no -> can lose new items when full?
    yes -> Queue.dropping
    no  -> can lose oldest buffered items when full?
      yes -> Queue.sliding
      no  -> Queue.bounded

Need every subscriber to see each message?
  yes -> PubSub
  no  -> Queue
```

Short version: need backpressure -> bounded; do not care about some messages ->
sliding or dropping; broadcast -> PubSub.

## Queue Constructors

```typescript
import { Queue } from "effect"

const bounded = Queue.bounded<string>(64)
const dropping = Queue.dropping<string>(64)
const sliding = Queue.sliding<string>(64)
const unbounded = Queue.unbounded<string>()
```

Constructor behavior:

| Constructor | Capacity | Overflow | Backpressure |
|---|---:|---|---|
| `Queue.bounded` | fixed | producer waits | yes |
| `Queue.dropping` | fixed | new item is dropped | no |
| `Queue.sliding` | fixed | oldest item is dropped | no |
| `Queue.unbounded` | unlimited | grows memory | no |

Only `Queue.bounded` suspends the offering fiber when full. Dropping and sliding
queues are still capacity-limited, but they resolve overflow by discarding
messages.

## Basic Queue Flow

```typescript
import { Effect, Queue } from "effect"

interface Job {
  readonly id: string
}

const program = Effect.gen(function* () {
  const queue = yield* Queue.bounded<Job>(64)

  yield* Queue.offer(queue, { id: "job-1" })

  const job = yield* Queue.take(queue)

  yield* Effect.logInfo(`processing ${job.id}`)
})
```

`Queue.offer` returns `Effect<boolean>`. For bounded queues it succeeds after
the item is accepted, possibly after waiting. For dropping queues it can return
`false` when a new item was rejected.

## Basic PubSub Flow

```typescript
import { Effect, PubSub, Queue } from "effect"

const program = Effect.gen(function* () {
  const bus = yield* PubSub.bounded<string>(16)

  yield* Effect.scoped(
    Effect.gen(function* () {
      const subscription = yield* PubSub.subscribe(bus)

      yield* PubSub.publish(bus, "cache-invalidated")

      const message = yield* Queue.take(subscription)

      yield* Effect.logInfo(message)
    })
  )
})
```

`PubSub.subscribe` is scoped. The subscription is active only while the scope is
open, and it is unsubscribed when that scope closes.

## Queue vs PubSub

Use a queue when exactly one consumer should claim a piece of work.

Use PubSub when all subscribers should observe a message. Each subscriber gets a
subscription queue, so a slow subscriber can lag independently from other
subscribers.

If you use PubSub for jobs, every worker may perform the same job. If you use a
Queue for events, only one consumer sees each event. Pick based on delivery
semantics first, not API convenience.

## Overflow Is a Product Decision

Overflow strategy is not an implementation detail:

| Need | Pick |
|---|---|
| Do not drop accepted work | `Queue.bounded` |
| Keep producer latency low and newest value is optional | `Queue.dropping` |
| Keep most recent values and old values are stale | `Queue.sliding` |
| Broadcast state changes or notifications | `PubSub` |
| Absorb a small known burst | `Queue.unbounded`, only with bounded input |

Never silently drop messages that represent work, money, audits, commands, or
user-visible state transitions. Use bounded queues and let backpressure tell
callers the system is saturated.

## Common Mistakes

Do not assume all queues backpressure. Only bounded queues use the back-pressure
strategy.

Do not use dropping or sliding queues for required work. Their entire purpose is
to discard on overflow.

Do not create a PubSub subscription outside `Effect.scoped`. Subscriptions need a
scope so they can be removed when the subscriber exits.

Do not use an unbounded queue as a default. It prevents producer suspension by
moving pressure into memory growth.

## Cross-references

See also:

- [02-bounded-queue.md](02-bounded-queue.md)
- [03-dropping-sliding-queue.md](03-dropping-sliding-queue.md)
- [05-pubsub.md](05-pubsub.md)
- [06-producer-consumer.md](06-producer-consumer.md)
