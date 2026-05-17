# Layer Scoped
Use `Layer.scoped` when service construction acquires a resource that must be released.

## Resource Lifecycle

`Layer.scoped` takes a scoped effect and removes `Scope.Scope` from the layer requirement.

```typescript
import { Context, Effect, Layer } from "effect"

class Connection extends Context.Tag("app/Connection")<
  Connection,
  {
    readonly query: (sql: string) => Effect.Effect<string>
  }
>() {}

const ConnectionLive = Layer.scoped(
  Connection,
  Effect.acquireRelease(
    Effect.logInfo("opening connection").pipe(
      Effect.as({
        query: (sql: string) => Effect.succeed(`result for ${sql}`)
      })
    ),
    () => Effect.logInfo("closing connection")
  )
)
```

The resource stays alive for the lifetime of the provided layer.

## Add Finalizers When Needed

Scoped construction can register additional finalizers.

```typescript
import { Effect, Layer } from "effect"

const ConnectionWithHeartbeat = Layer.scoped(
  Connection,
  Effect.gen(function* () {
    const connection = yield* Effect.acquireRelease(
      Effect.logInfo("connect").pipe(
        Effect.as({
          query: (sql: string) => Effect.succeed(`result for ${sql}`)
        })
      ),
      () => Effect.logInfo("disconnect")
    )

    yield* Effect.addFinalizer(() => Effect.logInfo("heartbeat stopped"))

    return connection
  })
)
```

Finalizers run when the layer scope closes.

## Use Cases

| Use case | Why scoped |
|---|---|
| Database pool | Needs close/drain |
| HTTP server | Needs shutdown |
| File watcher | Needs interruption |
| Subscription client | Needs unsubscribe |
| Managed runtime integration | Runtime disposal closes layers |

## Do Not Use Scoped For Pure Values

If there is no acquisition and release, use `Layer.succeed` or `Layer.effect`. Scoped layers are for lifecycle.

## Testing Scoped Services

A test can provide a scoped fake when it needs temporary state.

```typescript
import { Effect, Layer, Ref } from "effect"

const ConnectionTest = Layer.scoped(
  Connection,
  Effect.gen(function* () {
    const queries = yield* Ref.make<Array<string>>([])
    return {
      query: (sql: string) =>
        Ref.update(queries, (all) => [...all, sql]).pipe(
          Effect.as(`test result for ${sql}`)
        )
    }
  })
)
```

If the test body also needs to read the fake's supporting services, use `Layer.provideMerge` while composing.

## Scope Lifetime

The resource lives as long as the layer scope lives.

| Provision site | Resource lifetime |
|---|---|
| Program edge with `Effect.provide` | Until the provided effect completes |
| `ManagedRuntime.make` | Until runtime disposal |
| `Layer.launch` | Until launched fiber interruption |
| Local provision in a small effect | Only for that local effect |

This is why framework integrations should dispose their managed runtime on server shutdown.

## Failure During Acquire

If acquisition fails, release finalizers registered after the failed acquisition do not run because the resource was not acquired. Put cleanup in `Effect.acquireRelease` so the release action belongs to the acquisition it protects.

```typescript
const SafeConnectionLive = Layer.scoped(
  Connection,
  Effect.acquireRelease(
    Effect.logInfo("acquire").pipe(
      Effect.as({ query: (sql: string) => Effect.succeed(sql) })
    ),
    () => Effect.logInfo("release")
  )
)
```

## Do Not Run Scoped Services Manually

Avoid manually acquiring resources inside ordinary service methods. Put lifecycle at the layer boundary so Effect can interrupt and finalize correctly.

## Scoped Dependencies

A scoped layer can still depend on other services.

```typescript
const ConnectionFromConfig = Layer.scoped(
  Connection,
  Effect.gen(function* () {
    const config = yield* ConfigService
    return yield* Effect.acquireRelease(
      Effect.succeed({ query: (sql: string) => Effect.succeed(`${config.value}:${sql}`) }),
      () => Effect.logInfo("connection released")
    )
  })
)
```

Compose those dependencies with `Layer.provide` or `Layer.provideMerge` like any other layer.

## Cross-references

See also: [services-layers/07-layer-effect.md](../services-layers/07-layer-effect.md), [services-layers/13-layer-memoization.md](../services-layers/13-layer-memoization.md), [services-layers/14-managed-runtime.md](../services-layers/14-managed-runtime.md), [services-layers/17-fresh-vs-memoize.md](../services-layers/17-fresh-vs-memoize.md).
