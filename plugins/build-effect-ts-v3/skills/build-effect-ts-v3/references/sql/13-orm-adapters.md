# ORM Adapters
Use Drizzle and Kysely adapters when a codebase wants query-builder ergonomics over an Effect SQL client.

## Adapter Packages

Effect v3 ships two SQL adapter packages:

| Adapter | Package | Purpose |
|---|---|---|
| Drizzle | `@effect/sql-drizzle` | Remote Drizzle databases backed by `SqlClient.SqlClient` |
| Kysely | `@effect/sql-kysely` | Effect-aware Kysely builders and dialect adapters |

Both adapters sit on top of SQL clients. They do not replace driver layers,
migrations, or the shared SQL service.

## Drizzle Shape

Drizzle modules are dialect-specific subpaths: `Pg`, `Mysql`, and `Sqlite`.
They expose `make`, `makeWithConfig`, `layer`, `layerWithConfig`, and a service
tag.

```typescript
import { Effect, Layer } from "effect"
import { SqlClient } from "@effect/sql"
import * as SqliteDrizzle from "@effect/sql-drizzle/Sqlite"
import { SqliteClient } from "@effect/sql-sqlite-node"
import * as D from "drizzle-orm/sqlite-core"

const SqlLive = SqliteClient.layer({
  filename: "test.db"
})

const DrizzleLive = SqliteDrizzle.layer.pipe(
  Layer.provide(SqlLive)
)

const DatabaseLive = Layer.mergeAll(SqlLive, DrizzleLive)

const users = D.sqliteTable("users", {
  id: D.integer("id").primaryKey(),
  name: D.text("name")
})

const program = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient
  const db = yield* SqliteDrizzle.SqliteDrizzle

  yield* sql`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY,
      name TEXT
    )
  `
  yield* db.insert(users).values({ id: 1, name: "Ada" })
  return yield* db.select().from(users)
}).pipe(
  Effect.provide(DatabaseLive)
)
```

The Drizzle query promises are patched to be Effect values, so they can be
yielded directly.

## Drizzle Dialects

| Dialect | Import |
|---|---|
| PostgreSQL | `@effect/sql-drizzle/Pg` |
| MySQL | `@effect/sql-drizzle/Mysql` |
| SQLite | `@effect/sql-drizzle/Sqlite` |

Pick the adapter matching both the Drizzle schema module and the SQL driver.
For example, use `@effect/sql-drizzle/Pg` with `@effect/sql-pg`.

## Kysely Shape

Kysely adapters are also dialect-specific subpaths. The dialect modules create
a Kysely instance backed by `SqlClient.SqlClient`.

```typescript
import { Context, Effect, Layer } from "effect"
import * as SqliteKysely from "@effect/sql-kysely/Sqlite"
import { SqliteClient } from "@effect/sql-sqlite-node"
import type { Generated } from "kysely"

interface UserTable {
  readonly id: Generated<number>
  readonly name: string
}

interface Database {
  readonly users: UserTable
}

class DatabaseClient extends Context.Tag("app/DatabaseClient")<
  DatabaseClient,
  SqliteKysely.EffectKysely<Database>
>() {}

const SqlLive = SqliteClient.layer({
  filename: ":memory:"
})

const KyselyLive = Layer.effect(
  DatabaseClient,
  SqliteKysely.make<Database>()
).pipe(
  Layer.provide(SqlLive)
)

const createAndSelect = Effect.gen(function* () {
  const db = yield* DatabaseClient

  yield* db.schema
    .createTable("users")
    .addColumn("id", "integer", (column) => column.primaryKey().autoIncrement())
    .addColumn("name", "text", (column) => column.notNull())

  yield* db.insertInto("users").values({ name: "Ada" })

  return yield* db.selectFrom("users").selectAll()
}).pipe(
  Effect.provide(KyselyLive)
)
```

Kysely builders are patched so executable builders are Effect values. The
adapter also wires `withTransaction` to the underlying SQL client.

## Transactions

With Kysely, `db.withTransaction(effect)` delegates to the SQL client's
transaction method:

```typescript
import { Effect } from "effect"

const renameUser = (id: number, name: string) =>
  Effect.gen(function* () {
    const db = yield* DatabaseClient

    yield* db.withTransaction(
      Effect.gen(function* () {
        yield* db
          .updateTable("users")
          .set({ name })
          .where("id", "=", id)
      })
    )
  })
```

For Drizzle, use `SqlClient.SqlClient` directly for explicit transactional
boundaries when the adapter method does not model the needed transaction shape.

## When To Prefer Raw SQL

Use raw `@effect/sql` statements when:

- The query is short and clearer as SQL.
- You need exact dialect SQL.
- You are using `SqlResolver` batching.
- You are writing migrations.
- You need statement `.stream`, `.raw`, `.values`, or `.compile()`.

Use Drizzle or Kysely when the project already has table definitions, query
builder conventions, or generated types tied to those libraries.

## Adapter Checklist

- Still provide a concrete SQL driver layer.
- Match adapter dialect to driver dialect.
- Keep migrations in `@effect/sql` migrators.
- Keep request batching in `SqlResolver`.
- Use adapter service tags only where query-builder APIs add value.
- Use raw statements for SQL that is more readable as SQL.
- Avoid mixing Drizzle and Kysely in one repository module.
- Prefer the shared `SqlClient.SqlClient` for portable low-level operations.

## Cross-references

See also: [02-sql-client.md](02-sql-client.md), [04-transactions.md](04-transactions.md), [06-sql-resolver.md](06-sql-resolver.md), [08-sql-migrations.md](08-sql-migrations.md).
