# Domain-Driven Design
Model domain facts with schemas, branded ids, tagged errors, and pure functions before choosing an adapter.

## What Belongs In Domain

Domain files should be boring and strict:

- branded ids;
- schema classes or schema structs;
- domain constructors and transformations;
- tagged errors that describe business failures;
- policies that do not depend on HTTP, SQL, files, or clocks unless those are
  passed as services from a higher layer.

The official `examples/http-server` app keeps `PersonId`, `Person`, and
`PersonNotFound` in `Domain/Person.ts`, while `People.ts` and `People/Repo.ts`
handle orchestration and storage. Follow that separation.

## Branded Ids

Use branded schemas when ids cross boundaries:

```typescript
import { Schema } from "effect"

export const UserId = Schema.String.pipe(Schema.brand("UserId"))
export type UserId = typeof UserId.Type

export const UserIdFromString = Schema.String.pipe(Schema.compose(UserId))
```

The brand prevents mixing `UserId` with another string id after decoding. Keep
the string format at the boundary and the brand inside the application.

## Entities

Use `Schema.Class` for entities that need constructors and generated types:

```typescript
import { Option, Schema } from "effect"

export const Email = Schema.NonEmptyTrimmedString.pipe(Schema.brand("Email"))
export type Email = typeof Email.Type

export class User extends Schema.Class<User>("User")({
  id: UserId,
  email: Email,
  displayName: Option.Option(Schema.NonEmptyTrimmedString)
}) {}
```

This gives the domain a runtime decoder and a static type. It also gives
platform layers a single source of truth for request, response, and persistence
validation.

## Tagged Errors

Use tagged errors for expected domain failures:

```typescript
import { Schema } from "effect"

export class UserNotFound extends Schema.TaggedError<UserNotFound>()(
  "UserNotFound",
  { id: UserId }
) {}

export class EmailAlreadyRegistered
  extends Schema.TaggedError<EmailAlreadyRegistered>()(
    "EmailAlreadyRegistered",
    { email: Email }
  )
{}
```

These errors belong in the domain because they are part of the ubiquitous
language. A repository may discover `UserNotFound`, but HTTP should not own it.

## Aggregates

Keep aggregates as functions over immutable values. Do not make them reach into
services.

```typescript
import { Effect, Option } from "effect"

export type Team = {
  readonly id: string
  readonly ownerId: UserId
  readonly memberIds: ReadonlySet<UserId>
}

export const addMember = (team: Team, userId: UserId) =>
  team.memberIds.has(userId)
    ? Effect.succeed(team)
    : Effect.succeed({
        ...team,
        memberIds: new Set([...team.memberIds, userId])
      })

export const ownerOf = (team: Team): Option.Option<UserId> =>
  Option.some(team.ownerId)
```

If the aggregate needs persistence, put that in a use case:

```typescript
import { Effect } from "effect"

const AddTeamMember = Effect.fn("AddTeamMember")(function* (
  teamId: string,
  userId: UserId
) {
  const teams = yield* TeamRepository
  const team = yield* teams.get(teamId)
  const updated = yield* addMember(team, userId)
  yield* teams.save(updated)
  return updated
})
```

## Repository Ports

The domain may define repository vocabulary, but repository implementations stay
outside the domain:

```typescript
import { Context, Effect, Option } from "effect"

export class UserRepository extends Context.Tag("UserRepository")<
  UserRepository,
  {
    readonly findByEmail: (email: Email) => Effect.Effect<Option.Option<User>>
    readonly findById: (id: UserId) => Effect.Effect<Option.Option<User>>
    readonly save: (user: User) => Effect.Effect<void>
  }
>() {}
```

Use `Context.Tag` for ports with no universal default. Use `Effect.Service` for
application services that have a default implementation and dependencies.

## Use Case Boundary

A use case coordinates repositories and policies:

```typescript
import { Effect, Option } from "effect"

export const RegisterUser = Effect.fn("RegisterUser")(function* (
  id: UserId,
  email: Email
) {
  const users = yield* UserRepository
  const existing = yield* users.findByEmail(email)

  if (Option.isSome(existing)) {
    return yield* new EmailAlreadyRegistered({ email })
  }

  const user = new User({
    id,
    email,
    displayName: Option.none()
  })

  yield* users.save(user)
  return user
})
```

The use case does not know whether the repository is SQL, in-memory, or a remote
API. That decision is deferred to a layer.

## Domain Errors Versus Adapter Errors

Keep these separate:

| Error kind | Example | Owner | Boundary behavior |
|---|---|---|---|
| Domain | `EmailAlreadyRegistered` | Domain | Expose as typed application failure |
| Repository | `SqlError` | Adapter | Translate to application or boundary error |
| Platform | malformed request payload | HTTP or CLI | Normalize to protocol response |
| Defect | impossible invariant breach | Runtime | Let supervisor, logs, or process policy handle it |

Do not leak raw SQL or HTTP client failures to the public API. Translate them at
the use-case or platform boundary.

## Package Boundaries

For monorepos, the domain package should be the most stable package:

```text
packages/domain
packages/application
packages/sql-adapter
packages/http-server
packages/cli
```

Only `application` imports `domain`. Adapters import both application ports and
platform packages. Runtime packages compose adapters.

## Testing The Domain

Domain tests should need no layers unless the domain explicitly uses services:

```typescript
import { Effect } from "effect"

const program = Effect.gen(function* () {
  const email = Schema.decodeUnknownSync(Email)("a@example.com")
  const user = yield* RegisterUser(email)
  return user.email
})
```

For use cases, provide repository test layers. Do not run a full HTTP server to
test aggregate rules.

## Cross-references

See also: [shared-kernel.md](07-shared-kernel.md), [repository-pattern.md](04-repository-pattern.md), [use-case-pattern.md](05-use-case-pattern.md), [../schema/06-branded-types.md](../schema/06-branded-types.md), [../schema/05-schema-tagged-error.md](../schema/05-schema-tagged-error.md).
