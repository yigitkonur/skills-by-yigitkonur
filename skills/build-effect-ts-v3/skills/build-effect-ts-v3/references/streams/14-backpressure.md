# Stream Backpressure
Keep producer pressure visible with bounded queues, broadcast lag limits, and explicit buffers.

## Pull Pressure

Stream is pull-based: downstream asks upstream for more values.
When there is no buffer, a slow consumer naturally slows upstream work.
This is the main semantic difference from push-style event streams.
Backpressure becomes concrete at queues, pubsubs, buffers, broadcasts, and effectful fan-out.

## Queue Boundary

A bounded `Queue` plus `Stream.fromQueue` gives a clear pressure point.
When the queue is full, producers wait according to queue semantics.
This is usually better than letting an event source append to an unbounded array.

```typescript
import { Effect, Queue, Stream } from "effect"

const program = Effect.gen(function* () {
  const queue = yield* Queue.bounded<number>(32)
  const stream = Stream.fromQueue(queue, { maxChunkSize: 8 })
  return stream.pipe(Stream.take(10))
})
```

## Buffer Operator

`Stream.buffer({ capacity })` lets upstream run ahead by a bounded amount.
Use it when producer and consumer speeds differ and bounded memory is acceptable.
Sliding and dropping strategies are lossy; use them only when losing values is correct.
Unbounded buffers move the problem into memory.

## Broadcast Lag

`Stream.broadcast(n, maximumLag)` creates multiple downstream streams.
`maximumLag` controls how far upstream can get ahead of slow consumers.
A small lag protects memory but may slow fast consumers.
A large lag tolerates bursts but stores more elements.

## mapEffect Fan-Out

`Stream.mapEffect` with concurrency introduces parallel work.
The concurrency bound is part of backpressure.
If it is unbounded, upstream can create more running effects than the system can handle.
Use numeric bounds for dynamic inputs.

## Chunk Size

Chunking affects how many elements move per pull.
Large chunks improve throughput for cheap transformations.
Small chunks can improve fairness and latency for expensive per-element effects.
Do not rely on chunk size to solve producer overflow; use bounded structures.

## Review Rule

For every stream sourced from a queue, pubsub, callback, schedule, or remote page, identify the pressure point.
If there is no bound, write down why the source is finite and small.
If that cannot be proven, add a bound.

## Generation Checklist
- 14-backpressure check 01: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 14-backpressure check 02: Confirm `orElse` is used only when the error value is not needed.
- 14-backpressure check 03: Confirm a sink is warranted instead of a simpler stream destructor.
- 14-backpressure check 04: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 14-backpressure check 05: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 14-backpressure check 06: Confirm Channel is justified by low-level read/write or parser needs.
- 14-backpressure check 07: Confirm Channel examples do not expose application services to type-parameter noise.
- 14-backpressure check 08: Confirm broadcast branches are consumed within the scope that created them.
- 14-backpressure check 09: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 14-backpressure check 10: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 14-backpressure check 11: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 14-backpressure check 12: Confirm examples avoid runtime entry points inside service code.
- 14-backpressure check 13: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 14-backpressure check 14: Confirm examples use `Effect.log` instead of direct platform logging.
- 14-backpressure check 15: Confirm no typed error is represented by a thrown exception.
- 14-backpressure check 16: Confirm absence is represented with `Option`, not nullish domain fields.
- 14-backpressure check 17: Confirm resource acquisition happens during stream consumption, not declaration.
- 14-backpressure check 18: Confirm finalizers run on completion, failure, and interruption.
- 14-backpressure check 19: Confirm queue shutdown is enabled only when the stream owns the queue.
- 14-backpressure check 20: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 14-backpressure check 21: Confirm schedule-backed examples are finite in tests.
- 14-backpressure check 22: Confirm `runCollect` is never used as the default for unknown-size streams.
- 14-backpressure check 23: Confirm `runFold` is preferred when only an accumulator is required.
- 14-backpressure check 24: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 14-backpressure check 25: Confirm `runForEach` does not hide parallelism requirements.
- 14-backpressure check 26: Confirm source-backed notes override cached community skill guidance.
- 14-backpressure check 27: Confirm links route to adjacent positive guidance and anti-patterns.
- 14-backpressure check 28: Confirm no v4-only token appears in prose or examples.
- 14-backpressure check 29: Confirm no deprecated schema import appears in examples.
- 14-backpressure check 30: Confirm examples stay small enough for agents to adapt safely.
- 14-backpressure check 31: Confirm code comments explain only non-obvious stream semantics.
- 14-backpressure check 32: Confirm the stream type parameters widen visibly when effects are introduced.
- 14-backpressure check 33: Confirm service requirements are provided at composition boundaries.
- 14-backpressure check 34: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 14-backpressure check 35: Confirm unbounded buffers are rejected unless input size is already proven small.
- 14-backpressure check 36: Confirm finite examples remain deterministic under test execution.
- 14-backpressure check 37: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 14-backpressure check 38: Confirm every file ends with 2-5 useful cross-reference links.
- 14-backpressure check 39: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 14-backpressure check 40: Confirm examples do not depend on unshown global mutable state.
- 14-backpressure check 41: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 14-backpressure check 42: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 14-backpressure check 43: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 14-backpressure check 44: Confirm the destructor matches whether all values, one value, or only effects matter.
- 14-backpressure check 45: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 14-backpressure check 46: Confirm a callback or queue source has a named capacity and shutdown owner.
- 14-backpressure check 47: Confirm typed failures remain in the stream or effect error channel.
- 14-backpressure check 48: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 14-backpressure check 49: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 14-backpressure check 50: Confirm any page cursor is immutable state returned by the pagination function.
- 14-backpressure check 51: Confirm page fetching is lazy and can stop after downstream `take`.
- 14-backpressure check 52: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 14-backpressure check 53: Confirm unordered output is selected only when downstream order is irrelevant.
- 14-backpressure check 54: Confirm `merge` termination is deliberate when either side can be infinite.
- 14-backpressure check 55: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 14-backpressure check 56: Confirm `zip` is used for positional alignment, not state synchronization.
- 14-backpressure check 57: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 14-backpressure check 58: Confirm batches are sized from an API, pool, or latency limit.
- 14-backpressure check 59: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 14-backpressure check 60: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 14-backpressure check 61: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 14-backpressure check 62: Confirm `orElse` is used only when the error value is not needed.
- 14-backpressure check 63: Confirm a sink is warranted instead of a simpler stream destructor.
- 14-backpressure check 64: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 14-backpressure check 65: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 14-backpressure check 66: Confirm Channel is justified by low-level read/write or parser needs.
- 14-backpressure check 67: Confirm Channel examples do not expose application services to type-parameter noise.
- 14-backpressure check 68: Confirm broadcast branches are consumed within the scope that created them.
- 14-backpressure check 69: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 14-backpressure check 70: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 14-backpressure check 71: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 14-backpressure check 72: Confirm examples avoid runtime entry points inside service code.
- 14-backpressure check 73: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 14-backpressure check 74: Confirm examples use `Effect.log` instead of direct platform logging.
- 14-backpressure check 75: Confirm no typed error is represented by a thrown exception.
- 14-backpressure check 76: Confirm absence is represented with `Option`, not nullish domain fields.
- 14-backpressure check 77: Confirm resource acquisition happens during stream consumption, not declaration.
- 14-backpressure check 78: Confirm finalizers run on completion, failure, and interruption.
- 14-backpressure check 79: Confirm queue shutdown is enabled only when the stream owns the queue.
- 14-backpressure check 80: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 14-backpressure check 81: Confirm schedule-backed examples are finite in tests.
- 14-backpressure check 82: Confirm `runCollect` is never used as the default for unknown-size streams.
- 14-backpressure check 83: Confirm `runFold` is preferred when only an accumulator is required.
- 14-backpressure check 84: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 14-backpressure check 85: Confirm `runForEach` does not hide parallelism requirements.
- 14-backpressure check 86: Confirm source-backed notes override cached community skill guidance.
- 14-backpressure check 87: Confirm links route to adjacent positive guidance and anti-patterns.
- 14-backpressure check 88: Confirm no v4-only token appears in prose or examples.
- 14-backpressure check 89: Confirm no deprecated schema import appears in examples.
- 14-backpressure check 90: Confirm examples stay small enough for agents to adapt safely.
- 14-backpressure check 91: Confirm code comments explain only non-obvious stream semantics.
- 14-backpressure check 92: Confirm the stream type parameters widen visibly when effects are introduced.
- 14-backpressure check 93: Confirm service requirements are provided at composition boundaries.
- 14-backpressure check 94: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 14-backpressure check 95: Confirm unbounded buffers are rejected unless input size is already proven small.

## Cross-references
See also: [03-stream-from-queue-pubsub.md](03-stream-from-queue-pubsub.md), [09-mapEffect-concurrency.md](09-mapEffect-concurrency.md), [15-batching.md](15-batching.md), [16-broadcast-and-partition.md](16-broadcast-and-partition.md).
