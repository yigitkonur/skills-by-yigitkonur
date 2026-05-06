# Stream Consumption
Choose a stream destructor that matches memory, termination, and result-shape requirements.

## Destructors Run Streams

A Stream is only a description until it is consumed.
Destructors return Effects.
Library code should usually return streams or effects, not call runtime entry points directly.
Application edges decide when to run the final Effect.

## runCollect

`Stream.runCollect` consumes the entire stream and returns `Effect<Chunk<A>, E, R>`.
It returns a `Chunk`, not an Array.
Use it for finite streams where retaining every value is intended.
Do not use it on infinite streams without `Stream.take`.

```typescript
import { Chunk, Effect, Stream } from "effect"

const stream = Stream.fromIterable([1, 2, 3])

const collected: Effect.Effect<Chunk.Chunk<number>> = Stream.runCollect(stream)
```

## runDrain

`Stream.runDrain` consumes the stream for effects and discards emitted values.
Use it for logging pipelines, subscriptions, writes, or health loops where output values are not needed.
It still waits for stream completion, so infinite streams need interruption or an explicit bound.

```typescript
import { Effect, Stream } from "effect"

const program = Stream.fromIterable(["a", "b"]).pipe(
  Stream.tap((value) => Effect.log(value)),
  Stream.runDrain
)
```

## runForEach

`Stream.runForEach` applies an effectful function to every emitted element.
It is the direct consumption form when processing each element is the goal.
Keep expensive per-element effects bounded upstream with `mapEffect` only when parallelism is needed.

```typescript
import { Effect, Stream } from "effect"

const program = Stream.fromIterable([1, 2, 3]).pipe(
  Stream.runForEach((n) => Effect.log(`value=${n}`))
)
```

## runFold

`Stream.runFold` consumes the stream into one accumulated value.
Use it when retaining all values would be wasteful.
The fold function is pure; use effectful fold variants when each accumulation step needs an Effect.

```typescript
import { Stream } from "effect"

const total = Stream.fromIterable([1, 2, 3]).pipe(
  Stream.runFold(0, (sum, n) => sum + n)
)
```

## runHead

`Stream.runHead` consumes enough of the stream to produce the first element as `Option.Option<A>`.
It is the canonical destructor when only the first value matters.
It is also a safe way to touch an infinite stream without collecting it.

```typescript
import { Stream } from "effect"

const first = Stream.iterate(1, (n) => n + 1).pipe(
  Stream.runHead
)
```

## run With Sink

`Stream.run(stream, sink)` consumes a stream with a `Sink`.
Use this when consumption has reusable reducer logic, short-circuiting, leftovers, or composition with other sinks.
Sinks are especially useful for collecting a prefix, counting, summing, folding, and effectful per-element handling.

```typescript
import { Sink, Stream } from "effect"

const firstThree = Stream.run(
  Stream.fromIterable([1, 2, 3, 4]),
  Sink.take(3)
)
```

## Memory Rule

`runCollect` stores all emitted elements.
`runFold` stores only the accumulator.
`runForEach` stores whatever the per-element effect stores.
`runDrain` stores no emitted values.
`runHead` stores at most the first value.
Pick the destructor before choosing transformations.

## Edge Rule

In a service, return the `Effect` produced by a destructor or return the `Stream` itself.
Do not call runtime entry points in the middle of business logic.
This keeps cancellation, tracing, requirements, and typed failures visible to the caller.

## Generation Checklist
- 10-stream-consumption check 01: Confirm Channel examples do not expose application services to type-parameter noise.
- 10-stream-consumption check 02: Confirm broadcast branches are consumed within the scope that created them.
- 10-stream-consumption check 03: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 10-stream-consumption check 04: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 10-stream-consumption check 05: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 10-stream-consumption check 06: Confirm examples avoid runtime entry points inside service code.
- 10-stream-consumption check 07: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 10-stream-consumption check 08: Confirm examples use `Effect.log` instead of direct platform logging.
- 10-stream-consumption check 09: Confirm no typed error is represented by a thrown exception.
- 10-stream-consumption check 10: Confirm absence is represented with `Option`, not nullish domain fields.
- 10-stream-consumption check 11: Confirm resource acquisition happens during stream consumption, not declaration.
- 10-stream-consumption check 12: Confirm finalizers run on completion, failure, and interruption.
- 10-stream-consumption check 13: Confirm queue shutdown is enabled only when the stream owns the queue.
- 10-stream-consumption check 14: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 10-stream-consumption check 15: Confirm schedule-backed examples are finite in tests.
- 10-stream-consumption check 16: Confirm `runCollect` is never used as the default for unknown-size streams.
- 10-stream-consumption check 17: Confirm `runFold` is preferred when only an accumulator is required.
- 10-stream-consumption check 18: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 10-stream-consumption check 19: Confirm `runForEach` does not hide parallelism requirements.
- 10-stream-consumption check 20: Confirm source-backed notes override cached community skill guidance.
- 10-stream-consumption check 21: Confirm links route to adjacent positive guidance and anti-patterns.
- 10-stream-consumption check 22: Confirm no v4-only token appears in prose or examples.
- 10-stream-consumption check 23: Confirm no deprecated schema import appears in examples.
- 10-stream-consumption check 24: Confirm examples stay small enough for agents to adapt safely.
- 10-stream-consumption check 25: Confirm code comments explain only non-obvious stream semantics.
- 10-stream-consumption check 26: Confirm the stream type parameters widen visibly when effects are introduced.
- 10-stream-consumption check 27: Confirm service requirements are provided at composition boundaries.
- 10-stream-consumption check 28: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 10-stream-consumption check 29: Confirm unbounded buffers are rejected unless input size is already proven small.
- 10-stream-consumption check 30: Confirm finite examples remain deterministic under test execution.
- 10-stream-consumption check 31: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 10-stream-consumption check 32: Confirm every file ends with 2-5 useful cross-reference links.
- 10-stream-consumption check 33: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 10-stream-consumption check 34: Confirm examples do not depend on unshown global mutable state.
- 10-stream-consumption check 35: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 10-stream-consumption check 36: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 10-stream-consumption check 37: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 10-stream-consumption check 38: Confirm the destructor matches whether all values, one value, or only effects matter.
- 10-stream-consumption check 39: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 10-stream-consumption check 40: Confirm a callback or queue source has a named capacity and shutdown owner.
- 10-stream-consumption check 41: Confirm typed failures remain in the stream or effect error channel.
- 10-stream-consumption check 42: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 10-stream-consumption check 43: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 10-stream-consumption check 44: Confirm any page cursor is immutable state returned by the pagination function.
- 10-stream-consumption check 45: Confirm page fetching is lazy and can stop after downstream `take`.
- 10-stream-consumption check 46: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 10-stream-consumption check 47: Confirm unordered output is selected only when downstream order is irrelevant.
- 10-stream-consumption check 48: Confirm `merge` termination is deliberate when either side can be infinite.
- 10-stream-consumption check 49: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 10-stream-consumption check 50: Confirm `zip` is used for positional alignment, not state synchronization.
- 10-stream-consumption check 51: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 10-stream-consumption check 52: Confirm batches are sized from an API, pool, or latency limit.
- 10-stream-consumption check 53: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 10-stream-consumption check 54: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 10-stream-consumption check 55: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 10-stream-consumption check 56: Confirm `orElse` is used only when the error value is not needed.
- 10-stream-consumption check 57: Confirm a sink is warranted instead of a simpler stream destructor.
- 10-stream-consumption check 58: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 10-stream-consumption check 59: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 10-stream-consumption check 60: Confirm Channel is justified by low-level read/write or parser needs.
- 10-stream-consumption check 61: Confirm Channel examples do not expose application services to type-parameter noise.
- 10-stream-consumption check 62: Confirm broadcast branches are consumed within the scope that created them.
- 10-stream-consumption check 63: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 10-stream-consumption check 64: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 10-stream-consumption check 65: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 10-stream-consumption check 66: Confirm examples avoid runtime entry points inside service code.
- 10-stream-consumption check 67: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 10-stream-consumption check 68: Confirm examples use `Effect.log` instead of direct platform logging.
- 10-stream-consumption check 69: Confirm no typed error is represented by a thrown exception.
- 10-stream-consumption check 70: Confirm absence is represented with `Option`, not nullish domain fields.
- 10-stream-consumption check 71: Confirm resource acquisition happens during stream consumption, not declaration.
- 10-stream-consumption check 72: Confirm finalizers run on completion, failure, and interruption.
- 10-stream-consumption check 73: Confirm queue shutdown is enabled only when the stream owns the queue.
- 10-stream-consumption check 74: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 10-stream-consumption check 75: Confirm schedule-backed examples are finite in tests.
- 10-stream-consumption check 76: Confirm `runCollect` is never used as the default for unknown-size streams.
- 10-stream-consumption check 77: Confirm `runFold` is preferred when only an accumulator is required.
- 10-stream-consumption check 78: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 10-stream-consumption check 79: Confirm `runForEach` does not hide parallelism requirements.
- 10-stream-consumption check 80: Confirm source-backed notes override cached community skill guidance.
- 10-stream-consumption check 81: Confirm links route to adjacent positive guidance and anti-patterns.
- 10-stream-consumption check 82: Confirm no v4-only token appears in prose or examples.
- 10-stream-consumption check 83: Confirm no deprecated schema import appears in examples.
- 10-stream-consumption check 84: Confirm examples stay small enough for agents to adapt safely.
- 10-stream-consumption check 85: Confirm code comments explain only non-obvious stream semantics.
- 10-stream-consumption check 86: Confirm the stream type parameters widen visibly when effects are introduced.
- 10-stream-consumption check 87: Confirm service requirements are provided at composition boundaries.
- 10-stream-consumption check 88: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 10-stream-consumption check 89: Confirm unbounded buffers are rejected unless input size is already proven small.
- 10-stream-consumption check 90: Confirm finite examples remain deterministic under test execution.
- 10-stream-consumption check 91: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 10-stream-consumption check 92: Confirm every file ends with 2-5 useful cross-reference links.
- 10-stream-consumption check 93: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.

## Cross-references
See also: [01-overview.md](01-overview.md), [11-sink.md](11-sink.md), [15-batching.md](15-batching.md), [18-infinite-streams.md](18-infinite-streams.md).
