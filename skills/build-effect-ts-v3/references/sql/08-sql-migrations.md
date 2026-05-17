# SQL Migrations
Run database migrations with driver migrator layers and an explicit `loader` option.

## Migrator Model

`@effect/sql` defines the shared migration engine. Driver packages export
database-specific migrators:

| Driver | Migrator |
|---|---|
| PostgreSQL | `PgMigrator` from `@effect/sql-pg` |
| MySQL | `MysqlMigrator` from `@effect/sql-mysql2` |
| SQLite node | `SqliteMigrator` from `@effect/sql-sqlite-node` |
| SQLite bun | `SqliteMigrator` from `@effect/sql-sqlite-bun` |
| Other drivers | Their package-specific migrator where available |

The migrator reads migration definitions from `loader`, records applied ids in
a migrations table, and runs pending effects inside `sql.withTransaction`.

## Migration Effects

A migration is an Effect that requires `SqlClient.SqlClient`:

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

const createUsers = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient

  yield* sql`
    CREATE TABLE users (
      id integer PRIMARY KEY,
      email text NOT NULL,
      active boolean NOT NULL
    )
  `
})

const addUserName = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient

  yield* sql`
    ALTER TABLE users
    ADD COLUMN name text NOT NULL DEFAULT ''
  `
})
```

Keep migration code direct. It is infrastructure code, not a domain service.

## Loader Option

The migrator requires `loader`. `fromRecord` is useful in examples, tests, and
small applications:

```typescript
import { PgMigrator } from "@effect/sql-pg"

const loader = PgMigrator.fromRecord({
  "0001_create_users": createUsers,
  "0002_add_user_name": addUserName
})
```

Migration keys must start with a numeric id followed by an underscore and a
name. The loader sorts migrations by id.

## PostgreSQL Migrator

Use `PgMigrator.layer({ loader })` with the PostgreSQL client layer:

```typescript
import { Layer, Redacted } from "effect"
import { PgClient, PgMigrator } from "@effect/sql-pg"

const PgLive = PgClient.layer({
  url: Redacted.make("postgres://app:secret@localhost:5432/app")
})

const PgMigrations = PgMigrator.layer({
  loader: PgMigrator.fromRecord({
    "0001_create_users": createUsers,
    "0002_add_user_name": addUserName
  })
})

const PgMigrated = PgMigrations.pipe(
  Layer.provide(PgLive)
)
```

The PostgreSQL migrator can also dump schema when `schemaDirectory` is set and
the required platform services are provided.

## SQLite Migrator

SQLite driver packages export their own `SqliteMigrator`. For node:

```typescript
import { Layer } from "effect"
import {
  SqliteClient,
  SqliteMigrator
} from "@effect/sql-sqlite-node"

const SqliteLive = SqliteClient.layer({
  filename: "var/app.sqlite"
})

const SqliteMigrations = SqliteMigrator.layer({
  loader: SqliteMigrator.fromRecord({
    "0001_create_users": createUsers,
    "0002_add_user_name": addUserName
  })
})

const SqliteMigrated = SqliteMigrations.pipe(
  Layer.provide(SqliteLive)
)
```

Bun SQLite has the same migrator name from `@effect/sql-sqlite-bun`. Import it
from the selected driver package, not from a shared SQLite namespace.

## MySQL Migrator

MySQL uses `MysqlMigrator` from `@effect/sql-mysql2`:

```typescript
import { Layer, Redacted } from "effect"
import { MysqlClient, MysqlMigrator } from "@effect/sql-mysql2"

const MysqlLive = MysqlClient.layer({
  url: Redacted.make("mysql://app:secret@localhost:3306/app")
})

const MysqlMigrations = MysqlMigrator.layer({
  loader: MysqlMigrator.fromRecord({
    "0001_create_users": createUsers,
    "0002_add_user_name": addUserName
  })
})

const MysqlMigrated = MysqlMigrations.pipe(
  Layer.provide(MysqlLive)
)
```

Use MySQL-compatible DDL in the migration bodies. Do not reuse PostgreSQL DDL
blindly across engines.

## Layer Composition

Migrator layers require a SQL client. The final application layer should ensure
migrations run before services that depend on the schema.

```typescript
import { Context, Effect, Layer } from "effect"
import { SqlClient } from "@effect/sql"

class UsersRepo extends Context.Tag("app/UsersRepo")<
  UsersRepo,
  { readonly count: Effect.Effect<number> }
>() {}

const UsersRepoLive = Layer.effect(
  UsersRepo,
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient
    return {
      count: Effect.map(
        sql<{ readonly count: number }>`SELECT count(*) AS count FROM users`,
        (rows) => rows[0]?.count ?? 0
      )
    }
  })
)

const DatabaseLive = Layer.mergeAll(PgLive, PgMigrated)
const UsersAppLive = UsersRepoLive.pipe(Layer.provide(DatabaseLive))
```

If a composition becomes hard to read, name intermediate layers: client,
migrations, repositories, application.

## Migration Table

The default table is `effect_sql_migrations`. You can override it:

```typescript
import { PgMigrator } from "@effect/sql-pg"

const PgMigrations = PgMigrator.layer({
  table: "app_migrations",
  loader
})
```

Keep one migrations table per schema history. Changing the table name after
deployment makes existing migrations look unapplied.

## Error Handling

Migrators fail with `MigrationError` or `SqlError`. The shared engine detects:

- Duplicate ids in the loader.
- Import failures.
- Migration effects that fail.
- Concurrent migration lock conflicts.
- Bad migration state.

Let startup fail on migration errors unless the deployment has an explicit
manual recovery process.

## Multi-Driver Guidance

If the application supports several databases, keep migration sets separated by
dialect. Share application repository interfaces, not DDL files, unless the SQL
is genuinely portable.

```typescript
const pgLoader = PgMigrator.fromRecord({
  "0001_create_users": createUsers
})

const mysqlLoader = MysqlMigrator.fromRecord({
  "0001_create_users": createUsersMysql
})
```

Use dialect-specific migrations when column types, indexes, generated ids, or
JSON support differ.

## Migration Checklist

- Always pass `loader` to the driver migrator.
- Use the migrator from the same driver package as the client.
- Keep migration names stable once deployed.
- Keep ids unique and increasing.
- Run migrations before repository layers.
- Keep DDL dialect-specific when needed.
- Avoid domain service dependencies in migration effects.
- Let startup fail on migration errors.
- Test a fresh database from migration zero.
- Test an upgrade database with existing migration rows.
- Include rollback strategy in operations docs, not by silently editing old migrations.

## Cross-references

See also: [02-sql-client.md](02-sql-client.md), [04-transactions.md](04-transactions.md), [09-driver-postgres.md](09-driver-postgres.md), [10-driver-mysql.md](10-driver-mysql.md), [11-driver-sqlite.md](11-driver-sqlite.md).
