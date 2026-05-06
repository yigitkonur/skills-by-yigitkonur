# Repository Pattern
Define repositories as Effect service ports, then provide test and production Layers for the same Tag.

## Why Repositories Matter In Effect

A repository is a secondary port. It is not an ORM wrapper for its own sake. It
exists when a use case needs persistence but should not know whether persistence
is SQL, memory, a remote API, or a fixture.

Use a repository when:

- the same use case must run in tests without production infrastructure;
- storage errors need translation before reaching HTTP or CLI;
- domain ids and schemas should stay stable while storage changes;
- the adapter needs transactions, retries, tracing, migrations, or caching.

Do not create repositories for one-line config lookups or platform services that
are already modeled by Effect packages.

## The Port

Define the port as a `Context.Tag` when there is no universal default:

```typescript
import { Context, Effect, Option, Schema } from "effect"

export const UserId = Schema.String.pipe(Schema.brand("UserId"))
export type UserId = typeof UserId.Type

export const Email = Schema.NonEmptyTrimmedString.pipe(Schema.brand("Email"))
export type Email = typeof Email.Type

export class User extends Schema.Class<User>("User")({
  id: UserId,
  email: Email
}) {}

export class UserRepository extends Context.Tag("UserRepository")<
  UserRepository,
  {
    readonly findById: (id: UserId) => Effect.Effect<Option.Option<User>>
    readonly findByEmail: (email: Email) => Effect.Effect<Option.Option<User>>
    readonly save: (user: User) => Effect.Effect<void>
  }
>() {}
```

This tag is the contract. Both implementations below provide exactly the same
tag.

## In-Memory Test Implementation

Use `Layer.effect` when the implementation needs state:

```typescript
import { Effect, Layer, Option, Ref } from "effect"

export const UserRepositoryMemory = Layer.effect(
  UserRepository,
  Effect.gen(function* () {
    const state = yield* Ref.make(new Map<UserId, User>())

    const findById = (id: UserId) =>
      Ref.get(state).pipe(
        Effect.map((users) => Option.fromNullable(users.get(id)))
      )

    const findByEmail = (email: Email) =>
      Ref.get(state).pipe(
        Effect.map((users) =>
          Option.fromNullable([...users.values()].find((user) => user.email === email))
        )
      )

    const save = (user: User) =>
      Ref.update(state, (users) => new Map(users).set(user.id, user))

    return { findById, findByEmail, save }
  })
)
```

The test implementation owns state through `Ref`, not a module-level mutable
variable. Each layer construction gets an isolated repository.

## SQL Production Implementation

Use the same tag for production. The implementation can depend on SQL:

```typescript
import { SqlClient } from "@effect/sql"
import { Effect, Layer, Option } from "effect"

type UserRow = {
  readonly id: string
  readonly email: string
}

const decodeUser = (row: UserRow) =>
  Effect.gen(function* () {
    const id = yield* Schema.decodeUnknown(UserId)(row.id)
    const email = yield* Schema.decodeUnknown(Email)(row.email)
    return new User({ id, email })
  })

export const UserRepositorySql = Layer.effect(
  UserRepository,
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient

    const findById = (id: UserId) =>
      sql<UserRow>`SELECT id, email FROM users WHERE id = ${id}`.pipe(
        Effect.flatMap((rows) =>
          Option.match(Option.fromNullable(rows[0]), {
            onNone: () => Effect.succeed(Option.none()),
            onSome: (row) => decodeUser(row).pipe(Effect.map(Option.some))
          })
        )
      )

    const findByEmail = (email: Email) =>
      sql<UserRow>`SELECT id, email FROM users WHERE email = ${email}`.pipe(
        Effect.flatMap((rows) =>
          Option.match(Option.fromNullable(rows[0]), {
            onNone: () => Effect.succeed(Option.none()),
            onSome: (row) => decodeUser(row).pipe(Effect.map(Option.some))
          })
        )
      )

    const save = (user: User) =>
      sql`
        INSERT INTO users (id, email)
        VALUES (${user.id}, ${user.email})
        ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email
      `.pipe(Effect.asVoid)

    return { findById, findByEmail, save }
  })
)
```

The SQL adapter may fail with SQL or schema decoding errors. Do not expose those
directly from public boundaries. Normalize them in the use case or platform
boundary.

## Use Case Consumes The Port

```typescript
import { Effect, Option, Schema } from "effect"

export class EmailAlreadyRegistered
  extends Schema.TaggedError<EmailAlreadyRegistered>()(
    "EmailAlreadyRegistered",
    { email: Email }
  )
{}

export const RegisterUser = Effect.fn("RegisterUser")(function* (user: User) {
  const users = yield* UserRepository
  const existing = yield* users.findByEmail(user.email)

  if (Option.isSome(existing)) {
    return yield* new EmailAlreadyRegistered({ email: user.email })
  }

  yield* users.save(user)
  return user
})
```

The use case compiles against the port and can run with either repository layer.

## Wiring Test Versus Production

```typescript
import { Effect, Layer } from "effect"

declare const SqlLive: Layer.Layer<SqlClient.SqlClient>
declare const testUser: User

export const TestProgram = RegisterUser(testUser).pipe(
  Effect.provide(UserRepositoryMemory)
)

export const ProdLive = UserRepositorySql.pipe(Layer.provide(SqlLive))
```

Tests can replace only the repository. Production wires the SQL repository to
the SQL client.

## Effect.Service Alternative

Use `Effect.Service` for repositories when the default implementation is
obvious and belongs to the app package:

```typescript
import { Effect } from "effect"

export class PeopleRepository extends Effect.Service<PeopleRepository>()(
  "PeopleRepository",
  {
    effect: makePeopleRepository,
    dependencies: [SqlLive]
  }
) {}
```

The official HTTP example uses this style with SQL model repositories. For
library-like ports or ports with no default, prefer `Context.Tag`. For details
on `Effect.Service`, read [../services-layers/03-effect-service.md](../services-layers/03-effect-service.md).

## Transaction Placement

Put transactions around use-case units, not around individual repository
methods by default. Repositories expose operations; use cases decide the unit of
consistency.

## Cross-references

See also: [domain-driven-design.md](02-domain-driven-design.md), [hexagonal-architecture.md](03-hexagonal-architecture.md), [use-case-pattern.md](05-use-case-pattern.md), [../services-layers/03-effect-service.md](../services-layers/03-effect-service.md), [../sql/02-sql-client.md](../sql/02-sql-client.md).
