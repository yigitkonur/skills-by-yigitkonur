# Error Boundary Design
Normalize many internal typed failures into a small public error vocabulary at HTTP, CLI, queue, and worker boundaries.

## Error Layers

Use three layers of expected errors:

| Layer | Example | Who handles it |
|---|---|---|
| Domain | `UserNotFound`, `EmailAlreadyRegistered` | use cases and public boundary |
| Adapter | `SqlError`, upstream API failures, file errors | adapter or use case |
| Public boundary | `PublicNotFound`, `PublicConflict`, `PublicUnavailable` | HTTP, CLI, queue, RPC |

The inside of the app can be precise. The outside should be stable.

## Domain Errors Stay Specific

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

Use these errors where the business rule is known. Do not replace them with a
generic message too early.

## Public Errors Are Small

```typescript
import { Schema } from "effect"

export class PublicNotFound extends Schema.TaggedError<PublicNotFound>()(
  "PublicNotFound",
  { resource: Schema.String }
) {}

export class PublicConflict extends Schema.TaggedError<PublicConflict>()(
  "PublicConflict",
  { message: Schema.String }
) {}

export class PublicUnavailable extends Schema.TaggedError<PublicUnavailable>()(
  "PublicUnavailable",
  { service: Schema.String }
) {}
```

HTTP can map these to status codes. CLI can map them to exit output. A worker can
map them to retry or dead-letter behavior.

## Normalize At The Boundary

```typescript
import { Effect } from "effect"

export const registerUserBoundary = (request: RegisterUserRequest) =>
  RegisterUser(request).pipe(
    Effect.catchTag("EmailAlreadyRegistered", (error) =>
      Effect.fail(new PublicConflict({ message: `Email ${error.email} is taken` }))
    ),
    Effect.catchTag("SqlError", () =>
      Effect.fail(new PublicUnavailable({ service: "users" }))
    )
  )
```

This boundary keeps storage-specific errors from becoming part of the public
contract.

## Aggregator Services

Aggregator services often call multiple use cases and see many tagged errors.
Catch the internal set and re-emit the boundary set:

```typescript
import { Effect } from "effect"

export const OnboardAccount = Effect.fn("OnboardAccount")(function* (
  request: OnboardAccountRequest
) {
  const account = yield* CreateAccount(request.account)
  const user = yield* RegisterUser(request.user)
  yield* AddUserToAccount(account.id, user.id)
  return { account, user }
}).pipe(
  Effect.catchTags({
    AccountAlreadyExists: () =>
      Effect.fail(new PublicConflict({ message: "Account already exists" })),
    EmailAlreadyRegistered: () =>
      Effect.fail(new PublicConflict({ message: "Email already registered" })),
    SqlError: () =>
      Effect.fail(new PublicUnavailable({ service: "onboarding" }))
  })
)
```

The internal system keeps precise errors. The boundary exposes the public set.

## HttpApi Error Schemas

For HTTP, publish boundary errors in the endpoint contract:

```typescript
import { HttpApiEndpoint, HttpApiGroup } from "@effect/platform"

export class UsersApi extends HttpApiGroup.make("users")
  .add(
    HttpApiEndpoint.post("register", "/users")
      .setPayload(RegisterUserRequest)
      .addSuccess(UserResponse)
      .addError(PublicConflict)
      .addError(PublicUnavailable)
  )
{}
```

If domain errors are appropriate public errors, publish them directly. If not,
map them before the handler returns.

## Boundary Layer Placement

Put boundary normalization in the outer adapter when the mapping is
protocol-specific. Put it in an aggregator service when several protocols should
share the same public error vocabulary. Do not put protocol-specific response
decisions in repositories.

## Defects Are Not Public Errors

Expected failures belong in the error channel. Defects are unexpected bugs or
interrupted invariants. Do not normalize defects into business errors unless the
boundary explicitly owns a recovery policy.

Use `Effect.catchAllCause` only at a process or platform boundary where logging,
redaction, and shutdown policy are clear.

## Boundary Checklist

- Does the endpoint expose only errors the client can act on?
- Are SQL, file, and upstream client errors hidden or remapped?
- Are schema decode failures handled by the platform contract?
- Are defects logged or supervised instead of presented as domain failures?
- Do tests cover one success and each public error mapping?

## Cross-references

See also: [use-case-pattern.md](05-use-case-pattern.md), [hexagonal-architecture.md](03-hexagonal-architecture.md), [../error-handling/12-error-taxonomy.md](../error-handling/12-error-taxonomy.md), [../error-handling/13-error-remapping.md](../error-handling/13-error-remapping.md), [../http-server/08-error-responses.md](../http-server/08-error-responses.md).
