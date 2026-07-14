# Swagger
Add Swagger UI with `HttpApiSwagger.layer`; the default documentation URL is `/docs`.

## Default Route

`HttpApiSwagger.layer()` mounts Swagger UI at `/docs`.

```typescript
import { HttpApiBuilder, HttpApiSwagger } from "@effect/platform"
import { Layer } from "effect"

const ServerLive = HttpApiBuilder.serve().pipe(
  Layer.provide(HttpApiSwagger.layer()),
  Layer.provide(ApiLive)
)
```

The `/docs` URL convention is the default in Effect v3 and should be documented
for teams using the generated server.

## Custom Docs Path

```typescript
import { HttpApiSwagger } from "@effect/platform"

const SwaggerLive = HttpApiSwagger.layer({
  path: "/internal/docs"
})
```

Use a custom path when the deployment platform reserves `/docs` or when docs
are internal-only.

## Complete Server With Swagger

```typescript
import {
  HttpApiBuilder,
  HttpApiSwagger,
  HttpMiddleware,
  HttpServer
} from "@effect/platform"
import { NodeHttpServer, NodeRuntime } from "@effect/platform-node"
import { Layer } from "effect"
import { createServer } from "node:http"

const ServerLive = HttpApiBuilder.serve(HttpMiddleware.logger).pipe(
  Layer.provide(HttpApiSwagger.layer()),
  Layer.provide(ApiLive),
  HttpServer.withLogAddress,
  Layer.provide(NodeHttpServer.layer(createServer, { port: 3000 }))
)

Layer.launch(ServerLive).pipe(NodeRuntime.runMain)
```

Opening `http://localhost:3000/docs` shows the generated UI.

## Where The Spec Comes From

Swagger is generated from the `HttpApi`:

- API identifier and annotations
- group identifiers and annotations
- endpoint method and path
- request path, query, payload, and headers schemas
- success and error schemas
- security middleware metadata

Do not maintain a separate OpenAPI file for the same routes unless a downstream
system explicitly requires a checked-in artifact.

## OpenAPI Annotations

Use `OpenApi` annotations on APIs, groups, endpoints, and schemas to improve
generated docs without changing runtime behavior.

```typescript
import { HttpApiEndpoint, OpenApi } from "@effect/platform"
import { Schema } from "effect"

const listUsers = HttpApiEndpoint.get("listUsers", "/users")
  .addSuccess(Schema.Array(Schema.String))
  .annotate(OpenApi.Summary, "List users")
  .annotate(OpenApi.Description, "Returns users visible to the caller.")
```

Use annotations for descriptions, summaries, deprecation, and transformation of
the generated document.

## JSON Spec Endpoint

Swagger UI is not the only documentation output. Add `/openapi.json` with
`HttpApiBuilder.middlewareOpenApi`.

```typescript
import { HttpApiBuilder } from "@effect/platform"
import { Layer } from "effect"

const ServerLive = HttpApiBuilder.serve().pipe(
  Layer.provide(HttpApiBuilder.middlewareOpenApi({
    path: "/openapi.json"
  })),
  Layer.provide(HttpApiSwagger.layer()),
  Layer.provide(ApiLive)
)
```

Use this when clients, gateways, or contract tests need the raw OpenAPI JSON.

## Security In Swagger

When auth is modeled with `HttpApiSecurity` and `HttpApiMiddleware.Tag`, the
security scheme is available to OpenAPI generation.

```typescript
import { HttpApiMiddleware, HttpApiSecurity } from "@effect/platform"

class Auth extends HttpApiMiddleware.Tag<Auth>()("Auth", {
  security: {
    apiKey: HttpApiSecurity.apiKey({
      in: "header",
      key: "x-api-key"
    })
  }
}) {}
```

This is better than manually documenting an `x-api-key` header with prose.

## Deployment Notes

Swagger UI is usually enabled in local, staging, and internal environments. For
public production APIs, decide whether `/docs` is internet-accessible or
protected by upstream infrastructure.

The route is just another layer contribution. If an environment should not
serve docs, do not provide `HttpApiSwagger.layer()` in that environment's server
composition.

## Contract Drift Check

Because Swagger is generated from `HttpApi`, missing or inaccurate docs usually
mean the endpoint schema is incomplete. Fix the endpoint declaration first:

- add `setHeaders` instead of documenting headers manually
- add `setUrlParams` instead of describing query strings in text
- add `addError` for expected failure responses
- add schema annotations for descriptions and examples

## Cross-references

See also: [15-serving.md](15-serving.md), [09-middleware.md](09-middleware.md), [02-defining-endpoints.md](02-defining-endpoints.md), [10-cors-and-logger.md](10-cors-and-logger.md)
