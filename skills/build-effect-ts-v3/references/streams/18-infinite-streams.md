# Infinite Streams
Prevent infinite stream hangs by bounding collection or using first-value destructors.

## Infinite Is Valid

An infinite stream is a valid stream value.
Examples include ticks, repeated values, state changes, message subscriptions, and iterated numbers.
The bug is not creating an infinite stream.
The bug is consuming it with a destructor that waits for completion.

## Canonical Hang

This program never finishes because `Stream.runCollect` waits for the stream to end.
`Stream.repeatValue` does not end on its own.

```typescript
import { Stream } from "effect"

const hangs = Stream.repeatValue("tick").pipe(
  Stream.runCollect
)
```

The same problem appears with `Stream.iterate`, `Stream.tick`, queue subscriptions, pubsub subscriptions, and unbounded callback sources.

## Canonical Fix With take

Add `Stream.take(N)` before collecting when a finite prefix is the intended result.
The result is still `Effect<Chunk<A>>`, and the stream has a clear bound.

```typescript
import { Stream } from "effect"

const firstFive = Stream.repeatValue("tick").pipe(
  Stream.take(5),
  Stream.runCollect
)
```

## Canonical Fix With runHead

Use `Stream.runHead` when only the first emitted value matters.
It returns `Effect<Option.Option<A>, E, R>` and does not wait for stream completion.
`Stream.runFirst` is not exported by `effect@3.21.2`; use `Stream.runHead` in v3.
This was checked against `/tmp/effect-corpus/source/effect/packages/effect/src/Stream.ts`.

```typescript
import { Stream } from "effect"

const first = Stream.iterate(1, (n) => n + 1).pipe(
  Stream.runHead
)
```

## Long-Running Consumers

For service loops, prefer `Stream.runForEach` or `Stream.runDrain` with an external lifetime.
The fiber running the stream should be interruptible by the owning scope.
Do not pretend a forever stream is a startup task that will complete.

## Tests

Tests should never call `runCollect` on a source that can be infinite unless the pipeline includes `take`.
Use small bounds such as 1, 2, or 3 so tests remain fast.
For schedule-backed streams, use short durations or test clocks when available.

## Review Cues

Look for `repeatValue`, `iterate`, `tick`, `fromQueue`, `fromPubSub`, `forever`, and callback sources.
If any of those flow into `runCollect`, require a visible bound.
If the desired result is the first item, use `runHead`.
If the desired result is ongoing side effects, use a scoped long-running fiber.

## Generation Checklist
- 18-infinite-streams check 01: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 18-infinite-streams check 02: Confirm Channel is justified by low-level read/write or parser needs.
- 18-infinite-streams check 03: Confirm Channel examples do not expose application services to type-parameter noise.
- 18-infinite-streams check 04: Confirm broadcast branches are consumed within the scope that created them.
- 18-infinite-streams check 05: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 18-infinite-streams check 06: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 18-infinite-streams check 07: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 18-infinite-streams check 08: Confirm examples avoid runtime entry points inside service code.
- 18-infinite-streams check 09: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 18-infinite-streams check 10: Confirm examples use `Effect.log` instead of direct platform logging.
- 18-infinite-streams check 11: Confirm no typed error is represented by a thrown exception.
- 18-infinite-streams check 12: Confirm absence is represented with `Option`, not nullish domain fields.
- 18-infinite-streams check 13: Confirm resource acquisition happens during stream consumption, not declaration.
- 18-infinite-streams check 14: Confirm finalizers run on completion, failure, and interruption.
- 18-infinite-streams check 15: Confirm queue shutdown is enabled only when the stream owns the queue.
- 18-infinite-streams check 16: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 18-infinite-streams check 17: Confirm schedule-backed examples are finite in tests.
- 18-infinite-streams check 18: Confirm `runCollect` is never used as the default for unknown-size streams.
- 18-infinite-streams check 19: Confirm `runFold` is preferred when only an accumulator is required.
- 18-infinite-streams check 20: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 18-infinite-streams check 21: Confirm `runForEach` does not hide parallelism requirements.
- 18-infinite-streams check 22: Confirm source-backed notes override cached community skill guidance.
- 18-infinite-streams check 23: Confirm links route to adjacent positive guidance and anti-patterns.
- 18-infinite-streams check 24: Confirm no v4-only token appears in prose or examples.
- 18-infinite-streams check 25: Confirm no deprecated schema import appears in examples.
- 18-infinite-streams check 26: Confirm examples stay small enough for agents to adapt safely.
- 18-infinite-streams check 27: Confirm code comments explain only non-obvious stream semantics.
- 18-infinite-streams check 28: Confirm the stream type parameters widen visibly when effects are introduced.
- 18-infinite-streams check 29: Confirm service requirements are provided at composition boundaries.
- 18-infinite-streams check 30: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 18-infinite-streams check 31: Confirm unbounded buffers are rejected unless input size is already proven small.
- 18-infinite-streams check 32: Confirm finite examples remain deterministic under test execution.
- 18-infinite-streams check 33: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 18-infinite-streams check 34: Confirm every file ends with 2-5 useful cross-reference links.
- 18-infinite-streams check 35: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 18-infinite-streams check 36: Confirm examples do not depend on unshown global mutable state.
- 18-infinite-streams check 37: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 18-infinite-streams check 38: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 18-infinite-streams check 39: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 18-infinite-streams check 40: Confirm the destructor matches whether all values, one value, or only effects matter.
- 18-infinite-streams check 41: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 18-infinite-streams check 42: Confirm a callback or queue source has a named capacity and shutdown owner.
- 18-infinite-streams check 43: Confirm typed failures remain in the stream or effect error channel.
- 18-infinite-streams check 44: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 18-infinite-streams check 45: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 18-infinite-streams check 46: Confirm any page cursor is immutable state returned by the pagination function.
- 18-infinite-streams check 47: Confirm page fetching is lazy and can stop after downstream `take`.
- 18-infinite-streams check 48: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 18-infinite-streams check 49: Confirm unordered output is selected only when downstream order is irrelevant.
- 18-infinite-streams check 50: Confirm `merge` termination is deliberate when either side can be infinite.
- 18-infinite-streams check 51: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 18-infinite-streams check 52: Confirm `zip` is used for positional alignment, not state synchronization.
- 18-infinite-streams check 53: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 18-infinite-streams check 54: Confirm batches are sized from an API, pool, or latency limit.
- 18-infinite-streams check 55: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 18-infinite-streams check 56: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 18-infinite-streams check 57: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 18-infinite-streams check 58: Confirm `orElse` is used only when the error value is not needed.
- 18-infinite-streams check 59: Confirm a sink is warranted instead of a simpler stream destructor.
- 18-infinite-streams check 60: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 18-infinite-streams check 61: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 18-infinite-streams check 62: Confirm Channel is justified by low-level read/write or parser needs.
- 18-infinite-streams check 63: Confirm Channel examples do not expose application services to type-parameter noise.

## Cross-references
See also: [01-overview.md](01-overview.md), [04-stream-from-schedule.md](04-stream-from-schedule.md), [10-stream-consumption.md](10-stream-consumption.md), [11-sink.md](11-sink.md).
