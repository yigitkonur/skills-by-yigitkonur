# Platform Router
Use `HttpRouter` as the low-level alternative when a route should not be modeled as a typed `HttpApi` endpoint.

## When To Use `HttpRouter`

Prefer `HttpApi` for application APIs. Reach for `HttpRouter` when the route is:

- a raw health check outside OpenAPI
- a static file or asset route
- a proxy or webhook with intentionally loose shape
- framework interop
- a low-level route needing direct `HttpServerRequest`

`HttpRouter` is still Effect-native, but it does not give typed client
derivation from `HttpApi`.

## Router Service

`HttpRouter.Tag` creates a router service with route registration methods.
`HttpApiBuilder.Router` is the router used by the API builder, but you can
define your own router tag for low-level apps.

```typescript
import { HttpRouter, HttpServerResponse } from "@effect/platform"
import { Effect } from "effect"

class AppRouter extends HttpRouter.Tag("AppRouter")<AppRouter>() {}

const HealthLive = AppRouter.use((router) =>
  router.get("/healthz", Effect.succeed(HttpServerResponse.empty()))
)
```

The route handler returns a respondable value such as `HttpServerResponse`.

## Route Methods

The router service supports common HTTP methods:

| Method | Registration |
|---|---|
| any method | `router.all(path, handler)` |
| `GET` | `router.get(path, handler)` |
| `POST` | `router.post(path, handler)` |
| `PUT` | `router.put(path, handler)` |
| `PATCH` | `router.patch(path, handler)` |
| `DELETE` | `router.del(path, handler)` |
| `HEAD` | `router.head(path, handler)` |
| `OPTIONS` | `router.options(path, handler)` |

Use `HttpApiEndpoint` for typed application endpoints; use these for lower
level routes.

## Path Parameters

Use `HttpRouter.params` or `RouteContext` for path params.

```typescript
import { HttpRouter, HttpServerResponse } from "@effect/platform"
import { Effect } from "effect"

const RouteLive = AppRouter.use((router) =>
  router.get("/files/:id", Effect.gen(function*() {
    const params = yield* HttpRouter.params
    return HttpServerResponse.text(params.id ?? "missing")
  }))
)
```

For schema-decoded path parameters, prefer `HttpApi` unless this route is truly
low-level.

## Serving A Router

`HttpRouter.Tag` includes a `serve` helper.

```typescript
import { HttpMiddleware, HttpServer } from "@effect/platform"
import { NodeHttpServer, NodeRuntime } from "@effect/platform-node"
import { Layer } from "effect"
import { createServer } from "node:http"

const AppLive = AppRouter.serve(HttpMiddleware.logger).pipe(
  Layer.provide(HealthLive),
  HttpServer.withLogAddress,
  Layer.provide(NodeHttpServer.layer(createServer, { port: 3000 }))
)

Layer.launch(AppLive).pipe(NodeRuntime.runMain)
```

This is useful for small low-level servers or adapters.

## Mixing With `HttpApi`

`HttpApiSwagger.layer` and `HttpApiBuilder.middlewareOpenApi` add routes by
using the API builder router. Keep low-level router additions close to serving
assembly so it is clear which routes are outside the typed contract.

For typed endpoints, add an `HttpApiGroup`. For raw routes, mount or concatenate
routers with the low-level APIs.

## Mounting Apps

`HttpRouter` can mount another router or an `HttpApp`.

```typescript
import { HttpRouter } from "@effect/platform"

const MountLive = AppRouter.use((router) =>
  router.mount("/internal", internalRouter)
)
```

Use mounting for admin surfaces, static assets, or embedded tools that should
not be part of the typed public API.

## Request Schema Helpers

For low-level routes that still need validation, decode with router schema
helpers.

```typescript
import { HttpRouter, HttpServerResponse } from "@effect/platform"
import { Effect, Schema } from "effect"

const Params = Schema.Struct({
  id: Schema.NumberFromString
})

const RouteLive = AppRouter.use((router) =>
  router.get("/items/:id", Effect.gen(function*() {
    const params = yield* HttpRouter.schemaPathParams(Params)
    return HttpServerResponse.text(String(params.id))
  }))
)
```

This is a lower-level escape hatch. If the route belongs to your API contract,
use `HttpApiEndpoint` instead.

## Schema Helpers

`HttpRouter` exposes schema helpers for low-level decoding:

- `HttpRouter.schemaJson`
- `HttpRouter.schemaNoBody`
- `HttpRouter.schemaParams`
- `HttpRouter.schemaPathParams`

These are useful when `HttpApi` is too structured for a route but schema
validation is still desirable.

## Default Services

Router serving requires platform services such as `HttpPlatform`, `FileSystem`,
`Etag.Generator`, and `Path`. `NodeHttpServer.layer` provides the Node
platform context for normal servers.

When using low-level routers in tests, prefer `NodeHttpServer.layerTest` for the
same reason as `HttpApi`: it gives an ephemeral server and test client wiring.

## Cross-references

See also: [01-overview.md](01-overview.md), [15-serving.md](15-serving.md), [03-path-params.md](03-path-params.md), [13-streaming-responses.md](13-streaming-responses.md)
