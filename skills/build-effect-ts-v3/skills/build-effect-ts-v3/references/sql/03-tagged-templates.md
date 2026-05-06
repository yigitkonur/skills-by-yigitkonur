# Tagged Templates
Write SQL with the client tagged template so values are parameterized and fragments stay explicit.

## Value Placeholders

The SQL client is a tagged template. Interpolated values are converted into
statement parameters by the driver compiler:

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

type UserRow = {
  readonly id: number
  readonly email: string
}

const findByEmail = (email: string) =>
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient

    return yield* sql<UserRow>`
      SELECT id, email
      FROM users
      WHERE email = ${email}
    `
  })
```

If `email` contains quote characters, comments, or SQL syntax, it is still a
parameter value. It is not spliced into the SQL text.

## Injection Boundary

This is the safe pattern:

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

const searchUsers = (email: string) =>
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient
    return yield* sql`
      SELECT id, email
      FROM users
      WHERE email = ${email}
    `
  })
```

This protects the query because the compiled statement keeps SQL text and
parameters separate. Do not construct SQL by concatenating user input into the
template string before calling the client.

## IN Clauses

Use `sql.in(ids)` inside a template when the right-hand side of `IN` is a list.
This is the mission-critical form:

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

type UserRow = {
  readonly id: number
  readonly name: string
}

const findUsersByIds = (ids: ReadonlyArray<number>) =>
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient

    return yield* sql<UserRow>`
      SELECT id, name
      FROM users
      WHERE id IN ${sql.in(ids)}
    `
  })
```

`sql.in(ids)` expands to a dialect-correct placeholder list. The individual
values remain parameters.

The alternate column form creates the whole predicate:

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

const deleteUsersByIds = (ids: ReadonlyArray<number>) =>
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient
    return yield* sql`
      DELETE FROM users
      WHERE ${sql.in("id", ids)}
    `
  })
```

Use the first form when the SQL around the predicate is clearer. Use the column
form when composing predicate fragments.

## Identifiers

Call `sql(name)` for identifiers such as table and column names. It is not a
value placeholder; it escapes or quotes an identifier according to the dialect.

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

const countRows = (tableName: string) =>
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient
    const rows = yield* sql<{ readonly count: number }>`
      SELECT count(*) AS count
      FROM ${sql(tableName)}
    `
    return rows[0]?.count ?? 0
  })
```

Only pass trusted table or column names. Identifier escaping prevents syntax
breakage, but it does not decide whether a caller is authorized to choose a
table.

## Literal Fragments

Use `sql.literal(text)` only for SQL controlled by the application. It is a
fragment, not a parameter.

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

const orderByCreatedAt = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient
  return yield* sql`
    SELECT id, created_at
    FROM users
    ORDER BY ${sql.literal("created_at DESC")}
  `
})
```

If a value comes from a user, put it in `${value}`. If it is an identifier,
validate it against an allow-list before using `sql(name)`. If it is raw SQL,
do not accept it from outside the codebase.

## Inserts

`sql.insert` converts a record or array of records into an insert fragment:

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

const insertUsers = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient

  return yield* sql`
    INSERT INTO users ${sql.insert([
      { email: "ada@example.com", active: true },
      { email: "grace@example.com", active: true }
    ])}
  `
})
```

The keys become columns and the values become parameters. Use a stable object
shape so the generated column list is predictable.

## Updates

`sql.update(row, omit)` creates a single-row update assignment fragment:

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

const updateUserEmail = (id: number, email: string) =>
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient

    return yield* sql`
      UPDATE users
      SET ${sql.update({ id, email }, ["id"])}
      WHERE id = ${id}
    `
  })
```

Pass columns such as primary keys in the omit list when they identify the row
but should not be assigned.

## Boolean Fragments

`sql.and` and `sql.or` combine optional predicates. Empty lists compile to a
safe fallback, so callers do not have to special-case the first clause.

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

const listUsers = (activeOnly: boolean, domain: string) =>
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient
    const filters = [
      activeOnly ? sql`active = ${true}` : "1=1",
      domain.length > 0 ? sql`email LIKE ${`%@${domain}`}` : "1=1"
    ]

    return yield* sql`
      SELECT id, email
      FROM users
      WHERE ${sql.and(filters)}
    `
  })
```

Prefer explicit default predicates over dropping authorization or tenancy
filters accidentally.

## Parameterization Checklist

- Interpolate values with `${value}`.
- Interpolate lists with `sql.in(values)`.
- Interpolate identifiers with `sql(name)` only after trust checks.
- Use `sql.literal` only for code-owned SQL.
- Prefer helper fragments over manual placeholder text.
- Compile statements in tests when helper output matters.
- Never hide user input inside raw SQL text.
- Keep dynamic table names out of public request shapes.
- Keep insert and update records stable in key order and shape.
- Use schema validation before building queries from external input.

## Cross-references

See also: [02-sql-client.md](02-sql-client.md), [06-sql-resolver.md](06-sql-resolver.md), [07-sql-schema.md](07-sql-schema.md), [12-driver-other.md](12-driver-other.md).
