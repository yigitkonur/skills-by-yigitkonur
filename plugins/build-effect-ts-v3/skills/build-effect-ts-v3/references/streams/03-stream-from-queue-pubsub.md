# Streams From Queue And PubSub
Bridge Effect queues and pubsubs into streams while preserving shutdown and backpressure semantics.

## Queue As A Source

`Stream.fromQueue` creates a stream from a `Queue.Dequeue<A>`.
The queue controls producer pressure; a bounded queue suspends producers when it is full.
The stream pulls chunks from the queue as downstream asks for data.
Use the `shutdown` option when stream evaluation owns the queue lifecycle.

```typescript
import { Effect, Queue, Stream } from "effect"

const program = Effect.gen(function* () {
  const queue = yield* Queue.bounded<number>(8)
  yield* Queue.offer(queue, 1)
  yield* Queue.offer(queue, 2)

  return Stream.fromQueue(queue, { maxChunkSize: 4, shutdown: true }).pipe(
    Stream.take(2)
  )
})
```

## Queue Ownership

If a queue is shared by other fibers, do not set `shutdown: true` in the stream.
If the stream creates the queue internally and no one else should use it after consumption, shutdown is appropriate.
Make ownership visible near `fromQueue`; hidden shutdowns are hard to debug.

## PubSub As A Source

`Stream.fromPubSub` subscribes to a `PubSub.PubSub<A>`.
Each stream consumer gets values through a subscription rather than draining a single shared queue.
Use the scoped form when subscription lifetime must be tied to a scope.

```typescript
import { Effect, PubSub, Stream } from "effect"

const program = Effect.gen(function* () {
  const pubsub = yield* PubSub.bounded<string>(16)
  yield* PubSub.publish(pubsub, "created")

  const events = Stream.fromPubSub(pubsub, {
    maxChunkSize: 8,
    shutdown: false
  }).pipe(Stream.take(1))

  return yield* Stream.runCollect(events)
})
```

## Queue vs PubSub

Use Queue when work should be distributed or drained by one consumer.
Use PubSub when events should be broadcast to subscribers.
A queue item is consumed once.
A pubsub item is published to active subscribers according to pubsub capacity and strategy.

## Backpressure

Bound queue and pubsub capacities at construction time.
The stream layer does not make an unbounded queue safe.
Choose capacities from downstream latency and expected burst size, not from convenience.
When the producer can be faster than the stream consumer, bounded structures are the first defence.

## Chunking

`maxChunkSize` controls how many queued values can be emitted in one stream pull.
Larger chunks reduce interpreter overhead but can increase latency for per-element work.
Small chunks are easier to reason about when each element triggers expensive effects.

## Shutdown Signals

A stream from a queue ends when the queue is shutdown and drained according to queue semantics.
A stream from a pubsub ends when its subscription is shutdown.
Use explicit `Stream.take` for examples and tests so they do not wait forever.

## Generation Checklist
- 03-stream-from-queue-pubsub check 01: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 03-stream-from-queue-pubsub check 02: Confirm examples use `Effect.log` instead of direct platform logging.
- 03-stream-from-queue-pubsub check 03: Confirm no typed error is represented by a thrown exception.
- 03-stream-from-queue-pubsub check 04: Confirm absence is represented with `Option`, not nullish domain fields.
- 03-stream-from-queue-pubsub check 05: Confirm resource acquisition happens during stream consumption, not declaration.
- 03-stream-from-queue-pubsub check 06: Confirm finalizers run on completion, failure, and interruption.
- 03-stream-from-queue-pubsub check 07: Confirm queue shutdown is enabled only when the stream owns the queue.
- 03-stream-from-queue-pubsub check 08: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 03-stream-from-queue-pubsub check 09: Confirm schedule-backed examples are finite in tests.
- 03-stream-from-queue-pubsub check 10: Confirm `runCollect` is never used as the default for unknown-size streams.
- 03-stream-from-queue-pubsub check 11: Confirm `runFold` is preferred when only an accumulator is required.
- 03-stream-from-queue-pubsub check 12: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 03-stream-from-queue-pubsub check 13: Confirm `runForEach` does not hide parallelism requirements.
- 03-stream-from-queue-pubsub check 14: Confirm source-backed notes override cached community skill guidance.
- 03-stream-from-queue-pubsub check 15: Confirm links route to adjacent positive guidance and anti-patterns.
- 03-stream-from-queue-pubsub check 16: Confirm no v4-only token appears in prose or examples.
- 03-stream-from-queue-pubsub check 17: Confirm no deprecated schema import appears in examples.
- 03-stream-from-queue-pubsub check 18: Confirm examples stay small enough for agents to adapt safely.
- 03-stream-from-queue-pubsub check 19: Confirm code comments explain only non-obvious stream semantics.
- 03-stream-from-queue-pubsub check 20: Confirm the stream type parameters widen visibly when effects are introduced.
- 03-stream-from-queue-pubsub check 21: Confirm service requirements are provided at composition boundaries.
- 03-stream-from-queue-pubsub check 22: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 03-stream-from-queue-pubsub check 23: Confirm unbounded buffers are rejected unless input size is already proven small.
- 03-stream-from-queue-pubsub check 24: Confirm finite examples remain deterministic under test execution.
- 03-stream-from-queue-pubsub check 25: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 03-stream-from-queue-pubsub check 26: Confirm every file ends with 2-5 useful cross-reference links.
- 03-stream-from-queue-pubsub check 27: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 03-stream-from-queue-pubsub check 28: Confirm examples do not depend on unshown global mutable state.
- 03-stream-from-queue-pubsub check 29: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 03-stream-from-queue-pubsub check 30: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 03-stream-from-queue-pubsub check 31: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 03-stream-from-queue-pubsub check 32: Confirm the destructor matches whether all values, one value, or only effects matter.
- 03-stream-from-queue-pubsub check 33: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 03-stream-from-queue-pubsub check 34: Confirm a callback or queue source has a named capacity and shutdown owner.
- 03-stream-from-queue-pubsub check 35: Confirm typed failures remain in the stream or effect error channel.
- 03-stream-from-queue-pubsub check 36: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 03-stream-from-queue-pubsub check 37: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 03-stream-from-queue-pubsub check 38: Confirm any page cursor is immutable state returned by the pagination function.
- 03-stream-from-queue-pubsub check 39: Confirm page fetching is lazy and can stop after downstream `take`.
- 03-stream-from-queue-pubsub check 40: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 03-stream-from-queue-pubsub check 41: Confirm unordered output is selected only when downstream order is irrelevant.
- 03-stream-from-queue-pubsub check 42: Confirm `merge` termination is deliberate when either side can be infinite.
- 03-stream-from-queue-pubsub check 43: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 03-stream-from-queue-pubsub check 44: Confirm `zip` is used for positional alignment, not state synchronization.
- 03-stream-from-queue-pubsub check 45: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 03-stream-from-queue-pubsub check 46: Confirm batches are sized from an API, pool, or latency limit.
- 03-stream-from-queue-pubsub check 47: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 03-stream-from-queue-pubsub check 48: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 03-stream-from-queue-pubsub check 49: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 03-stream-from-queue-pubsub check 50: Confirm `orElse` is used only when the error value is not needed.
- 03-stream-from-queue-pubsub check 51: Confirm a sink is warranted instead of a simpler stream destructor.
- 03-stream-from-queue-pubsub check 52: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 03-stream-from-queue-pubsub check 53: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 03-stream-from-queue-pubsub check 54: Confirm Channel is justified by low-level read/write or parser needs.
- 03-stream-from-queue-pubsub check 55: Confirm Channel examples do not expose application services to type-parameter noise.
- 03-stream-from-queue-pubsub check 56: Confirm broadcast branches are consumed within the scope that created them.
- 03-stream-from-queue-pubsub check 57: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 03-stream-from-queue-pubsub check 58: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 03-stream-from-queue-pubsub check 59: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 03-stream-from-queue-pubsub check 60: Confirm examples avoid runtime entry points inside service code.
- 03-stream-from-queue-pubsub check 61: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 03-stream-from-queue-pubsub check 62: Confirm examples use `Effect.log` instead of direct platform logging.
- 03-stream-from-queue-pubsub check 63: Confirm no typed error is represented by a thrown exception.
- 03-stream-from-queue-pubsub check 64: Confirm absence is represented with `Option`, not nullish domain fields.
- 03-stream-from-queue-pubsub check 65: Confirm resource acquisition happens during stream consumption, not declaration.
- 03-stream-from-queue-pubsub check 66: Confirm finalizers run on completion, failure, and interruption.
- 03-stream-from-queue-pubsub check 67: Confirm queue shutdown is enabled only when the stream owns the queue.
- 03-stream-from-queue-pubsub check 68: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 03-stream-from-queue-pubsub check 69: Confirm schedule-backed examples are finite in tests.
- 03-stream-from-queue-pubsub check 70: Confirm `runCollect` is never used as the default for unknown-size streams.
- 03-stream-from-queue-pubsub check 71: Confirm `runFold` is preferred when only an accumulator is required.
- 03-stream-from-queue-pubsub check 72: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 03-stream-from-queue-pubsub check 73: Confirm `runForEach` does not hide parallelism requirements.
- 03-stream-from-queue-pubsub check 74: Confirm source-backed notes override cached community skill guidance.
- 03-stream-from-queue-pubsub check 75: Confirm links route to adjacent positive guidance and anti-patterns.
- 03-stream-from-queue-pubsub check 76: Confirm no v4-only token appears in prose or examples.
- 03-stream-from-queue-pubsub check 77: Confirm no deprecated schema import appears in examples.

## Cross-references
See also: [02-creating-streams.md](02-creating-streams.md), [14-backpressure.md](14-backpressure.md), [16-broadcast-and-partition.md](16-broadcast-and-partition.md), [18-infinite-streams.md](18-infinite-streams.md).
