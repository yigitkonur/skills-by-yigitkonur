# SQL Overview
Use `@effect/sql` as the typed database boundary for Effect programs.

## Package Shape

`@effect/sql` is the shared layer for SQL work. It defines the client tag,
statement model, schema helpers, request resolvers, stream bridge, errors, and
migration machinery. Driver packages provide concrete clients for a database
engine and install both their driver-specific tag and the shared
`SqlClient.SqlClient` tag.

| Package area | Primary modules |
|---|---|
| Client | `SqlClient`, `SqlConnection`, `SqlError`, `Statement` |
| Validation | `SqlSchema`, `Model` |
| Batching | `SqlResolver` |
| Streaming | `SqlStream`, `Statement.stream` |
| Migrations | `Migrator`, driver migrators |
| Drivers | `@effect/sql-pg`, `@effect/sql-mysql2`, SQLite and other drivers |
| Adapters | `@effect/sql-drizzle`, `@effect/sql-kysely` |

## Mental Model

The client value is a tagged template function:

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

const listActiveUsers = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient
  return yield* sql<{ readonly id: number; readonly name: string }>`
    SELECT id, name
    FROM users
    WHERE active = ${true}
    ORDER BY name
  `
})
```

The template placeholders become statement parameters. Helper calls like
`sql("users")`, `sql.in(ids)`, `sql.insert(row)`, and `sql.update(row)` become
SQL fragments rather than plain values.

## Runtime Boundary

Application code depends on `SqlClient.SqlClient`. The concrete driver is
selected at the edge:

```typescript
import { Effect, Redacted } from "effect"
import { SqlClient } from "@effect/sql"
import { PgClient } from "@effect/sql-pg"

const PgLive = PgClient.layer({
  url: Redacted.make("postgres://app:secret@localhost:5432/app")
})

const program = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient
  const rows = yield* sql<{ readonly id: number }>`SELECT id FROM users`
  yield* Effect.logInfo(`rows=${rows.length}`)
})

const runnable = Effect.provide(program, PgLive)
```

Use `PgClient.PgClient` only when you need PostgreSQL-specific operations such
as `listen`, `notify`, or `json`. Most repositories should expose only the
shared client to data-access services.

## Public Surface

`SqlClient.SqlClient` extends the statement constructor. The same `sql` value
does four jobs:

- Template tag for parameterized statements.
- Identifier helper for table and column names.
- Fragment helper for `IN`, `AND`, `OR`, CSV, insert, and update.
- Transaction runner via `sql.withTransaction(effect)`.

Statements are effects. A statement can be yielded directly, streamed through
`.stream`, evaluated as raw driver output through `.raw`, compiled for
inspection with `.compile()`, or executed without row transforms using
`.withoutTransform`.

## Driver Family

Each driver package owns its own layer constructor:

| Database | Package | Layer shape |
|---|---|---|
| PostgreSQL | `@effect/sql-pg` | `PgClient.layer({ url })` |
| MySQL | `@effect/sql-mysql2` | `MysqlClient.layer({ url })` |
| SQLite node | `@effect/sql-sqlite-node` | `SqliteClient.layer({ filename })` |
| SQLite bun | `@effect/sql-sqlite-bun` | `SqliteClient.layer({ filename })` |
| SQLite wasm | `@effect/sql-sqlite-wasm` | `SqliteClient.layer(config)` |
| SQLite durable object | `@effect/sql-sqlite-do` | `SqliteClient.layer(config)` |
| Microsoft SQL Server | `@effect/sql-mssql` | `MssqlClient.layer(config)` |
| ClickHouse | `@effect/sql-clickhouse` | `ClickhouseClient.layer(config)` |
| libSQL | `@effect/sql-libsql` | `LibsqlClient.layer(config)` |
| Cloudflare D1 | `@effect/sql-d1` | `D1Client.layer(config)` |

The layer always provides the shared `SqlClient.SqlClient` service plus the
driver-specific client tag. That makes most code portable while still allowing
driver escape hatches near the edge.

## When To Use What

Use tagged statements for simple repositories and hand-authored SQL. Use
`SqlSchema` when request or row validation matters at the database boundary.
Use `SqlResolver` when many small reads should collapse into batched queries.
Use statement streams when result sets are too large to materialize. Use
migrator layers at startup so schema changes happen before application services
run.

Prefer one thin repository layer per aggregate. Keep raw SQL close to the
domain that owns it, and inject `SqlClient.SqlClient` rather than passing
driver pools around.

## Source Anchors

- `packages/sql/src/SqlClient.ts` defines the shared tag, transaction method,
  reactive query helpers, and construction options.
- `packages/sql/src/Statement.ts` defines the template constructor, statement
  effect shape, fragment helpers, and dialect compiler.
- `packages/sql/src/SqlSchema.ts` validates request and row shapes.
- `packages/sql/src/SqlResolver.ts` builds request resolvers over batched SQL.
- Driver packages expose `layer`, `layerConfig`, and `make` for their concrete
  clients.

## Operational Checklist

- Depend on `SqlClient.SqlClient` in service code.
- Build one concrete driver layer at the program edge.
- Use placeholders for values; use `sql(name)` only for trusted identifiers.
- Validate external inputs before they reach SQL helpers.
- Use `SqlSchema` for untrusted row shapes or boundary decoding.
- Use `SqlResolver.findById` for N user-by-id reads.
- Wrap migrations in driver migrator layers with an explicit `loader`.
- Keep transaction scope as small as the business invariant allows.
- Stream large result sets instead of collecting every row.
- Reserve driver-specific clients for features the shared client does not have.

## Cross-references

See also: [02-sql-client.md](02-sql-client.md), [03-tagged-templates.md](03-tagged-templates.md), [06-sql-resolver.md](06-sql-resolver.md), [08-sql-migrations.md](08-sql-migrations.md).
