# Manual Cleanup
Use this when resource lifecycle is hidden in manual finalization instead of Effect scopes.

## Symptom — Bad Code
```typescript
import { Effect } from "effect"

type Connection = { readonly close: () => Promise<void>; readonly query: (sql: string) => Promise<string> }
declare const openConnection: () => Promise<Connection>

const program = Effect.tryPromise(async () => {
  const connection = await openConnection()
  try {
    return await connection.query("select 1")
  } finally {
    await connection.close()
  }
})
```

## Why Bad
The lifecycle is buried inside a Promise callback rather than a scoped Effect resource.
Manual cleanup is easy to get wrong under interruption, retries, and sharing.
The runtime cannot supervise a finalizer it cannot see.

## Fix — Correct Pattern
```typescript
import { Effect } from "effect"

type Connection = { readonly close: () => Promise<void>; readonly query: (sql: string) => Promise<string> }
declare const openConnection: () => Promise<Connection>

const connection = Effect.acquireRelease(
  Effect.tryPromise(() => openConnection()),
  (conn) => Effect.promise(() => conn.close())
)

const program = Effect.scoped(
  Effect.gen(function* () {
    const conn = yield* connection
    return yield* Effect.tryPromise(() => conn.query("select 1"))
  })
)
```

## Cross-references
See also: [resource overview](../resource-management/01-overview.md), [acquire release](../resource-management/03-acquire-release.md), [scopes](../resource-management/02-scope.md).
