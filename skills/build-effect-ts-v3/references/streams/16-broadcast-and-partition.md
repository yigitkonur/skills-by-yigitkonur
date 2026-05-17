# Broadcast And Partition
Split one stream into multiple consumers or branches without losing pressure and termination semantics.

## Broadcast

`Stream.broadcast(n, maximumLag)` creates `n` streams from one upstream source.
Each downstream stream can be consumed independently.
`maximumLag` limits how far the upstream can outrun the slowest consumer.
Use it when one source truly needs multiple subscribers.

```typescript
import { Effect, Stream } from "effect"

const source = Stream.fromIterable([1, 2, 3])

const program = Effect.scoped(
  Effect.gen(function* () {
    const [left, right] = yield* Stream.broadcast(source, 2, 8)

    return yield* Effect.all(
      [Stream.runCollect(left), Stream.runCollect(right)],
      { concurrency: 2 }
    )
  })
)
```

## Scoped Result

In v3, `Stream.broadcast` returns an `Effect` that requires `Scope.Scope`.
That shape is intentional because the branch streams are valid inside the broadcast scope.
Wrap short examples in `Effect.scoped`, or keep the scope requirement visible in library code.
Do not treat broadcast as a pure stream transformation.

```typescript
import { Effect, Stream } from "effect"

const branches = Effect.scoped(
  Stream.fromIterable(["a", "b"]).pipe(
    Stream.broadcast(2, { capacity: 16, strategy: "suspend" })
  )
)
```

## Broadcast Ownership

Broadcasted streams are tied to the source evaluation.
Consume the branches in the scope created by the broadcast.
Do not return one branch and discard the other unless that is exactly the lifecycle you intended.
A forgotten branch can hold back upstream progress.

## partitionEither

`Stream.partitionEither` classifies each input with a function returning an `Effect` of `Either`.
It returns scoped left and right streams for the two branches.
Use it when classification is part of the data model.
Use `bufferSize` to make the internal buffering explicit.

```typescript
import { Effect, Either, Stream } from "effect"

const source = Stream.fromIterable([1, 2, 3, 4])

const partitioned = source.pipe(
  Stream.partitionEither(
    (n) =>
      Effect.succeed(
        n % 2 === 0
          ? Either.right(n)
          : Either.left(`odd-${n}`)
      ),
    { bufferSize: 8 }
  )
)
```

`partitionEither` also returns a scoped Effect containing the branch streams.
Consume both branches within that scope unless you intentionally return the scoped effect to the caller.

## Partitioning Work

Partition when downstream handling differs by branch.
For a small local branch, mapping or matching inside one stream is clearer.
For independent branch consumers, partitioning makes ownership explicit.

## Backpressure

Broadcast and partition operators have internal buffers.
Those buffers are part of your pressure design.
Set sizes from expected consumer skew rather than copying defaults blindly.
If one branch is much slower, decide whether slowing the source is correct.

## Termination

All branches must be considered.
If a branch is infinite or never consumed, the whole topology can stall.
Tests should consume every branch with `take`, `runHead`, `runDrain`, or a finite source.

## Generation Checklist
- 16-broadcast-and-partition check 01: Confirm examples avoid runtime entry points inside service code.
- 16-broadcast-and-partition check 02: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 16-broadcast-and-partition check 03: Confirm examples use `Effect.log` instead of direct platform logging.
- 16-broadcast-and-partition check 04: Confirm no typed error is represented by a thrown exception.
- 16-broadcast-and-partition check 05: Confirm absence is represented with `Option`, not nullish domain fields.
- 16-broadcast-and-partition check 06: Confirm resource acquisition happens during stream consumption, not declaration.
- 16-broadcast-and-partition check 07: Confirm finalizers run on completion, failure, and interruption.
- 16-broadcast-and-partition check 08: Confirm queue shutdown is enabled only when the stream owns the queue.
- 16-broadcast-and-partition check 09: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 16-broadcast-and-partition check 10: Confirm schedule-backed examples are finite in tests.
- 16-broadcast-and-partition check 11: Confirm `runCollect` is never used as the default for unknown-size streams.
- 16-broadcast-and-partition check 12: Confirm `runFold` is preferred when only an accumulator is required.
- 16-broadcast-and-partition check 13: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 16-broadcast-and-partition check 14: Confirm `runForEach` does not hide parallelism requirements.
- 16-broadcast-and-partition check 15: Confirm source-backed notes override cached community skill guidance.
- 16-broadcast-and-partition check 16: Confirm links route to adjacent positive guidance and anti-patterns.
- 16-broadcast-and-partition check 17: Confirm no v4-only token appears in prose or examples.
- 16-broadcast-and-partition check 18: Confirm no deprecated schema import appears in examples.
- 16-broadcast-and-partition check 19: Confirm examples stay small enough for agents to adapt safely.
- 16-broadcast-and-partition check 20: Confirm code comments explain only non-obvious stream semantics.
- 16-broadcast-and-partition check 21: Confirm the stream type parameters widen visibly when effects are introduced.
- 16-broadcast-and-partition check 22: Confirm service requirements are provided at composition boundaries.
- 16-broadcast-and-partition check 23: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 16-broadcast-and-partition check 24: Confirm unbounded buffers are rejected unless input size is already proven small.
- 16-broadcast-and-partition check 25: Confirm finite examples remain deterministic under test execution.
- 16-broadcast-and-partition check 26: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 16-broadcast-and-partition check 27: Confirm every file ends with 2-5 useful cross-reference links.
- 16-broadcast-and-partition check 28: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 16-broadcast-and-partition check 29: Confirm examples do not depend on unshown global mutable state.
- 16-broadcast-and-partition check 30: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 16-broadcast-and-partition check 31: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 16-broadcast-and-partition check 32: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 16-broadcast-and-partition check 33: Confirm the destructor matches whether all values, one value, or only effects matter.
- 16-broadcast-and-partition check 34: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 16-broadcast-and-partition check 35: Confirm a callback or queue source has a named capacity and shutdown owner.
- 16-broadcast-and-partition check 36: Confirm typed failures remain in the stream or effect error channel.
- 16-broadcast-and-partition check 37: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 16-broadcast-and-partition check 38: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 16-broadcast-and-partition check 39: Confirm any page cursor is immutable state returned by the pagination function.
- 16-broadcast-and-partition check 40: Confirm page fetching is lazy and can stop after downstream `take`.
- 16-broadcast-and-partition check 41: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 16-broadcast-and-partition check 42: Confirm unordered output is selected only when downstream order is irrelevant.
- 16-broadcast-and-partition check 43: Confirm `merge` termination is deliberate when either side can be infinite.
- 16-broadcast-and-partition check 44: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 16-broadcast-and-partition check 45: Confirm `zip` is used for positional alignment, not state synchronization.
- 16-broadcast-and-partition check 46: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 16-broadcast-and-partition check 47: Confirm batches are sized from an API, pool, or latency limit.
- 16-broadcast-and-partition check 48: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 16-broadcast-and-partition check 49: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 16-broadcast-and-partition check 50: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 16-broadcast-and-partition check 51: Confirm `orElse` is used only when the error value is not needed.
- 16-broadcast-and-partition check 52: Confirm a sink is warranted instead of a simpler stream destructor.
- 16-broadcast-and-partition check 53: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 16-broadcast-and-partition check 54: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 16-broadcast-and-partition check 55: Confirm Channel is justified by low-level read/write or parser needs.
- 16-broadcast-and-partition check 56: Confirm Channel examples do not expose application services to type-parameter noise.
- 16-broadcast-and-partition check 57: Confirm broadcast branches are consumed within the scope that created them.
- 16-broadcast-and-partition check 58: Confirm partition branches are both consumed or intentionally returned as scoped values.

## Cross-references
See also: [03-stream-from-queue-pubsub.md](03-stream-from-queue-pubsub.md), [08-merging-zipping.md](08-merging-zipping.md), [14-backpressure.md](14-backpressure.md).
