# SQL Schema
Use `SqlSchema` when SQL request inputs or result rows must be validated with Effect Schema.

## What It Provides

`SqlSchema` is a small set of helpers around request encoding, SQL execution,
and result decoding:

| Helper | Result shape |
|---|---|
| `SqlSchema.findAll` | `ReadonlyArray<A>` |
| `SqlSchema.findOne` | `Option.Option<A>` |
| `SqlSchema.single` | One `A` or no-such-element failure |
| `SqlSchema.void` | `void` after request encoding |

Use these helpers when a repository should verify both query inputs and row
outputs at the Effect boundary.

## Find All

`findAll` accepts a request schema, a result schema, and an execute callback.
The returned function accepts the decoded request input.

```typescript
import { Effect, Schema } from "effect"
import { SqlClient, SqlSchema } from "@effect/sql"

const UserSearch = Schema.Struct({
  active: Schema.Boolean,
  limit: Schema.Number.pipe(Schema.int(), Schema.between(1, 100))
})

const UserRow = Schema.Struct({
  id: Schema.Number,
  email: Schema.String
})

const makeFindUsers = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient

  return SqlSchema.findAll({
    Request: UserSearch,
    Result: UserRow,
    execute: (request) =>
      sql`
        SELECT id, email
        FROM users
        WHERE active = ${request.active}
        ORDER BY id
        LIMIT ${request.limit}
      `
  })
})

const program = Effect.gen(function* () {
  const findUsers = yield* makeFindUsers
  return yield* findUsers({ active: true, limit: 25 })
})
```

The request is encoded before execution. The raw rows are decoded as an array of
`UserRow`.

## Find One

`findOne` returns `Option.Option<A>`, which is the right shape when missing data
is expected:

```typescript
import { Effect, Option, Schema } from "effect"
import { SqlClient, SqlSchema } from "@effect/sql"

const UserById = Schema.Struct({
  id: Schema.Number.pipe(Schema.int(), Schema.positive())
})

const findOneUser = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient

  const findUser = SqlSchema.findOne({
    Request: UserById,
    Result: UserRow,
    execute: (request) =>
      sql`
        SELECT id, email
        FROM users
        WHERE id = ${request.id}
      `
  })

  const maybeUser = yield* findUser({ id: 1 })

  return Option.match(maybeUser, {
    onNone: () => "missing",
    onSome: (user) => user.email
  })
})
```

Do not force missing rows into exceptions if the domain can handle absence.

## Single

Use `single` when the query must return at least one row:

```typescript
import { Effect, Schema } from "effect"
import { SqlClient, SqlSchema } from "@effect/sql"

const tenantSettings = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient

  const getSettings = SqlSchema.single({
    Request: Schema.Struct({ tenantId: Schema.String }),
    Result: Schema.Struct({
      tenantId: Schema.String,
      billingPlan: Schema.String
    }),
    execute: (request) =>
      sql`
        SELECT tenant_id AS "tenantId", billing_plan AS "billingPlan"
        FROM tenant_settings
        WHERE tenant_id = ${request.tenantId}
      `
  })

  return yield* getSettings({ tenantId: "acme" })
})
```

`single` fails if no row exists. Use it for required configuration rows,
metadata rows, or repository operations where absence is a bug in the caller's
state.

## Void

`void` validates the request and discards the SQL result:

```typescript
import { Effect, Schema } from "effect"
import { SqlClient, SqlSchema } from "@effect/sql"

const ArchiveUser = Schema.Struct({
  id: Schema.Number.pipe(Schema.int(), Schema.positive()),
  reason: Schema.String
})

const archiveUser = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient

  const archive = SqlSchema.void({
    Request: ArchiveUser,
    execute: (request) =>
      sql`
        UPDATE users
        SET archived = ${true}, archive_reason = ${request.reason}
        WHERE id = ${request.id}
      `
  })

  yield* archive({ id: 1, reason: "requested" })
})
```

For write operations, still include row-count checks where the business rule
requires exactly one affected row. `SqlSchema.void` validates inputs but does
not infer write cardinality.

## Row Name Strategy

Result schemas decode object keys. Align row keys with schemas in one of three
ways:

| Strategy | Use when |
|---|---|
| SQL aliases | One query needs a different field name |
| `transformResultNames` | Whole driver should convert names |
| Schema transform | Encoded database shape differs from domain shape |

Keep the chosen strategy consistent. Mixed ad hoc aliases and global transforms
make row decoding hard to reason about.

## Boundary Failures

`SqlSchema` can fail with SQL errors or schema parse errors. Preserve both in
the error channel and recover at the service boundary:

```typescript
import { Effect } from "effect"

const handled = program.pipe(
  Effect.catchAll((error) =>
    Effect.logError(`query-boundary-failed=${String(error)}`).pipe(
      Effect.zipRight(Effect.fail(error))
    )
  )
)
```

Avoid broad recovery inside a repository unless it can return a meaningful
domain error.

## Design Guidance

- Use `SqlSchema` at boundaries with untrusted input or externally shaped rows.
- Keep request schemas small.
- Keep result schemas named and reusable.
- Prefer `findOne` over `single` when absence is part of the domain.
- Use `single` when missing rows indicate broken state.
- Use `void` for validated commands, not for cardinality enforcement.
- Align row aliases and result transforms deliberately.
- Test schema failures with at least one malformed row fixture.
- Keep database-only fields out of domain schemas unless callers need them.
- Use `SqlResolver` when the same schema-backed query should batch requests.

## Cross-references

See also: [03-tagged-templates.md](03-tagged-templates.md), [06-sql-resolver.md](06-sql-resolver.md), [08-sql-migrations.md](08-sql-migrations.md), [13-orm-adapters.md](13-orm-adapters.md).
