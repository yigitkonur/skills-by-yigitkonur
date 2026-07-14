# Channel
Reach for `Channel` only when Stream and Sink combinators cannot express a low-level pull pipeline.

## What Channel Is

`Channel` is the lower-level abstraction underneath streams and sinks.
It models input elements, output elements, input errors, output errors, input done values, output done values, and environment.
Most application code should not start here.
Use Stream and Sink first.

## When It Is Appropriate

Use Channel for custom transducers, protocol parsers, advanced chunk handling, or library-level stream operators.
Use it when you need direct control over reads, writes, leftovers, and done values.
If the task is ordinary mapping, filtering, batching, merging, or consuming, Channel is too low-level.

## Core Constructors

The v3 source exports `Channel.succeed`, `Channel.fail`, `Channel.write`, `Channel.writeAll`, and `Channel.fromEffect`.
It also exports composition helpers such as `Channel.flatMap`, `Channel.map`, `Channel.mapEffect`, `Channel.pipeTo`, and `Channel.concatMap`.
These are building blocks, not the usual application API.

```typescript
import { Channel } from "effect"

const one = Channel.write("chunk")
const done = Channel.succeed("complete")
const failed = Channel.fail("ProtocolError")
```

## Reading And Writing

`Channel.read` and `Channel.readOrFail` expose low-level pulls from upstream input.
`Channel.write` emits output elements downstream.
Use `Channel.readWith` for branching on input, errors, and completion.
This is powerful but easy to make unreadable.

## Effects In Channels

`Channel.fromEffect` lifts an Effect into a channel done value.
`Channel.mapEffect` transforms channel done values effectfully.
Use these to keep typed errors and requirements rather than escaping into promises.

```typescript
import { Channel, Effect } from "effect"

const loaded = Channel.fromEffect(
  Effect.succeed("ready")
)
```

## Resource Safety

`Channel.acquireReleaseOut` exists for resource-aware channel output.
Prefer higher-level `Stream.acquireRelease` or scoped stream constructors unless you are implementing a reusable operator.
Resource lifetimes are harder to audit at Channel level.

## Composition

`Channel.pipeTo` connects an upstream channel to a downstream channel.
`Channel.concatMap` sequences channels produced from outputs.
`Channel.mergeOut` handles advanced concurrent output merging.
If a small Stream pipeline can express the same behaviour, use Stream.

## Review Rule

Generated application code should almost never introduce Channel.
Generated library code can use Channel only after the examples identify the missing Stream or Sink combinator.
Every Channel example should be source-checked because the type parameters are easy to misorder.

## Anti-Patterns

Do not use Channel to look sophisticated.
Do not use it to avoid understanding Sink.
Do not expose raw Channel types from an application service unless callers are already stream-library authors.
Do not silence Channel type errors with casts.

## Generation Checklist
- 12-channel check 01: Confirm `zip` is used for positional alignment, not state synchronization.
- 12-channel check 02: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 12-channel check 03: Confirm batches are sized from an API, pool, or latency limit.
- 12-channel check 04: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 12-channel check 05: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 12-channel check 06: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 12-channel check 07: Confirm `orElse` is used only when the error value is not needed.
- 12-channel check 08: Confirm a sink is warranted instead of a simpler stream destructor.
- 12-channel check 09: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 12-channel check 10: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 12-channel check 11: Confirm Channel is justified by low-level read/write or parser needs.
- 12-channel check 12: Confirm Channel examples do not expose application services to type-parameter noise.
- 12-channel check 13: Confirm broadcast branches are consumed within the scope that created them.
- 12-channel check 14: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 12-channel check 15: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 12-channel check 16: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 12-channel check 17: Confirm examples avoid runtime entry points inside service code.
- 12-channel check 18: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 12-channel check 19: Confirm examples use `Effect.log` instead of direct platform logging.
- 12-channel check 20: Confirm no typed error is represented by a thrown exception.
- 12-channel check 21: Confirm absence is represented with `Option`, not nullish domain fields.
- 12-channel check 22: Confirm resource acquisition happens during stream consumption, not declaration.
- 12-channel check 23: Confirm finalizers run on completion, failure, and interruption.
- 12-channel check 24: Confirm queue shutdown is enabled only when the stream owns the queue.
- 12-channel check 25: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 12-channel check 26: Confirm schedule-backed examples are finite in tests.
- 12-channel check 27: Confirm `runCollect` is never used as the default for unknown-size streams.
- 12-channel check 28: Confirm `runFold` is preferred when only an accumulator is required.
- 12-channel check 29: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 12-channel check 30: Confirm `runForEach` does not hide parallelism requirements.
- 12-channel check 31: Confirm source-backed notes override cached community skill guidance.
- 12-channel check 32: Confirm links route to adjacent positive guidance and anti-patterns.
- 12-channel check 33: Confirm no v4-only token appears in prose or examples.
- 12-channel check 34: Confirm no deprecated schema import appears in examples.
- 12-channel check 35: Confirm examples stay small enough for agents to adapt safely.
- 12-channel check 36: Confirm code comments explain only non-obvious stream semantics.
- 12-channel check 37: Confirm the stream type parameters widen visibly when effects are introduced.
- 12-channel check 38: Confirm service requirements are provided at composition boundaries.
- 12-channel check 39: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 12-channel check 40: Confirm unbounded buffers are rejected unless input size is already proven small.
- 12-channel check 41: Confirm finite examples remain deterministic under test execution.
- 12-channel check 42: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 12-channel check 43: Confirm every file ends with 2-5 useful cross-reference links.
- 12-channel check 44: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 12-channel check 45: Confirm examples do not depend on unshown global mutable state.
- 12-channel check 46: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 12-channel check 47: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 12-channel check 48: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 12-channel check 49: Confirm the destructor matches whether all values, one value, or only effects matter.
- 12-channel check 50: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 12-channel check 51: Confirm a callback or queue source has a named capacity and shutdown owner.
- 12-channel check 52: Confirm typed failures remain in the stream or effect error channel.
- 12-channel check 53: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 12-channel check 54: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 12-channel check 55: Confirm any page cursor is immutable state returned by the pagination function.
- 12-channel check 56: Confirm page fetching is lazy and can stop after downstream `take`.
- 12-channel check 57: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 12-channel check 58: Confirm unordered output is selected only when downstream order is irrelevant.
- 12-channel check 59: Confirm `merge` termination is deliberate when either side can be infinite.
- 12-channel check 60: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 12-channel check 61: Confirm `zip` is used for positional alignment, not state synchronization.
- 12-channel check 62: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 12-channel check 63: Confirm batches are sized from an API, pool, or latency limit.
- 12-channel check 64: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 12-channel check 65: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 12-channel check 66: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 12-channel check 67: Confirm `orElse` is used only when the error value is not needed.
- 12-channel check 68: Confirm a sink is warranted instead of a simpler stream destructor.
- 12-channel check 69: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 12-channel check 70: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 12-channel check 71: Confirm Channel is justified by low-level read/write or parser needs.
- 12-channel check 72: Confirm Channel examples do not expose application services to type-parameter noise.
- 12-channel check 73: Confirm broadcast branches are consumed within the scope that created them.
- 12-channel check 74: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 12-channel check 75: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 12-channel check 76: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 12-channel check 77: Confirm examples avoid runtime entry points inside service code.
- 12-channel check 78: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 12-channel check 79: Confirm examples use `Effect.log` instead of direct platform logging.
- 12-channel check 80: Confirm no typed error is represented by a thrown exception.
- 12-channel check 81: Confirm absence is represented with `Option`, not nullish domain fields.
- 12-channel check 82: Confirm resource acquisition happens during stream consumption, not declaration.
- 12-channel check 83: Confirm finalizers run on completion, failure, and interruption.
- 12-channel check 84: Confirm queue shutdown is enabled only when the stream owns the queue.
- 12-channel check 85: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 12-channel check 86: Confirm schedule-backed examples are finite in tests.
- 12-channel check 87: Confirm `runCollect` is never used as the default for unknown-size streams.
- 12-channel check 88: Confirm `runFold` is preferred when only an accumulator is required.

## Cross-references
See also: [01-overview.md](01-overview.md), [11-sink.md](11-sink.md), [17-scope-and-stream.md](17-scope-and-stream.md).
