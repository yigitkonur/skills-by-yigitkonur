# SQL Client
Use `SqlClient.SqlClient` as the service tag for parameterized statements, transactions, streams, and dialect-aware fragments.

## The Tag

`SqlClient.SqlClient` is the shared service consumed by SQL-aware application
code. It is a `Context.Tag`, and the service value is a function that can be
called as a tagged template.

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

type UserRow = {
  readonly id: number
  readonly email: string
}

const findUserRows = (limit: number) =>
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient

    return yield* sql<UserRow>`
      SELECT id, email
      FROM users
      ORDER BY id
      LIMIT ${limit}
    `
  })
```

The success type is the array of rows returned by the statement. The error type
is `SqlError.SqlError`, and the requirement is `SqlClient.SqlClient` until a
driver layer is provided.

## Driver Layer

Each driver has its own layer constructor. For PostgreSQL, use
`PgClient.layer({ url })`:

```typescript
import { Effect, Redacted } from "effect"
import { PgClient } from "@effect/sql-pg"

const PgLive = PgClient.layer({
  url: Redacted.make("postgres://app:secret@localhost:5432/app")
})

const runnable = findUserRows(20).pipe(
  Effect.provide(PgLive)
)
```

The layer provides both `PgClient.PgClient` and `SqlClient.SqlClient`. Keep the
shared tag in repositories unless a driver-specific method is required.

## Configuration Layers

Use `layerConfig` when connection settings are read from `Config` values. This
keeps secrets in Effect's configuration system instead of constructing them in
module scope.

```typescript
import { Config } from "effect"
import { PgClient } from "@effect/sql-pg"

const PgLive = PgClient.layerConfig({
  url: Config.redacted("DATABASE_URL"),
  maxConnections: Config.integer("DATABASE_POOL_SIZE")
})
```

For drivers with separate fields, the same pattern applies:

```typescript
import { Config } from "effect"
import { MysqlClient } from "@effect/sql-mysql2"

const MysqlLive = MysqlClient.layerConfig({
  host: Config.string("DATABASE_HOST"),
  port: Config.integer("DATABASE_PORT"),
  database: Config.string("DATABASE_NAME"),
  username: Config.string("DATABASE_USER"),
  password: Config.redacted("DATABASE_PASSWORD")
})
```

## Statement Capabilities

A statement is more than an array-returning query:

| Capability | Use |
|---|---|
| `yield* sql\`...\`` | Execute and return transformed rows |
| `.withoutTransform` | Execute without row-name transforms |
| `.raw` | Return raw driver result |
| `.values` | Return rows as arrays of values |
| `.unprepared` | Execute without statement preparation |
| `.stream` | Stream rows through `Stream` |
| `.compile()` | Inspect generated SQL and parameters |

Use `.compile()` for tests, diagnostics, and explaining generated fragments. Do
not build application control flow around compiled SQL strings.

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

const inspectStatement = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient
  const statement = sql`SELECT id FROM users WHERE email = ${"a@example.com"}`
  const [text, params] = statement.compile()

  yield* Effect.logInfo(`sql=${text}`)
  yield* Effect.logInfo(`params=${params.length}`)
})
```

## Row Transforms

Drivers support optional name transforms:

- `transformQueryNames` changes names used when compiling identifiers.
- `transformResultNames` changes row field names returned to application code.
- PostgreSQL also supports `transformJson` for JSON value conversion.

Use transforms when the database naming convention differs from TypeScript
names. Keep the transform in the driver layer so repository code sees the
application naming style consistently.

```typescript
import { Redacted } from "effect"
import { PgClient } from "@effect/sql-pg"

const snakeToCamel = (name: string) =>
  name.replace(/_([a-z])/g, (_, char: string) => char.toUpperCase())

const PgLive = PgClient.layer({
  url: Redacted.make("postgres://app:secret@localhost:5432/app"),
  transformResultNames: snakeToCamel
})
```

## Reserved Connections

`sql.reserve` acquires a connection in a scope. Most code should use normal
statements and `sql.withTransaction`; reserve a connection only when a driver
workflow requires a stable connection outside a transaction.

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

const useReservedConnection = Effect.scoped(
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient
    const connection = yield* sql.reserve

    return yield* connection.execute(
      "SELECT id FROM users WHERE active = ?",
      [true],
      undefined
    )
  })
)
```

Prefer tagged statements over manual connection execution because the statement
constructor handles dialect compilation, fragments, tracing, and row transforms.

## Driver-Specific Clients

Driver tags expose extra operations:

```typescript
import { Effect } from "effect"
import { PgClient } from "@effect/sql-pg"

const notifyUsersChanged = Effect.gen(function* () {
  const pg = yield* PgClient.PgClient
  yield* pg.notify("users_changed", "refresh")
})
```

Keep these calls in infrastructure modules. If domain services start requiring
`PgClient.PgClient`, the service becomes harder to test against another SQL
backend.

## Client Design Rules

- Acquire `SqlClient.SqlClient` inside `Effect.gen` where the query runs.
- Provide exactly one concrete driver layer to an application runtime.
- Use `layerConfig` for deployments and `layer` for tests or explicit values.
- Keep connection URLs and passwords redacted.
- Prefer statement templates over `reserve` and raw connection methods.
- Use `.stream` for large reads.
- Use `sql.withTransaction` for write invariants.
- Keep driver-specific tags behind narrow infrastructure functions.
- Test fragments with `.compile()` when helper behavior is non-obvious.
- Document row transforms in the module that builds the driver layer.

## Cross-references

See also: [01-overview.md](01-overview.md), [03-tagged-templates.md](03-tagged-templates.md), [04-transactions.md](04-transactions.md), [09-driver-postgres.md](09-driver-postgres.md).
