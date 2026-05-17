# PostgreSQL Driver
Use `@effect/sql-pg` for PostgreSQL clients, migrations, JSON helpers, and listen-notify.

## Client Layer

The PostgreSQL package exports `PgClient` and `PgMigrator`:

```typescript
import { Effect, Redacted } from "effect"
import { SqlClient } from "@effect/sql"
import { PgClient } from "@effect/sql-pg"

const PgLive = PgClient.layer({
  url: Redacted.make("postgres://app:secret@localhost:5432/app")
})

const listUsers = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient
  return yield* sql<{ readonly id: number; readonly email: string }>`
    SELECT id, email
    FROM users
  `
}).pipe(
  Effect.provide(PgLive)
)
```

`PgClient.layer({ url })` provides both `PgClient.PgClient` and
`SqlClient.SqlClient`.

## Configuration

`PgClientConfig` supports URL-based and field-based configuration:

| Field group | Examples |
|---|---|
| Location | `url`, `host`, `port`, `path`, `database` |
| Auth | `username`, `password` |
| Pooling | `maxConnections`, `minConnections`, `idleTimeout`, `connectionTTL` |
| Connection | `ssl`, `connectTimeout`, `stream` |
| Observability | `applicationName`, `spanAttributes` |
| Transforms | `transformResultNames`, `transformQueryNames`, `transformJson` |
| Types | `types` |

Use `Config.redacted` for URLs and passwords in deployable applications:

```typescript
import { Config } from "effect"
import { PgClient } from "@effect/sql-pg"

const PgLive = PgClient.layerConfig({
  url: Config.redacted("DATABASE_URL"),
  maxConnections: Config.integer("DATABASE_MAX_CONNECTIONS"),
  applicationName: Config.succeed("users-service")
})
```

## JSON Helper

`PgClient.PgClient` extends the shared client with `json`:

```typescript
import { Effect } from "effect"
import { PgClient } from "@effect/sql-pg"

const insertJsonPayload = (payload: unknown) =>
  Effect.gen(function* () {
    const pg = yield* PgClient.PgClient

    yield* pg`
      INSERT INTO events ${pg.insert({
        payload: pg.json(payload)
      })}
    `
  })
```

Use this when the value must be encoded as PostgreSQL JSON. For plain values,
normal placeholders are enough.

## Listen And Notify

The driver exposes PostgreSQL notifications:

```typescript
import { Effect, Stream } from "effect"
import { PgClient } from "@effect/sql-pg"

const publishUsersChanged = Effect.gen(function* () {
  const pg = yield* PgClient.PgClient
  yield* pg.notify("users_changed", "refresh")
})

const observeUsersChanged = Effect.gen(function* () {
  const pg = yield* PgClient.PgClient

  return yield* pg.listen("users_changed").pipe(
    Stream.take(1),
    Stream.runForEach((payload) =>
      Effect.logInfo(`users-changed=${payload}`)
    )
  )
})
```

Keep listen-notify code in infrastructure services. Repository methods should
not require a PostgreSQL-specific client just to query tables.

## Pool Integration

The package also exposes `fromPool` and `layerFromPool` for applications that
already own a `pg` pool. Prefer `PgClient.layer` unless integration with an
existing pool is required.

## Migrations

Use `PgMigrator.layer({ loader })` with a `PgClient` layer:

```typescript
import { Effect, Layer, Redacted } from "effect"
import { SqlClient } from "@effect/sql"
import { PgClient, PgMigrator } from "@effect/sql-pg"

const createUsers = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient
  yield* sql`
    CREATE TABLE users (
      id serial PRIMARY KEY,
      email text NOT NULL
    )
  `
})

const PgLive = PgClient.layer({
  url: Redacted.make("postgres://app:secret@localhost:5432/app")
})

const PgMigrations = PgMigrator.layer({
  loader: PgMigrator.fromRecord({
    "0001_create_users": createUsers
  })
})

const PgMigrated = PgMigrations.pipe(
  Layer.provide(PgLive)
)
```

PostgreSQL migrator support includes schema dumping when platform command and
filesystem services are available.

## Dialect Notes

PostgreSQL compiler placeholders use `$1`, `$2`, and so on. Identifier escaping
uses PostgreSQL rules. The driver supports custom type configuration through
the `types` option.

## Usage Rules

- Use `PgClient.layer({ url })` or `PgClient.layerConfig`.
- Keep URL and password values redacted.
- Consume `SqlClient.SqlClient` in portable repository code.
- Consume `PgClient.PgClient` only for PostgreSQL-specific operations.
- Use `pg.json` for JSON parameters that should be PostgreSQL JSON.
- Use `listen` and `notify` in infrastructure modules.
- Use `PgMigrator.layer({ loader })` at startup.
- Keep PostgreSQL DDL in PostgreSQL migration files.
- Configure row-name transforms in one place.
- Test SQL fragments that rely on PostgreSQL-specific syntax.

## Cross-references

See also: [02-sql-client.md](02-sql-client.md), [03-tagged-templates.md](03-tagged-templates.md), [08-sql-migrations.md](08-sql-migrations.md), [12-driver-other.md](12-driver-other.md).
