# Acquire Use Release
Use `Effect.acquireUseRelease` for the bracket pattern when one local use owns the whole resource lifetime.

## The Bracket Shape

`Effect.acquireUseRelease(acquire, use, release)` is the direct bracket form:

1. acquire a resource
2. use it
3. release it after use completes, fails, or is interrupted

Unlike `Effect.acquireRelease`, the result is not a scoped resource value that
requires `Scope.Scope`. The scope is internal to the bracket.

```typescript
import { Effect } from "effect"

type FileHandle = {
  readonly read: Effect.Effect<string, "ReadError">
  readonly close: Effect.Effect<void>
}

declare const openFile: Effect.Effect<FileHandle, "OpenError">

const program = Effect.acquireUseRelease(
  openFile,
  (file) => file.read,
  (file) => file.close
)
```

The program's error channel is the union of acquire and use failures. The
release effect must not fail with typed errors.

## When To Prefer It

Use `acquireUseRelease` when the resource does not need to escape the local
operation.

| Situation | Prefer |
|---|---|
| open file, read it, close file | `Effect.acquireUseRelease` |
| checkout connection for one query | `Effect.acquireUseRelease` |
| lock, mutate, unlock | `Effect.acquireUseRelease` |
| create shared database pool service | `Effect.acquireRelease` inside `Layer.scoped` |
| allocate resource and pass it to several scoped components | `Effect.acquireRelease` plus `Effect.scoped` |

The bracket is the simplest correct shape for one local resource region.

## Release Receives The Use Exit

The release function receives the resource and the `Exit` of the use effect.
That lets cleanup commit, roll back, or log based on outcome.

```typescript
import { Effect, Exit } from "effect"

type Transaction = {
  readonly commit: Effect.Effect<void>
  readonly rollback: Effect.Effect<void>
}

declare const beginTransaction: Effect.Effect<Transaction, "BeginError">
declare const writeRows: (tx: Transaction) => Effect.Effect<number, "WriteError">

const program = Effect.acquireUseRelease(
  beginTransaction,
  (tx) => writeRows(tx),
  (tx, exit) =>
    Exit.isSuccess(exit)
      ? tx.commit
      : tx.rollback
)
```

This keeps transaction outcome logic in the resource boundary instead of
scattering it through the use body.

## Interruption Safety

The bracket release runs even when the use effect is interrupted.

```typescript
import { Effect } from "effect"

type Lease = {
  readonly id: string
  readonly release: Effect.Effect<void>
}

declare const acquireLease: Effect.Effect<Lease, "LeaseError">

const program = Effect.acquireUseRelease(
  acquireLease,
  (lease) =>
    Effect.logInfo(`using ${lease.id}`).pipe(
      Effect.zipRight(Effect.never)
    ),
  (lease) => lease.release
)
```

If another fiber interrupts `program`, the lease release still runs.

## Avoid Nested Manual Cleanup

Do not put manual cleanup inside the `use` function. Let the bracket release
own resource disposal.

```typescript
import { Effect } from "effect"

type Lock = {
  readonly update: Effect.Effect<void, "UpdateError">
  readonly unlock: Effect.Effect<void>
}

declare const lock: Effect.Effect<Lock, "LockError">

const updateSafely = Effect.acquireUseRelease(
  lock,
  (resource) => resource.update,
  (resource) => resource.unlock
)
```

That shape ensures the unlock operation belongs to the acquired lock and runs
once.

## Multiple Resources

For a few dependent local resources, nested brackets are explicit and correct,
but they can become noisy.

```typescript
import { Effect } from "effect"

type Database = { readonly close: Effect.Effect<void> }
type Cursor = {
  readonly next: Effect.Effect<string>
  readonly close: Effect.Effect<void>
}

declare const openDatabase: Effect.Effect<Database, "DbError">
declare const openCursor: (db: Database) => Effect.Effect<Cursor, "CursorError">

const program = Effect.acquireUseRelease(
  openDatabase,
  (db) =>
    Effect.acquireUseRelease(
      openCursor(db),
      (cursor) => cursor.next,
      (cursor) => cursor.close
    ),
  (db) => db.close
)
```

For larger compositions, use multiple `Effect.acquireRelease` resources inside
one `Effect.scoped` block. The code reads more linearly and the LIFO cleanup
order remains the same.

## Error Channel Shape

The type of `Effect.acquireUseRelease(acquire, use, release)` combines:

| Part | Contributes to |
|---|---|
| `acquire` success | input to `use` and `release` |
| `acquire` failure | program error channel |
| `use` success | program success channel |
| `use` failure | program error channel |
| `release` requirements | program requirements |
| `release` failure | must be `never` |

If release needs services, those services remain in the requirement channel.

## Cross-references

See also: [Acquire Release](03-acquire-release.md), [Effect Scoped](05-effect-scoped.md), [Effect Ensuring](07-effect-ensuring.md), [Cleanup Order](08-cleanup-order.md).
