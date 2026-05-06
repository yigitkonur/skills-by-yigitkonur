# Fork Types
Use this to choose the correct v3 fork variant and keep fiber lifetimes explicit.

## The Four v3 Fork APIs

Effect v3 exposes these fork variants:

| API | Lifetime owner | Typical use |
|---|---|---|
| `Effect.fork` | Parent fiber | Concurrent child work owned by the current operation |
| `Effect.forkDaemon` | Runtime global scope | Runtime-long background process |
| `Effect.forkScoped` | Current scope | Background process tied to a scoped lifetime |
| `Effect.forkIn` | Explicit `Scope.Scope` | Fiber owned by a scope selected by the caller |

These names are the v3 names. Do not use renamed APIs from other major versions
in this skill or in v3 code examples.

## `Effect.fork`

`Effect.fork(effect)` creates a child fiber supervised by the parent.

```typescript
import { Effect, Fiber } from "effect"

const compute = (n: number) =>
  Effect.gen(function* () {
    yield* Effect.sleep("100 millis")
    return n * 2
  })

const program = Effect.gen(function* () {
  const fiber = yield* Effect.fork(compute(21))
  yield* Effect.logInfo("parent can continue")
  return yield* Fiber.join(fiber)
})
```

Use `fork` when the parent operation still owns the child work. If the parent is
interrupted, the child is interrupted too. This is the default because most
concurrent work should not leak beyond its request, job, transaction, or scope.

## `Effect.forkDaemon`

`Effect.forkDaemon(effect)` creates a background fiber that is not tied to the
parent fiber lifecycle.

```typescript
import { Effect, Schedule } from "effect"

const heartbeat = Effect.logInfo("heartbeat").pipe(
  Effect.repeat(Schedule.spaced("30 seconds"))
)

const startHeartbeat = Effect.gen(function* () {
  yield* Effect.forkDaemon(heartbeat)
  yield* Effect.logInfo("heartbeat started")
})
```

Use it sparingly. The correct question is not "do I want this in the
background?" The correct question is "who owns stopping this?" If the answer is
"the whole runtime", daemon may be correct. If the answer is a request, route,
worker, or resource scope, use another variant.

## `Effect.forkScoped`

`Effect.forkScoped(effect)` creates a fiber tied to the current scope. The fiber
can outlive the current parent fiber, but it is interrupted when the scope
closes.

```typescript
import { Effect, Fiber, Schedule } from "effect"

const pollMetrics = Effect.logInfo("poll metrics").pipe(
  Effect.repeat(Schedule.spaced("5 seconds"))
)

const scopedMetrics = Effect.scoped(
  Effect.gen(function* () {
    const fiber = yield* Effect.forkScoped(pollMetrics)
    yield* Effect.sleep("15 seconds")
    yield* Fiber.interrupt(fiber)
  })
)
```

Use `forkScoped` for resource-local background processes: health checks,
subscription listeners, pollers, or stream drains that should live exactly as
long as the scope that created them.

## `Effect.forkIn`

`Effect.forkIn(effect, scope)` forks into a specific scope.

```typescript
import { Effect, Fiber, Scope } from "effect"

declare const processJob: Effect.Effect<void>

const startJobInScope = (scope: Scope.Scope) =>
  Effect.gen(function* () {
    const fiber = yield* Effect.forkIn(processJob, scope)
    yield* Effect.logInfo("job attached to selected scope")
    return fiber
  })
```

Use `forkIn` when the lifetime owner is not the current scope but is still a
real scope. This is useful when an inner setup step needs to start work owned by
an outer component.

## Decision Table

| Situation | Use | Reason |
|---|---|---|
| Start work and await its result later in the same operation | `Effect.fork` | Parent owns the child |
| Start a metrics poller for a scoped service | `Effect.forkScoped` | Scope closure stops the poller |
| Start a child in an outer scope from inside nested setup | `Effect.forkIn` | Ownership is explicit |
| Start runtime-level telemetry once | `Effect.forkDaemon` | Lifetime is intentionally global |
| Map over a collection | `Effect.forEach` | You probably do not need manual fibers |
| Race providers | `Effect.race` / `Effect.raceAll` | Losers are interrupted automatically |

## Joining and Observing

Fork returns a `Fiber.RuntimeFiber<A, E>`. A fiber handle lets you:

- `Fiber.join` to obtain `A` or fail with `E`
- `Fiber.await` to obtain the full `Exit<A, E>`
- `Fiber.interrupt` to request cancellation and wait for termination
- `Fiber.poll` to check whether it is already done

```typescript
import { Effect, Fiber, Exit } from "effect"

const observe = Effect.gen(function* () {
  const fiber = yield* Effect.fork(Effect.succeed("ok"))
  const exit = yield* Fiber.await(fiber)

  if (Exit.isSuccess(exit)) {
    yield* Effect.logInfo(`fiber completed: ${exit.value}`)
  }
})
```

Use `join` when failure should propagate like ordinary effect failure. Use
`await` when you need to inspect success, failure, defects, or interruption as
data.

## Lifetime Smells

Watch for these smells:

- a `fork` result is ignored
- daemon work has no shutdown story
- a scoped fiber uses a global lifetime by accident
- a request handler starts a background task and returns immediately
- a retry loop forks a new child on each attempt without joining or scoping

The fix is usually to move up one level of abstraction: `Effect.all`,
`Effect.forEach`, `Effect.race`, `Effect.acquireRelease`, or `Effect.scoped`.

## Source Notes

In the v3 source:

- `Effect.fork` returns `Effect<Fiber.RuntimeFiber<A, E>, never, R>`
- `Effect.forkDaemon` has the same return shape but uses the global scope
- `Effect.forkScoped` requires `Scope.Scope | R`
- `Effect.forkIn` accepts an explicit `Scope.Scope`

The official docs state that `Effect.fork` uses structured concurrency: child
fiber lifetimes are tied to their parent. The source comments also describe
auto-supervision for `fork` and scope ownership for `forkScoped` / `forkIn`.

## Cross-References

See also:

- [01-overview.md](01-overview.md)
- [03-fiber-operations.md](03-fiber-operations.md)
- [11-interruption.md](11-interruption.md)
- [14-effect-disconnect.md](14-effect-disconnect.md)
