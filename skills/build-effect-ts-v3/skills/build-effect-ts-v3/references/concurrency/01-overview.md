# Concurrency Overview
Use this when choosing Effect fibers, collection concurrency, or coordination primitives instead of raw promises.

## Core Model

Effect concurrency is fiber-based.

A fiber is a lightweight runtime execution unit managed by Effect. It is not an
operating-system thread, and it is not a JavaScript `Promise`. It has:

- a typed success value
- a typed failure channel
- a cause that can record defects and interruption
- a parent-child relationship
- finalizers that run on success, failure, and interruption

The runtime creates a fiber whenever an Effect program is executed. You create
additional fibers when you ask for concurrency with APIs such as:

- `Effect.fork`
- `Effect.all(..., { concurrency: N })`
- `Effect.forEach(..., { concurrency: N })`
- `Effect.race`
- `Effect.raceAll`

The practical rule is simple: do not reach for JavaScript promise fan-out inside
an Effect codebase. Use Effect APIs so interruption, finalizers, typed errors,
tracing, fiber refs, and supervision remain part of the same runtime model.

## Structured Concurrency

Structured concurrency means spawned work has an owner.

With `Effect.fork`, the new fiber is supervised by the parent fiber. If the
parent fiber terminates before the child completes, the child is interrupted.
That default prevents accidental background work from surviving past the
operation that started it.

Use this default unless you can name the owner that should outlive the parent.
If a background fiber should live for a scope, fork it into that scope. If it
should live for the whole runtime, make that choice explicit and document why.

```typescript
import { Effect, Fiber } from "effect"

const refreshCache = Effect.gen(function* () {
  yield* Effect.sleep("1 second")
  yield* Effect.logInfo("cache refreshed")
  return "ready"
})

const program = Effect.gen(function* () {
  const fiber = yield* Effect.fork(refreshCache)
  const status = yield* Fiber.join(fiber)
  return status
})
```

This is structured because the parent owns the child fiber, then joins it before
returning. If the parent is interrupted, the child receives the same shutdown
pressure.

## Prefer Higher-Level APIs

Direct fibers are powerful, but most application work should start with
collection and racing APIs:

| Need | Prefer | Why |
|---|---|---|
| Run known tasks and collect all results | `Effect.all` | Preserves result order and typed failures |
| Map over a collection effectfully | `Effect.forEach` | Avoids building intermediate arrays of effects |
| Keep at most N tasks active | `{ concurrency: N }` | Prevents memory, socket, and rate-limit spikes |
| First successful result wins | `Effect.race` or `Effect.raceAll` | Interrupts losing work safely |
| Coordinate one-time readiness | `Deferred` | Avoids polling and shared mutable flags |
| Guard shared capacity | `Effect.makeSemaphore` | Releases permits on failure and interruption |

Use `Effect.fork` directly when the task must continue while the current fiber
does other work, when you need a `Fiber` handle, or when supervision is the
point of the design.

## The Concurrency Budget

Every fan-out needs a budget. The budget is not just CPU. It includes:

- database pool capacity
- outbound socket limits
- third-party API limits
- file descriptors
- heap retained by in-flight tasks
- queue depth in downstream services
- telemetry volume

Default `Effect.all` and `Effect.forEach` execution is sequential when no
`concurrency` option is supplied. Sequential is safe but may be slow. Explicit
bounded concurrency is usually the production default.

```typescript
import { Effect } from "effect"

declare const userIds: ReadonlyArray<string>
declare const rebuildUserIndex: (id: string) => Effect.Effect<void>

const rebuildAllIndexes = Effect.forEach(
  userIds,
  (id) => rebuildUserIndex(id),
  {
    concurrency: 8,
    discard: true
  }
)
```

The number `8` is a contract with the outside world. It says this program will
not rebuild more than eight users at the same time, even if tomorrow's input is
100 times larger.

## Interruption Is Normal

In Effect, interruption is not an exceptional hack. It is how concurrent work is
cancelled.

Interruption can happen when:

- a parent fiber exits while a child is still running
- a timeout expires
- a race has a winner and interrupts the loser
- a caller interrupts a `Fiber`
- a scope closes

Finalizers still run. Semaphore permits are returned. Scoped resources release.
This is the main reason to keep concurrency inside Effect instead of mixing in
ad hoc promise cancellation.

```typescript
import { Effect } from "effect"

const worker = Effect.gen(function* () {
  yield* Effect.sleep("10 seconds")
  yield* Effect.logInfo("finished")
}).pipe(
  Effect.onInterrupt(() => Effect.logInfo("worker interrupted"))
)
```

Register `onInterrupt` for cancellation-specific observability. Use scoped
resource APIs for resource cleanup.

## Minimum Version

This reference targets `effect@3.21.2`.

The cloned source confirms these v3 APIs:

- `Effect.fork`
- `Effect.forkDaemon`
- `Effect.forkScoped`
- `Effect.forkIn`
- `Effect.makeSemaphore`
- `Deferred.make`
- `Effect.makeLatch`

The latch API is newer than the core fiber APIs and is marked `@since 3.8.0` in
the source. The other core concurrency APIs used here are present in the v3
source targeted by this skill.

## Anti-Patterns

Avoid these patterns in Effect code:

- unbounded fan-out over dynamic input
- manually tracking child fibers without joining, interrupting, or scoping them
- replacing `Deferred` with polling flags
- guarding capacity with mutable counters instead of `Semaphore`
- treating interruption as a domain failure
- detaching background work because joining feels inconvenient

## Cross-References

See also:

- [02-fork-types.md](02-fork-types.md)
- [05-effect-all-concurrency.md](05-effect-all-concurrency.md)
- [07-bounded-parallelism.md](07-bounded-parallelism.md)
- [11-interruption.md](11-interruption.md)
