# Other SQL Drivers
Use the non-core SQL drivers when the database runtime is MSSQL, ClickHouse, libSQL, D1, or another platform-specific backend.

## Driver Matrix

Beyond PostgreSQL, MySQL, and SQLite node or bun, Effect v3 includes these SQL
driver packages:

| Database | Package | Client |
|---|---|---|
| Microsoft SQL Server | `@effect/sql-mssql` | `MssqlClient` |
| ClickHouse | `@effect/sql-clickhouse` | `ClickhouseClient` |
| libSQL | `@effect/sql-libsql` | `LibsqlClient` |
| Cloudflare D1 | `@effect/sql-d1` | `D1Client` |
| SQLite wasm | `@effect/sql-sqlite-wasm` | `SqliteClient` |
| SQLite durable object | `@effect/sql-sqlite-do` | `SqliteClient` |

Each concrete layer provides the shared `SqlClient.SqlClient` tag.

## Microsoft SQL Server

Use `MssqlClient.layer(config)`:

```typescript
import { Effect, Redacted } from "effect"
import { SqlClient } from "@effect/sql"
import { MssqlClient } from "@effect/sql-mssql"

const MssqlLive = MssqlClient.layer({
  server: "localhost",
  port: 1433,
  database: "app",
  username: "app",
  password: Redacted.make("secret"),
  trustServer: true
})

const listUsers = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient
  return yield* sql`
    SELECT id, email
    FROM users
  `
}).pipe(
  Effect.provide(MssqlLive)
)
```

The driver also has procedure and parameter modules for SQL Server-specific
stored procedure workflows. Keep those behind infrastructure interfaces.

## ClickHouse

Use `ClickhouseClient.layer(config)` for analytical workloads:

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"
import { ClickhouseClient } from "@effect/sql-clickhouse"

const ClickhouseLive = ClickhouseClient.layer({
  url: "http://localhost:8123",
  database: "analytics"
})

const eventCounts = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient
  return yield* sql`
    SELECT event_type, count() AS count
    FROM events
    GROUP BY event_type
  `
}).pipe(
  Effect.provide(ClickhouseLive)
)
```

## libSQL

Use `LibsqlClient.layer(config)`:

```typescript
import { Effect, Redacted } from "effect"
import { SqlClient } from "@effect/sql"
import { LibsqlClient } from "@effect/sql-libsql"

const LibsqlLive = LibsqlClient.layer({
  url: "file:local.db",
  authToken: Redacted.make("token")
})

const countUsers = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient
  const rows = yield* sql<{ readonly count: number }>`
    SELECT count(*) AS count
    FROM users
  `
  return rows[0]?.count ?? 0
}).pipe(
  Effect.provide(LibsqlLive)
)
```

## Cloudflare D1

Use `D1Client.layer({ db })` at the Cloudflare boundary:

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"
import { D1Client } from "@effect/sql-d1"

declare const db: D1Database

const D1Live = D1Client.layer({ db })

const findUser = (id: number) =>
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient
    return yield* sql`
      SELECT id, email
      FROM users
      WHERE id = ${id}
    `
  }).pipe(
    Effect.provide(D1Live)
  )
```

## Migrators

Several other drivers export package-specific migrators. Use the migrator from
the same package as the client and always pass `loader`:

```typescript
import { Effect, Layer } from "effect"
import { SqlClient } from "@effect/sql"
import { LibsqlClient, LibsqlMigrator } from "@effect/sql-libsql"

const createUsers = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient
  yield* sql`
    CREATE TABLE users (
      id integer PRIMARY KEY,
      email text NOT NULL
    )
  `
})

const LibsqlLive = LibsqlClient.layer({
  url: "file:local.db"
})

const LibsqlMigrations = LibsqlMigrator.layer({
  loader: LibsqlMigrator.fromRecord({
    "0001_create_users": createUsers
  })
})

const LibsqlMigrated = LibsqlMigrations.pipe(
  Layer.provide(LibsqlLive)
)
```

## Cross-references

See also: [01-overview.md](01-overview.md), [03-tagged-templates.md](03-tagged-templates.md), [08-sql-migrations.md](08-sql-migrations.md), [11-driver-sqlite.md](11-driver-sqlite.md).
