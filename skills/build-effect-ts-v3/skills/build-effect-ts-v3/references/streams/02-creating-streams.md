# Creating Streams
Create streams from in-memory values, effects, failures, and callback APIs without losing typed errors.

## Constructors To Know

`Stream.fromIterable` turns any iterable into a finite stream.
`Stream.succeed` emits one value and completes.
`Stream.fail` fails the stream before any later concatenated stream can run.
`Stream.empty` emits no values.
`Stream.fromEffect` lifts one effectful value into a single-element stream.
`Stream.async` and `Stream.asyncEffect` bridge callback APIs that may emit many chunks over time.

```typescript
import { Stream } from "effect"

const many = Stream.fromIterable([1, 2, 3])
const one = Stream.succeed(4)
const none = Stream.empty
const failed = Stream.fail("MissingInput")
```

## From Iterable

Use `fromIterable` for already-loaded finite collections.
It does not make fetching lazy by itself; it only streams values that are already in memory.
For a database, API, or filesystem boundary, first model the boundary as an `Effect` or pagination stream.

```typescript
import { Chunk, Effect, Stream } from "effect"

const stream = Stream.fromIterable(["a", "b", "c"])

const program: Effect.Effect<Chunk.Chunk<string>> = Stream.runCollect(stream)
```

## Single Values And Failures

Use `Stream.succeed` when a branch needs to return one value as a stream.
Use `Stream.fail` to keep errors typed in the stream failure channel.
Do not throw inside mapping callbacks; return a failing stream or failing effectful transformation instead.

```typescript
import { Stream } from "effect"

const parsePositive = (input: number) =>
  input > 0
    ? Stream.succeed(input)
    : Stream.fail("NonPositive")
```

## From Effect

`Stream.fromEffect` is the constructor for one effectful value.
It is not a pagination primitive and it does not repeat.
Use it when the source has one logical result that participates in a stream pipeline.

```typescript
import { Effect, Stream } from "effect"

const loadConfig: Effect.Effect<string> = Effect.succeed("ready")

const stream = Stream.fromEffect(loadConfig).pipe(
  Stream.map((value) => value.toUpperCase())
)
```

## Callback Sources

`Stream.async` registers a callback that can emit chunks.
The callback can terminate by emitting a failing pull with `Option.none()`.
At this callback boundary, `Option.none()` ends the stream and `Option.some(error)` fails it.
Use a finite buffer or strategy when bridging a push source that can outpace consumption.
For effectful registration, use `Stream.asyncEffect`.

```typescript
import { Chunk, Effect, Option, Stream } from "effect"
import type { StreamEmit } from "effect"

const numbers = Stream.async(
  (emit: StreamEmit.Emit<never, never, number, void>) => {
    emit(Effect.succeed(Chunk.of(1)))
    emit(Effect.succeed(Chunk.of(2)))
    emit(Effect.fail(Option.none()))
  },
  { bufferSize: 16, strategy: "suspend" }
)
```

## Async Effect Registration

Use `asyncEffect` when registering the callback needs an Effect service, acquisition step, or typed failure.
The registration effect runs when the stream is consumed.
Keep teardown in scoped constructors when the callback represents a real subscription.

```typescript
import { Chunk, Effect, Option, Stream } from "effect"
import type { StreamEmit } from "effect"

const registered = Stream.asyncEffect(
  (emit: StreamEmit.Emit<never, "RegisterFailed", string, void>) =>
    Effect.sync(() => {
      emit(Effect.succeed(Chunk.of("ready")))
      emit(Effect.fail(Option.none()))
    }),
  { bufferSize: 8, strategy: "suspend" }
)
```

## Buffer Choice

A numeric buffer suspends the producer when full.
`strategy: "dropping"` discards new values when the buffer is full.
`strategy: "sliding"` keeps recent values and drops older buffered values.
`"unbounded"` should be reserved for already-controlled sources.

## Common Mistakes

Do not use `Stream.fromIterable` around a promise list and then call a promise inside `map`; use `mapEffect`.
Do not use `Stream.fail` to represent ordinary absence; emit `Option` values or filter them.
Do not bridge a callback source with an unbounded buffer by default.
Do not collect an infinite callback source without a termination condition.

## Generation Checklist
- 02-creating-streams check 01: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 02-creating-streams check 02: Confirm Channel is justified by low-level read/write or parser needs.
- 02-creating-streams check 03: Confirm Channel examples do not expose application services to type-parameter noise.
- 02-creating-streams check 04: Confirm broadcast branches are consumed within the scope that created them.
- 02-creating-streams check 05: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 02-creating-streams check 06: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 02-creating-streams check 07: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 02-creating-streams check 08: Confirm examples avoid runtime entry points inside service code.
- 02-creating-streams check 09: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 02-creating-streams check 10: Confirm examples use `Effect.log` instead of direct platform logging.
- 02-creating-streams check 11: Confirm no typed error is represented by a thrown exception.
- 02-creating-streams check 12: Confirm absence is represented with `Option`, not nullish domain fields.
- 02-creating-streams check 13: Confirm resource acquisition happens during stream consumption, not declaration.
- 02-creating-streams check 14: Confirm finalizers run on completion, failure, and interruption.
- 02-creating-streams check 15: Confirm queue shutdown is enabled only when the stream owns the queue.
- 02-creating-streams check 16: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 02-creating-streams check 17: Confirm schedule-backed examples are finite in tests.
- 02-creating-streams check 18: Confirm `runCollect` is never used as the default for unknown-size streams.
- 02-creating-streams check 19: Confirm `runFold` is preferred when only an accumulator is required.
- 02-creating-streams check 20: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 02-creating-streams check 21: Confirm `runForEach` does not hide parallelism requirements.
- 02-creating-streams check 22: Confirm source-backed notes override cached community skill guidance.
- 02-creating-streams check 23: Confirm links route to adjacent positive guidance and anti-patterns.
- 02-creating-streams check 24: Confirm no v4-only token appears in prose or examples.
- 02-creating-streams check 25: Confirm no deprecated schema import appears in examples.
- 02-creating-streams check 26: Confirm examples stay small enough for agents to adapt safely.
- 02-creating-streams check 27: Confirm code comments explain only non-obvious stream semantics.
- 02-creating-streams check 28: Confirm the stream type parameters widen visibly when effects are introduced.
- 02-creating-streams check 29: Confirm service requirements are provided at composition boundaries.
- 02-creating-streams check 30: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 02-creating-streams check 31: Confirm unbounded buffers are rejected unless input size is already proven small.
- 02-creating-streams check 32: Confirm finite examples remain deterministic under test execution.
- 02-creating-streams check 33: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 02-creating-streams check 34: Confirm every file ends with 2-5 useful cross-reference links.
- 02-creating-streams check 35: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 02-creating-streams check 36: Confirm examples do not depend on unshown global mutable state.
- 02-creating-streams check 37: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 02-creating-streams check 38: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 02-creating-streams check 39: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 02-creating-streams check 40: Confirm the destructor matches whether all values, one value, or only effects matter.
- 02-creating-streams check 41: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 02-creating-streams check 42: Confirm a callback or queue source has a named capacity and shutdown owner.
- 02-creating-streams check 43: Confirm typed failures remain in the stream or effect error channel.
- 02-creating-streams check 44: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 02-creating-streams check 45: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 02-creating-streams check 46: Confirm any page cursor is immutable state returned by the pagination function.
- 02-creating-streams check 47: Confirm page fetching is lazy and can stop after downstream `take`.
- 02-creating-streams check 48: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 02-creating-streams check 49: Confirm unordered output is selected only when downstream order is irrelevant.
- 02-creating-streams check 50: Confirm `merge` termination is deliberate when either side can be infinite.
- 02-creating-streams check 51: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 02-creating-streams check 52: Confirm `zip` is used for positional alignment, not state synchronization.
- 02-creating-streams check 53: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 02-creating-streams check 54: Confirm batches are sized from an API, pool, or latency limit.
- 02-creating-streams check 55: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 02-creating-streams check 56: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 02-creating-streams check 57: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 02-creating-streams check 58: Confirm `orElse` is used only when the error value is not needed.
- 02-creating-streams check 59: Confirm a sink is warranted instead of a simpler stream destructor.
- 02-creating-streams check 60: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 02-creating-streams check 61: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 02-creating-streams check 62: Confirm Channel is justified by low-level read/write or parser needs.
- 02-creating-streams check 63: Confirm Channel examples do not expose application services to type-parameter noise.
- 02-creating-streams check 64: Confirm broadcast branches are consumed within the scope that created them.
- 02-creating-streams check 65: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 02-creating-streams check 66: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 02-creating-streams check 67: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 02-creating-streams check 68: Confirm examples avoid runtime entry points inside service code.
- 02-creating-streams check 69: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 02-creating-streams check 70: Confirm examples use `Effect.log` instead of direct platform logging.
- 02-creating-streams check 71: Confirm no typed error is represented by a thrown exception.
- 02-creating-streams check 72: Confirm absence is represented with `Option`, not nullish domain fields.
- 02-creating-streams check 73: Confirm resource acquisition happens during stream consumption, not declaration.
- 02-creating-streams check 74: Confirm finalizers run on completion, failure, and interruption.
- 02-creating-streams check 75: Confirm queue shutdown is enabled only when the stream owns the queue.
- 02-creating-streams check 76: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 02-creating-streams check 77: Confirm schedule-backed examples are finite in tests.
- 02-creating-streams check 78: Confirm `runCollect` is never used as the default for unknown-size streams.
- 02-creating-streams check 79: Confirm `runFold` is preferred when only an accumulator is required.
- 02-creating-streams check 80: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 02-creating-streams check 81: Confirm `runForEach` does not hide parallelism requirements.
- 02-creating-streams check 82: Confirm source-backed notes override cached community skill guidance.
- 02-creating-streams check 83: Confirm links route to adjacent positive guidance and anti-patterns.
- 02-creating-streams check 84: Confirm no v4-only token appears in prose or examples.
- 02-creating-streams check 85: Confirm no deprecated schema import appears in examples.
- 02-creating-streams check 86: Confirm examples stay small enough for agents to adapt safely.
- 02-creating-streams check 87: Confirm code comments explain only non-obvious stream semantics.
- 02-creating-streams check 88: Confirm the stream type parameters widen visibly when effects are introduced.
- 02-creating-streams check 89: Confirm service requirements are provided at composition boundaries.
- 02-creating-streams check 90: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 02-creating-streams check 91: Confirm unbounded buffers are rejected unless input size is already proven small.
- 02-creating-streams check 92: Confirm finite examples remain deterministic under test execution.
- 02-creating-streams check 93: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 02-creating-streams check 94: Confirm every file ends with 2-5 useful cross-reference links.

## Cross-references
See also: [01-overview.md](01-overview.md), [03-stream-from-queue-pubsub.md](03-stream-from-queue-pubsub.md), [05-stream-pagination.md](05-stream-pagination.md), [17-scope-and-stream.md](17-scope-and-stream.md).
