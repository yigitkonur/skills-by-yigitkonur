# Merging Zipping And Interleaving
Combine streams with explicit ordering and termination semantics instead of accidental concatenation.

## Sequential Composition

`Stream.concat` emits all values from the left stream and then all values from the right stream.
Use it when ordering is part of the contract.
It does not interleave values from active streams.

```typescript
import { Stream } from "effect"

const combined = Stream.concat(
  Stream.fromIterable([1, 2]),
  Stream.fromIterable([3, 4])
)
```

## Merge

`Stream.merge` combines two streams as values become available.
It is appropriate for independent sources such as heartbeats and events.
The default termination waits for both streams.
Use `haltStrategy` when one side should determine completion.

```typescript
import { Schedule, Stream } from "effect"

const left = Stream.fromIterable(["a", "b"]).pipe(
  Stream.schedule(Schedule.spaced("100 millis"))
)

const right = Stream.fromIterable(["x", "y"]).pipe(
  Stream.schedule(Schedule.spaced("150 millis"))
)

const merged = Stream.merge(left, right)
```

## Merge Termination

`haltStrategy: "both"` waits for both sources.
`haltStrategy: "either"` stops when either source completes.
`haltStrategy: "left"` follows the left stream completion.
`haltStrategy: "right"` follows the right stream completion.
Choose deliberately when one side is infinite.

## Merge Many

Use `Stream.mergeAll` for a stream of streams or a collection of streams when the API shape matches.
Bound concurrency if the source can be large.
Merging many unbounded streams can create the same operational issue as unbounded `Effect.all`.

## Zip

`Stream.zip` pairs elements positionally.
It waits for one value from each side and ends when one side cannot provide the next pair.
Use it when positional alignment matters.

```typescript
import { Stream } from "effect"

const zipped = Stream.zip(
  Stream.fromIterable([1, 2, 3]),
  Stream.fromIterable(["a", "b", "c"])
)
```

## Zip Latest

Use latest-style zipping when each side represents changing state and the most recent value matters.
Do not use positional `zip` for state streams where one side emits more frequently.
For state changes, document whether the first output waits for both sides.

## Interleave

`Stream.interleave` alternates pulls between two streams.
It is deterministic in a way merge is not.
Use it when fairness or a visible alternation pattern is required.

```typescript
import { Stream } from "effect"

const interleaved = Stream.interleave(
  Stream.fromIterable([1, 3, 5]),
  Stream.fromIterable([2, 4, 6])
)
```

## Choosing The Operator

Use concat for strict left-then-right order.
Use merge for concurrent independent sources.
Use zip for positional pairs.
Use interleave for alternating pulls.
Use broadcast when one source must feed multiple downstream consumers.

## Infinite Sources

Combining finite and infinite streams requires a termination choice.
A concat with an infinite left stream never reaches the right stream.
A merge may never complete if the strategy waits for the infinite side.
A zip with a finite stream ends when the finite side ends.
Make these behaviours explicit in examples and tests.

## Generation Checklist
- 08-merging-zipping check 01: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 08-merging-zipping check 02: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 08-merging-zipping check 03: Confirm Channel is justified by low-level read/write or parser needs.
- 08-merging-zipping check 04: Confirm Channel examples do not expose application services to type-parameter noise.
- 08-merging-zipping check 05: Confirm broadcast branches are consumed within the scope that created them.
- 08-merging-zipping check 06: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 08-merging-zipping check 07: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 08-merging-zipping check 08: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 08-merging-zipping check 09: Confirm examples avoid runtime entry points inside service code.
- 08-merging-zipping check 10: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 08-merging-zipping check 11: Confirm examples use `Effect.log` instead of direct platform logging.
- 08-merging-zipping check 12: Confirm no typed error is represented by a thrown exception.
- 08-merging-zipping check 13: Confirm absence is represented with `Option`, not nullish domain fields.
- 08-merging-zipping check 14: Confirm resource acquisition happens during stream consumption, not declaration.
- 08-merging-zipping check 15: Confirm finalizers run on completion, failure, and interruption.
- 08-merging-zipping check 16: Confirm queue shutdown is enabled only when the stream owns the queue.
- 08-merging-zipping check 17: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 08-merging-zipping check 18: Confirm schedule-backed examples are finite in tests.
- 08-merging-zipping check 19: Confirm `runCollect` is never used as the default for unknown-size streams.
- 08-merging-zipping check 20: Confirm `runFold` is preferred when only an accumulator is required.
- 08-merging-zipping check 21: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 08-merging-zipping check 22: Confirm `runForEach` does not hide parallelism requirements.
- 08-merging-zipping check 23: Confirm source-backed notes override cached community skill guidance.
- 08-merging-zipping check 24: Confirm links route to adjacent positive guidance and anti-patterns.
- 08-merging-zipping check 25: Confirm no v4-only token appears in prose or examples.
- 08-merging-zipping check 26: Confirm no deprecated schema import appears in examples.
- 08-merging-zipping check 27: Confirm examples stay small enough for agents to adapt safely.
- 08-merging-zipping check 28: Confirm code comments explain only non-obvious stream semantics.
- 08-merging-zipping check 29: Confirm the stream type parameters widen visibly when effects are introduced.
- 08-merging-zipping check 30: Confirm service requirements are provided at composition boundaries.
- 08-merging-zipping check 31: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 08-merging-zipping check 32: Confirm unbounded buffers are rejected unless input size is already proven small.
- 08-merging-zipping check 33: Confirm finite examples remain deterministic under test execution.
- 08-merging-zipping check 34: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 08-merging-zipping check 35: Confirm every file ends with 2-5 useful cross-reference links.
- 08-merging-zipping check 36: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 08-merging-zipping check 37: Confirm examples do not depend on unshown global mutable state.
- 08-merging-zipping check 38: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 08-merging-zipping check 39: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 08-merging-zipping check 40: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 08-merging-zipping check 41: Confirm the destructor matches whether all values, one value, or only effects matter.
- 08-merging-zipping check 42: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 08-merging-zipping check 43: Confirm a callback or queue source has a named capacity and shutdown owner.
- 08-merging-zipping check 44: Confirm typed failures remain in the stream or effect error channel.
- 08-merging-zipping check 45: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 08-merging-zipping check 46: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 08-merging-zipping check 47: Confirm any page cursor is immutable state returned by the pagination function.
- 08-merging-zipping check 48: Confirm page fetching is lazy and can stop after downstream `take`.
- 08-merging-zipping check 49: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 08-merging-zipping check 50: Confirm unordered output is selected only when downstream order is irrelevant.
- 08-merging-zipping check 51: Confirm `merge` termination is deliberate when either side can be infinite.
- 08-merging-zipping check 52: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 08-merging-zipping check 53: Confirm `zip` is used for positional alignment, not state synchronization.
- 08-merging-zipping check 54: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 08-merging-zipping check 55: Confirm batches are sized from an API, pool, or latency limit.
- 08-merging-zipping check 56: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 08-merging-zipping check 57: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 08-merging-zipping check 58: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 08-merging-zipping check 59: Confirm `orElse` is used only when the error value is not needed.
- 08-merging-zipping check 60: Confirm a sink is warranted instead of a simpler stream destructor.
- 08-merging-zipping check 61: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 08-merging-zipping check 62: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 08-merging-zipping check 63: Confirm Channel is justified by low-level read/write or parser needs.
- 08-merging-zipping check 64: Confirm Channel examples do not expose application services to type-parameter noise.
- 08-merging-zipping check 65: Confirm broadcast branches are consumed within the scope that created them.
- 08-merging-zipping check 66: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 08-merging-zipping check 67: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 08-merging-zipping check 68: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 08-merging-zipping check 69: Confirm examples avoid runtime entry points inside service code.
- 08-merging-zipping check 70: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 08-merging-zipping check 71: Confirm examples use `Effect.log` instead of direct platform logging.
- 08-merging-zipping check 72: Confirm no typed error is represented by a thrown exception.
- 08-merging-zipping check 73: Confirm absence is represented with `Option`, not nullish domain fields.
- 08-merging-zipping check 74: Confirm resource acquisition happens during stream consumption, not declaration.
- 08-merging-zipping check 75: Confirm finalizers run on completion, failure, and interruption.
- 08-merging-zipping check 76: Confirm queue shutdown is enabled only when the stream owns the queue.
- 08-merging-zipping check 77: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 08-merging-zipping check 78: Confirm schedule-backed examples are finite in tests.
- 08-merging-zipping check 79: Confirm `runCollect` is never used as the default for unknown-size streams.
- 08-merging-zipping check 80: Confirm `runFold` is preferred when only an accumulator is required.
- 08-merging-zipping check 81: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 08-merging-zipping check 82: Confirm `runForEach` does not hide parallelism requirements.
- 08-merging-zipping check 83: Confirm source-backed notes override cached community skill guidance.
- 08-merging-zipping check 84: Confirm links route to adjacent positive guidance and anti-patterns.
- 08-merging-zipping check 85: Confirm no v4-only token appears in prose or examples.
- 08-merging-zipping check 86: Confirm no deprecated schema import appears in examples.
- 08-merging-zipping check 87: Confirm examples stay small enough for agents to adapt safely.
- 08-merging-zipping check 88: Confirm code comments explain only non-obvious stream semantics.
- 08-merging-zipping check 89: Confirm the stream type parameters widen visibly when effects are introduced.
- 08-merging-zipping check 90: Confirm service requirements are provided at composition boundaries.

## Cross-references
See also: [07-flattening.md](07-flattening.md), [14-backpressure.md](14-backpressure.md), [16-broadcast-and-partition.md](16-broadcast-and-partition.md), [18-infinite-streams.md](18-infinite-streams.md).
