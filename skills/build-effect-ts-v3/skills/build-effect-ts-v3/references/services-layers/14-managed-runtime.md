# Managed Runtime
Use `ManagedRuntime` at framework edges that need to run Effect programs without making the framework itself Effect-native.

## What It Does

`ManagedRuntime.make(layer)` converts a fully resolved layer into a runtime object. The v3 source exposes `runPromise`, `runSync`, `runFork`, `runPromiseExit`, `dispose`, and `disposeEffect`.

The layer passed to `ManagedRuntime.make` must require `never`.

```typescript
import { Context, Effect, Layer, ManagedRuntime } from "effect"

class GreetingService extends Context.Tag("app/GreetingService")<
  GreetingService,
  { readonly greet: (name: string) => Effect.Effect<string> }
>() {}

const GreetingLive = Layer.succeed(GreetingService, {
  greet: (name) => Effect.succeed(`hello ${name}`)
})

const runtime = ManagedRuntime.make(GreetingLive)

const greet = (name: string) =>
  Effect.gen(function* () {
    const greetings = yield* GreetingService
    return yield* greetings.greet(name)
  })
```

Use runtime runners only at edges.

## Complete Hono Integration

This pattern keeps request handlers small and keeps services in Effect.

```typescript
import { serve } from "@hono/node-server"
import { Hono } from "hono"
import { Context, Effect, Layer, ManagedRuntime } from "effect"

class UserRepository extends Context.Tag("app/UserRepository")<
  UserRepository,
  {
    readonly findById: (
      id: string
    ) => Effect.Effect<{ readonly id: string; readonly name: string }>
  }
>() {}

const UserRepositoryLive = Layer.succeed(UserRepository, {
  findById: (id) => Effect.succeed({ id, name: "Ada Lovelace" })
})

class AppLogger extends Context.Tag("app/AppLogger")<
  AppLogger,
  {
    readonly info: (message: string) => Effect.Effect<void>
  }
>() {}

const AppLoggerLive = Layer.succeed(AppLogger, {
  info: (message) => Effect.logInfo(message)
})

const AppLive = Layer.merge(UserRepositoryLive, AppLoggerLive)
const runtime = ManagedRuntime.make(AppLive)

const getUser = (id: string) =>
  Effect.gen(function* () {
    const logger = yield* AppLogger
    const users = yield* UserRepository
    yield* logger.info(`loading user ${id}`)
    return yield* users.findById(id)
  })

export const app = new Hono()

app.get("/users/:id", async (c) => {
  const id = c.req.param("id")
  const user = await runtime.runPromise(getUser(id))
  return c.json(user)
})

app.onError(async (error, c) => {
  await runtime.runPromise(
    Effect.logError("request failed", { message: error.message })
  )
  return c.json({ error: "internal error" }, 500)
})

const server = serve({
  fetch: app.fetch,
  port: 3000
})

export const shutdown = async () => {
  await runtime.dispose()
  server.close()
}

process.once("SIGINT", shutdown)
process.once("SIGTERM", shutdown)
```

The Hono handler converts HTTP input to an Effect program, runs it through the managed runtime, and converts the result back to an HTTP response.

## Disposal

Call `runtime.dispose()` when the host framework shuts down. For scoped layers, disposal releases the resources acquired by the layer graph.

If your platform offers shutdown hooks, wire them to `shutdown`. Keep disposal at the process or server edge, not inside request handlers.

## Error Boundary

Choose how framework errors are represented:

| Approach | Use when |
|---|---|
| `runPromise` | Framework already has promise error handling |
| `runPromiseExit` | You need to map typed failures and defects separately |
| Effect-level error mapping | You want domain errors converted before leaving Effect |

For HTTP APIs, prefer mapping expected domain failures inside the Effect program and reserve framework error handlers for defects or unexpected exceptions.

## Runtime Ownership

Create one managed runtime for the framework application, not one per request.

| Pattern | Result |
|---|---|
| Runtime at module or server startup | Shared layer graph, predictable disposal |
| Runtime inside each handler | Repeated acquisition and slower requests |
| Runtime disposed on shutdown | Scoped resources release correctly |
| Runtime never disposed | Long-lived resources can leak |

If your app has multiple independent Hono apps, each can own its own runtime, but each runtime should have a clear shutdown path.

## Mapping Domain Failures

Keep expected HTTP mapping in Effect code when possible.

```typescript
const getUserResponse = (id: string) =>
  getUser(id).pipe(
    Effect.map((user) => ({ status: 200 as const, body: user }))
  )
```

The Hono handler can then stay a thin adapter from request to effect and from effect result to response.

## Requirements Must Be Closed

If `ManagedRuntime.make(AppLive)` fails to type-check because `AppLive` still has requirements, fix the layer graph. Do not create a runtime from an incomplete layer.

Common causes are hidden provider outputs, missing config layers, or parameterized layer constructors called in only one branch.

## Request Cancellation

`runtime.runPromise` accepts an optional `AbortSignal`. Frameworks that expose request cancellation can pass that signal to interrupt the underlying Effect.

```typescript
const user = await runtime.runPromise(
  getUser(id),
  { signal: c.req.raw.signal }
)
```

Use this when the platform provides a real request signal. It prevents abandoned requests from continuing expensive work.

## Do Not Hide Runtime Globally

Exporting a module-level runtime is fine for a small app, but large systems should keep ownership explicit:

| Location | Use |
|---|---|
| `runtime.ts` | Builds and exports runtime plus shutdown |
| HTTP adapter | Imports runtime and runs request effects |
| Tests | Build a separate runtime with test layers |

This keeps disposal and test replacement visible.

## Cross-references

See also: [services-layers/08-layer-scoped.md](../services-layers/08-layer-scoped.md), [services-layers/13-layer-memoization.md](../services-layers/13-layer-memoization.md), [services-layers/15-effect-provide.md](../services-layers/15-effect-provide.md), [services-layers/16-layer-tap-debug.md](../services-layers/16-layer-tap-debug.md).
