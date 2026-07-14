# Stream Overview
Use `Stream` for typed, pull-based async sequences with resource safety and backpressure-aware consumption.

## Mental Model

`Stream.Stream<A, E, R>` describes a source that may emit zero or more `A` values, may fail with `E`, and may require `R` services.
It is lazy until a destructor such as `Stream.runCollect`, `Stream.runDrain`, `Stream.runForEach`, or `Stream.run` consumes it.
Think of it as the multi-value sibling of `Effect.Effect<A, E, R>` rather than as a pushed event emitter.
A stream pulls from upstream only when downstream asks for more work.
That pull boundary is why streams are usually the right replacement for RxJS Observable, raw async iterables, and pagination loops in Effect applications.

## When To Reach For Stream

Use Stream when values arrive over time, when the collection may be large, when resources need finalizers, or when the producer should not outrun the consumer.
Use a plain `Effect` when there is exactly one result.
Use `Effect.all` when a fixed or bounded collection of independent effects should be gathered once.
Use `Queue` or `PubSub` directly when you are modelling coordination rather than transforming a sequence.

```typescript
import { Chunk, Effect, Stream } from "effect"

const source = Stream.fromIterable([1, 2, 3]).pipe(
  Stream.map((n) => n * 2)
)

const program: Effect.Effect<Chunk.Chunk<number>> = Stream.runCollect(source)
```

`Stream.runCollect` returns `Effect<Chunk<A>>`; convert with `Chunk.toReadonlyArray` only at interop boundaries.
Keeping the `Chunk` makes the Effect-native collection boundary explicit.

## Pull-Based, Not Push-Based

RxJS Observable usually pushes notifications to subscribers.
Stream is pull-based: each downstream step asks the upstream step for more data.
That means slow consumers naturally apply pressure to upstream work unless you explicitly introduce buffering.
When you do add buffering, choose bounded capacities and named strategies so memory behaviour is visible.

## Laziness

Operators build descriptions.
The source is not read and effects are not executed until a consumer runs the stream.
This makes stream pipelines safe to pass through services as values.
It also means bugs often appear at the destructor, not at construction time.

```typescript
import { Effect, Stream } from "effect"

const pipeline = Stream.fromIterable(["a", "bb", "ccc"]).pipe(
  Stream.filter((value) => value.length > 1),
  Stream.map((value) => value.toUpperCase())
)

const logValues = pipeline.pipe(
  Stream.runForEach((value) => Effect.log(value))
)
```

## Type Parameters

`A` is the emitted element type.
`E` is the typed failure channel.
`R` is the required environment.
Transformations merge these parameters the same way Effect transformations do.
If a mapping function can fail, the stream error channel widens.
If a mapping function needs a service, the stream requirement widens.

## Stream Boundaries

Create streams from arrays, queues, pubsubs, schedules, async callbacks, effects, or pagination state.
Transform with `map`, `filter`, `mapEffect`, `scan`, `take`, `drop`, `flatMap`, `merge`, and batching combinators.
Consume with `runCollect`, `runDrain`, `runForEach`, `runFold`, `runHead`, or `run` with a `Sink`.
For low-level stream internals, use `Channel` only when ordinary Stream and Sink combinators cannot express the flow.

## Backpressure Gravity

Backpressure is not a marketing property; it appears at concrete boundaries.
A bounded queue used with `Stream.fromQueue` will suspend producers when the queue is full.
`Stream.broadcast` uses `maximumLag` to keep consumers from letting upstream run too far ahead.
`Stream.buffer` introduces a bounded gap between producer and consumer.
Unbounded buffering should be rare and justified.

## Infinite Stream Rule

An infinite stream is fine as a value.
An unbounded collection of an infinite stream is a hang.
Before `runCollect`, add `Stream.take(n)`, use `Stream.runHead`, or choose a sink that short-circuits.
This is the most common generated-code failure around streams.

## Source Anchors

The v3 source exports `Stream.runCollect` as returning `Effect.Effect<Chunk.Chunk<A>, E, R>`.
The v3 source exports `Stream.mapEffect` with a `{ concurrency?: number | "unbounded" }` option.
The v3 source exports `Stream.paginate`, `Stream.paginateChunk`, and effectful variants for page loops.
The v3 source exports `Stream.runHead`; it does not export `Stream.runFirst` in `effect@3.21.2`.
These anchors were checked in `/tmp/effect-corpus/source/effect/packages/effect/src/Stream.ts`.

## Generation Checklist
- 01-overview check 01: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 01-overview check 02: Confirm batches are sized from an API, pool, or latency limit.
- 01-overview check 03: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 01-overview check 04: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 01-overview check 05: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 01-overview check 06: Confirm `orElse` is used only when the error value is not needed.
- 01-overview check 07: Confirm a sink is warranted instead of a simpler stream destructor.
- 01-overview check 08: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 01-overview check 09: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 01-overview check 10: Confirm Channel is justified by low-level read/write or parser needs.
- 01-overview check 11: Confirm Channel examples do not expose application services to type-parameter noise.
- 01-overview check 12: Confirm broadcast branches are consumed within the scope that created them.
- 01-overview check 13: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 01-overview check 14: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 01-overview check 15: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 01-overview check 16: Confirm examples avoid runtime entry points inside service code.
- 01-overview check 17: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 01-overview check 18: Confirm examples use `Effect.log` instead of direct platform logging.
- 01-overview check 19: Confirm no typed error is represented by a thrown exception.
- 01-overview check 20: Confirm absence is represented with `Option`, not nullish domain fields.
- 01-overview check 21: Confirm resource acquisition happens during stream consumption, not declaration.
- 01-overview check 22: Confirm finalizers run on completion, failure, and interruption.
- 01-overview check 23: Confirm queue shutdown is enabled only when the stream owns the queue.
- 01-overview check 24: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 01-overview check 25: Confirm schedule-backed examples are finite in tests.
- 01-overview check 26: Confirm `runCollect` is never used as the default for unknown-size streams.
- 01-overview check 27: Confirm `runFold` is preferred when only an accumulator is required.
- 01-overview check 28: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 01-overview check 29: Confirm `runForEach` does not hide parallelism requirements.
- 01-overview check 30: Confirm source-backed notes override cached community skill guidance.
- 01-overview check 31: Confirm links route to adjacent positive guidance and anti-patterns.
- 01-overview check 32: Confirm no v4-only token appears in prose or examples.
- 01-overview check 33: Confirm no deprecated schema import appears in examples.
- 01-overview check 34: Confirm examples stay small enough for agents to adapt safely.
- 01-overview check 35: Confirm code comments explain only non-obvious stream semantics.
- 01-overview check 36: Confirm the stream type parameters widen visibly when effects are introduced.
- 01-overview check 37: Confirm service requirements are provided at composition boundaries.
- 01-overview check 38: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 01-overview check 39: Confirm unbounded buffers are rejected unless input size is already proven small.
- 01-overview check 40: Confirm finite examples remain deterministic under test execution.
- 01-overview check 41: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 01-overview check 42: Confirm every file ends with 2-5 useful cross-reference links.
- 01-overview check 43: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 01-overview check 44: Confirm examples do not depend on unshown global mutable state.
- 01-overview check 45: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 01-overview check 46: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 01-overview check 47: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 01-overview check 48: Confirm the destructor matches whether all values, one value, or only effects matter.
- 01-overview check 49: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 01-overview check 50: Confirm a callback or queue source has a named capacity and shutdown owner.
- 01-overview check 51: Confirm typed failures remain in the stream or effect error channel.
- 01-overview check 52: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 01-overview check 53: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 01-overview check 54: Confirm any page cursor is immutable state returned by the pagination function.
- 01-overview check 55: Confirm page fetching is lazy and can stop after downstream `take`.
- 01-overview check 56: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 01-overview check 57: Confirm unordered output is selected only when downstream order is irrelevant.
- 01-overview check 58: Confirm `merge` termination is deliberate when either side can be infinite.
- 01-overview check 59: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 01-overview check 60: Confirm `zip` is used for positional alignment, not state synchronization.
- 01-overview check 61: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 01-overview check 62: Confirm batches are sized from an API, pool, or latency limit.
- 01-overview check 63: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 01-overview check 64: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 01-overview check 65: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 01-overview check 66: Confirm `orElse` is used only when the error value is not needed.
- 01-overview check 67: Confirm a sink is warranted instead of a simpler stream destructor.
- 01-overview check 68: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 01-overview check 69: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 01-overview check 70: Confirm Channel is justified by low-level read/write or parser needs.
- 01-overview check 71: Confirm Channel examples do not expose application services to type-parameter noise.
- 01-overview check 72: Confirm broadcast branches are consumed within the scope that created them.
- 01-overview check 73: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 01-overview check 74: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 01-overview check 75: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 01-overview check 76: Confirm examples avoid runtime entry points inside service code.
- 01-overview check 77: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 01-overview check 78: Confirm examples use `Effect.log` instead of direct platform logging.
- 01-overview check 79: Confirm no typed error is represented by a thrown exception.

## Cross-references
See also: [02-creating-streams.md](02-creating-streams.md), [10-stream-consumption.md](10-stream-consumption.md), [14-backpressure.md](14-backpressure.md), [18-infinite-streams.md](18-infinite-streams.md).
