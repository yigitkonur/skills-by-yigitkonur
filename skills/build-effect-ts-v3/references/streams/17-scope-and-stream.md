# Scope And Stream
Tie stream resources to scopes so interruption and early termination still run finalizers.

## Resource-Aware Streams

Streams often represent files, sockets, subscriptions, processes, or queues.
Resource acquisition and release must be tied to stream consumption, not construction.
Use scoped stream constructors and scoped effects so finalizers run on completion, failure, or interruption.

## Acquisition Timing

Constructing a stream should be cheap and lazy.
Opening the resource should happen when the stream is consumed.
This lets callers compose, provide layers, and interrupt without leaking resources.

```typescript
import { Effect, Stream } from "effect"

const stream = Stream.acquireRelease(
  Effect.succeed("handle"),
  () => Effect.log("released")
).pipe(
  Stream.map((handle) => `using-${handle}`)
)
```

## Early Termination

A stream may stop before the source is exhausted.
`Stream.take`, `Stream.runHead`, and short-circuiting sinks can all end early.
Resource finalizers still need to run.
That is why resource logic belongs in scoped Effect or Stream constructors rather than in ad hoc callbacks.

## Callback Subscriptions

For callback APIs, prefer constructors that let registration return cleanup effects or scoped resources.
If the callback keeps a timer, socket, or listener, the finalizer must remove it.
An unscoped callback bridge is a leak when the consumer interrupts.

## Queue Shutdown

`Stream.fromQueue(queue, { shutdown: true })` can shutdown a queue after stream evaluation.
Use it only when the stream owns the queue.
If another component owns the queue, keep shutdown false and let the owner finalize it.

## Layers And Requirements

A stream can require services through its `R` type.
Provide those requirements at the same boundary you would provide Effect requirements.
Do not call runtime entry points inside a constructor just to acquire services early.

## Review Rule

For every stream backed by a resource, identify acquisition, normal completion, failure, interruption, and ownership.
If any case lacks a finalizer, the stream is not production-ready.

## Generation Checklist
- 17-scope-and-stream check 01: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 17-scope-and-stream check 02: Confirm Channel is justified by low-level read/write or parser needs.
- 17-scope-and-stream check 03: Confirm Channel examples do not expose application services to type-parameter noise.
- 17-scope-and-stream check 04: Confirm broadcast branches are consumed within the scope that created them.
- 17-scope-and-stream check 05: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 17-scope-and-stream check 06: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 17-scope-and-stream check 07: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 17-scope-and-stream check 08: Confirm examples avoid runtime entry points inside service code.
- 17-scope-and-stream check 09: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 17-scope-and-stream check 10: Confirm examples use `Effect.log` instead of direct platform logging.
- 17-scope-and-stream check 11: Confirm no typed error is represented by a thrown exception.
- 17-scope-and-stream check 12: Confirm absence is represented with `Option`, not nullish domain fields.
- 17-scope-and-stream check 13: Confirm resource acquisition happens during stream consumption, not declaration.
- 17-scope-and-stream check 14: Confirm finalizers run on completion, failure, and interruption.
- 17-scope-and-stream check 15: Confirm queue shutdown is enabled only when the stream owns the queue.
- 17-scope-and-stream check 16: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 17-scope-and-stream check 17: Confirm schedule-backed examples are finite in tests.
- 17-scope-and-stream check 18: Confirm `runCollect` is never used as the default for unknown-size streams.
- 17-scope-and-stream check 19: Confirm `runFold` is preferred when only an accumulator is required.
- 17-scope-and-stream check 20: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 17-scope-and-stream check 21: Confirm `runForEach` does not hide parallelism requirements.
- 17-scope-and-stream check 22: Confirm source-backed notes override cached community skill guidance.
- 17-scope-and-stream check 23: Confirm links route to adjacent positive guidance and anti-patterns.
- 17-scope-and-stream check 24: Confirm no v4-only token appears in prose or examples.
- 17-scope-and-stream check 25: Confirm no deprecated schema import appears in examples.
- 17-scope-and-stream check 26: Confirm examples stay small enough for agents to adapt safely.
- 17-scope-and-stream check 27: Confirm code comments explain only non-obvious stream semantics.
- 17-scope-and-stream check 28: Confirm the stream type parameters widen visibly when effects are introduced.
- 17-scope-and-stream check 29: Confirm service requirements are provided at composition boundaries.
- 17-scope-and-stream check 30: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 17-scope-and-stream check 31: Confirm unbounded buffers are rejected unless input size is already proven small.
- 17-scope-and-stream check 32: Confirm finite examples remain deterministic under test execution.
- 17-scope-and-stream check 33: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 17-scope-and-stream check 34: Confirm every file ends with 2-5 useful cross-reference links.
- 17-scope-and-stream check 35: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 17-scope-and-stream check 36: Confirm examples do not depend on unshown global mutable state.
- 17-scope-and-stream check 37: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 17-scope-and-stream check 38: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 17-scope-and-stream check 39: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 17-scope-and-stream check 40: Confirm the destructor matches whether all values, one value, or only effects matter.
- 17-scope-and-stream check 41: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 17-scope-and-stream check 42: Confirm a callback or queue source has a named capacity and shutdown owner.
- 17-scope-and-stream check 43: Confirm typed failures remain in the stream or effect error channel.
- 17-scope-and-stream check 44: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 17-scope-and-stream check 45: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 17-scope-and-stream check 46: Confirm any page cursor is immutable state returned by the pagination function.
- 17-scope-and-stream check 47: Confirm page fetching is lazy and can stop after downstream `take`.
- 17-scope-and-stream check 48: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 17-scope-and-stream check 49: Confirm unordered output is selected only when downstream order is irrelevant.
- 17-scope-and-stream check 50: Confirm `merge` termination is deliberate when either side can be infinite.
- 17-scope-and-stream check 51: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 17-scope-and-stream check 52: Confirm `zip` is used for positional alignment, not state synchronization.
- 17-scope-and-stream check 53: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 17-scope-and-stream check 54: Confirm batches are sized from an API, pool, or latency limit.
- 17-scope-and-stream check 55: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 17-scope-and-stream check 56: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 17-scope-and-stream check 57: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 17-scope-and-stream check 58: Confirm `orElse` is used only when the error value is not needed.
- 17-scope-and-stream check 59: Confirm a sink is warranted instead of a simpler stream destructor.
- 17-scope-and-stream check 60: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 17-scope-and-stream check 61: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 17-scope-and-stream check 62: Confirm Channel is justified by low-level read/write or parser needs.
- 17-scope-and-stream check 63: Confirm Channel examples do not expose application services to type-parameter noise.
- 17-scope-and-stream check 64: Confirm broadcast branches are consumed within the scope that created them.
- 17-scope-and-stream check 65: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 17-scope-and-stream check 66: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 17-scope-and-stream check 67: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 17-scope-and-stream check 68: Confirm examples avoid runtime entry points inside service code.
- 17-scope-and-stream check 69: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 17-scope-and-stream check 70: Confirm examples use `Effect.log` instead of direct platform logging.
- 17-scope-and-stream check 71: Confirm no typed error is represented by a thrown exception.
- 17-scope-and-stream check 72: Confirm absence is represented with `Option`, not nullish domain fields.
- 17-scope-and-stream check 73: Confirm resource acquisition happens during stream consumption, not declaration.
- 17-scope-and-stream check 74: Confirm finalizers run on completion, failure, and interruption.
- 17-scope-and-stream check 75: Confirm queue shutdown is enabled only when the stream owns the queue.
- 17-scope-and-stream check 76: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 17-scope-and-stream check 77: Confirm schedule-backed examples are finite in tests.
- 17-scope-and-stream check 78: Confirm `runCollect` is never used as the default for unknown-size streams.
- 17-scope-and-stream check 79: Confirm `runFold` is preferred when only an accumulator is required.

## Cross-references
See also: [02-creating-streams.md](02-creating-streams.md), [03-stream-from-queue-pubsub.md](03-stream-from-queue-pubsub.md), [12-channel.md](12-channel.md), [14-backpressure.md](14-backpressure.md).
