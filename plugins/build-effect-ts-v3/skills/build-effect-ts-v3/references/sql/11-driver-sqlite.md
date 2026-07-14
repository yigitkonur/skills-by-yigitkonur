# SQLite Drivers
Use the SQLite driver package that matches the runtime: node, bun, wasm, durable object, or React Native.

## Driver Packages

Effect v3 has several SQLite packages:

| Runtime | Package |
|---|---|
| Node.js | `@effect/sql-sqlite-node` |
| Bun | `@effect/sql-sqlite-bun` |
| WebAssembly | `@effect/sql-sqlite-wasm` |
| Cloudflare Durable Object | `@effect/sql-sqlite-do` |
| React Native | `@effect/sql-sqlite-react-native` |

Each package exports a `SqliteClient` module. The node and bun packages also
export `SqliteMigrator` with filesystem-backed loader helpers.

## Node SQLite

Use `SqliteClient.layer({ filename })` from `@effect/sql-sqlite-node`:

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"
import { SqliteClient } from "@effect/sql-sqlite-node"

const SqliteLive = SqliteClient.layer({
  filename: "var/app.sqlite"
})

const listUsers = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient
  return yield* sql<{ readonly id: number; readonly email: string }>`
    SELECT id, email
    FROM users
  `
}).pipe(
  Effect.provide(SqliteLive)
)
```

The node client also exposes SQLite-specific operations such as export, backup,
and extension loading through `SqliteClient.SqliteClient`.

## Bun SQLite

Bun uses the same module names from a different package:

```typescript
import { SqliteClient } from "@effect/sql-sqlite-bun"

const BunSqliteLive = SqliteClient.layer({
  filename: "var/app.sqlite"
})
```

Do not mix the node client and bun client in the same runtime layer. Pick the
package that matches the runtime process.

## WASM SQLite

The wasm package supports file-backed and memory-backed construction:

```typescript
import { Effect } from "effect"
import { SqliteClient } from "@effect/sql-sqlite-wasm"

const WasmSqliteLive = SqliteClient.layer({
  worker: Effect.acquireRelease(
    Effect.sync(() => new Worker("/sqlite-worker.js")),
    (worker) => Effect.sync(() => worker.terminate())
  )
})

const WasmMemoryLive = SqliteClient.layerMemory({})
```

Use wasm SQLite when the application runs in browser-like or worker-like
contexts that cannot use native node bindings.

## Durable Object SQLite

Cloudflare Durable Object SQLite uses the durable object's storage handle:

```typescript
import { SqliteClient } from "@effect/sql-sqlite-do"

declare const db: SqlStorage

const DurableObjectSqliteLive = SqliteClient.layer({
  db
})
```

Keep this layer at the Cloudflare adapter boundary. Domain repositories should
still depend on `SqlClient.SqlClient`.

## Migrations

SQLite migrators use the `loader` option:

```typescript
import { Effect, Layer } from "effect"
import { SqlClient } from "@effect/sql"
import {
  SqliteClient,
  SqliteMigrator
} from "@effect/sql-sqlite-node"

const createUsers = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient
  yield* sql`
    CREATE TABLE users (
      id integer PRIMARY KEY,
      email text NOT NULL
    )
  `
})

const SqliteLive = SqliteClient.layer({
  filename: "var/app.sqlite"
})

const SqliteMigrations = SqliteMigrator.layer({
  loader: SqliteMigrator.fromRecord({
    "0001_create_users": createUsers
  })
})

const SqliteMigrated = SqliteMigrations.pipe(
  Layer.provide(SqliteLive)
)
```

Use the migrator exported by the same package as the client.

## SQLite SQL Differences

SQLite differs from server databases in ways that affect examples:

- `sql.updateValues` is not supported.
- Column types are affinity-based.
- Some `ALTER TABLE` forms are limited.
- Write concurrency depends on runtime and journaling mode.
- `RETURNING` support depends on SQLite version.

When portability matters, test every migration against the exact runtime driver.

## Configuration

Common node and bun options include:

| Option | Use |
|---|---|
| `filename` | Database path |
| `readonly` | Open without writes |
| `prepareCacheSize` | Prepared statement cache capacity |
| `prepareCacheTTL` | Prepared statement cache lifetime |
| `disableWAL` | Disable write-ahead logging |
| `transformResultNames` | Convert returned row names |
| `transformQueryNames` | Convert compiled identifier names |

Use memory databases in tests when persistence is not part of the behavior.

## SQLite Checklist

- Import `SqliteClient` from the runtime-specific package.
- Use `SqliteClient.layer({ filename })` for node and bun.
- Use wasm or durable-object packages only in matching runtimes.
- Keep repositories on the shared SQL client.
- Use runtime-specific migration DDL when SQLite limitations matter.
- Use the matching `SqliteMigrator`.
- Avoid `sql.updateValues` in SQLite code.
- Test migrations on the exact SQLite driver.
- Configure prepared-statement cache only after measurement.
- Keep database file paths in config for deployed services.

## Cross-references

See also: [02-sql-client.md](02-sql-client.md), [05-sql-streams.md](05-sql-streams.md), [08-sql-migrations.md](08-sql-migrations.md), [12-driver-other.md](12-driver-other.md).
