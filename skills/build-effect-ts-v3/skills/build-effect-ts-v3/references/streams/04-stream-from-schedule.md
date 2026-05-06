# Streams From Schedule
Use schedule-backed streams for ticks, repeated values, and time-paced pull loops.

## Time Sources

`Stream.tick(interval)` emits `void` values at a fixed interval.
`Stream.fromSchedule(schedule)` emits schedule outputs.
`Stream.repeatValue(value)` creates an infinite stream of the same value.
All of these are usually infinite unless followed by `Stream.take`, a short-circuiting sink, or external interruption.

```typescript
import { Effect, Stream } from "effect"

const ticks = Stream.tick("1 second").pipe(
  Stream.take(3),
  Stream.runDrain
)
```

## From Schedule

Use `Stream.fromSchedule` when the schedule output matters.
The stream requires whatever environment the schedule requires.
Pair it with `take` in tests and finite jobs.

```typescript
import { Schedule, Stream } from "effect"

const attempts = Stream.fromSchedule(Schedule.recurs(4)).pipe(
  Stream.map((index) => `attempt-${index}`)
)
```

## Repeat Value

`Stream.repeatValue` is an infinite stream.
It is useful for heartbeats, polling intents, and test sources when bounded immediately.
It is dangerous with `runCollect` unless a finite limit appears before the destructor.

```typescript
import { Stream } from "effect"

const threeHeartbeats = Stream.repeatValue("heartbeat").pipe(
  Stream.take(3)
)
```

## Pacing Existing Streams

Use `Stream.schedule` to delay elements from an existing stream.
This differs from `fromSchedule`: it transforms a source stream rather than creating the values itself.

```typescript
import { Schedule, Stream } from "effect"

const paced = Stream.fromIterable(["a", "b", "c"]).pipe(
  Stream.schedule(Schedule.spaced("200 millis"))
)
```

## Testing Rule

Every schedule-backed stream example should be finite.
Use `Stream.take(n)` before `runCollect` or `runDrain`.
If you only need the first event, prefer `Stream.runHead`.

## Operational Rule

Intervals are not throughput guarantees.
If downstream work takes longer than the interval, pull-based execution and buffering choices determine actual behaviour.
Do not use an unbounded buffer to hide slow consumers.

## Generation Checklist
- 04-stream-from-schedule check 01: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 04-stream-from-schedule check 02: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 04-stream-from-schedule check 03: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 04-stream-from-schedule check 04: Confirm examples avoid runtime entry points inside service code.
- 04-stream-from-schedule check 05: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 04-stream-from-schedule check 06: Confirm examples use `Effect.log` instead of direct platform logging.
- 04-stream-from-schedule check 07: Confirm no typed error is represented by a thrown exception.
- 04-stream-from-schedule check 08: Confirm absence is represented with `Option`, not nullish domain fields.
- 04-stream-from-schedule check 09: Confirm resource acquisition happens during stream consumption, not declaration.
- 04-stream-from-schedule check 10: Confirm finalizers run on completion, failure, and interruption.
- 04-stream-from-schedule check 11: Confirm queue shutdown is enabled only when the stream owns the queue.
- 04-stream-from-schedule check 12: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 04-stream-from-schedule check 13: Confirm schedule-backed examples are finite in tests.
- 04-stream-from-schedule check 14: Confirm `runCollect` is never used as the default for unknown-size streams.
- 04-stream-from-schedule check 15: Confirm `runFold` is preferred when only an accumulator is required.
- 04-stream-from-schedule check 16: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 04-stream-from-schedule check 17: Confirm `runForEach` does not hide parallelism requirements.
- 04-stream-from-schedule check 18: Confirm source-backed notes override cached community skill guidance.
- 04-stream-from-schedule check 19: Confirm links route to adjacent positive guidance and anti-patterns.
- 04-stream-from-schedule check 20: Confirm no v4-only token appears in prose or examples.
- 04-stream-from-schedule check 21: Confirm no deprecated schema import appears in examples.
- 04-stream-from-schedule check 22: Confirm examples stay small enough for agents to adapt safely.
- 04-stream-from-schedule check 23: Confirm code comments explain only non-obvious stream semantics.
- 04-stream-from-schedule check 24: Confirm the stream type parameters widen visibly when effects are introduced.
- 04-stream-from-schedule check 25: Confirm service requirements are provided at composition boundaries.
- 04-stream-from-schedule check 26: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 04-stream-from-schedule check 27: Confirm unbounded buffers are rejected unless input size is already proven small.
- 04-stream-from-schedule check 28: Confirm finite examples remain deterministic under test execution.
- 04-stream-from-schedule check 29: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 04-stream-from-schedule check 30: Confirm every file ends with 2-5 useful cross-reference links.
- 04-stream-from-schedule check 31: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 04-stream-from-schedule check 32: Confirm examples do not depend on unshown global mutable state.
- 04-stream-from-schedule check 33: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 04-stream-from-schedule check 34: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 04-stream-from-schedule check 35: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 04-stream-from-schedule check 36: Confirm the destructor matches whether all values, one value, or only effects matter.
- 04-stream-from-schedule check 37: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 04-stream-from-schedule check 38: Confirm a callback or queue source has a named capacity and shutdown owner.
- 04-stream-from-schedule check 39: Confirm typed failures remain in the stream or effect error channel.
- 04-stream-from-schedule check 40: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 04-stream-from-schedule check 41: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 04-stream-from-schedule check 42: Confirm any page cursor is immutable state returned by the pagination function.
- 04-stream-from-schedule check 43: Confirm page fetching is lazy and can stop after downstream `take`.
- 04-stream-from-schedule check 44: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 04-stream-from-schedule check 45: Confirm unordered output is selected only when downstream order is irrelevant.
- 04-stream-from-schedule check 46: Confirm `merge` termination is deliberate when either side can be infinite.
- 04-stream-from-schedule check 47: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 04-stream-from-schedule check 48: Confirm `zip` is used for positional alignment, not state synchronization.
- 04-stream-from-schedule check 49: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 04-stream-from-schedule check 50: Confirm batches are sized from an API, pool, or latency limit.
- 04-stream-from-schedule check 51: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 04-stream-from-schedule check 52: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 04-stream-from-schedule check 53: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 04-stream-from-schedule check 54: Confirm `orElse` is used only when the error value is not needed.
- 04-stream-from-schedule check 55: Confirm a sink is warranted instead of a simpler stream destructor.
- 04-stream-from-schedule check 56: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 04-stream-from-schedule check 57: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 04-stream-from-schedule check 58: Confirm Channel is justified by low-level read/write or parser needs.
- 04-stream-from-schedule check 59: Confirm Channel examples do not expose application services to type-parameter noise.
- 04-stream-from-schedule check 60: Confirm broadcast branches are consumed within the scope that created them.
- 04-stream-from-schedule check 61: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 04-stream-from-schedule check 62: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 04-stream-from-schedule check 63: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 04-stream-from-schedule check 64: Confirm examples avoid runtime entry points inside service code.
- 04-stream-from-schedule check 65: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 04-stream-from-schedule check 66: Confirm examples use `Effect.log` instead of direct platform logging.
- 04-stream-from-schedule check 67: Confirm no typed error is represented by a thrown exception.
- 04-stream-from-schedule check 68: Confirm absence is represented with `Option`, not nullish domain fields.
- 04-stream-from-schedule check 69: Confirm resource acquisition happens during stream consumption, not declaration.
- 04-stream-from-schedule check 70: Confirm finalizers run on completion, failure, and interruption.
- 04-stream-from-schedule check 71: Confirm queue shutdown is enabled only when the stream owns the queue.
- 04-stream-from-schedule check 72: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 04-stream-from-schedule check 73: Confirm schedule-backed examples are finite in tests.

## Cross-references
See also: [02-creating-streams.md](02-creating-streams.md), [06-transformations.md](06-transformations.md), [15-batching.md](15-batching.md), [18-infinite-streams.md](18-infinite-streams.md).
