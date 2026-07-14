# Effect Service
Use `Effect.Service` for app-level services where the module owns a normal default implementation.

## What It Generates

`Effect.Service` defines the tag and layer in one declaration. In v3.21.2 it is present in `Effect.ts` with `@since 3.9.0` and remains marked experimental.

```typescript
import { Effect } from "effect"

class IdGenerator extends Effect.Service<IdGenerator>()("app/IdGenerator", {
  sync: () => ({
    next: Effect.succeed("id-1")
  })
}) {}

const program = Effect.gen(function* () {
  const ids = yield* IdGenerator
  return yield* ids.next
})

const runnable = program.pipe(Effect.provide(IdGenerator.Default))
```

The class is the tag. `IdGenerator.Default` is the generated layer.

## Constructor Forms

An `Effect.Service` declaration must provide exactly one implementation form.

| Form | Use when | Layer construction |
|---|---|---|
| `succeed` | The service value is static | `Layer.succeed` |
| `sync` | Construction is synchronous | `Layer.sync` |
| `effect` | Construction is effectful | `Layer.effect` |
| `scoped` | Construction has acquisition and release | `Layer.scoped` |

```typescript
import { Effect } from "effect"

class FeatureFlags extends Effect.Service<FeatureFlags>()("app/FeatureFlags", {
  succeed: {
    isEnabled: (_name: string) => Effect.succeed(false)
  }
}) {}

class StartupClock extends Effect.Service<StartupClock>()("app/StartupClock", {
  effect: Effect.gen(function* () {
    const startedAt = yield* Effect.sync(() => Date.now())
    return {
      startedAt: Effect.succeed(startedAt)
    }
  })
}) {}
```

## Dependencies

Use `dependencies` when the service implementation needs other layers and those dependencies are part of its normal default.

```typescript
import { Effect } from "effect"

class Prefix extends Effect.Service<Prefix>()("app/Prefix", {
  succeed: { value: "app" }
}) {}

class AppLogger extends Effect.Service<AppLogger>()("app/AppLogger", {
  effect: Effect.gen(function* () {
    const prefix = yield* Prefix
    return {
      info: (message: string) => Effect.logInfo(`${prefix.value}: ${message}`)
    }
  }),
  dependencies: [Prefix.Default]
}) {}

const program = Effect.gen(function* () {
  const logger = yield* AppLogger
  yield* logger.info("started")
})

const runnable = program.pipe(Effect.provide(AppLogger.Default))
```

When `dependencies` is present, v3 generates both:

| Property | Meaning |
|---|---|
| `.DefaultWithoutDependencies` | Builds only this service and still requires its dependencies |
| `.Default` | Builds this service and provides the dependency layers |

Use `.DefaultWithoutDependencies` when tests want to replace a dependency layer.

## Parameterized Defaults

Function-valued `effect` and `scoped` forms can accept arguments. The v3 source marks service make arguments as `@since 3.16.0`.

```typescript
import { Effect } from "effect"

class TenantConfig extends Effect.Service<TenantConfig>()("app/TenantConfig", {
  effect: (tenantId: string) =>
    Effect.succeed({
      tenantId,
      bucket: `tenant-${tenantId}`
    })
}) {}

const TenantALive = TenantConfig.Default("tenant-a")
```

Store parameterized layers in constants. Recalling the constructor inline creates a different layer reference.

## Accessors Tradeoff

`accessors: true` generates static method accessors on the service tag.

```typescript
import { Effect } from "effect"

class Slugger extends Effect.Service<Slugger>()("app/Slugger", {
  accessors: true,
  sync: () => ({
    slug: (value: string) => Effect.succeed(value.toLowerCase().replaceAll(" ", "-"))
  })
}) {}

const program = Slugger.slug("Hello Effect")
```

There is no single universal rule in the cached skills:

| Style | Benefit | Cost |
|---|---|---|
| Enable accessors | Less boilerplate at call sites; easy service-method syntax |
| Avoid accessors | More explicit `const svc = yield* Service`; fewer generated statics |

Treat this as a project-style choice. For a codebase that values concise application services, enabling accessors can be reasonable. For a library or a team that wants all dependencies visually obvious in `Effect.gen`, avoid accessors and yield the service explicitly.

Direct method access also has a documented limitation: it does not work with generic methods.

## When Not To Use It

Prefer `Context.Tag` when:

| Situation | Reason |
|---|---|
| Library API | The library should not ship a default runtime implementation |
| Multiple equal implementations | A single `.Default` would be arbitrary |
| Per-request service | The value is contextual, not a singleton default |
| Experimental risk matters | The v3 source marks `Effect.Service` experimental |

See the decision matrix in [services-layers/04-context-vs-effect-service.md](../services-layers/04-context-vs-effect-service.md).

## Mocking The Service

The generated class has `make`, and the class itself remains the tag.

```typescript
import { Effect } from "effect"

const TestIds = IdGenerator.make({
  next: Effect.succeed("test-id")
})

const testProgram = program.pipe(
  Effect.provideService(IdGenerator, TestIds)
)
```

Use this for narrow tests. Use replacement layers when you want to exercise the real service through fake dependencies.

## Default Layer Caching

For non-parameterized services, v3 caches the generated default layer internally. Accessing `IdGenerator.Default` repeatedly returns the same layer value after the first construction.

Parameterized defaults are different because the function call creates a layer for the supplied arguments.

```typescript
const TenantALive = TenantConfig.Default("tenant-a")
const TenantBLive = TenantConfig.Default("tenant-b")
```

Store parameterized layers in constants and reuse them. If you call `TenantConfig.Default("tenant-a")` in two branches, you have created two layer references.

## Dependencies Are Hidden By Default

When `dependencies` is present, `.Default` uses dependency provision internally. That means dependency outputs are not normally exposed to the final program.

If tests need both the service and one of its dependencies, use `.DefaultWithoutDependencies` plus explicit composition.

```typescript
const TestLive = AppLogger.DefaultWithoutDependencies.pipe(
  Layer.provideMerge(Prefix.Default)
)
```

This keeps `Prefix` visible to the test body while still building `AppLogger`.

Use that pattern only when the dependency is intentionally part of the test surface.

## Cross-references

See also: [services-layers/02-context-tag.md](../services-layers/02-context-tag.md), [services-layers/04-context-vs-effect-service.md](../services-layers/04-context-vs-effect-service.md), [services-layers/07-layer-effect.md](../services-layers/07-layer-effect.md), [services-layers/08-layer-scoped.md](../services-layers/08-layer-scoped.md), [services-layers/17-fresh-vs-memoize.md](../services-layers/17-fresh-vs-memoize.md).
