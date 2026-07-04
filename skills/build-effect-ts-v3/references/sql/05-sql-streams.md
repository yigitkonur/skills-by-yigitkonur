# SQL Streams
Use statement streams for large result sets and row-by-row processing.

## Statement Stream

Every SQL statement exposes `.stream`. It returns an Effect `Stream` of rows
with `SqlError.SqlError` as the failure type.

```typescript
import { Effect, Stream } from "effect"
import { SqlClient } from "@effect/sql"

type UserRow = {
  readonly id: number
  readonly email: string
}

const streamActiveUsers = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient

  return sql<UserRow>`
    SELECT id, email
    FROM users
    WHERE active = ${true}
    ORDER BY id
  `.stream
})

const logActiveUsers = streamActiveUsers.pipe(
  Effect.flatMap(
    Stream.runForEach((row) => Effect.logInfo(`user=${row.id}:${row.email}`))
  )
)
```

Use the stream when the result set can be large or when downstream processing
should apply backpressure.

## Streaming Pipeline

SQL streams compose with normal `Stream` operators:

```typescript
import { Effect, Stream } from "effect"
import { SqlClient } from "@effect/sql"

const exportUserEmails = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient

  const rows = sql<{ readonly email: string }>`
    SELECT email
    FROM users
    WHERE active = ${true}
  `.stream

  return yield* rows.pipe(
    Stream.map((row) => row.email.toLowerCase()),
    Stream.grouped(100),
    Stream.runForEach((batch) =>
      Effect.logInfo(`exported-batch-size=${batch.length}`)
    )
  )
})
```

Keep expensive per-row work in the stream pipeline so interruption and
backpressure remain visible to the runtime.

## Parameters Still Work

Streaming does not change parameterization:

```typescript
import { Effect, Stream } from "effect"
import { SqlClient } from "@effect/sql"

const streamUsersByIds = (ids: ReadonlyArray<number>) =>
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient

    return yield* sql<{ readonly id: number; readonly email: string }>`
      SELECT id, email
      FROM users
      WHERE id IN ${sql.in(ids)}
    `.stream.pipe(
      Stream.runCollect
    )
  })
```

For small result sets, yielding the statement directly is simpler. Use streams
when memory, backpressure, or early termination matter.

## Driver Behavior

Drivers implement `Connection.executeStream` differently:

| Driver family | Stream source |
|---|---|
| PostgreSQL | driver cursor or stream support |
| MySQL | query stream |
| SQLite | iterative statement execution |
| ClickHouse | query stream |
| D1 and durable object SQLite | platform-specific result iteration |

The shared API hides those details. Tune database-level fetch size or driver
configuration only when production metrics show stream pressure.

## Scope And Finalization

Streams can hold a database connection while they run. Consume them inside the
same effect that constructs them, or return a scoped stream from a service whose
caller understands the lifetime.

```typescript
import { Effect, Stream } from "effect"
import { SqlClient } from "@effect/sql"

const countStreamedRows = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient
  return yield* sql<{ readonly id: number }>`
    SELECT id
    FROM audit_log
    ORDER BY id
  `.stream.pipe(
    Stream.runFold(0, (count) => count + 1)
  )
})
```

Avoid returning an unconsumed stream from a request handler unless the HTTP
response is also streaming and has clear interruption behavior.

## Error Handling

Handle expected SQL failures with stream combinators or around the final stream
run:

```typescript
import { Effect, Stream } from "effect"
import { SqlClient, SqlError } from "@effect/sql"

const safeCount = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient

  return yield* sql<{ readonly id: number }>`
    SELECT id
    FROM users
  `.stream.pipe(
    Stream.runFold(0, (count) => count + 1),
    Effect.catchTags({
      SqlError: (error: SqlError.SqlError) =>
        Effect.logError(`sql-stream-failed=${error.message}`).pipe(
          Effect.as(0)
        )
    })
  )
})
```

Prefer logging with structured context outside hot row loops. Per-row logging
can dominate the cost of a streaming query.

## Stream Checklist

- Use `.stream` for large or incremental reads.
- Keep statement placeholders and fragments the same as normal queries.
- Consume the stream in a clear scope.
- Use `Stream.grouped` or batching operators for downstream sinks.
- Keep write transactions short when streaming reads are active.
- Avoid collecting the stream unless the result set is known to be small.
- Handle SQL failures at the stream boundary.
- Benchmark downstream row processing before changing driver settings.
- Prefer typed row aliases so stream stages see stable field names.
- Include `ORDER BY` when deterministic streaming order matters.

## Cross-references

See also: [02-sql-client.md](02-sql-client.md), [03-tagged-templates.md](03-tagged-templates.md), [04-transactions.md](04-transactions.md), [12-driver-other.md](12-driver-other.md).
