# Interruption
Use this to reason about cancellation, finalizers, and interruptible regions in concurrent Effect code.

## Interruption Is Not Failure

Interruption is how Effect stops fibers.

It is distinct from typed domain failure. A validation error says the domain
rejected an input. An interruption says a fiber was asked to stop because its
owner, scope, timeout, or race no longer needs it.

Interruption can be triggered by:

- `Fiber.interrupt`
- parent fiber termination
- scope closure
- race losers
- timeout losers
- `Effect.interrupt`
- completing a `Deferred` with interruption

Treat interruption as normal control flow for concurrent programs.

## Register Cleanup With `onInterrupt`

Use `Effect.onInterrupt` for interruption-specific logging or cleanup.

```typescript
import { Effect } from "effect"

const worker = Effect.gen(function* () {
  yield* Effect.sleep("1 minute")
  yield* Effect.logInfo("finished")
}).pipe(
  Effect.onInterrupt(() => Effect.logInfo("worker stopped early"))
)
```

`onInterrupt` runs when the effect is interrupted. It does not run for ordinary
success or ordinary typed failure.

For resources, prefer scoped APIs. Use `onInterrupt` for cancellation-specific
side effects, not as the primary resource-management tool.

## `uninterruptible`

`Effect.uninterruptible(effect)` makes a region ignore interruption signals
until the region exits.

```typescript
import { Effect } from "effect"

const writeCommitMarker = Effect.uninterruptible(
  Effect.logInfo("commit marker written")
)
```

Use it for small critical sections where being interrupted halfway would corrupt
state. Keep the region tiny. A large uninterruptible region can make shutdown,
timeouts, and races appear stuck.

## `uninterruptibleMask`

`Effect.uninterruptibleMask` starts uninterruptible but gives a `restore`
function for regions that should remain interruptible.

```typescript
import { Effect } from "effect"

declare const reserve: Effect.Effect<string>
declare const waitForRemote: (id: string) => Effect.Effect<void>
declare const commit: (id: string) => Effect.Effect<void>

const program = Effect.uninterruptibleMask((restore) =>
  Effect.gen(function* () {
    const reservationId = yield* reserve
    yield* restore(waitForRemote(reservationId))
    yield* commit(reservationId)
  })
)
```

The reservation and commit are protected. The remote wait remains interruptible.
This is the usual shape: protect state transitions, restore around waiting.

## `interruptible`

`Effect.interruptible(effect)` marks a region interruptible. It is mainly useful
inside a larger uninterruptible region or when normalizing code whose
interruptibility was changed by a parent combinator.

```typescript
import { Effect } from "effect"

const program = Effect.uninterruptible(
  Effect.interruptible(
    Effect.sleep("10 seconds")
  )
)
```

Prefer `uninterruptibleMask` when only part of a region needs protection.

## `interruptibleMask`

`Effect.interruptibleMask` starts interruptible and gives `restore` to restore
the previous interruptibility where needed.

Most application code needs `uninterruptibleMask` more often. Use
`interruptibleMask` when building lower-level combinators that must preserve a
caller-controlled interruptibility state.

## Interruption and `acquireRelease`

`Effect.acquireRelease(acquire, release)` is the primary scoped resource API.
See [../resource-management/03-acquire-release.md](../resource-management/03-acquire-release.md).

The interaction with interruption is the important part:

- acquisition is protected so a partially acquired resource does not leak
- release runs when the scope closes
- release runs on success, failure, or interruption
- release itself must not fail
- if acquisition succeeds, release is guaranteed to be registered

```typescript
import { Effect } from "effect"

type Connection = {
  readonly id: string
}

const acquireConnection = Effect.succeed({ id: "primary" } satisfies Connection)

const releaseConnection = (connection: Connection) =>
  Effect.logInfo(`released ${connection.id}`)

const connection = Effect.acquireRelease(
  acquireConnection,
  (connection) => releaseConnection(connection)
)

const useConnection = Effect.scoped(
  Effect.gen(function* () {
    const conn = yield* connection
    yield* Effect.logInfo(`using ${conn.id}`)
    yield* Effect.sleep("1 minute")
  })
)
```

If `useConnection` is interrupted during the sleep, the release action still
runs. This is why resource cleanup should live in `acquireRelease`, not in a
best-effort branch after the use site.

If acquisition itself must be interruptible, v3 also provides
`Effect.acquireReleaseInterruptible`. Use that only when the acquire operation
is safe to stop halfway or can clean up its own partial state.

## Finalizer Back-Pressure

Interrupting a fiber usually waits for the interrupted fiber to finish
termination, including finalizers.

```typescript
import { Effect, Fiber } from "effect"

const program = Effect.gen(function* () {
  const fiber = yield* Effect.fork(
    Effect.sleep("1 minute").pipe(
      Effect.onInterrupt(() => Effect.logInfo("cleanup observed"))
    )
  )

  yield* Fiber.interrupt(fiber)
  yield* Effect.logInfo("interrupt completed")
})
```

The final log happens after the interrupted fiber's interruption path completes.
This back-pressure is usually correct.

## Races and Timeouts

Race losers and timed-out effects are interrupted.

```typescript
import { Effect } from "effect"

const slow = Effect.sleep("10 seconds").pipe(
  Effect.onInterrupt(() => Effect.logInfo("slow branch interrupted"))
)

const fast = Effect.succeed("fast")

const program = Effect.race(slow, fast)
```

If the slow branch owns scoped resources, their finalizers run before the race
fully settles unless the branch is disconnected.

## When to Disconnect

Use `Effect.disconnect` when the caller should not wait for interruption
cleanup to finish. This changes latency, not the fact that interruption is
requested.

Reach for it after you can explain why back-pressure is harmful in this
specific path. Common cases are graceful shutdown orchestration and
latency-sensitive races whose losers have slow but independent cleanup.

## Anti-Patterns

- treating interruption as a domain error
- catching all failures and assuming interruptions are included
- wrapping a long network call in `uninterruptible`
- using `onInterrupt` instead of `acquireRelease` for resources
- disconnecting every slow cleanup path by default
- ignoring returned fibers so interruption ownership is invisible

## Cross-References

See also:

- [03-fiber-operations.md](03-fiber-operations.md)
- [04-effect-race.md](04-effect-race.md)
- [13-effect-timeout.md](13-effect-timeout.md)
- [14-effect-disconnect.md](14-effect-disconnect.md)
