# CORS And Logger
Use platform HTTP middleware at serve time for cross-cutting request and response behavior.

## Logger Middleware

`HttpMiddleware.logger` is passed to `HttpApiBuilder.serve`.

```typescript
import { HttpApiBuilder, HttpMiddleware } from "@effect/platform"

const ServerLive = HttpApiBuilder.serve(HttpMiddleware.logger)
```

This applies to the generated `HttpApp` before it is served.

## CORS Layer

`HttpApiBuilder.middlewareCors` is a layer provided to the server assembly.

```typescript
import { HttpApiBuilder } from "@effect/platform"
import { Layer } from "effect"

const ServerLive = HttpApiBuilder.serve().pipe(
  Layer.provide(HttpApiBuilder.middlewareCors())
)
```

The CORS layer registers middleware in the API builder middleware service.

## CORS Options

```typescript
import { HttpApiBuilder } from "@effect/platform"

const CorsLive = HttpApiBuilder.middlewareCors({
  allowedOrigins: ["https://app.example.com"],
  allowedMethods: ["GET", "POST", "PATCH", "DELETE"],
  allowedHeaders: ["authorization", "content-type", "x-request-id"],
  exposedHeaders: ["x-request-id"],
  credentials: true,
  maxAge: 86_400
})
```

Keep header names lowercase in CORS options too. That matches the rest of the
HTTP contract and avoids case drift.

## Combined Server

```typescript
import {
  HttpApiBuilder,
  HttpMiddleware,
  HttpServer
} from "@effect/platform"
import { NodeHttpServer, NodeRuntime } from "@effect/platform-node"
import { Layer } from "effect"
import { createServer } from "node:http"

const ServerLive = HttpApiBuilder.serve(HttpMiddleware.logger).pipe(
  Layer.provide(HttpApiBuilder.middlewareCors({
    allowedOrigins: ["https://app.example.com"],
    allowedHeaders: ["authorization", "content-type", "x-request-id"]
  })),
  Layer.provide(ApiLive),
  HttpServer.withLogAddress,
  Layer.provide(NodeHttpServer.layer(createServer, { port: 3000 }))
)

Layer.launch(ServerLive).pipe(NodeRuntime.runMain)
```

Use one serve layer and provide middleware layers into it.

## API Middleware vs HTTP Middleware

| Need | Use |
|---|---|
| Decode auth and provide `CurrentUser` | `HttpApiMiddleware.Tag` |
| Add CORS headers | `HttpApiBuilder.middlewareCors` |
| Log requests | `HttpMiddleware.logger` |
| Wrap all generated routes | `HttpApiBuilder.middleware` |
| One endpoint authorization rule | endpoint `.middleware(...)` |

Do not use API middleware for generic response decoration unless it needs typed
errors or service provision.

## OpenAPI JSON Middleware

`HttpApiBuilder.middlewareOpenApi` adds an `openapi.json` endpoint.

```typescript
import { HttpApiBuilder } from "@effect/platform"

const OpenApiJsonLive = HttpApiBuilder.middlewareOpenApi({
  path: "/openapi.json"
})
```

Use this alongside or instead of Swagger UI when another system consumes the
OpenAPI document.

## Environment-Specific CORS

Use ordinary Effect configuration to choose CORS options at the edge. Keep the
API contract independent of deployment origin policy.

```typescript
import { Config, Effect, Layer } from "effect"

const CorsLive = Layer.unwrapEffect(
  Effect.map(Config.string("APP_ORIGIN"), (origin) =>
    HttpApiBuilder.middlewareCors({
      allowedOrigins: [origin],
      allowedHeaders: ["authorization", "content-type", "x-request-id"],
      credentials: true
    })
  )
)
```

Do not read process variables directly in server modules. Use `Config` so tests,
deployments, and local runs use the same dependency model.

## Disable Logging By Composition

When a test or embedding runtime does not want request logs, omit
`HttpMiddleware.logger`.

```typescript
const TestServerLive = HttpApiBuilder.serve().pipe(
  Layer.provide(ApiLive),
  Layer.provideMerge(NodeHttpServer.layerTest)
)
```

Logging is an edge concern, not part of the endpoint declaration.

## Cross-references

See also: [09-middleware.md](09-middleware.md), [11-swagger.md](11-swagger.md), [15-serving.md](15-serving.md), [05-headers.md](05-headers.md)
