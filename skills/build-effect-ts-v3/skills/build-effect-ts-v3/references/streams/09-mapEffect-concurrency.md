# MapEffect Concurrency
Use `Stream.mapEffect` concurrency as bounded stream fan-out, not as accidental unbounded parallelism.

## The API Shape

`Stream.mapEffect` maps each element with a function returning `Effect`.
The v3 source supports `options?: { concurrency?: number | "unbounded"; unordered?: boolean }`.
It also supports keyed mapping with `{ key, bufferSize }` for per-key ordering use cases.
For ordinary I/O fan-out, use a numeric concurrency bound.

```typescript
import { Effect, Stream } from "effect"

declare const fetchUser: (id: string) => Effect.Effect<string, "FetchUserFailed">

const users = Stream.fromIterable(["u1", "u2", "u3"]).pipe(
  Stream.mapEffect((id) => fetchUser(id), { concurrency: 4 })
)
```

## Sequential Default

Without a concurrency option, treat `mapEffect` as sequential unless source verification for the target version says otherwise.
Sequential mapping is often correct for ordered writes, rate-limited APIs, and stateful dependencies.
Use concurrency only when the per-element effects are independent.

## Bounded Parallelism

A bounded number makes resource usage reviewable.
Pick the bound from downstream capacity: database pool size, HTTP limit, API budget, or CPU budget.
Do not copy arbitrary high numbers into generated code.
If the input can exceed five elements, the bound should be visible in the code.

## Ordering

Concurrent `mapEffect` preserves order unless `unordered: true` is selected.
Use `unordered: true` only when downstream does not depend on order and lower latency matters.
Name that tradeoff in code review; unordered output is a behavioural choice.

```typescript
import { Effect, Stream } from "effect"

declare const enrich: (id: string) => Effect.Effect<string, "EnrichFailed">

const fastest = Stream.fromIterable(["a", "b", "c"]).pipe(
  Stream.mapEffect((id) => enrich(id), {
    concurrency: 3,
    unordered: true
  })
)
```

## Keyed Mapping

The keyed overload coordinates work by key with an internal buffer.
Use it when items for the same key must preserve a relationship while different keys may progress independently.
Prefer the ordinary numeric concurrency overload unless keyed semantics are specifically required.

## Failure Semantics

If the mapping effect fails, the stream fails with the original stream error or the mapping error.
Do not catch all mapping errors just to keep the stream alive.
If skipping bad items is semantically correct, convert failures to an explicit `Either` or `Option` value at that point.

## Unbounded Warning

`concurrency: "unbounded"` is rarely appropriate in generated code.
It starts as much work as the upstream can provide.
That can overwhelm file descriptors, connection pools, memory, and remote rate limits.
Reach for it only with tiny, already-controlled inputs.

## Required Cross-Checks

Before using this pattern, read [concurrency/07-bounded-parallelism.md](../concurrency/07-bounded-parallelism.md).
Before accepting unbounded stream fan-out, read [anti-patterns/05-unbounded-parallelism.md](../anti-patterns/05-unbounded-parallelism.md).
The same operational limit applies to streams and `Effect.all`.

## Review Questions

Is each element independent.
Is the input size bounded by construction.
Does order matter downstream.
What real resource sets the concurrency number.
Should retries happen per element or around the whole stream.
Is backpressure still visible after buffering or fan-out.

## Generation Checklist
- 09-mapEffect-concurrency check 01: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 09-mapEffect-concurrency check 02: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 09-mapEffect-concurrency check 03: Confirm examples avoid runtime entry points inside service code.
- 09-mapEffect-concurrency check 04: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 09-mapEffect-concurrency check 05: Confirm examples use `Effect.log` instead of direct platform logging.
- 09-mapEffect-concurrency check 06: Confirm no typed error is represented by a thrown exception.
- 09-mapEffect-concurrency check 07: Confirm absence is represented with `Option`, not nullish domain fields.
- 09-mapEffect-concurrency check 08: Confirm resource acquisition happens during stream consumption, not declaration.
- 09-mapEffect-concurrency check 09: Confirm finalizers run on completion, failure, and interruption.
- 09-mapEffect-concurrency check 10: Confirm queue shutdown is enabled only when the stream owns the queue.
- 09-mapEffect-concurrency check 11: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 09-mapEffect-concurrency check 12: Confirm schedule-backed examples are finite in tests.
- 09-mapEffect-concurrency check 13: Confirm `runCollect` is never used as the default for unknown-size streams.
- 09-mapEffect-concurrency check 14: Confirm `runFold` is preferred when only an accumulator is required.
- 09-mapEffect-concurrency check 15: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 09-mapEffect-concurrency check 16: Confirm `runForEach` does not hide parallelism requirements.
- 09-mapEffect-concurrency check 17: Confirm source-backed notes override cached community skill guidance.
- 09-mapEffect-concurrency check 18: Confirm links route to adjacent positive guidance and anti-patterns.
- 09-mapEffect-concurrency check 19: Confirm no v4-only token appears in prose or examples.
- 09-mapEffect-concurrency check 20: Confirm no deprecated schema import appears in examples.
- 09-mapEffect-concurrency check 21: Confirm examples stay small enough for agents to adapt safely.
- 09-mapEffect-concurrency check 22: Confirm code comments explain only non-obvious stream semantics.
- 09-mapEffect-concurrency check 23: Confirm the stream type parameters widen visibly when effects are introduced.
- 09-mapEffect-concurrency check 24: Confirm service requirements are provided at composition boundaries.
- 09-mapEffect-concurrency check 25: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 09-mapEffect-concurrency check 26: Confirm unbounded buffers are rejected unless input size is already proven small.
- 09-mapEffect-concurrency check 27: Confirm finite examples remain deterministic under test execution.
- 09-mapEffect-concurrency check 28: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 09-mapEffect-concurrency check 29: Confirm every file ends with 2-5 useful cross-reference links.
- 09-mapEffect-concurrency check 30: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 09-mapEffect-concurrency check 31: Confirm examples do not depend on unshown global mutable state.
- 09-mapEffect-concurrency check 32: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 09-mapEffect-concurrency check 33: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 09-mapEffect-concurrency check 34: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 09-mapEffect-concurrency check 35: Confirm the destructor matches whether all values, one value, or only effects matter.
- 09-mapEffect-concurrency check 36: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 09-mapEffect-concurrency check 37: Confirm a callback or queue source has a named capacity and shutdown owner.
- 09-mapEffect-concurrency check 38: Confirm typed failures remain in the stream or effect error channel.
- 09-mapEffect-concurrency check 39: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 09-mapEffect-concurrency check 40: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 09-mapEffect-concurrency check 41: Confirm any page cursor is immutable state returned by the pagination function.
- 09-mapEffect-concurrency check 42: Confirm page fetching is lazy and can stop after downstream `take`.
- 09-mapEffect-concurrency check 43: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 09-mapEffect-concurrency check 44: Confirm unordered output is selected only when downstream order is irrelevant.
- 09-mapEffect-concurrency check 45: Confirm `merge` termination is deliberate when either side can be infinite.
- 09-mapEffect-concurrency check 46: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 09-mapEffect-concurrency check 47: Confirm `zip` is used for positional alignment, not state synchronization.
- 09-mapEffect-concurrency check 48: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 09-mapEffect-concurrency check 49: Confirm batches are sized from an API, pool, or latency limit.
- 09-mapEffect-concurrency check 50: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 09-mapEffect-concurrency check 51: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 09-mapEffect-concurrency check 52: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 09-mapEffect-concurrency check 53: Confirm `orElse` is used only when the error value is not needed.
- 09-mapEffect-concurrency check 54: Confirm a sink is warranted instead of a simpler stream destructor.
- 09-mapEffect-concurrency check 55: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 09-mapEffect-concurrency check 56: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 09-mapEffect-concurrency check 57: Confirm Channel is justified by low-level read/write or parser needs.
- 09-mapEffect-concurrency check 58: Confirm Channel examples do not expose application services to type-parameter noise.
- 09-mapEffect-concurrency check 59: Confirm broadcast branches are consumed within the scope that created them.
- 09-mapEffect-concurrency check 60: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 09-mapEffect-concurrency check 61: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 09-mapEffect-concurrency check 62: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 09-mapEffect-concurrency check 63: Confirm examples avoid runtime entry points inside service code.
- 09-mapEffect-concurrency check 64: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 09-mapEffect-concurrency check 65: Confirm examples use `Effect.log` instead of direct platform logging.
- 09-mapEffect-concurrency check 66: Confirm no typed error is represented by a thrown exception.
- 09-mapEffect-concurrency check 67: Confirm absence is represented with `Option`, not nullish domain fields.
- 09-mapEffect-concurrency check 68: Confirm resource acquisition happens during stream consumption, not declaration.
- 09-mapEffect-concurrency check 69: Confirm finalizers run on completion, failure, and interruption.
- 09-mapEffect-concurrency check 70: Confirm queue shutdown is enabled only when the stream owns the queue.
- 09-mapEffect-concurrency check 71: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 09-mapEffect-concurrency check 72: Confirm schedule-backed examples are finite in tests.
- 09-mapEffect-concurrency check 73: Confirm `runCollect` is never used as the default for unknown-size streams.
- 09-mapEffect-concurrency check 74: Confirm `runFold` is preferred when only an accumulator is required.
- 09-mapEffect-concurrency check 75: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 09-mapEffect-concurrency check 76: Confirm `runForEach` does not hide parallelism requirements.
- 09-mapEffect-concurrency check 77: Confirm source-backed notes override cached community skill guidance.
- 09-mapEffect-concurrency check 78: Confirm links route to adjacent positive guidance and anti-patterns.
- 09-mapEffect-concurrency check 79: Confirm no v4-only token appears in prose or examples.

## Cross-references
See also: [06-transformations.md](06-transformations.md), [14-backpressure.md](14-backpressure.md), [../concurrency/07-bounded-parallelism.md](../concurrency/07-bounded-parallelism.md), [../anti-patterns/05-unbounded-parallelism.md](../anti-patterns/05-unbounded-parallelism.md).
