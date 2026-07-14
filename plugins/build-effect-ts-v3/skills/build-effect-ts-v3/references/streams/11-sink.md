# Sink
Use `Sink` as the typed consumption side of Stream for reusable reducers, short-circuiting, and effectful drains.

## What A Sink Is

`Sink.Sink<A, In, L, E, R>` consumes input elements of type `In` and eventually produces `A`.
It may leave leftovers `L`, fail with `E`, and require `R`.
Use it when consumption logic should be named, reused, composed, or short-circuiting.
For one-off per-element effects, `Stream.runForEach` can be simpler.

## Running A Sink

Use `Stream.run(stream, sink)` to consume with a sink.
The result is an Effect with the sink result type.
The stream error and sink error are both represented in the resulting failure channel.

```typescript
import { Sink, Stream } from "effect"

const count = Stream.run(
  Stream.fromIterable(["a", "b", "c"]),
  Sink.count
)
```

## Primitive Sinks

- `Sink.collectAll<In>()` collects every input into a `Chunk.Chunk<In>`.
- `Sink.collectAllN<In>(n)` collects the first `n` inputs into a chunk and may leave the rest.
- `Sink.count` counts all consumed inputs.
- `Sink.sum` sums numeric inputs.
- `Sink.drain` consumes and discards inputs.
- `Sink.head<In>()` returns the first input as `Option.Option<In>`.
- `Sink.last<In>()` returns the last input as `Option.Option<In>`.
- `Sink.take<In>(n)` takes `n` values and returns them as a chunk.
- `Sink.foldLeft(initial, f)` reduces all inputs into one value.
- `Sink.forEach(f)` runs an effect for each input and returns void.
- `Sink.succeed(value)` finishes with a constant value.
- `Sink.fail(error)` fails with a typed sink error.

## Collecting

Use collection sinks only for finite or explicitly bounded streams.
Like `Stream.runCollect`, collection sinks retain values in memory.
For large streams, prefer folding, draining, or batching upstream.

```typescript
import { Sink, Stream } from "effect"

const firstTwo = Stream.run(
  Stream.fromIterable([1, 2, 3]),
  Sink.collectAllN<number>(2)
)
```

## Short-Circuiting

Some sinks finish before the upstream stream ends.
`Sink.head`, `Sink.take`, and bounded fold variants can short-circuit.
This is useful for infinite streams because consumption can stop once the sink has enough input.

```typescript
import { Sink, Stream } from "effect"

const first = Stream.run(
  Stream.iterate(1, (n) => n + 1),
  Sink.head<number>()
)
```

## Folding

Use `Sink.foldLeft` for pure accumulation.
Use `Sink.fold` when a continuation predicate should stop consumption.
Use `Sink.foldUntil` when a fixed maximum number of elements should be consumed.
Keep accumulator types explicit when the initial value is ambiguous.

```typescript
import { Sink, Stream } from "effect"

const total = Stream.run(
  Stream.fromIterable([1, 2, 3]),
  Sink.foldLeft(0, (sum, n) => sum + n)
)
```

## Mapping Results

Use `Sink.map` to transform the final result.
Use `Sink.mapEffect` when final result transformation needs an Effect.
Use input mapping combinators when the sink should accept a different input shape.
Avoid wrapping a stream transformation inside a sink if a stream operator is clearer.

## Input Adaptation

Sink input adaptation lets a reusable sink consume a projected field.
The v3 source exports `Sink.mapInput`, `Sink.mapInputEffect`, `Sink.mapInputChunks`, `Sink.dimap`, and `Sink.dimapEffect`.
It does not export `Sink.contramap` in `effect@3.21.2`; generated v3 code should use the source-backed input mapping helpers instead.
This was checked against `/tmp/effect-corpus/source/effect/packages/effect/src/Sink.ts`.

## Concurrency

Sinks can be zipped or raced for concurrent consumption patterns.
Use these sparingly; they are advanced reducers, not a substitute for simple stream transformations.
When combining sinks, reason about leftovers and early completion.

## Leftovers

Leftovers represent input not consumed by a sink.
Most application-level usage can ignore leftovers.
They matter in parsers, protocols, and chunk-level consumers where one sink may leave data for the next step.

## Choosing Stream Destructor Or Sink

Use `runCollect` for simple finite collection.
Use `runFold` for one local fold.
Use `runForEach` for one local effectful action.
Use `Stream.run` with a sink when the consumer deserves a name or composition.

## Generation Checklist
- 11-sink check 01: Confirm unordered output is selected only when downstream order is irrelevant.
- 11-sink check 02: Confirm `merge` termination is deliberate when either side can be infinite.
- 11-sink check 03: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 11-sink check 04: Confirm `zip` is used for positional alignment, not state synchronization.
- 11-sink check 05: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 11-sink check 06: Confirm batches are sized from an API, pool, or latency limit.
- 11-sink check 07: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 11-sink check 08: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 11-sink check 09: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 11-sink check 10: Confirm `orElse` is used only when the error value is not needed.
- 11-sink check 11: Confirm a sink is warranted instead of a simpler stream destructor.
- 11-sink check 12: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 11-sink check 13: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 11-sink check 14: Confirm Channel is justified by low-level read/write or parser needs.
- 11-sink check 15: Confirm Channel examples do not expose application services to type-parameter noise.
- 11-sink check 16: Confirm broadcast branches are consumed within the scope that created them.
- 11-sink check 17: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 11-sink check 18: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 11-sink check 19: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 11-sink check 20: Confirm examples avoid runtime entry points inside service code.
- 11-sink check 21: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 11-sink check 22: Confirm examples use `Effect.log` instead of direct platform logging.
- 11-sink check 23: Confirm no typed error is represented by a thrown exception.
- 11-sink check 24: Confirm absence is represented with `Option`, not nullish domain fields.
- 11-sink check 25: Confirm resource acquisition happens during stream consumption, not declaration.
- 11-sink check 26: Confirm finalizers run on completion, failure, and interruption.
- 11-sink check 27: Confirm queue shutdown is enabled only when the stream owns the queue.
- 11-sink check 28: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 11-sink check 29: Confirm schedule-backed examples are finite in tests.
- 11-sink check 30: Confirm `runCollect` is never used as the default for unknown-size streams.
- 11-sink check 31: Confirm `runFold` is preferred when only an accumulator is required.
- 11-sink check 32: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 11-sink check 33: Confirm `runForEach` does not hide parallelism requirements.
- 11-sink check 34: Confirm source-backed notes override cached community skill guidance.
- 11-sink check 35: Confirm links route to adjacent positive guidance and anti-patterns.
- 11-sink check 36: Confirm no v4-only token appears in prose or examples.
- 11-sink check 37: Confirm no deprecated schema import appears in examples.
- 11-sink check 38: Confirm examples stay small enough for agents to adapt safely.
- 11-sink check 39: Confirm code comments explain only non-obvious stream semantics.
- 11-sink check 40: Confirm the stream type parameters widen visibly when effects are introduced.
- 11-sink check 41: Confirm service requirements are provided at composition boundaries.
- 11-sink check 42: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 11-sink check 43: Confirm unbounded buffers are rejected unless input size is already proven small.
- 11-sink check 44: Confirm finite examples remain deterministic under test execution.
- 11-sink check 45: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 11-sink check 46: Confirm every file ends with 2-5 useful cross-reference links.
- 11-sink check 47: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 11-sink check 48: Confirm examples do not depend on unshown global mutable state.
- 11-sink check 49: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 11-sink check 50: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 11-sink check 51: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 11-sink check 52: Confirm the destructor matches whether all values, one value, or only effects matter.
- 11-sink check 53: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 11-sink check 54: Confirm a callback or queue source has a named capacity and shutdown owner.
- 11-sink check 55: Confirm typed failures remain in the stream or effect error channel.
- 11-sink check 56: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 11-sink check 57: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 11-sink check 58: Confirm any page cursor is immutable state returned by the pagination function.
- 11-sink check 59: Confirm page fetching is lazy and can stop after downstream `take`.
- 11-sink check 60: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 11-sink check 61: Confirm unordered output is selected only when downstream order is irrelevant.
- 11-sink check 62: Confirm `merge` termination is deliberate when either side can be infinite.
- 11-sink check 63: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 11-sink check 64: Confirm `zip` is used for positional alignment, not state synchronization.
- 11-sink check 65: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 11-sink check 66: Confirm batches are sized from an API, pool, or latency limit.
- 11-sink check 67: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 11-sink check 68: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 11-sink check 69: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 11-sink check 70: Confirm `orElse` is used only when the error value is not needed.
- 11-sink check 71: Confirm a sink is warranted instead of a simpler stream destructor.
- 11-sink check 72: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 11-sink check 73: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 11-sink check 74: Confirm Channel is justified by low-level read/write or parser needs.
- 11-sink check 75: Confirm Channel examples do not expose application services to type-parameter noise.
- 11-sink check 76: Confirm broadcast branches are consumed within the scope that created them.
- 11-sink check 77: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 11-sink check 78: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 11-sink check 79: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 11-sink check 80: Confirm examples avoid runtime entry points inside service code.
- 11-sink check 81: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 11-sink check 82: Confirm examples use `Effect.log` instead of direct platform logging.
- 11-sink check 83: Confirm no typed error is represented by a thrown exception.
- 11-sink check 84: Confirm absence is represented with `Option`, not nullish domain fields.
- 11-sink check 85: Confirm resource acquisition happens during stream consumption, not declaration.
- 11-sink check 86: Confirm finalizers run on completion, failure, and interruption.
- 11-sink check 87: Confirm queue shutdown is enabled only when the stream owns the queue.
- 11-sink check 88: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 11-sink check 89: Confirm schedule-backed examples are finite in tests.
- 11-sink check 90: Confirm `runCollect` is never used as the default for unknown-size streams.
- 11-sink check 91: Confirm `runFold` is preferred when only an accumulator is required.
- 11-sink check 92: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 11-sink check 93: Confirm `runForEach` does not hide parallelism requirements.
- 11-sink check 94: Confirm source-backed notes override cached community skill guidance.
- 11-sink check 95: Confirm links route to adjacent positive guidance and anti-patterns.
- 11-sink check 96: Confirm no v4-only token appears in prose or examples.
- 11-sink check 97: Confirm no deprecated schema import appears in examples.

## Cross-references
See also: [10-stream-consumption.md](10-stream-consumption.md), [12-channel.md](12-channel.md), [15-batching.md](15-batching.md), [18-infinite-streams.md](18-infinite-streams.md).
