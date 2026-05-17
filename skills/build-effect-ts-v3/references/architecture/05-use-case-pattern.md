# Use Case Pattern
Write use cases as traced Effect functions that orchestrate domain policy, repositories, and adapter services.

## What A Use Case Owns

A use case is the application layer. It owns the workflow for one business
action:

- decode or receive already-decoded domain input;
- load state through repository ports;
- call pure domain functions and policies;
- persist the state change;
- translate low-level adapter failures if needed;
- return domain output or a small application error set.

It does not own HTTP status codes, CLI output formatting, SQL schema, or runtime
launch.

## Prefer Effect.fn

Use `Effect.fn` for named, traced use cases:

```typescript
import { Effect, Option } from "effect"

export const RegisterUser = Effect.fn("RegisterUser")(function* (input: {
  readonly id: UserId
  readonly email: Email
}) {
  const users = yield* UserRepository
  const existing = yield* users.findByEmail(input.email)

  if (Option.isSome(existing)) {
    return yield* new EmailAlreadyRegistered({ email: input.email })
  }

  const user = new User({
    id: input.id,
    email: input.email
  })

  yield* users.save(user)
  return user
})
```

The function name appears in traces. The environment type tells you which
services still need layers.

## Use Case Service

When a feature has many use cases, group them in an `Effect.Service`:

```typescript
import { Effect, Option } from "effect"

export class Users extends Effect.Service<Users>()("Users", {
  effect: Effect.gen(function* () {
    const repository = yield* UserRepository

    const register = Effect.fn("Users.register")(function* (user: User) {
      const existing = yield* repository.findByEmail(user.email)
      if (Option.isSome(existing)) {
        return yield* new EmailAlreadyRegistered({ email: user.email })
      }
      yield* repository.save(user)
      return user
    })

    const findById = Effect.fn("Users.findById")(function* (id: UserId) {
      const found = yield* repository.findById(id)
      return yield* Option.match(found, {
        onNone: () => Effect.fail(new UserNotFound({ id })),
        onSome: Effect.succeed
      })
    })

    return { register, findById }
  }),
  dependencies: [UserRepositoryMemory]
}) {}
```

The official HTTP example uses feature services like `People` this way: the
service obtains repositories and SQL, exposes methods, and lists dependencies.

## Dependencies In Defaults

Do not hide production infrastructure in domain code. If you put dependencies in
an `Effect.Service`, treat `.Default` as app-level wiring:

```typescript
export class Billing extends Effect.Service<Billing>()("Billing", {
  effect: Effect.gen(function* () {
    const invoices = yield* InvoiceRepository
    return {
      closeInvoice: (id: InvoiceId) =>
        Effect.gen(function* () {
          yield* invoices.close(id)
        })
    }
  }),
  dependencies: [InvoiceRepositorySql]
}) {}
```

If tests need a different repository, provide `Billing.DefaultWithoutDependencies`
and then provide the test repository layer.

## Policy Composition

Keep authorization, validation, and policy as effects so they compose with the
workflow:

```typescript
import { Effect } from "effect"

const requirePermission = (action: string) =>
  Effect.gen(function* () {
    const actor = yield* CurrentActor
    if (!actor.permissions.has(action)) {
      return yield* new PermissionDenied({ action })
    }
  })

export const UpdateUserEmail = Effect.fn("UpdateUserEmail")(function* (
  id: UserId,
  email: Email
) {
  yield* requirePermission("user:update")
  const users = yield* UserRepository
  const user = yield* getExistingUser(users, id)
  const updated = new User({ ...user, email })
  yield* users.save(updated)
  return updated
})
```

Policies are application concerns unless they are pure domain invariants.

## Error Narrowing

Use cases should not accumulate every adapter error from every dependency. Catch
and remap at the right level:

```typescript
import { Effect } from "effect"

export class RegistrationUnavailable
  extends Schema.TaggedError<RegistrationUnavailable>()(
    "RegistrationUnavailable",
    { reason: Schema.String }
  )
{}

export const RegisterUserPublic = (user: User) =>
  RegisterUser(user).pipe(
    Effect.catchTag("SqlError", () =>
      Effect.fail(new RegistrationUnavailable({ reason: "storage" }))
    )
  )
```

The public boundary now handles `EmailAlreadyRegistered` and
`RegistrationUnavailable`, not the full database error surface.

## Platform Adapters Call Use Cases

HTTP and CLI handlers should be thin:

```typescript
import { Effect, Schema } from "effect"

export const handleRegisterUser = (payload: unknown) =>
  Effect.gen(function* () {
    const input = yield* Schema.decodeUnknown(RegisterUserRequest)(payload)
    const user = yield* RegisterUser(input)
    return yield* Schema.encode(UserResponse)(user)
  })
```

Keep request parsing and response encoding at the edge. Keep business branching
inside the use case.

## Cross-references

See also: [repository-pattern.md](04-repository-pattern.md), [error-boundary-design.md](06-error-boundary-design.md), [../core/07-effect-fn.md](../core/07-effect-fn.md), [../services-layers/15-effect-provide.md](../services-layers/15-effect-provide.md), [../observability/06-tracing-basics.md](../observability/06-tracing-basics.md).
