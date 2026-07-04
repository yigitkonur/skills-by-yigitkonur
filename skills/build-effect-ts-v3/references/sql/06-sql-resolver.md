# SQL Resolver
Use `SqlResolver` to batch request-style database reads and avoid N-plus-one query patterns.

## Why It Exists

`SqlResolver` builds an Effect `RequestResolver` around SQL. A caller executes
small request-shaped effects, and Effect batches compatible requests into a
single SQL execution.

Use it when many fibers or service calls ask for records by key:

- User by id.
- Orders by customer id.
- Permissions by role id.
- Feature flags by workspace id.
- Delete or update requests that can run as a batch.

## User By Id Batching

This example batches N user-by-id reads into one query with `IN`:

```typescript
import { Effect, Option, Schema } from "effect"
import { SqlClient, SqlResolver } from "@effect/sql"

const User = Schema.Struct({
  id: Schema.Number,
  email: Schema.String,
  name: Schema.String
})

type User = Schema.Schema.Type<typeof User>

const makeUserById = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient

  return yield* SqlResolver.findById("UserById", {
    Id: Schema.Number,
    Result: User,
    ResultId: (user) => user.id,
    execute: (ids) =>
      sql`
        SELECT id, email, name
        FROM users
        WHERE id IN ${sql.in(ids)}
      `
  })
})

const loadThreeUsers = Effect.gen(function* () {
  const userById = yield* makeUserById

  const users = yield* Effect.all([
    userById.execute(1),
    userById.execute(2),
    userById.execute(3)
  ], { concurrency: 3 })

  return users
})
```

The three `execute` calls become requests. The resolver receives the encoded id
array `[1, 2, 3]`, runs one `SELECT ... WHERE id IN (...)`, decodes returned
rows with `User`, and completes each request with `Option.some(user)` or
`Option.none()`.

## Return Shape

`findById` returns `Option.Option<A>` because a requested id may not exist:

```typescript
import { Effect, Option } from "effect"

const requireUser = (id: number) =>
  Effect.gen(function* () {
    const userById = yield* makeUserById
    const maybeUser = yield* userById.execute(id)

    return yield* Option.match(maybeUser, {
      onNone: () => Effect.fail(`missing-user:${id}`),
      onSome: Effect.succeed
    })
  })
```

Keep the optional result at the resolver boundary. Convert it into a domain
error in the repository or service that knows whether missing data is expected.

## Resolver Variants

| Constructor | Use |
|---|---|
| `SqlResolver.findById` | Many ids, at most one result per id |
| `SqlResolver.grouped` | Many requests, many results per group |
| `SqlResolver.ordered` | Result order and request order must match exactly |
| `SqlResolver.void` | Batched side effects where no value is returned |

Use `findById` for most primary-key reads. Use `grouped` for one-to-many reads
such as orders by customer id.

## Grouped Example

`grouped` maps many rows back to each request by group key:

```typescript
import { Effect, Schema } from "effect"
import { SqlClient, SqlResolver } from "@effect/sql"

const Order = Schema.Struct({
  id: Schema.Number,
  userId: Schema.Number,
  total: Schema.Number
})

const makeOrdersByUserId = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient

  return yield* SqlResolver.grouped("OrdersByUserId", {
    Request: Schema.Number,
    RequestGroupKey: (userId) => userId,
    Result: Order,
    ResultGroupKey: (order) => order.userId,
    execute: (userIds) =>
      sql`
        SELECT id, user_id AS "userId", total
        FROM orders
        WHERE user_id IN ${sql.in(userIds)}
      `
  })
})
```

Every requested user id completes with an array. Missing groups complete with an
empty array rather than failing.

## Ordered Example

Use `ordered` only when the query naturally returns one row per request in the
same order, or when the SQL explicitly preserves order.

```typescript
import { Effect, Schema } from "effect"
import { SqlClient, SqlResolver } from "@effect/sql"

const UserName = Schema.Struct({
  id: Schema.Number,
  name: Schema.String
})

const makeOrderedNames = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient

  return yield* SqlResolver.ordered("OrderedUserNames", {
    Request: Schema.Number,
    Result: UserName,
    execute: (ids) =>
      sql`
        SELECT id, name
        FROM users
        WHERE id IN ${sql.in(ids)}
        ORDER BY id
      `
  })
})
```

If the returned row count differs from the request count, `ordered` fails with
`ResultLengthMismatch`. For key-based reads, prefer `findById`.

## Request Encoding

Every resolver accepts a request schema. The schema validates and encodes the
input before it reaches SQL. Use branded schemas when ids must not be mixed.

```typescript
import { Schema } from "effect"

const UserId = Schema.Number.pipe(Schema.int(), Schema.positive())
```

The encoded value is what the `execute` callback receives. Keep request schemas
small and serializable.

## Context-Aware Resolvers

Set `withContext: true` when the `execute` callback needs services beyond
`SqlClient.SqlClient` or schema dependencies:

```typescript
import { Context, Effect, Schema } from "effect"
import { SqlClient, SqlResolver } from "@effect/sql"

class TenantContext extends Context.Tag("app/TenantContext")<
  TenantContext,
  { readonly tenantId: string }
>() {}

const makeTenantUserById = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient

  return yield* SqlResolver.findById("TenantUserById", {
    Id: Schema.Number,
    Result: User,
    ResultId: (user) => user.id,
    withContext: true,
    execute: (ids) =>
      Effect.gen(function* () {
        const tenant = yield* TenantContext
        return yield* sql`
          SELECT id, email, name
          FROM users
          WHERE tenant_id = ${tenant.tenantId}
          AND id IN ${sql.in(ids)}
        `
      })
  })
})
```

The resolver preserves transaction context, so request execution inside
`sql.withTransaction` uses the transaction connection.

## Resolver Checklist

- Use `findById` for primary-key reads.
- Use `grouped` for one-to-many reads.
- Use `ordered` only when order and cardinality are guaranteed.
- Keep request schemas precise and small.
- Use `sql.in(ids)` for batched ids.
- Add tenancy predicates inside the batched query.
- Decode rows with `Result` schemas.
- Convert `Option.none()` to domain errors near the use case.
- Set `withContext: true` only when the execute callback needs additional services.

## Cross-references

See also: [03-tagged-templates.md](03-tagged-templates.md), [07-sql-schema.md](07-sql-schema.md), [04-transactions.md](04-transactions.md), [10-driver-mysql.md](10-driver-mysql.md).
