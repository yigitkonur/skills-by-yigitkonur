# Stream Flattening
Flatten nested streams deliberately with ordering, concurrency, and cardinality made explicit.

## Nested Streams

A nested stream appears when each input element expands into another stream.
Use `Stream.flatMap` for the usual case.
Use `Stream.flatten` when the stream already emits streams.
Use cross combinators when you intentionally want Cartesian products.

```typescript
import { Stream } from "effect"

const expanded = Stream.fromIterable([1, 2]).pipe(
  Stream.flatMap((n) => Stream.fromIterable([n, n * 10]))
)
```

## Flatten

`Stream.flatten` removes one stream layer.
It is clearer than `flatMap((stream) => stream)` when the element type is already a stream.
Check the emitted stream error and requirement types; flattening merges them into the outer stream.

```typescript
import { Stream } from "effect"

const nested = Stream.fromIterable([
  Stream.fromIterable([1, 2]),
  Stream.fromIterable([3, 4])
])

const flat = nested.pipe(Stream.flatten)
```

## FlatMap

`flatMap` preserves the pull-based model while expanding each element.
By default, it is the safe choice for dependent stream expansion.
Use concurrency options only when inner streams are independent and bounded.

```typescript
import { Stream } from "effect"

const repeated = Stream.fromIterable(["a", "b"]).pipe(
  Stream.flatMap((value) => Stream.repeatValue(value).pipe(Stream.take(2)))
)
```

## Cross Products

`Stream.cross`, `Stream.crossWith`, and related `crossAll`-style APIs model combinations, not flattening for convenience.
Use them when every left element should combine with every right element.
Avoid them for large or unbounded streams unless the product size is intentional.

## Concurrency

Concurrent flattening can improve throughput for independent inner streams.
It can also multiply resource usage quickly.
Prefer a finite numeric concurrency bound and document why ordering can or cannot be relaxed.
If inner streams perform HTTP or database work, unbounded flattening is an operational bug.

## Error And Requirement Merging

The outer stream error type and inner stream error type both remain visible.
The outer requirements and inner requirements both remain visible.
Do not hide this with casts.
Provide layers at the program edge or service composition boundary.

## When Not To Flatten

Do not flatten just to avoid designing a domain type.
A stream of pages may be the correct shape if page metadata matters.
A stream of batches may be the correct shape if downstream writes in batches.
Flatten only when individual elements are the real unit of work.

## Generation Checklist
- 07-flattening check 01: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 07-flattening check 02: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 07-flattening check 03: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 07-flattening check 04: Confirm `orElse` is used only when the error value is not needed.
- 07-flattening check 05: Confirm a sink is warranted instead of a simpler stream destructor.
- 07-flattening check 06: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 07-flattening check 07: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 07-flattening check 08: Confirm Channel is justified by low-level read/write or parser needs.
- 07-flattening check 09: Confirm Channel examples do not expose application services to type-parameter noise.
- 07-flattening check 10: Confirm broadcast branches are consumed within the scope that created them.
- 07-flattening check 11: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 07-flattening check 12: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 07-flattening check 13: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 07-flattening check 14: Confirm examples avoid runtime entry points inside service code.
- 07-flattening check 15: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 07-flattening check 16: Confirm examples use `Effect.log` instead of direct platform logging.
- 07-flattening check 17: Confirm no typed error is represented by a thrown exception.
- 07-flattening check 18: Confirm absence is represented with `Option`, not nullish domain fields.
- 07-flattening check 19: Confirm resource acquisition happens during stream consumption, not declaration.
- 07-flattening check 20: Confirm finalizers run on completion, failure, and interruption.
- 07-flattening check 21: Confirm queue shutdown is enabled only when the stream owns the queue.
- 07-flattening check 22: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 07-flattening check 23: Confirm schedule-backed examples are finite in tests.
- 07-flattening check 24: Confirm `runCollect` is never used as the default for unknown-size streams.
- 07-flattening check 25: Confirm `runFold` is preferred when only an accumulator is required.
- 07-flattening check 26: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 07-flattening check 27: Confirm `runForEach` does not hide parallelism requirements.
- 07-flattening check 28: Confirm source-backed notes override cached community skill guidance.
- 07-flattening check 29: Confirm links route to adjacent positive guidance and anti-patterns.
- 07-flattening check 30: Confirm no v4-only token appears in prose or examples.
- 07-flattening check 31: Confirm no deprecated schema import appears in examples.
- 07-flattening check 32: Confirm examples stay small enough for agents to adapt safely.
- 07-flattening check 33: Confirm code comments explain only non-obvious stream semantics.
- 07-flattening check 34: Confirm the stream type parameters widen visibly when effects are introduced.
- 07-flattening check 35: Confirm service requirements are provided at composition boundaries.
- 07-flattening check 36: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 07-flattening check 37: Confirm unbounded buffers are rejected unless input size is already proven small.
- 07-flattening check 38: Confirm finite examples remain deterministic under test execution.
- 07-flattening check 39: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 07-flattening check 40: Confirm every file ends with 2-5 useful cross-reference links.
- 07-flattening check 41: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 07-flattening check 42: Confirm examples do not depend on unshown global mutable state.
- 07-flattening check 43: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 07-flattening check 44: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 07-flattening check 45: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 07-flattening check 46: Confirm the destructor matches whether all values, one value, or only effects matter.
- 07-flattening check 47: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 07-flattening check 48: Confirm a callback or queue source has a named capacity and shutdown owner.
- 07-flattening check 49: Confirm typed failures remain in the stream or effect error channel.
- 07-flattening check 50: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 07-flattening check 51: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 07-flattening check 52: Confirm any page cursor is immutable state returned by the pagination function.
- 07-flattening check 53: Confirm page fetching is lazy and can stop after downstream `take`.
- 07-flattening check 54: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 07-flattening check 55: Confirm unordered output is selected only when downstream order is irrelevant.
- 07-flattening check 56: Confirm `merge` termination is deliberate when either side can be infinite.
- 07-flattening check 57: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 07-flattening check 58: Confirm `zip` is used for positional alignment, not state synchronization.
- 07-flattening check 59: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 07-flattening check 60: Confirm batches are sized from an API, pool, or latency limit.
- 07-flattening check 61: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 07-flattening check 62: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 07-flattening check 63: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 07-flattening check 64: Confirm `orElse` is used only when the error value is not needed.
- 07-flattening check 65: Confirm a sink is warranted instead of a simpler stream destructor.
- 07-flattening check 66: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 07-flattening check 67: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 07-flattening check 68: Confirm Channel is justified by low-level read/write or parser needs.
- 07-flattening check 69: Confirm Channel examples do not expose application services to type-parameter noise.
- 07-flattening check 70: Confirm broadcast branches are consumed within the scope that created them.
- 07-flattening check 71: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 07-flattening check 72: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 07-flattening check 73: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 07-flattening check 74: Confirm examples avoid runtime entry points inside service code.
- 07-flattening check 75: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 07-flattening check 76: Confirm examples use `Effect.log` instead of direct platform logging.
- 07-flattening check 77: Confirm no typed error is represented by a thrown exception.
- 07-flattening check 78: Confirm absence is represented with `Option`, not nullish domain fields.
- 07-flattening check 79: Confirm resource acquisition happens during stream consumption, not declaration.

## Cross-references
See also: [06-transformations.md](06-transformations.md), [08-merging-zipping.md](08-merging-zipping.md), [09-mapEffect-concurrency.md](09-mapEffect-concurrency.md), [14-backpressure.md](14-backpressure.md).
