# Context Tag Vs Effect Service
Choose the service definition style based on ownership of the default implementation.

## Decision Matrix

| Question | Prefer `Context.Tag` | Prefer `Effect.Service` |
|---|---|---|
| Is this library code? | Yes | Usually no |
| Does the module own a normal default? | Not required | Yes |
| Are there many equal implementations? | Yes | No |
| Do you want generated `.Default`? | No | Yes |
| Do you need no default at all? | Yes | No |
| Is the service per request or per tenant? | Often yes | Only with parameterized defaults |
| Do you want generated accessors? | No | Optional |

## Library Boundary Rule

Library code should usually export only tags and pure constructors. Let the application decide how to build the layer.

```typescript
import { Context, Effect } from "effect"

export class Payments extends Context.Tag("billing/Payments")<
  Payments,
  {
    readonly charge: (invoiceId: string) => Effect.Effect<void, PaymentError>
  }
>() {}
```

This keeps the package neutral. A caller can wire Stripe, test doubles, a sandbox gateway, or a local stub.

## Application Default Rule

Application code often has a normal runtime implementation. `Effect.Service` keeps the tag and live layer together.

```typescript
import { Effect } from "effect"

class AppClock extends Effect.Service<AppClock>()("app/AppClock", {
  sync: () => ({
    now: Effect.sync(() => Date.now())
  })
}) {}
```

The service is easy to provide at the app root with `AppClock.Default`.

## Testability

Both patterns test well. The difference is where the default lives.

| Test need | Recommended pattern |
|---|---|
| Replace the whole service | `Effect.provideService(Tag, value)` |
| Replace one dependency of a service | `.DefaultWithoutDependencies` or manual `Layer.provideMerge` |
| Publish a reusable test contract | `Context.Tag` plus `Test` layer |
| Fast app-level unit test | `Effect.Service.make` value |

## Migration Guideline

Do not mechanically rewrite all tags to `Effect.Service`. Only migrate a service when all of these are true:

1. The module owns a default implementation.
2. The default implementation is useful in normal app execution.
3. The service is not a public library contract that should remain implementation-free.
4. The team accepts the experimental status of `Effect.Service` in v3.

## Naming

Use stable namespaced keys in both styles.

```typescript
class UserRepository extends Context.Tag("app/UserRepository")<
  UserRepository,
  UserRepositoryShape
>() {}

class UserRepositoryLive extends Effect.Service<UserRepositoryLive>()(
  "app/UserRepositoryLive",
  { succeed: { findById: (id: string) => Effect.succeed({ id }) } }
) {}
```

Do not reuse the same key for two unrelated services. If you split interface and implementation, name them differently.

## Practical Default

For this skill's examples:

| Example kind | Default style |
|---|---|
| Teaching DI mechanics | `Context.Tag` |
| Showing generated defaults | `Effect.Service` |
| Framework integration | `Context.Tag` plus explicit layers |
| Parameterized app services | `Effect.Service` with stored layer constants |

## Anti-Collision Rule

Do not let the convenience of `Effect.Service` erase architecture boundaries.

| Boundary | Safer choice |
|---|---|
| Published package API | `Context.Tag` |
| Application implementation module | `Effect.Service` |
| Adapter wrapping a vendor SDK | Either, depending on ownership |
| Test-only helper | Either, but keep it local |

The practical question is not which API is newer; it is who owns the live implementation.

## Refactoring Direction

When a service starts as `Effect.Service` and later becomes a library boundary, split it:

1. Export a `Context.Tag` for the stable contract.
2. Move the generated default into an app adapter or normal layer.
3. Keep call sites depending on the tag, not the concrete default.

When a tag has one obvious app implementation and no library consumers, migrating to `Effect.Service` can reduce boilerplate.

## Generated Accessors Are Orthogonal

Choosing `Effect.Service` does not force accessors. You can still require explicit service extraction:

```typescript
const program = Effect.gen(function* () {
  const clock = yield* AppClock
  return yield* clock.now
})
```

That makes the dependency visible in the body even though the service has a generated `.Default`.

## Cross-references

See also: [services-layers/02-context-tag.md](../services-layers/02-context-tag.md), [services-layers/03-effect-service.md](../services-layers/03-effect-service.md), [services-layers/05-context-reference.md](../services-layers/05-context-reference.md), [services-layers/15-effect-provide.md](../services-layers/15-effect-provide.md).
