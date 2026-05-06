# Stream Error Handling
Handle stream failures with typed fallback, retry, and recovery combinators instead of exceptions.

## Failure Channel

A stream can fail with its `E` type.
When a source fails, downstream consumers receive the failure through the Effect returned by the destructor.
Use stream error combinators to recover inside the pipeline.
Use Effect error combinators after the destructor only when recovery belongs at the consumption boundary.

## catchAll

`Stream.catchAll` replaces a failed stream with another stream.
The fallback can emit a different success type and can have its own requirements.
Use it when the fallback values are a real continuation, not when you want to hide a bug.

```typescript
import { Stream } from "effect"

const primary = Stream.fail("RemoteUnavailable")
const fallback = Stream.fromIterable(["cached-a", "cached-b"])

const stream = primary.pipe(
  Stream.catchAll(() => fallback)
)
```

## orElse

`Stream.orElse` switches to an alternate stream if the first stream fails.
Use it for simple fallback where the error value itself does not drive recovery.
Use `catchAll` when the error value determines the fallback.

```typescript
import { Stream } from "effect"

const stream = Stream.orElse(
  Stream.fail("EmptyPrimary"),
  () => Stream.succeed("fallback")
)
```

## retry

`Stream.retry(schedule)` retries a failing stream according to a `Schedule`.
Use it when repeating the failing pull or page request is safe.
Avoid retrying streams that perform non-idempotent writes unless the operation has idempotency protection.

```typescript
import { Schedule, Stream } from "effect"

declare const remote: Stream.Stream<string, "TransientRemoteError">

const retried = remote.pipe(
  Stream.retry(Schedule.exponential("100 millis").pipe(Schedule.compose(Schedule.recurs(3))))
)
```

## onError

Use `Stream.onError` for cleanup or diagnostics that should run when the stream fails.
Do not use it as a recovery mechanism.
If recovery is needed, use `catchAll`, `catchSome`, or `orElse`.

## Defects

Defects are not typed failures.
Avoid creating defects in domain logic.
If source code can fail as part of normal operation, use typed failures with `Stream.fail` or effectful stream constructors.

## Per-Item Errors

If a single element can fail validation and the stream should continue, put that result in the success channel as `Either` or `Option`.
If the whole stream should stop, keep the error in the stream failure channel.
This distinction is a domain decision.

## Boundary Recovery

Recover inside the stream when the fallback is another stream of values.
Recover after consumption when the fallback is a final result.
Do not mix both without a reason; it makes termination and retries hard to reason about.

## Generation Checklist
- 13-error-handling check 01: Confirm a sink is warranted instead of a simpler stream destructor.
- 13-error-handling check 02: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 13-error-handling check 03: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 13-error-handling check 04: Confirm Channel is justified by low-level read/write or parser needs.
- 13-error-handling check 05: Confirm Channel examples do not expose application services to type-parameter noise.
- 13-error-handling check 06: Confirm broadcast branches are consumed within the scope that created them.
- 13-error-handling check 07: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 13-error-handling check 08: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 13-error-handling check 09: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 13-error-handling check 10: Confirm examples avoid runtime entry points inside service code.
- 13-error-handling check 11: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 13-error-handling check 12: Confirm examples use `Effect.log` instead of direct platform logging.
- 13-error-handling check 13: Confirm no typed error is represented by a thrown exception.
- 13-error-handling check 14: Confirm absence is represented with `Option`, not nullish domain fields.
- 13-error-handling check 15: Confirm resource acquisition happens during stream consumption, not declaration.
- 13-error-handling check 16: Confirm finalizers run on completion, failure, and interruption.
- 13-error-handling check 17: Confirm queue shutdown is enabled only when the stream owns the queue.
- 13-error-handling check 18: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 13-error-handling check 19: Confirm schedule-backed examples are finite in tests.
- 13-error-handling check 20: Confirm `runCollect` is never used as the default for unknown-size streams.
- 13-error-handling check 21: Confirm `runFold` is preferred when only an accumulator is required.
- 13-error-handling check 22: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 13-error-handling check 23: Confirm `runForEach` does not hide parallelism requirements.
- 13-error-handling check 24: Confirm source-backed notes override cached community skill guidance.
- 13-error-handling check 25: Confirm links route to adjacent positive guidance and anti-patterns.
- 13-error-handling check 26: Confirm no v4-only token appears in prose or examples.
- 13-error-handling check 27: Confirm no deprecated schema import appears in examples.
- 13-error-handling check 28: Confirm examples stay small enough for agents to adapt safely.
- 13-error-handling check 29: Confirm code comments explain only non-obvious stream semantics.
- 13-error-handling check 30: Confirm the stream type parameters widen visibly when effects are introduced.
- 13-error-handling check 31: Confirm service requirements are provided at composition boundaries.
- 13-error-handling check 32: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 13-error-handling check 33: Confirm unbounded buffers are rejected unless input size is already proven small.
- 13-error-handling check 34: Confirm finite examples remain deterministic under test execution.
- 13-error-handling check 35: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 13-error-handling check 36: Confirm every file ends with 2-5 useful cross-reference links.
- 13-error-handling check 37: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 13-error-handling check 38: Confirm examples do not depend on unshown global mutable state.
- 13-error-handling check 39: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 13-error-handling check 40: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 13-error-handling check 41: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 13-error-handling check 42: Confirm the destructor matches whether all values, one value, or only effects matter.
- 13-error-handling check 43: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 13-error-handling check 44: Confirm a callback or queue source has a named capacity and shutdown owner.
- 13-error-handling check 45: Confirm typed failures remain in the stream or effect error channel.
- 13-error-handling check 46: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 13-error-handling check 47: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 13-error-handling check 48: Confirm any page cursor is immutable state returned by the pagination function.
- 13-error-handling check 49: Confirm page fetching is lazy and can stop after downstream `take`.
- 13-error-handling check 50: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 13-error-handling check 51: Confirm unordered output is selected only when downstream order is irrelevant.
- 13-error-handling check 52: Confirm `merge` termination is deliberate when either side can be infinite.
- 13-error-handling check 53: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 13-error-handling check 54: Confirm `zip` is used for positional alignment, not state synchronization.
- 13-error-handling check 55: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 13-error-handling check 56: Confirm batches are sized from an API, pool, or latency limit.
- 13-error-handling check 57: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 13-error-handling check 58: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 13-error-handling check 59: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 13-error-handling check 60: Confirm `orElse` is used only when the error value is not needed.
- 13-error-handling check 61: Confirm a sink is warranted instead of a simpler stream destructor.
- 13-error-handling check 62: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 13-error-handling check 63: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 13-error-handling check 64: Confirm Channel is justified by low-level read/write or parser needs.
- 13-error-handling check 65: Confirm Channel examples do not expose application services to type-parameter noise.
- 13-error-handling check 66: Confirm broadcast branches are consumed within the scope that created them.
- 13-error-handling check 67: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 13-error-handling check 68: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 13-error-handling check 69: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 13-error-handling check 70: Confirm examples avoid runtime entry points inside service code.
- 13-error-handling check 71: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 13-error-handling check 72: Confirm examples use `Effect.log` instead of direct platform logging.
- 13-error-handling check 73: Confirm no typed error is represented by a thrown exception.
- 13-error-handling check 74: Confirm absence is represented with `Option`, not nullish domain fields.
- 13-error-handling check 75: Confirm resource acquisition happens during stream consumption, not declaration.
- 13-error-handling check 76: Confirm finalizers run on completion, failure, and interruption.
- 13-error-handling check 77: Confirm queue shutdown is enabled only when the stream owns the queue.
- 13-error-handling check 78: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 13-error-handling check 79: Confirm schedule-backed examples are finite in tests.
- 13-error-handling check 80: Confirm `runCollect` is never used as the default for unknown-size streams.
- 13-error-handling check 81: Confirm `runFold` is preferred when only an accumulator is required.
- 13-error-handling check 82: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 13-error-handling check 83: Confirm `runForEach` does not hide parallelism requirements.

## Cross-references
See also: [05-stream-pagination.md](05-stream-pagination.md), [09-mapEffect-concurrency.md](09-mapEffect-concurrency.md), [10-stream-consumption.md](10-stream-consumption.md), [../error-handling/06-catch-all.md](../error-handling/06-catch-all.md).
