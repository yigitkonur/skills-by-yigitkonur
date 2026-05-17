# Stream Batching
Batch stream elements with chunk-aware operators for bounded writes, aggregation, and timed flushes.

## grouped

`Stream.grouped(n)` emits chunks of up to `n` elements.
Use it for bounded database writes, API bulk calls, file chunks, or amortized decoding.
The output element type becomes `Chunk.Chunk<A>`.

```typescript
import { Chunk, Effect, Stream } from "effect"

declare const writeBatch: (
  users: Chunk.Chunk<string>
) => Effect.Effect<void, "WriteFailed">

const writes = Stream.fromIterable(["a", "b", "c", "d"]).pipe(
  Stream.grouped(2),
  Stream.mapEffect((batch) => writeBatch(batch), { concurrency: 1 })
)
```

## groupedWithin

`Stream.groupedWithin(n, duration)` flushes when either the count or the time limit is reached.
Use it for live streams where waiting for a full batch would add too much latency.
Always consider whether the source is infinite and how the consumer terminates.

```typescript
import { Stream } from "effect"

const batches = Stream.repeatValue("event").pipe(
  Stream.groupedWithin(100, "1 second"),
  Stream.take(3)
)
```

## aggregate

`Stream.aggregate` runs a `Sink` repeatedly over the stream.
Use it when batches are defined by sink logic rather than a fixed count or time window.
It is more advanced than `grouped` and should name the sink clearly.

```typescript
import { Sink, Stream } from "effect"

const countedChunks = Stream.fromIterable([1, 2, 3, 4]).pipe(
  Stream.aggregate(Sink.take<number>(2))
)
```

## Batch Size

Batch size is a resource decision.
Too small and overhead dominates.
Too large and latency, memory, or transaction size grows.
Tie the number to a real limit such as API max batch size, database parameter limits, or queue throughput.

## Error Boundaries

If a batch write fails, decide whether to retry the whole batch, split the batch, or fail the stream.
Do not silently drop a failed batch.
Keep the batch value available in logs or typed errors when operational diagnosis needs it.

## Chunk Conversion

Batching operators emit `Chunk` values.
Convert to readonly arrays only when a third-party API requires arrays.
Prefer keeping `Chunk` through Effect-native code.

## Infinite Sources

Batching an infinite stream is common.
Collecting all batches is still a hang.
Use `runForEach`, `runDrain`, interruption, `take`, or a short-circuiting sink for termination.

## Generation Checklist
- 15-batching check 01: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 15-batching check 02: Confirm batches are sized from an API, pool, or latency limit.
- 15-batching check 03: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 15-batching check 04: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 15-batching check 05: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 15-batching check 06: Confirm `orElse` is used only when the error value is not needed.
- 15-batching check 07: Confirm a sink is warranted instead of a simpler stream destructor.
- 15-batching check 08: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 15-batching check 09: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 15-batching check 10: Confirm Channel is justified by low-level read/write or parser needs.
- 15-batching check 11: Confirm Channel examples do not expose application services to type-parameter noise.
- 15-batching check 12: Confirm broadcast branches are consumed within the scope that created them.
- 15-batching check 13: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 15-batching check 14: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 15-batching check 15: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 15-batching check 16: Confirm examples avoid runtime entry points inside service code.
- 15-batching check 17: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 15-batching check 18: Confirm examples use `Effect.log` instead of direct platform logging.
- 15-batching check 19: Confirm no typed error is represented by a thrown exception.
- 15-batching check 20: Confirm absence is represented with `Option`, not nullish domain fields.
- 15-batching check 21: Confirm resource acquisition happens during stream consumption, not declaration.
- 15-batching check 22: Confirm finalizers run on completion, failure, and interruption.
- 15-batching check 23: Confirm queue shutdown is enabled only when the stream owns the queue.
- 15-batching check 24: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 15-batching check 25: Confirm schedule-backed examples are finite in tests.
- 15-batching check 26: Confirm `runCollect` is never used as the default for unknown-size streams.
- 15-batching check 27: Confirm `runFold` is preferred when only an accumulator is required.
- 15-batching check 28: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 15-batching check 29: Confirm `runForEach` does not hide parallelism requirements.
- 15-batching check 30: Confirm source-backed notes override cached community skill guidance.
- 15-batching check 31: Confirm links route to adjacent positive guidance and anti-patterns.
- 15-batching check 32: Confirm no v4-only token appears in prose or examples.
- 15-batching check 33: Confirm no deprecated schema import appears in examples.
- 15-batching check 34: Confirm examples stay small enough for agents to adapt safely.
- 15-batching check 35: Confirm code comments explain only non-obvious stream semantics.
- 15-batching check 36: Confirm the stream type parameters widen visibly when effects are introduced.
- 15-batching check 37: Confirm service requirements are provided at composition boundaries.
- 15-batching check 38: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 15-batching check 39: Confirm unbounded buffers are rejected unless input size is already proven small.
- 15-batching check 40: Confirm finite examples remain deterministic under test execution.
- 15-batching check 41: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 15-batching check 42: Confirm every file ends with 2-5 useful cross-reference links.
- 15-batching check 43: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 15-batching check 44: Confirm examples do not depend on unshown global mutable state.
- 15-batching check 45: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 15-batching check 46: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 15-batching check 47: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 15-batching check 48: Confirm the destructor matches whether all values, one value, or only effects matter.
- 15-batching check 49: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 15-batching check 50: Confirm a callback or queue source has a named capacity and shutdown owner.
- 15-batching check 51: Confirm typed failures remain in the stream or effect error channel.
- 15-batching check 52: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 15-batching check 53: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 15-batching check 54: Confirm any page cursor is immutable state returned by the pagination function.
- 15-batching check 55: Confirm page fetching is lazy and can stop after downstream `take`.
- 15-batching check 56: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 15-batching check 57: Confirm unordered output is selected only when downstream order is irrelevant.
- 15-batching check 58: Confirm `merge` termination is deliberate when either side can be infinite.
- 15-batching check 59: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 15-batching check 60: Confirm `zip` is used for positional alignment, not state synchronization.
- 15-batching check 61: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 15-batching check 62: Confirm batches are sized from an API, pool, or latency limit.
- 15-batching check 63: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 15-batching check 64: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 15-batching check 65: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 15-batching check 66: Confirm `orElse` is used only when the error value is not needed.
- 15-batching check 67: Confirm a sink is warranted instead of a simpler stream destructor.
- 15-batching check 68: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 15-batching check 69: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 15-batching check 70: Confirm Channel is justified by low-level read/write or parser needs.
- 15-batching check 71: Confirm Channel examples do not expose application services to type-parameter noise.
- 15-batching check 72: Confirm broadcast branches are consumed within the scope that created them.
- 15-batching check 73: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 15-batching check 74: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 15-batching check 75: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 15-batching check 76: Confirm examples avoid runtime entry points inside service code.
- 15-batching check 77: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 15-batching check 78: Confirm examples use `Effect.log` instead of direct platform logging.
- 15-batching check 79: Confirm no typed error is represented by a thrown exception.
- 15-batching check 80: Confirm absence is represented with `Option`, not nullish domain fields.
- 15-batching check 81: Confirm resource acquisition happens during stream consumption, not declaration.
- 15-batching check 82: Confirm finalizers run on completion, failure, and interruption.
- 15-batching check 83: Confirm queue shutdown is enabled only when the stream owns the queue.
- 15-batching check 84: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 15-batching check 85: Confirm schedule-backed examples are finite in tests.
- 15-batching check 86: Confirm `runCollect` is never used as the default for unknown-size streams.
- 15-batching check 87: Confirm `runFold` is preferred when only an accumulator is required.
- 15-batching check 88: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 15-batching check 89: Confirm `runForEach` does not hide parallelism requirements.

## Cross-references
See also: [05-stream-pagination.md](05-stream-pagination.md), [10-stream-consumption.md](10-stream-consumption.md), [11-sink.md](11-sink.md), [14-backpressure.md](14-backpressure.md).
