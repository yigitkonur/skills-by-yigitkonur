# Running Effects
Run effects only at application edges, choosing the runner that preserves the outcome shape you need.

## Runtime Boundary

Most application code should return `Effect.Effect<A, E, R>`. A runner turns
that description into actual execution. Calling a runner too early collapses
typed errors into JavaScript exceptions or Promise rejection, detaches the work
from the larger fiber tree, and makes services harder to provide.

Use runners at boundaries:

- command entry points
- HTTP adapter handlers
- queue consumers
- test harnesses
- one-off scripts

Avoid runners inside repositories, domain services, business workflows, and
helpers called by other effects.

## Runner Matrix

| Runner | Returns | Throws or rejects on failure | Async allowed |
|---|---|---|---|
| `Effect.runSync(effect)` | `A` | yes | no |
| `Effect.runSyncExit(effect)` | `Exit.Exit<A, E>` | no | no |
| `Effect.runPromise(effect)` | `Promise<A>` | rejects | yes |
| `Effect.runPromiseExit(effect)` | `Promise<Exit.Exit<A, E>>` | no | yes |
| `Effect.runFork(effect)` | `RuntimeFiber<A, E>` | no direct value | yes |

`runSync` and `runSyncExit` are for synchronous effects. If the effect performs
async work, `runSync` throws and `runSyncExit` returns a failure Exit with a
defect cause.

## Synchronous Success

Use `runSync` when the effect is synchronous and cannot fail in the expected
error channel.

```typescript
import { Effect } from "effect"

const program = Effect.succeed(42).pipe(
  Effect.map((n) => n + 1)
)

const value = Effect.runSync(program)
```

This is common in small pure adapters and tests. It is a poor default for
programs with I/O.

## Synchronous Exit

Use `runSyncExit` when you want an `Exit` value instead of an exception.

```typescript
import { Effect, Exit } from "effect"

const program = Effect.fail("InvalidInput")
const exit = Effect.runSyncExit(program)

const handled = Exit.match(exit, {
  onFailure: () => "failed",
  onSuccess: (value) => `value=${value}`
})
```

`Exit` preserves success versus failure as data. It is useful for tests and
adapters that need to inspect causes.

## Promise Boundary

Use `runPromise` when integrating with Promise-based code that expects either a
resolved success value or a rejected failure.

```typescript
import { Effect } from "effect"

const program = Effect.succeed("ready").pipe(
  Effect.tap(Effect.log)
)

const promise: Promise<string> = Effect.runPromise(program)
```

`runPromise` resolves with the success value. It rejects for expected failures
and defects using Effect's fiber failure representation. That behavior is right
for many JavaScript adapter edges but wrong for internal Effect workflows.

## Promise Exit Boundary

Use `runPromiseExit` when the caller must receive all outcomes as data.

```typescript
import { Effect, Exit } from "effect"

const program = Effect.fail("NotReady")

const rendered = Effect.runPromiseExit(program).then((exit) =>
  Exit.match(exit, {
    onFailure: () => "not ready",
    onSuccess: (value) => `value=${value}`
  })
)
```

`runPromiseExit` returns `Promise<Exit.Exit<A, E>>` and does not reject for an
Effect failure. That makes it a good fit for tests, adapters that have their own
response format, and diagnostics.

## Forking

Use `runFork` when an edge must start an effect and keep a fiber handle.

```typescript
import { Effect, Fiber } from "effect"

const background = Effect.sleep("1 minute").pipe(
  Effect.zipRight(Effect.log("background finished"))
)

const fiber = Effect.runFork(background)
const interrupt = Fiber.interrupt(fiber)
```

`runFork` returns immediately with a runtime fiber. Supervise and interrupt it
deliberately; do not use it to avoid modeling concurrency inside Effect.

## Production Entrypoints

For Node programs, prefer `NodeRuntime.runMain` at the executable edge. It
connects process lifecycle behavior to the Effect runtime; see
[platform/12-node-runtime.md](../platform/12-node-runtime.md).

For applications with shared layers and long-lived services, use
`ManagedRuntime` to build a runtime once and run many effects through it; see
[services-layers/14-managed-runtime.md](../services-layers/14-managed-runtime.md).

## Anti-pattern: Running Mid-library

This is the boundary leak to avoid:

```typescript
import { Effect } from "effect"

const fetchUserName = (id: string): Promise<string> =>
  Effect.runPromise(loadUser(id).pipe(Effect.map((user) => user.name)))

declare const loadUser: (
  id: string
) => Effect.Effect<{ readonly name: string }, "MissingUser">
```

The caller sees `Promise<string>` and loses the `MissingUser` type. Keep the
function effectful instead:

```typescript
import { Effect } from "effect"

const fetchUserName = (id: string) =>
  loadUser(id).pipe(Effect.map((user) => user.name))

declare const loadUser: (
  id: string
) => Effect.Effect<{ readonly name: string }, "MissingUser">
```

Run once, at the adapter boundary.

## Cross-references

See also: [the Effect type](01-effect-type.md), [creating effects](02-creating-effects.md), [short-circuiting](11-short-circuiting.md), [effect match](12-effect-match.md).
