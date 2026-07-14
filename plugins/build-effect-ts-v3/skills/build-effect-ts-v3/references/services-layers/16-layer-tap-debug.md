# Layer Tap Debug
Use `Layer.tap`, `Layer.tapError`, and type inspection to debug layer construction without changing the service graph.

## Tap Success

`Layer.tap` runs an effect after successful layer construction. The layer output stays the same.

```typescript
import { Context, Effect, Layer } from "effect"

class Database extends Context.Tag("app/Database")<
  Database,
  {
    readonly query: (sql: string) => Effect.Effect<string>
  }
>() {}

const DatabaseLive = Layer.succeed(Database, {
  query: (sql) => Effect.succeed(`result for ${sql}`)
}).pipe(
  Layer.tap(() => Effect.logInfo("database layer ready"))
)
```

Use this for startup logs and smoke checks.

## Tap Failure

`Layer.tapError` runs when construction fails.

```typescript
import { Config, Effect, Layer } from "effect"

const DatabaseFromConfig = Layer.effect(
  Database,
  Config.string("DATABASE_URL").pipe(
    Effect.map((url) => ({
      query: (sql: string) => Effect.succeed(`${url}:${sql}`)
    }))
  )
).pipe(
  Layer.tapError((error) =>
    Effect.logError("database layer failed", { error })
  )
)
```

This does not recover. It only observes. Use `Layer.catchAll` when you intentionally want recovery.

## Debug Missing Services

For missing-service type errors, inspect the types:

```typescript
const TestLive = MyServiceLive.pipe(
  Layer.provide(SomeServiceLive)
)
```

Ask:

1. What does `program` require?
2. What does `TestLive` produce?
3. Did `Layer.provide` hide a service the program still yields?

If yes, use `Layer.provideMerge`.

## Tap Is Not Composition

Do not use `tap` to smuggle dependencies. It is for observation.

```typescript
const Observed = MyServiceLive.pipe(
  Layer.tap(() => Effect.logInfo("built"))
)
```

If `MyServiceLive` requires `SomeService`, `Observed` still requires `SomeService`.

## Practical Checklist

| Symptom | Check |
|---|---|
| Construction never logs | Layer is not provided or runtime not started |
| Service remains in `R` | Layer does not produce it, or `provide` hid it |
| Startup failure hidden | Use `tapError` or `runPromiseExit` at the edge |
| Duplicate initialization | Check inline layer constructors and memoization |

## Tap Context Carefully

The success callback receives a `Context.Context` for the layer output. Use it for diagnostics, not for building another service.

```typescript
const ObservedDatabase = DatabaseLive.pipe(
  Layer.tap((context) =>
    Effect.logInfo("database context ready", {
      hasDatabase: Context.get(context, Database) !== undefined
    })
  )
)
```

If a diagnostic needs another service, that service becomes a requirement of the tapped layer. That is valid, but it should be intentional.

## Prefer Type Debugging First

For missing-service errors, logging may never run because the program does not type-check. Inspect the layer type before adding runtime diagnostics.

```typescript
const Live = MyServiceLive.pipe(
  Layer.provide(SomeServiceLive)
)
```

If `SomeService` is needed by the final program, no amount of tapping fixes the hidden output. Change the combinator.

## Startup Smoke Check

At an application edge, `Layer.tap` can prove the graph constructed successfully.

```typescript
const AppLive = Layer.merge(DatabaseLive, LoggerLive).pipe(
  Layer.tap(() => Effect.logInfo("app layer ready"))
)
```

Keep smoke checks cheap. Expensive checks should be explicit health-check programs, not hidden startup side effects.

## Cross-references

See also: [services-layers/12-layer-composition-gotchas.md](../services-layers/12-layer-composition-gotchas.md), [services-layers/13-layer-memoization.md](../services-layers/13-layer-memoization.md), [services-layers/14-managed-runtime.md](../services-layers/14-managed-runtime.md), [services-layers/17-fresh-vs-memoize.md](../services-layers/17-fresh-vs-memoize.md).
