# Serving
Serve an `HttpApi` by combining API, handler, middleware, Swagger, and platform server layers.

## Required Pieces

A running HTTP API needs:

| Piece | Typical value |
|---|---|
| API contract | `HttpApiBuilder.api(Api)` |
| group handlers | `HttpApiBuilder.group(Api, "group", ...)` |
| generated app server | `HttpApiBuilder.serve(...)` |
| optional docs | `HttpApiSwagger.layer()` |
| optional CORS | `HttpApiBuilder.middlewareCors()` |
| Node server | `NodeHttpServer.layer(createServer, { port })` |
| process edge | `Layer.launch(ServerLive).pipe(NodeRuntime.runMain)` |

## Complete Invocation

This is the complete shape expected for a Node server.

```typescript
import {
  HttpApi,
  HttpApiBuilder,
  HttpApiEndpoint,
  HttpApiGroup,
  HttpApiSwagger,
  HttpMiddleware,
  HttpServer
} from "@effect/platform"
import { NodeHttpServer, NodeRuntime } from "@effect/platform-node"
import { Effect, Layer, Schema } from "effect"
import { createServer } from "node:http"

class User extends Schema.Class<User>("User")({
  id: Schema.Int,
  name: Schema.String
}) {}

const users = HttpApiGroup.make("users").add(
  HttpApiEndpoint.get("listUsers", "/users")
    .addSuccess(Schema.Array(User))
)

class Api extends HttpApi.make("api").add(users) {}

const UsersLive = HttpApiBuilder.group(Api, "users", (handlers) =>
  handlers.handle("listUsers", () =>
    Effect.succeed([new User({ id: 1, name: "Ada" })])
  )
)

const ApiLive = HttpApiBuilder.api(Api).pipe(
  Layer.provide(UsersLive)
)

const ServerLive = HttpApiBuilder.serve(HttpMiddleware.logger).pipe(
  Layer.provide(HttpApiSwagger.layer()),
  Layer.provide(HttpApiBuilder.middlewareCors()),
  Layer.provide(ApiLive),
  HttpServer.withLogAddress,
  Layer.provide(NodeHttpServer.layer(createServer, { port: 3000 }))
)

Layer.launch(ServerLive).pipe(NodeRuntime.runMain)
```

The final line is intentionally complete:
`Layer.launch(ServerLive).pipe(NodeRuntime.runMain)`.

## Layer Direction

`HttpApiBuilder.serve` requires an `HttpServer`, router default services, and
`HttpApi.Api`. Provide the API and platform layers into the serve layer.

```typescript
const ServerLive = HttpApiBuilder.serve().pipe(
  Layer.provide(ApiLive),
  Layer.provide(NodeHttpServer.layer(createServer, { port: 3000 }))
)
```

Do not run handlers directly. The builder assembles route decoding,
middleware, error encoding, and response encoding.

## Logging Address

`HttpServer.withLogAddress` logs the bound address after the server starts.

```typescript
const ServerLive = HttpApiBuilder.serve().pipe(
  Layer.provide(ApiLive),
  HttpServer.withLogAddress,
  Layer.provide(NodeHttpServer.layer(createServer, { port: 3000 }))
)
```

Use it in application entry points. Omit it in tests that assert logs.

## Test Server

Use `NodeHttpServer.layerTest` for tests. It binds an ephemeral port and
provides a test client layer.

```typescript
import { NodeHttpServer } from "@effect/platform-node"
import { Layer } from "effect"

const HttpLive = HttpApiBuilder.serve().pipe(
  Layer.provide(ApiLive),
  Layer.provideMerge(NodeHttpServer.layerTest)
)
```

This avoids hard-coded test ports.

## Configured Port

Use `Config` for deployment-supplied ports instead of reading process variables
directly.

```typescript
import { Config, Effect, Layer } from "effect"
import { createServer } from "node:http"

const NodeServerLive = Layer.unwrapEffect(
  Effect.map(Config.integer("PORT"), (port) =>
    NodeHttpServer.layer(createServer, { port })
  )
)

const ServerLive = HttpApiBuilder.serve(HttpMiddleware.logger).pipe(
  Layer.provide(ApiLive),
  HttpServer.withLogAddress,
  Layer.provide(NodeServerLive)
)
```

This keeps configuration in the Effect environment and makes tests easier to
override.

## Middleware Order

Provide middleware layers before or around the API layer as ordinary layers.
The builder collects API middleware and applies the `serve` HTTP middleware to
the generated app.

```typescript
const ServerLive = HttpApiBuilder.serve(HttpMiddleware.logger).pipe(
  Layer.provide(HttpApiBuilder.middlewareCors()),
  Layer.provide(ApiLive),
  Layer.provide(NodeHttpServer.layer(createServer, { port: 3000 }))
)
```

Keep all serving concerns in the entry point so libraries stay runtime-neutral.

## Library Boundary

Export `Api`, group layers, and `ApiLive` from library modules. Put
`Layer.launch(ServerLive).pipe(NodeRuntime.runMain)` only in executable entry
points.

```typescript
export { Api, ApiLive }
```

That separation lets tests provide `NodeHttpServer.layerTest` and production
provide a real `NodeHttpServer.layer` without changing route code.

## Cross-references

See also: [01-overview.md](01-overview.md), [07-handlers.md](07-handlers.md), [10-cors-and-logger.md](10-cors-and-logger.md), [11-swagger.md](11-swagger.md)
