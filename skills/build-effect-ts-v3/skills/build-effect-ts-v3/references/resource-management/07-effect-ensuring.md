# Effect Ensuring
Use `Effect.ensuring`, `Effect.onExit`, and `Effect.onError` for action-level cleanup that is not resource acquisition.

## The Difference

`Effect.ensuring(finalizer)` attaches a cleanup effect to one effect. The
cleanup runs after the effect starts and then exits through success, failure, or
interruption.

It is not the same as `Effect.acquireRelease`. `ensuring` does not model an
acquired value. It just says, "after this action, run this finalizer."

```typescript
import { Effect } from "effect"

const program = Effect.logInfo("write audit entry").pipe(
  Effect.ensuring(Effect.logInfo("audit attempt finished"))
)
```

Use it for cleanup that is independent of a resource value.

## ensuring

Use `ensuring` when the cleanup is the same for every exit.

```typescript
import { Effect } from "effect"

declare const flushMetrics: Effect.Effect<void>
declare const handleRequest: Effect.Effect<string, "RequestError">

const program = handleRequest.pipe(
  Effect.ensuring(flushMetrics)
)
```

The finalizer itself must not fail with typed errors.

## onExit

Use `Effect.onExit` when cleanup needs the result of the effect.

```typescript
import { Effect, Exit } from "effect"

declare const runJob: Effect.Effect<string, "JobError">

const program = runJob.pipe(
  Effect.onExit((exit) =>
    Exit.isSuccess(exit)
      ? Effect.logInfo(`job succeeded: ${exit.value}`)
      : Effect.logInfo("job did not complete successfully")
  )
)
```

`onExit` sees success, typed failure, defects, and interruption through the
`Exit` value.

## onError

Use `Effect.onError` when cleanup should run only for failure causes, including
interruption.

```typescript
import { Effect } from "effect"

declare const processBatch: Effect.Effect<number, "BatchError">

const program = processBatch.pipe(
  Effect.onError((cause) =>
    Effect.logInfo(`batch stopped with cause: ${cause}`)
  )
)
```

Use this for failure diagnostics, rollback signals, or cleanup that should not
run after success.

## acquireRelease Versus ensuring

`Effect.acquireRelease` is the right tool when cleanup depends on an acquired
resource value.

```typescript
import { Effect } from "effect"

type Lock = {
  readonly update: Effect.Effect<void, "UpdateError">
  readonly release: Effect.Effect<void>
}

declare const acquireLock: Effect.Effect<Lock, "LockError">

const program = Effect.acquireUseRelease(
  acquireLock,
  (lock) => lock.update,
  (lock) => lock.release
)
```

An `ensuring` finalizer cannot receive the acquired `lock` unless you capture it
manually, which is exactly the lifecycle coupling `acquireRelease` models for
you.

## Do Not Use ensuring To Hide Resource State

Do not capture a handle in mutable outer state and then read that state from an
`ensuring` finalizer. The cleanup becomes disconnected from the acquisition
that made the handle valid.

Keep the handle in the acquisition boundary:

```typescript
import { Effect } from "effect"

const safe = Effect.acquireUseRelease(
  openHandle,
  (handle) => useHandle(handle),
  (handle) => handle.close
)
```

The safe version passes the acquired value directly to release.

## Choosing The Hook

| Need | Use |
|---|---|
| same cleanup after any exit | `Effect.ensuring` |
| cleanup depends on success or failure exit | `Effect.onExit` |
| cleanup only after failure or interruption | `Effect.onError` |
| cleanup is tied to an acquired value | `Effect.acquireRelease` or `Effect.acquireUseRelease` |
| cleanup belongs to a wider scope | `Effect.addFinalizer` |

## Cross-references

See also: [Acquire Use Release](04-acquire-use-release.md), [Add Finalizer](06-add-finalizer.md), [Effect Scoped](05-effect-scoped.md), [Cleanup Order](08-cleanup-order.md).
