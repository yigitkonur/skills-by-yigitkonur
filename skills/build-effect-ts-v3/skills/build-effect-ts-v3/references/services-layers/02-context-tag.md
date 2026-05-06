# Context Tag
Use `Context.Tag` when you want to publish a service contract separately from its implementation.

## Canonical Class Pattern

The class pattern gives the service a stable identity, a readable key, and a service shape.

```typescript
import { Context, Effect, Layer } from "effect"

export class UserRepository extends Context.Tag("app/UserRepository")<
  UserRepository,
  {
    readonly findById: (id: string) => Effect.Effect<{ readonly id: string; readonly name: string }>
    readonly saveName: (id: string, name: string) => Effect.Effect<void>
  }
>() {}

export const UserRepositoryLive = Layer.succeed(UserRepository, {
  findById: (id) => Effect.succeed({ id, name: "Ada" }),
  saveName: (_id, _name) => Effect.void
})
```

The first generic parameter is the identifier type. The second is the service value shape.

## Requesting A Service

Yielding the tag requests the implementation from the current context.

```typescript
import { Effect } from "effect"

const renameUser = (id: string, name: string) =>
  Effect.gen(function* () {
    const users = yield* UserRepository
    yield* users.saveName(id, name)
    return yield* users.findById(id)
  })
```

The inferred requirement is `UserRepository`. This is a feature: the type tells callers exactly which capability they must provide.

## Why Library Code Usually Uses Tags

Library code should not assume a default database, clock, logger, or HTTP client. `Context.Tag` lets the library export only the contract.

| Library concern | Why `Context.Tag` fits |
|---|---|
| Multiple runtime implementations | Callers choose the layer |
| Test doubles | Tests can provide small values |
| No sensible default | The tag does not require one |
| Public API stability | The tag shape is the boundary |

Use `Effect.Service` when the module really owns the default implementation.

## Static Live Layer

It is common to put a live layer next to the tag.

```typescript
import { Context, Effect, Layer } from "effect"

class AuditLog extends Context.Tag("app/AuditLog")<
  AuditLog,
  {
    readonly record: (event: string) => Effect.Effect<void>
  }
>() {
  static readonly Live = Layer.succeed(this, {
    record: (event) => Effect.logInfo("audit event", { event })
  })
}

const program = AuditLog.record("user-renamed")
const runnable = program.pipe(Effect.provide(AuditLog.Live))
```

This pattern keeps discovery local while preserving the fact that the layer is optional.

## GenericTag

`Context.GenericTag` creates a tag from a string key without a class declaration.

```typescript
import { Context, Effect, Layer } from "effect"

type RequestInfo = {
  readonly requestId: string
}

const RequestInfo = Context.GenericTag<RequestInfo>("app/RequestInfo")

const RequestInfoLive = Layer.succeed(RequestInfo, {
  requestId: "req-123"
})

const program = Effect.gen(function* () {
  const request = yield* RequestInfo
  return request.requestId
}).pipe(Effect.provide(RequestInfoLive))
```

Prefer class tags for exported service APIs. `GenericTag` is useful for local wiring, migration work, or compatibility with older code that already uses string keys.

## Key Collision Discipline

Tag keys are strings. Use namespaced keys such as `app/UserRepository`, `billing/InvoiceGateway`, or `test/RequestInfo`.

Two tags with the same key are the same logical slot. That is useful when intentionally sharing a key, and dangerous when accidental.

## Service Shape Rules

Keep service methods effectful when they can fail, block, allocate, or depend on other services.

```typescript
type EmailService = {
  readonly sendWelcome: (userId: string) => Effect.Effect<void, EmailError>
}
```

Do not hide effects behind promises in service methods. Returning `Effect` keeps errors, interruption, tracing, and dependencies visible.

## Test Layer Pattern

Tests can provide a minimal value directly.

```typescript
import { Effect, Layer } from "effect"

const UserRepositoryTest = Layer.succeed(UserRepository, {
  findById: (id) => Effect.succeed({ id, name: "Test User" }),
  saveName: (_id, _name) => Effect.void
})

const testProgram = renameUser("u1", "Grace").pipe(
  Effect.provide(UserRepositoryTest)
)
```

For broad integration tests that also need dependency services visible to the test body, compose test layers with `Layer.provideMerge`.

## Interface Evolution

Treat the service shape as a public contract when the tag is exported.

| Change | Compatibility |
|---|---|
| Add a new method | All live and test layers must implement it |
| Change a method error type | Call sites may need new error handling |
| Add a dependency to a live layer | Layer composition changes, not tag users |
| Split one service into two tags | Programs gain two explicit requirements |

Prefer small capability tags over one broad application context. A broad tag makes every consumer depend on every method, even when it needs only one capability.

## Service Methods Should Stay Lazy

Methods should return `Effect` rather than doing work when the method is called.

```typescript
type LazyAuditLog = {
  readonly record: (event: string) => Effect.Effect<void>
}
```

This lets callers compose, retry, interrupt, trace, and test the operation. It also keeps failures in the typed error channel.

## Static Helpers

Static helper methods on the tag class are fine when they return effects and do not allocate hidden global state.

```typescript
class AuditLog extends Context.Tag("app/AuditLog")<
  AuditLog,
  { readonly record: (event: string) => Effect.Effect<void> }
>() {
  static readonly record = (event: string) =>
    Effect.gen(function* () {
      const audit = yield* AuditLog
      yield* audit.record(event)
    })
}
```

This is explicit and works without generated accessors.

## Cross-references

See also: [services-layers/01-overview.md](../services-layers/01-overview.md), [services-layers/03-effect-service.md](../services-layers/03-effect-service.md), [services-layers/04-context-vs-effect-service.md](../services-layers/04-context-vs-effect-service.md), [services-layers/06-layer-succeed.md](../services-layers/06-layer-succeed.md), [services-layers/15-effect-provide.md](../services-layers/15-effect-provide.md).
