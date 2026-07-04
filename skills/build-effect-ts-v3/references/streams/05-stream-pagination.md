# Stream Pagination
Model paginated APIs as streams with explicit cursor state and typed page failures.

## Why Stream Pagination

Pagination is a natural stream: each page produces zero or more items plus the next cursor.
A stream keeps the loop lazy, typed, and interruptible.
It also lets callers decide whether to collect all items, take a prefix, process each item, or batch downstream.

## Pure Pagination

Use `Stream.paginate` when page state and emitted value are computed synchronously.
The function returns a pair: the emitted value and an `Option` containing the next state.
`Option.none()` ends the stream.

```typescript
import { Option, Stream } from "effect"

const pages = Stream.paginate(0, (page) => [
  `page-${page}`,
  page < 2 ? Option.some(page + 1) : Option.none()
])
```

## Chunk Pagination

Use `Stream.paginateChunk` when each page produces many items.
This avoids emitting arrays as individual page records.
The stream emits the chunk contents as stream elements.

```typescript
import { Chunk, Option, Stream } from "effect"

const users = Stream.paginateChunk(0, (page) => [
  Chunk.make(`user-${page}-a`, `user-${page}-b`),
  page < 2 ? Option.some(page + 1) : Option.none()
])
```

## Effectful Pages

Use `Stream.paginateEffect` or `Stream.paginateChunkEffect` for HTTP, database, or SDK calls.
The fetch failure becomes the stream error channel.
The page function should return the next cursor explicitly, not mutate outer state.

```typescript
import { Chunk, Effect, Option, Stream } from "effect"

type Cursor = string
interface Page {
  readonly users: Chunk.Chunk<string>
  readonly next: Option.Option<Cursor>
}

declare const fetchPage: (
  cursor: Option.Option<Cursor>
) => Effect.Effect<Page, "PageLoadFailed">

const stream = Stream.paginateChunkEffect(Option.none<Cursor>(), (cursor) =>
  fetchPage(cursor).pipe(
    Effect.map((page) => [page.users, page.next] as const)
  )
)
```

## Cursor Shape

Keep cursor state small and serializable when possible.
Use `Option` for absence rather than sentinel strings.
If the API returns page numbers, the state can be a number.
If it returns opaque cursors, keep them opaque.
Do not parse cursor internals unless the remote contract says they are stable.

## Early Termination

A caller can stop a pagination stream without loading later pages.
This is the main advantage over an eager loop.

```typescript
import { Stream } from "effect"

declare const allUsers: Stream.Stream<string, "PageLoadFailed">

const firstTen = allUsers.pipe(Stream.take(10))
```

## Batching Downstream

Do not fetch all pages just to batch items later.
Use `Stream.grouped` or `Stream.groupedWithin` after the paginated stream.
This lets downstream process bounded chunks while upstream remains lazy.

## Error Strategy

Retry page fetches with `Stream.retry` when the whole page operation is retryable.
Recover with `Stream.catchAll` only when a fallback stream is semantically correct.
If a single malformed item should be skipped, decode inside `mapEffect` and decide per item.

## Anti-Patterns

Do not use a mutable `let cursor` loop inside `Effect.promise`.
Do not collect every page before transforming items.
Do not use native arrays to mean stream chunks in type signatures.
Do not hide an API error by ending the stream with `Option.none()`.

## Generation Checklist
- 05-stream-pagination check 01: Confirm Channel is justified by low-level read/write or parser needs.
- 05-stream-pagination check 02: Confirm Channel examples do not expose application services to type-parameter noise.
- 05-stream-pagination check 03: Confirm broadcast branches are consumed within the scope that created them.
- 05-stream-pagination check 04: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 05-stream-pagination check 05: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 05-stream-pagination check 06: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 05-stream-pagination check 07: Confirm examples avoid runtime entry points inside service code.
- 05-stream-pagination check 08: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 05-stream-pagination check 09: Confirm examples use `Effect.log` instead of direct platform logging.
- 05-stream-pagination check 10: Confirm no typed error is represented by a thrown exception.
- 05-stream-pagination check 11: Confirm absence is represented with `Option`, not nullish domain fields.
- 05-stream-pagination check 12: Confirm resource acquisition happens during stream consumption, not declaration.
- 05-stream-pagination check 13: Confirm finalizers run on completion, failure, and interruption.
- 05-stream-pagination check 14: Confirm queue shutdown is enabled only when the stream owns the queue.
- 05-stream-pagination check 15: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 05-stream-pagination check 16: Confirm schedule-backed examples are finite in tests.
- 05-stream-pagination check 17: Confirm `runCollect` is never used as the default for unknown-size streams.
- 05-stream-pagination check 18: Confirm `runFold` is preferred when only an accumulator is required.
- 05-stream-pagination check 19: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 05-stream-pagination check 20: Confirm `runForEach` does not hide parallelism requirements.
- 05-stream-pagination check 21: Confirm source-backed notes override cached community skill guidance.
- 05-stream-pagination check 22: Confirm links route to adjacent positive guidance and anti-patterns.
- 05-stream-pagination check 23: Confirm no v4-only token appears in prose or examples.
- 05-stream-pagination check 24: Confirm no deprecated schema import appears in examples.
- 05-stream-pagination check 25: Confirm examples stay small enough for agents to adapt safely.
- 05-stream-pagination check 26: Confirm code comments explain only non-obvious stream semantics.
- 05-stream-pagination check 27: Confirm the stream type parameters widen visibly when effects are introduced.
- 05-stream-pagination check 28: Confirm service requirements are provided at composition boundaries.
- 05-stream-pagination check 29: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 05-stream-pagination check 30: Confirm unbounded buffers are rejected unless input size is already proven small.
- 05-stream-pagination check 31: Confirm finite examples remain deterministic under test execution.
- 05-stream-pagination check 32: Confirm low-level API claims mention the cloned v3 source when they reject a guessed API.
- 05-stream-pagination check 33: Confirm every file ends with 2-5 useful cross-reference links.
- 05-stream-pagination check 34: Confirm the first paragraph gives agents the decision boundary, not a tutorial detour.
- 05-stream-pagination check 35: Confirm examples do not depend on unshown global mutable state.
- 05-stream-pagination check 36: Confirm downstream consumers decide whether to collect, fold, drain, or take a prefix.
- 05-stream-pagination check 37: Confirm replacing RxJS Observable preserves the important pull-based difference.
- 05-stream-pagination check 38: Confirm the source constructor is finite, scoped, or explicitly interrupted.
- 05-stream-pagination check 39: Confirm the destructor matches whether all values, one value, or only effects matter.
- 05-stream-pagination check 40: Confirm every emitted collection stays as `Chunk` until a real interop boundary.
- 05-stream-pagination check 41: Confirm a callback or queue source has a named capacity and shutdown owner.
- 05-stream-pagination check 42: Confirm typed failures remain in the stream or effect error channel.
- 05-stream-pagination check 43: Confirm `Option.none()` means end-of-stream only where the API defines it.
- 05-stream-pagination check 44: Confirm `Option.some(error)` is used only for a real typed stream failure.
- 05-stream-pagination check 45: Confirm any page cursor is immutable state returned by the pagination function.
- 05-stream-pagination check 46: Confirm page fetching is lazy and can stop after downstream `take`.
- 05-stream-pagination check 47: Confirm `mapEffect` has a numeric concurrency bound for dynamic inputs.
- 05-stream-pagination check 48: Confirm unordered output is selected only when downstream order is irrelevant.
- 05-stream-pagination check 49: Confirm `merge` termination is deliberate when either side can be infinite.
- 05-stream-pagination check 50: Confirm `concat` cannot be blocked forever by an infinite left stream.
- 05-stream-pagination check 51: Confirm `zip` is used for positional alignment, not state synchronization.
- 05-stream-pagination check 52: Confirm `interleave` is chosen for alternating pulls rather than timing races.
- 05-stream-pagination check 53: Confirm batches are sized from an API, pool, or latency limit.
- 05-stream-pagination check 54: Confirm grouped output is handled as `Chunk.Chunk<A>`.
- 05-stream-pagination check 55: Confirm retry wraps retryable page or pull effects, not non-idempotent writes.
- 05-stream-pagination check 56: Confirm fallbacks with `catchAll` preserve meaningful replacement values.
- 05-stream-pagination check 57: Confirm `orElse` is used only when the error value is not needed.
- 05-stream-pagination check 58: Confirm a sink is warranted instead of a simpler stream destructor.
- 05-stream-pagination check 59: Confirm sink leftovers matter before choosing leftover-aware combinators.
- 05-stream-pagination check 60: Confirm input adaptation uses source-backed `Sink.mapInput` or `Sink.dimap` helpers.
- 05-stream-pagination check 61: Confirm Channel is justified by low-level read/write or parser needs.
- 05-stream-pagination check 62: Confirm Channel examples do not expose application services to type-parameter noise.
- 05-stream-pagination check 63: Confirm broadcast branches are consumed within the scope that created them.
- 05-stream-pagination check 64: Confirm partition branches are both consumed or intentionally returned as scoped values.
- 05-stream-pagination check 65: Confirm `maximumLag` or buffer capacity explains the tolerated consumer skew.
- 05-stream-pagination check 66: Confirm every infinite source has `take`, `runHead`, interruption, or a short-circuiting sink.
- 05-stream-pagination check 67: Confirm examples avoid runtime entry points inside service code.
- 05-stream-pagination check 68: Confirm imports use the `effect` barrel or named `@effect/*` packages.
- 05-stream-pagination check 69: Confirm examples use `Effect.log` instead of direct platform logging.
- 05-stream-pagination check 70: Confirm no typed error is represented by a thrown exception.
- 05-stream-pagination check 71: Confirm absence is represented with `Option`, not nullish domain fields.
- 05-stream-pagination check 72: Confirm resource acquisition happens during stream consumption, not declaration.
- 05-stream-pagination check 73: Confirm finalizers run on completion, failure, and interruption.
- 05-stream-pagination check 74: Confirm queue shutdown is enabled only when the stream owns the queue.
- 05-stream-pagination check 75: Confirm pubsub streams are bounded by subscription lifetime or `take` in examples.
- 05-stream-pagination check 76: Confirm schedule-backed examples are finite in tests.
- 05-stream-pagination check 77: Confirm `runCollect` is never used as the default for unknown-size streams.
- 05-stream-pagination check 78: Confirm `runFold` is preferred when only an accumulator is required.
- 05-stream-pagination check 79: Confirm `runDrain` is used when emitted values are intentionally ignored.
- 05-stream-pagination check 80: Confirm `runForEach` does not hide parallelism requirements.
- 05-stream-pagination check 81: Confirm source-backed notes override cached community skill guidance.
- 05-stream-pagination check 82: Confirm links route to adjacent positive guidance and anti-patterns.
- 05-stream-pagination check 83: Confirm no v4-only token appears in prose or examples.
- 05-stream-pagination check 84: Confirm no deprecated schema import appears in examples.
- 05-stream-pagination check 85: Confirm examples stay small enough for agents to adapt safely.
- 05-stream-pagination check 86: Confirm code comments explain only non-obvious stream semantics.
- 05-stream-pagination check 87: Confirm the stream type parameters widen visibly when effects are introduced.
- 05-stream-pagination check 88: Confirm service requirements are provided at composition boundaries.
- 05-stream-pagination check 89: Confirm buffer strategies named `dropping` or `sliding` tolerate data loss.
- 05-stream-pagination check 90: Confirm unbounded buffers are rejected unless input size is already proven small.

## Cross-references
See also: [02-creating-streams.md](02-creating-streams.md), [06-transformations.md](06-transformations.md), [09-mapEffect-concurrency.md](09-mapEffect-concurrency.md), [15-batching.md](15-batching.md).
