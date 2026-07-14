# Hexagonal Architecture
Use Effect services as ports and Layers as adapters so business workflows stay independent of infrastructure.

## The Mapping

Hexagonal architecture has a direct Effect v3 mapping:

| Hexagonal term | Effect v3 term | Example |
|---|---|---|
| Domain model | `Schema`, branded ids, tagged errors | `User`, `UserId`, `UserNotFound` |
| Primary port | use case function or service | `RegisterUser`, `People` |
| Secondary port | service tag | `UserRepository` |
| Adapter | layer implementation | `UserRepositorySql`, `UserRepositoryMemory` |
| Composition root | platform layer | `HttpLive`, `CliLive`, `AppLive` |

The official HTTP example demonstrates this shape without naming it hexagonal:
`People/Http.ts` is a primary adapter, `People.ts` is an application service,
`People/Repo.ts` is a repository service, and `Sql.ts` wires the SQL platform.

## Directory Shape

```text
src/
  domain/
    User.ts
    errors.ts
  application/
    RegisterUser.ts
    UserRepository.ts
  adapters/
    sql/UserRepositorySql.ts
    memory/UserRepositoryMemory.ts
  platform/
    http/UserHttp.ts
    cli/UserCli.ts
    Runtime.ts
```

For small apps, feature folders are acceptable:

```text
src/
  User/
    Domain.ts
    Repository.ts
    Register.ts
    Sql.ts
    Http.ts
```

Pick the first shape when boundaries matter across teams or packages. Pick the
second when one team owns the whole app and navigation speed matters more.

## Ports Are Tags

Define secondary ports as tags:

```typescript
import { Context, Effect, Option } from "effect"

export class UserRepository extends Context.Tag("UserRepository")<
  UserRepository,
  {
    readonly findById: (id: UserId) => Effect.Effect<Option.Option<User>>
    readonly save: (user: User) => Effect.Effect<void>
  }
>() {}
```

The port declares what the application needs. It does not declare how the data
is stored.

## Adapters Are Layers

Adapters satisfy the port:

```typescript
import { Effect, Layer, Option, Ref } from "effect"

export const UserRepositoryMemory = Layer.effect(
  UserRepository,
  Effect.gen(function* () {
    const users = yield* Ref.make(new Map<UserId, User>())

    return {
      findById: (id) =>
        Ref.get(users).pipe(
          Effect.map((map) => Option.fromNullable(map.get(id)))
        ),
      save: (user) =>
        Ref.update(users, (map) => new Map(map).set(user.id, user))
    }
  })
)
```

A SQL adapter can provide the same tag, and tests do not need to change.

## Primary Adapters

Primary adapters translate inbound protocols into use cases:

```typescript
import { Effect } from "effect"

export const registerHandler = (input: unknown) =>
  Effect.gen(function* () {
    const request = yield* Schema.decodeUnknown(RegisterUserRequest)(input)
    const user = yield* RegisterUser(request.email)
    return yield* Schema.encode(UserResponse)(user)
  })
```

In a real HTTP app, `HttpApiEndpoint` owns path, payload, success, and error
schemas. In a CLI app, `@effect/cli` owns args and options. In both cases the
adapter calls the same use case.

## Composition Root

Only the composition root chooses implementations:

```typescript
import { Layer } from "effect"

declare const UserRepositorySql: Layer.Layer<UserRepository, never, SqlClient.SqlClient>
declare const RegisterUserLive: Layer.Layer<RegisterUserService, never, UserRepository>
declare const HttpLive: Layer.Layer<never, never, RegisterUserService>
declare const SqlLive: Layer.Layer<SqlClient.SqlClient>

export const AppLive = HttpLive.pipe(
  Layer.provide(RegisterUserLive),
  Layer.provide(UserRepositorySql),
  Layer.provide(SqlLive)
)
```

If `SqlLive` should also be available to another output layer, compose with
`Layer.provideMerge` at the point where both services should survive.

## Boundary Direction

Allowed imports:

```text
domain      -> effect
application -> domain, effect
adapters    -> application, domain, effect, external packages
platform    -> application, adapters, effect, @effect/platform
```

Forbidden imports:

```text
domain      -> adapters
domain      -> platform
application -> platform HTTP modules
repositories -> concrete platform runtime launchers
```

## Error Flow

Keep typed failures on the inside:

```typescript
import { Effect } from "effect"

const program = RegisterUser(email).pipe(
  Effect.catchTag("EmailAlreadyRegistered", (error) =>
    Effect.fail(new PublicConflict({ message: `Email ${error.email} is taken` }))
  )
)
```

At the platform edge, convert the small public error set into HTTP statuses,
CLI exit messages, or queue nack decisions.

## When Not To Use It

Use a flatter structure for scripts, throwaway migrations, and single-purpose
internal utilities. The moment the same business action is reachable through
HTTP and CLI, or the same persistence port has test and production
implementations, hexagonal architecture pays for itself.

## Cross-references

See also: [overview.md](01-overview.md), [repository-pattern.md](04-repository-pattern.md), [error-boundary-design.md](06-error-boundary-design.md), [../http-server/07-handlers.md](../http-server/07-handlers.md), [../cli/09-providing-services.md](../cli/09-providing-services.md).
