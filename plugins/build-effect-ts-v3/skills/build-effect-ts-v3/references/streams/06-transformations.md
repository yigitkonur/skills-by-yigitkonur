# Stream Transformations
Transform stream elements lazily with pure, effectful, filtering, slicing, and stateful operators.

## Pure Mapping

Use `Stream.map` for pure element-to-element transformations.
The function should not perform asynchronous work or throw.
If a transformation can fail, model it as an effect and use `Stream.mapEffect`.

```typescript
import { Stream } from "effect"

const labels = Stream.fromIterable([1, 2, 3]).pipe(
  Stream.map((n) => `item-${n}`)
)
```

## Effectful Mapping

Use `Stream.mapEffect` when each element needs an Effect.
Bound concurrency when work can overlap.
Use sequential mapping when order and pressure matter more than throughput.

```typescript
import { Effect, Stream } from "effect"

declare const loadName: (id: number) => Effect.Effect<string, "LoadNameFailed">

const names = Stream.fromIterable([1, 2, 3]).pipe(
  Stream.mapEffect((id) => loadName(id), { concurrency: 2 })
)
```

## Filtering

Use `Stream.filter` for pure predicates.
For optional parsing, use `Stream.filterMap` when source confirms the helper exists in your target version; otherwise map to `Option` and flatten with available combinators.
Keep predicates total and side-effect free.

```typescript
import { Stream } from "effect"

const even = Stream.fromIterable([1, 2, 3, 4]).pipe(
  Stream.filter((n) => n % 2 === 0)
)
```

## Take And Drop

`Stream.take(n)` bounds a stream to the first `n` elements.
`Stream.drop(n)` skips a prefix.
Use `take` before `runCollect` when the source might be infinite or very large.

```typescript
import { Stream } from "effect"

const page = Stream.iterate(1, (n) => n + 1).pipe(
  Stream.drop(20),
  Stream.take(10)
)
```

## Scanning

`Stream.scan` emits intermediate states.
Use it for running totals, progress, or state snapshots.
If you only need the final state, prefer `Stream.runFold` at the consumer boundary.

```typescript
import { Stream } from "effect"

const totals = Stream.fromIterable([1, 2, 3]).pipe(
  Stream.scan(0, (sum, n) => sum + n)
)
```

## Accumulating With Output

`Stream.mapAccum` threads state while emitting a transformed value.
It is the stream equivalent of a stateful map.
Keep the state local to the combinator rather than mutating a variable outside the stream.

```typescript
import { Stream } from "effect"

const indexed = Stream.fromIterable(["a", "b", "c"]).pipe(
  Stream.mapAccum(0, (index, value) => [index + 1, `${index}:${value}`])
)
```

## Chunk Awareness

Stream elements are not necessarily source chunks.
Operators generally preserve element semantics while the runtime may process chunks internally.
Use chunk-specific operators only when chunk shape is part of the behaviour.
For batching, use `grouped` or `groupedWithin` rather than relying on source chunk boundaries.

## Ordering

Pure mapping and sequential `mapEffect` preserve order.
Concurrent `mapEffect` preserves output order unless `unordered: true` is supplied.
Use unordered only when downstream does not care about element order and latency matters.

## Failure Widening

A pure `map` does not add typed failures.
An effectful map widens the stream error channel with the effect error.
Do not collapse errors to strings just to simplify a stream signature.
Keep domain failures typed until a boundary translates them.

## Transformation Checklist

Choose the smallest operator that communicates intent.
Use `map` for pure transformations.
Use `mapEffect` for effectful transformations.
Use `filter` for pure exclusion.
Use `take` to make large or infinite streams finite.
Use `scan` when intermediate state matters.
Use `mapAccum` when each output depends on prior state.

## Generation Checklist
- 06-transformations check 01: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 06-transformations check 02: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 06-transformations check 03: Confirm Channel is justified by low-level read/write or parser needs.
- 06-transformations check 04: Confirm Channel examples do not expose application services to type-parameter noise.
- 06-transformations check 05: Confirm broadcast branches are consumed within the scope that created them.
- 06-transformations check 06: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 06-transformations check 07: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 06-transformations check 08: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 06-transformations check 09: Confirm examples avoid runtime entry points inside service code.
- 06-transformations check 10: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 06-transformations check 11: Confirm examples use `Effect.log` instead of direct platform logging.
- 06-transformations check 12: Confirm no typed error is represented by a thrown exception.
- 06-transformations check 13: Confirm absence is represented with `Option`, not nullish domain fields.
- 06-transformations check 14: Confirm resource acquisition happens during stream consumption, not declaration.
- 06-transformations check 15: Confirm finalizers run on completion, failure, and interruption.
- 06-transformations check 16: Confirm queue shutdown is enabled only when the stream owns the queue.
- 06-transformations check 17: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 06-transformations check 18: Confirm schedule-backed examples are finite in tests.
- 06-transformations check 19: Confirm `runCollect` is never used as the default for unknown-size streams.
- 06-transformations check 20: Confirm `runFold` is preferred when only an accumulator is required.
- 06-transformations check 21: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 06-transformations check 22: Confirm `runForEach` does not hide parallelism requirements.
- 06-transformations check 23: Confirm source-backed notes override cached community skill guidance.
- 06-transformations check 24: Confirm links route to adjacent positive guidance and anti-patterns.
- 06-transformations check 25: Confirm no v4-only token appears in prose or examples.
- 06-transformations check 26: Confirm no deprecated schema import appears in examples.
- 06-transformations check 27: Confirm examples stay small enough for agents to adapt safely.
- 06-transformations check 28: Confirm code comments explain only non-obvious stream semantics.
- 06-transformations check 29: Confirm the stream type parameters widen visibly when effects are introduced.
- 06-transformations check 30: Confirm service requirements are provided at composition boundaries.
- 06-transformations check 31: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 06-transformations check 32: Confirm unbounded buffers are rejected unless input size is already proven small.
- 06-transformations check 33: Confirm finite examples remain deterministic under test execution.
- 06-transformations check 34: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 06-transformations check 35: Confirm every file ends with 2-5 useful cross-reference links.
- 06-transformations check 36: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 06-transformations check 37: Confirm examples do not depend on unshown global mutable state.
- 06-transformations check 38: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 06-transformations check 39: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 06-transformations check 40: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 06-transformations check 41: Confirm the destructor matches whether all values, one value, or only effects matter.
- 06-transformations check 42: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 06-transformations check 43: Confirm a callback or queue source has a named capacity and shutdown owner.
- 06-transformations check 44: Confirm typed failures remain in the stream or effect error channel.
- 06-transformations check 45: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 06-transformations check 46: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 06-transformations check 47: Confirm any page cursor is immutable state returned by the pagination function.
- 06-transformations check 48: Confirm page fetching is lazy and can stop after downstream `take`.
- 06-transformations check 49: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 06-transformations check 50: Confirm unordered output is selected only when downstream order is irrelevant.
- 06-transformations check 51: Confirm `merge` termination is deliberate when either side can be infinite.
- 06-transformations check 52: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 06-transformations check 53: Confirm `zip` is used for positional alignment, not state synchronization.
- 06-transformations check 54: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 06-transformations check 55: Confirm batches are sized from an API, pool, or latency limit.
- 06-transformations check 56: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 06-transformations check 57: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 06-transformations check 58: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 06-transformations check 59: Confirm `orElse` is used only when the error value is not needed.
- 06-transformations check 60: Confirm a sink is warranted instead of a simpler stream destructor.
- 06-transformations check 61: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 06-transformations check 62: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 06-transformations check 63: Confirm Channel is justified by low-level read/write or parser needs.
- 06-transformations check 64: Confirm Channel examples do not expose application services to type-parameter noise.
- 06-transformations check 65: Confirm broadcast branches are consumed within the scope that created them.
- 06-transformations check 66: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 06-transformations check 67: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 06-transformations check 68: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 06-transformations check 69: Confirm examples avoid runtime entry points inside service code.
- 06-transformations check 70: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 06-transformations check 71: Confirm examples use `Effect.log` instead of direct platform logging.
- 06-transformations check 72: Confirm no typed error is represented by a thrown exception.
- 06-transformations check 73: Confirm absence is represented with `Option`, not nullish domain fields.
- 06-transformations check 74: Confirm resource acquisition happens during stream consumption, not declaration.
- 06-transformations check 75: Confirm finalizers run on completion, failure, and interruption.
- 06-transformations check 76: Confirm queue shutdown is enabled only when the stream owns the queue.
- 06-transformations check 77: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 06-transformations check 78: Confirm schedule-backed examples are finite in tests.
- 06-transformations check 79: Confirm `runCollect` is never used as the default for unknown-size streams.
- 06-transformations check 80: Confirm `runFold` is preferred when only an accumulator is required.
- 06-transformations check 81: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 06-transformations check 82: Confirm `runForEach` does not hide parallelism requirements.
- 06-transformations check 83: Confirm source-backed notes override cached community skill guidance.
- 06-transformations check 84: Confirm links route to adjacent positive guidance and anti-patterns.
- 06-transformations check 85: Confirm no v4-only token appears in prose or examples.
- 06-transformations check 86: Confirm no deprecated schema import appears in examples.
- 06-transformations check 87: Confirm examples stay small enough for agents to adapt safely.
- 06-transformations check 88: Confirm code comments explain only non-obvious stream semantics.
- 06-transformations check 89: Confirm the stream type parameters widen visibly when effects are introduced.
- 06-transformations check 90: Confirm service requirements are provided at composition boundaries.
- 06-transformations check 91: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 06-transformations check 92: Confirm unbounded buffers are rejected unless input size is already proven small.
- 06-transformations check 93: Confirm finite examples remain deterministic under test execution.
- 06-transformations check 94: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 06-transformations check 95: Confirm every file ends with 2-5 useful cross-reference links.

## Cross-references
See also: [05-stream-pagination.md](05-stream-pagination.md), [07-flattening.md](07-flattening.md), [09-mapEffect-concurrency.md](09-mapEffect-concurrency.md), [10-stream-consumption.md](10-stream-consumption.md).
