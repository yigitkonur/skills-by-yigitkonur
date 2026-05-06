# MySQL Driver
Use `@effect/sql-mysql2` for MySQL-compatible clients and migrations.

## Client Layer

`MysqlClient.layer({ url })` constructs the MySQL client layer:

```typescript
import { Effect, Redacted } from "effect"
import { SqlClient } from "@effect/sql"
import { MysqlClient } from "@effect/sql-mysql2"

const MysqlLive = MysqlClient.layer({
  url: Redacted.make("mysql://app:secret@localhost:3306/app")
})

const findUsers = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient
  return yield* sql<{ readonly id: number; readonly email: string }>`
    SELECT id, email
    FROM users
    WHERE active = ${true}
  `
}).pipe(
  Effect.provide(MysqlLive)
)
```

The layer provides `MysqlClient.MysqlClient` and the shared
`SqlClient.SqlClient`.

## Configuration

`MysqlClientConfig` supports URL-based configuration and individual connection
fields:

| Field group | Examples |
|---|---|
| Location | `url`, `host`, `port`, `database` |
| Auth | `username`, `password` |
| Pooling | `maxConnections`, `connectionTTL`, `poolConfig` |
| Observability | `spanAttributes` |
| Transforms | `transformResultNames`, `transformQueryNames` |

Use `layerConfig` for deployed services:

```typescript
import { Config } from "effect"
import { MysqlClient } from "@effect/sql-mysql2"

const MysqlLive = MysqlClient.layerConfig({
  host: Config.string("DATABASE_HOST"),
  port: Config.integer("DATABASE_PORT"),
  database: Config.string("DATABASE_NAME"),
  username: Config.string("DATABASE_USER"),
  password: Config.redacted("DATABASE_PASSWORD"),
  maxConnections: Config.integer("DATABASE_MAX_CONNECTIONS")
})
```

Use `poolConfig` only when the mysql2 driver option is not exposed directly by
the Effect config shape.

## Placeholder And Dialect

The MySQL compiler uses MySQL placeholders and identifier quoting. Normal
tagged templates are still parameterized:

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

const findByEmails = (emails: ReadonlyArray<string>) =>
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient

    return yield* sql`
      SELECT id, email
      FROM users
      WHERE email IN ${sql.in(emails)}
    `
  })
```

Keep MySQL-specific SQL in MySQL modules when it uses engine-specific syntax.

## Streaming

The MySQL driver implements statement `.stream` with mysql2 query streams:

```typescript
import { Effect, Stream } from "effect"
import { SqlClient } from "@effect/sql"

const countActiveUsers = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient

  return yield* sql<{ readonly id: number }>`
    SELECT id
    FROM users
    WHERE active = ${true}
  `.stream.pipe(
    Stream.runFold(0, (count) => count + 1)
  )
})
```

Use streams for large reads and normal statements for small query results.

## Migrations

Use `MysqlMigrator.layer({ loader })`:

```typescript
import { Effect, Layer, Redacted } from "effect"
import { SqlClient } from "@effect/sql"
import { MysqlClient, MysqlMigrator } from "@effect/sql-mysql2"

const createUsers = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient
  yield* sql`
    CREATE TABLE users (
      id integer unsigned NOT NULL AUTO_INCREMENT,
      email varchar(255) NOT NULL,
      PRIMARY KEY (id)
    )
  `
})

const MysqlLive = MysqlClient.layer({
  url: Redacted.make("mysql://app:secret@localhost:3306/app")
})

const MysqlMigrations = MysqlMigrator.layer({
  loader: MysqlMigrator.fromRecord({
    "0001_create_users": createUsers
  })
})

const MysqlMigrated = MysqlMigrations.pipe(
  Layer.provide(MysqlLive)
)
```

The migration layer requires the MySQL client and platform services needed for
schema dumping when that option is used.

## MySQL Guidance

- Use `MysqlClient.layer({ url })` for explicit local construction.
- Use `MysqlClient.layerConfig` for environment-driven configuration.
- Keep passwords redacted.
- Keep repositories on `SqlClient.SqlClient` unless they need MySQL-only APIs.
- Use MySQL-compatible DDL in migrations.
- Do not assume PostgreSQL `RETURNING` syntax is available.
- Use `sql.insert` and `sql.update` for portable insert and update fragments.
- Use `sql.in(values)` for dynamic lists.
- Stream large reads.
- Put pool tuning behind production metrics.

## Cross-references

See also: [02-sql-client.md](02-sql-client.md), [03-tagged-templates.md](03-tagged-templates.md), [05-sql-streams.md](05-sql-streams.md), [08-sql-migrations.md](08-sql-migrations.md).
