# Layer Effect
Use `Layer.effect` when constructing a service requires an effect.

## Signature Shape

`Layer.effect(tag, effect)` builds the service by running the effect during layer construction.

```typescript
import { Config, Context, Effect, Layer } from "effect"

class ApiConfig extends Context.Tag("app/ApiConfig")<
  ApiConfig,
  { readonly baseUrl: string }
>() {}

const ApiConfigLive = Layer.effect(
  ApiConfig,
  Effect.gen(function* () {
    const baseUrl = yield* Config.string("API_BASE_URL")
    return { baseUrl }
  })
)
```

The layer's error and input types come from the construction effect.

## Reading Dependencies During Construction

Layer construction can request other services.

```typescript
import { Context, Effect, Layer } from "effect"

class ApiConfig extends Context.Tag("app/ApiConfig")<
  ApiConfig,
  { readonly baseUrl: string }
>() {}

class HttpClient extends Context.Tag("app/HttpClient")<
  HttpClient,
  { readonly get: (url: string) => Effect.Effect<string> }
>() {}

class UsersClient extends Context.Tag("app/UsersClient")<
  UsersClient,
  { readonly getUser: (id: string) => Effect.Effect<string> }
>() {}

const UsersClientLive = Layer.effect(
  UsersClient,
  Effect.gen(function* () {
    const config = yield* ApiConfig
    const http = yield* HttpClient
    return {
      getUser: (id: string) => http.get(`${config.baseUrl}/users/${id}`)
    }
  })
)
```

`UsersClientLive` produces `UsersClient` and requires `ApiConfig | HttpClient`.

## Wiring Dependencies

Provide dependency layers to the service layer.

```typescript
const ApiConfigTest = Layer.succeed(ApiConfig, {
  baseUrl: "https://example.test"
})

const HttpClientTest = Layer.succeed(HttpClient, {
  get: (url) => Effect.succeed(`GET ${url}`)
})

const UsersClientTest = UsersClientLive.pipe(
  Layer.provide(Layer.merge(ApiConfigTest, HttpClientTest))
)
```

Use `Layer.provide` when only `UsersClient` should be visible to the final program. Use `Layer.provideMerge` when tests also need `ApiConfig` or `HttpClient` available.

## Construction Errors

If the construction effect can fail, the layer can fail.

```typescript
import { Config, Context, Layer } from "effect"

class Port extends Context.Tag("app/Port")<
  Port,
  { readonly value: number }
>() {}

const PortLive = Layer.effect(
  Port,
  Config.integer("PORT").pipe(
    Effect.map((value) => ({ value }))
  )
)
```

Do not hide startup failures by converting them to defects unless the failure is unrecoverable and should crash the fiber.

## Service Construction Boundary

Keep construction logic in the layer, not in every service method.

```typescript
const UsersClientLiveFromConfig = Layer.effect(
  UsersClient,
  Effect.gen(function* () {
    const baseUrl = yield* Config.string("USERS_BASE_URL")
    const http = yield* HttpClient
    return {
      getUser: (id: string) => http.get(`${baseUrl}/users/${id}`)
    }
  })
)
```

The config lookup happens once during layer construction. Each method call reuses the constructed service value.

## Keep Requirements Honest

If construction reads `Config` or another service, that requirement belongs in the layer type. Do not work around it with global variables or unchecked casts.

| Construction need | Correct expression |
|---|---|
| Read application config | `Config.string` inside `Layer.effect` |
| Allocate mutable state | `Ref.make` inside `Layer.effect` |
| Read another service | `yield* OtherService` inside the constructor |
| Acquire and release resource | `Layer.scoped` instead |

## Combine After Construction

When an effectful layer has dependencies, build its supporting layers separately and compose them.

```typescript
const UsersClientReady = UsersClientLiveFromConfig.pipe(
  Layer.provideMerge(HttpClientTest)
)
```

Use `provideMerge` when the test or app also needs `HttpClientTest` visible.

## Cross-references

See also: [services-layers/06-layer-succeed.md](../services-layers/06-layer-succeed.md), [services-layers/08-layer-scoped.md](../services-layers/08-layer-scoped.md), [services-layers/10-layer-provide.md](../services-layers/10-layer-provide.md), [services-layers/11-layer-providemerge.md](../services-layers/11-layer-providemerge.md).
