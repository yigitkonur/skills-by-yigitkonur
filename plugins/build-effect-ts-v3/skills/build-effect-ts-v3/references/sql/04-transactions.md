# Transactions
Use `sql.withTransaction` to keep related SQL changes on one transactional connection.

## Basic Shape

`SqlClient.SqlClient` exposes `withTransaction`. Pass it the effect that must
run atomically:

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

const transferCredits = (
  fromUserId: number,
  toUserId: number,
  amount: number
) =>
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient

    return yield* sql.withTransaction(
      Effect.gen(function* () {
        yield* sql`
          UPDATE accounts
          SET balance = balance - ${amount}
          WHERE user_id = ${fromUserId}
        `
        yield* sql`
          UPDATE accounts
          SET balance = balance + ${amount}
          WHERE user_id = ${toUserId}
        `
      })
    )
  })
```

Every statement inside the effect reuses the transaction connection. If the
effect fails, the transaction rolls back. If it succeeds, the transaction
commits.

## Keep Scope Tight

Put only the invariant-protecting database work inside the transaction. Do
validation, request decoding, and non-database calls before entering it when
possible.

```typescript
import { Effect, Schema } from "effect"
import { SqlClient } from "@effect/sql"

const Transfer = Schema.Struct({
  fromUserId: Schema.Number,
  toUserId: Schema.Number,
  amount: Schema.Number.pipe(Schema.positive())
})

const decodeTransfer = Schema.decodeUnknown(Transfer)

const applyTransfer = (input: unknown) =>
  Effect.gen(function* () {
    const request = yield* decodeTransfer(input)
    const sql = yield* SqlClient.SqlClient

    yield* sql.withTransaction(
      Effect.gen(function* () {
        yield* sql`
          INSERT INTO ledger_entries ${sql.insert({
            user_id: request.fromUserId,
            amount: -request.amount
          })}
        `
        yield* sql`
          INSERT INTO ledger_entries ${sql.insert({
            user_id: request.toUserId,
            amount: request.amount
          })}
        `
      })
    )
  })
```

The schema parse is outside the transaction. Only the two ledger writes are
inside.

## Nested Transactions

Nested `withTransaction` calls use savepoints. The source constructs savepoint
names with an `effect_sql_` prefix and increments a transaction depth counter.

```typescript
import { Effect } from "effect"
import { SqlClient } from "@effect/sql"

const createUserAndProfile = (email: string, displayName: string) =>
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient

    yield* sql.withTransaction(
      Effect.gen(function* () {
        const users = yield* sql<{ readonly id: number }>`
          INSERT INTO users ${sql.insert({ email })}
          RETURNING id
        `
        const id = users[0]!.id

        yield* sql.withTransaction(
          sql`
            INSERT INTO profiles ${sql.insert({
              user_id: id,
              display_name: displayName
            })}
          `
        )
      })
    )
  })
```

Use nesting when a reusable function already owns a transaction boundary. Do
not add nesting for style; it still emits savepoint commands and should reflect
real composition.

## Failure And Rollback

Represent expected business failures in the error channel. The failed effect
causes rollback and keeps the error typed for the caller.

```typescript
import { Data, Effect } from "effect"
import { SqlClient } from "@effect/sql"

class InsufficientFunds extends Data.TaggedError("InsufficientFunds")<{
  readonly userId: number
}> {}

const debit = (userId: number, amount: number) =>
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient

    yield* sql.withTransaction(
      Effect.gen(function* () {
        const rows = yield* sql<{ readonly balance: number }>`
          SELECT balance
          FROM accounts
          WHERE user_id = ${userId}
        `
        const balance = rows[0]?.balance ?? 0

        if (balance < amount) {
          return yield* new InsufficientFunds({ userId })
        }

        yield* sql`
          UPDATE accounts
          SET balance = balance - ${amount}
          WHERE user_id = ${userId}
        `
      })
    )
  })
```

Do not convert these failures into defects. Let callers recover with
`Effect.catchTag` or with a higher-level policy.

## Transaction Requirements

`withTransaction` preserves the original requirements of the effect. This means
you can call services inside the transaction if they are already part of the
program environment:

```typescript
import { Context, Effect } from "effect"
import { SqlClient } from "@effect/sql"

class AuditClock extends Context.Tag("app/AuditClock")<
  AuditClock,
  { readonly now: Effect.Effect<Date> }
>() {}

const writeAudit = (message: string) =>
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient
    const clock = yield* AuditClock

    yield* sql.withTransaction(
      Effect.gen(function* () {
        const createdAt = yield* clock.now
        yield* sql`
          INSERT INTO audit_log ${sql.insert({
            message,
            created_at: createdAt
          })}
        `
      })
    )
  })
```

Avoid slow remote calls in the transaction body. If the call must be
coordinated with a database write, prefer an outbox table written in the same
transaction and processed later.

## Dialect Commands

The driver defines begin, commit, rollback, savepoint, and rollback-savepoint
SQL when constructing the client. PostgreSQL, MySQL, SQLite, MSSQL, and
ClickHouse drivers use their compilers and transaction commands internally.
Application code should normally not issue those commands by hand.

## Transaction Checklist

- Put only database-invariant work inside `sql.withTransaction`.
- Decode and validate before entering the transaction.
- Keep driver-specific transaction SQL out of repositories.
- Let expected failures fail the transaction effect.
- Use nested transactions only for reusable transactional functions.
- Prefer an outbox table over remote calls inside a transaction.
- Keep streaming reads outside long write transactions when possible.
- Include tenancy and authorization predicates in every write query.
- Avoid connection reservation unless a driver feature requires it.
- Test rollback behavior for the failure path that matters.

## Cross-references

See also: [02-sql-client.md](02-sql-client.md), [03-tagged-templates.md](03-tagged-templates.md), [08-sql-migrations.md](08-sql-migrations.md), [11-driver-sqlite.md](11-driver-sqlite.md).
