# Architecture Overview
Choose an Effect v3 application shape that keeps domain rules pure, adapters replaceable, and dependency wiring visible.

## The Default Shape

Use this shape for real Effect applications:

```text
src/
  domain/
    User.ts
    Order.ts
    errors.ts
  use-cases/
    RegisterUser.ts
    PlaceOrder.ts
  repositories/
    UserRepository.ts
    OrderRepository.ts
  adapters/
    sql/
      UserRepositorySql.ts
    memory/
      UserRepositoryMemory.ts
  platform/
    http/
      Api.ts
      Http.ts
    cli/
      Main.ts
  AppLayer.ts
```

The split is not ceremony. It follows the same pressure visible in the official
`examples/http-server` app:

- `Domain/*` holds branded ids, schema models, and tagged errors.
- feature services such as `People` orchestrate policy and repository work.
- `People/Repo.ts` hides SQL persistence behind an Effect service.
- `People/Http.ts` adapts HttpApi handlers to application services.
- `Sql.ts` and `Http.ts` assemble platform layers.
- `main.ts` runs only the completed platform layer.

EffectPatterns uses the same larger shape in a different vocabulary: API server,
MCP transport, toolkit database layer, services, route factories, and a central
error handler. The common idea is boundary separation.

## Four Rings

| Ring | Owns | Effect tools |
|---|---|---|
| Domain | Schemas, branded ids, invariants, tagged errors | `Schema`, `Brand`, `Data`, `Option` |
| Use cases | Business workflows and policy orchestration | `Effect.fn`, `Effect.gen`, `catchTag` |
| Adapters | Repositories, clients, external systems | `Context.Tag`, `Effect.Service`, `Layer` |
| Platform | HTTP, CLI, workers, runtime launch | `HttpApi`, `Command`, `Layer.launch`, `NodeRuntime` |

Keep dependencies pointing inward. Domain code imports no adapters. Use cases
depend on repository tags, not concrete SQL clients. Adapters implement the tags.
Platform code composes layers and normalizes typed failures into protocol
responses.

## Which Architecture To Use

| Option | Score | Use when | Tradeoff |
|---|---:|---|---|
| Feature modules | 86 | Small to mid-size apps with one platform | Fast navigation, but adapters can creep into feature folders |
| Hexagonal | 94 | Apps with tests, SQL, queues, HTTP, CLI, or workers | More files, much clearer dependency direction |
| Package-per-ring | 80 | Large monorepos with independent domain packages | Strong boundaries, more build configuration |

Recommend hexagonal as the default for non-trivial Effect code. Effect already
has the primitives that make it cheap: tags are ports, layers are adapters, and
the environment type tells you which ports a use case still needs.

## Effect-Specific Rules

Do not model architecture as classes with hidden constructors. Model capability
as services:

```typescript
import { Context, Effect, Layer, Option } from "effect"

type UserId = string
type User = { readonly id: UserId; readonly email: string }

class UserRepository extends Context.Tag("UserRepository")<
  UserRepository,
  {
    readonly findById: (id: UserId) => Effect.Effect<Option.Option<User>>
    readonly save: (user: User) => Effect.Effect<void>
  }
>() {}

const RegisterUser = Effect.fn("RegisterUser")(function* (
  id: UserId,
  email: string
) {
  const users = yield* UserRepository
  const user = { id, email }
  yield* users.save(user)
  return user
})

const UserRepositoryMemory = Layer.succeed(UserRepository, {
  findById: () => Effect.succeed(Option.none()),
  save: () => Effect.void
})

export const RegisterUserTest = RegisterUser("user-1", "a@example.com").pipe(
  Effect.provide(UserRepositoryMemory)
)
```

This example is intentionally small:

- the use case requires `UserRepository`;
- the implementation is swappable;
- the test provides a layer;
- the runtime boundary stays outside the library code.

## Dependency Wiring

Use `Layer.provide` when one layer only satisfies another layer's requirements.
Use `Layer.provideMerge` when the provided layer should remain in the output.
The official docs show this distinction, and the Effect Language Server can
surface requirement leaks while editing.

```typescript
import { Context, Layer } from "effect"

class Config extends Context.Tag("Config")<Config, { readonly port: number }>() {}
class Logger extends Context.Tag("Logger")<Logger, { readonly info: (message: string) => void }>() {}
class Server extends Context.Tag("Server")<Server, { readonly start: void }>() {}

declare const ConfigLive: Layer.Layer<Config>
declare const LoggerLive: Layer.Layer<Logger, never, Config>
declare const ServerLive: Layer.Layer<Server, never, Logger>

const LoggingLive = LoggerLive.pipe(Layer.provideMerge(ConfigLive))
const AppLive = ServerLive.pipe(Layer.provide(LoggingLive))
```

`LoggingLive` outputs both `Logger` and `Config`. `AppLive` outputs only
`Server`. That is architecture encoded in types.

## Built On The Primitive References

Architecture work should route back to the primitive references instead of
re-explaining them:

- Core and types: [core](../core/01-effect-type.md), [data-types](../data-types/01-overview.md), [schema](../schema/01-overview.md), [pattern matching](../pattern-matching/01-overview.md).
- Failure and dependencies: [error handling](../error-handling/01-overview.md), [services and layers](../services-layers/01-overview.md), [config](../config/01-overview.md), [resource management](../resource-management/01-overview.md).
- Runtime mechanics: [concurrency](../concurrency/01-overview.md), [scheduling](../scheduling/01-overview.md), [streams](../streams/01-overview.md), [queue/pubsub](../queue-pubsub/01-overview.md), [state](../state/01-overview.md), [caching](../caching/01-overview.md).
- Boundaries: [HTTP client](../http-client/01-overview.md), [HTTP server](../http-server/01-overview.md), [CLI](../cli/01-overview.md), [platform](../platform/01-overview.md), [SQL](../sql/01-overview.md), [RPC](../rpc/01-overview.md), [frontend atoms](../frontend-atom/01-overview.md).
- Delivery quality: [testing](../testing/01-overview.md), [observability](../observability/01-overview.md), [migration](../migration/01-overview.md), [anti-patterns](../anti-patterns/01-overview.md).

## Cross-references

See also: [domain-driven-design.md](02-domain-driven-design.md), [hexagonal-architecture.md](03-hexagonal-architecture.md), [repository-pattern.md](04-repository-pattern.md), [../services-layers/01-overview.md](../services-layers/01-overview.md), [../core/07-effect-fn.md](../core/07-effect-fn.md).
