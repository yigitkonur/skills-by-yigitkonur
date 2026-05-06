# Dropping and Sliding Queues
Use dropping or sliding queues only when losing messages is an explicit choice.

## The Non-backpressure Rule

Dropping, sliding, and unbounded queues do not backpressure producers.

Only `Queue.bounded` suspends the producer when the queue is full. Dropping and
sliding queues have fixed capacity, but they resolve overflow by discarding
messages instead of making the producer wait.

This is the most important rule in this file: if the message must not be lost,
do not use dropping or sliding.

## Dropping Queue

`Queue.dropping<A>(capacity)` keeps the existing buffered values and rejects new
values when full.

```typescript
import { Effect, Queue } from "effect"

const program = Effect.gen(function* () {
  const queue = yield* Queue.dropping<string>(1)

  yield* Queue.offer(queue, "kept")
  const accepted = yield* Queue.offer(queue, "dropped")

  yield* Effect.logInfo(`second accepted: ${accepted}`)
})
```

For a dropping queue, an overflowed `offer` returns `false`. The producer keeps
running; no backpressure is applied.

Use dropping when a missing update is acceptable and keeping producer latency low
is more important than preserving every value.

Good candidates:

| Workload | Why dropping fits |
|---|---|
| refresh hints | future hints can replace missed hints |
| optional telemetry | sampling loss is acceptable |
| best-effort notifications | no command semantics |

Bad candidates:

| Workload | Risk |
|---|---|
| billing events | data loss |
| user commands | visible lost action |
| audit records | compliance failure |

## Sliding Queue

`Queue.sliding<A>(capacity)` accepts the new value and drops old buffered values
when full.

```typescript
import { Effect, Queue } from "effect"

const program = Effect.gen(function* () {
  const queue = yield* Queue.sliding<string>(1)

  yield* Queue.offer(queue, "old")
  const accepted = yield* Queue.offer(queue, "new")
  const current = yield* Queue.take(queue)

  yield* Effect.logInfo(`accepted: ${accepted}`)
  yield* Effect.logInfo(`current: ${current}`)
})
```

The second offer returns `true`, and the queue contains `"new"`. The older value
was discarded to make room.

Use sliding when only the latest state matters.

Good candidates:

| Workload | Why sliding fits |
|---|---|
| cursor positions | stale positions are useless |
| latest metrics snapshot | newest observation wins |
| progress percentage | old progress values are obsolete |

Bad candidates:

| Workload | Risk |
|---|---|
| tasks | old tasks disappear |
| domain events | history becomes incomplete |
| retry commands | failed work can vanish |

## Dropping vs Sliding

Pick based on which value is more important during overflow.

| Question | Pick |
|---|---|
| Existing buffered work is more valuable than new work | `Queue.dropping` |
| New state is more valuable than old buffered state | `Queue.sliding` |
| All values are required | `Queue.bounded` |

Dropping protects the queue contents. Sliding protects freshness.

## Offer All Behavior

`Queue.offerAll` follows the same strategy.

For dropping queues, values that do not fit are not enqueued and the effect can
return `false`.

For sliding queues, new values are accepted by evicting old values and the effect
returns `true`.

```typescript
import { Effect, Queue } from "effect"

const program = Effect.gen(function* () {
  const queue = yield* Queue.dropping<number>(2)

  const accepted = yield* Queue.offerAll(queue, [1, 2, 3])

  yield* Effect.logInfo(`all accepted: ${accepted}`)
})
```

Do not ignore the boolean from dropping queues. It is the only signal that an
offered item was discarded.

## Unbounded Is Also No Backpressure

`Queue.unbounded<A>()` never blocks producers because of queue capacity. That can
be appropriate for a small, known finite input, but it is not a safe default for
open-ended streams of work.

```typescript
import { Queue } from "effect"

const queue = Queue.unbounded<string>()
```

Unbounded queues move overload into memory. If consumers cannot keep up, the
process can grow until it fails outside the Effect error channel.

## Make Data Loss Visible

When using dropping queues, name the result.

```typescript
import { Effect, Queue } from "effect"

const enqueueMetric = (
  queue: Queue.Enqueue<string>,
  metric: string
) =>
  Effect.gen(function* () {
    const accepted = yield* Queue.offer(queue, metric)

    yield* Effect.logInfo(`metric accepted: ${accepted}`)
  })
```

That log line is not required in every production path, but the design should
make loss visible somewhere: counters, traces, or explicit return values.

## Anti-patterns

Do not say "bounded dropping queue backpressures." It is capacity-limited, but it
does not backpressure.

Do not use sliding queues for work queues because "latest worker will catch up."
Sliding drops old work.

Do not switch from bounded to dropping to fix slow tests unless the product
semantics permit data loss.

## Cross-references

See also:

- [01-overview.md](01-overview.md)
- [02-bounded-queue.md](02-bounded-queue.md)
- [04-queue-operations.md](04-queue-operations.md)
- [06-producer-consumer.md](06-producer-consumer.md)
