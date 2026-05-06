# Middleware
Use `HttpApiMiddleware.Tag` for typed API middleware and security middleware that can provide services to handlers.

## Middleware Tag Shape

An HTTP API middleware is a context tag with optional failure and optional
provided service.

```typescript
import { HttpApiMiddleware } from "@effect/platform"
import { Context, Schema } from "effect"

class CurrentUser extends Context.Tag("CurrentUser")<
  CurrentUser,
  { readonly id: number; readonly name: string }
>() {}

class Unauthorized extends Schema.TaggedError<Unauthorized>()(
  "Unauthorized",
  {}
) {}

class Auth extends HttpApiMiddleware.Tag<Auth>()("Auth", {
  failure: Unauthorized,
  provides: CurrentUser
}) {}
```

Attach the tag to an API, group, or endpoint with `.middleware(Auth)`.

## Complete Auth Middleware Example

This example declares bearer-token auth, decodes the token, provides
`CurrentUser`, attaches the middleware to a group, implements handlers, and
serves the API.

```typescript
import {
  HttpApi,
  HttpApiBuilder,
  HttpApiEndpoint,
  HttpApiGroup,
  HttpApiMiddleware,
  HttpApiSchema,
  HttpApiSecurity,
  HttpApiSwagger,
  HttpMiddleware,
  HttpServer
} from "@effect/platform"
import { NodeHttpServer, NodeRuntime } from "@effect/platform-node"
import { Context, Effect, Layer, Redacted, Schema } from "effect"
import { createServer } from "node:http"

class User extends Schema.Class<User>("User")({
  id: Schema.Int,
  name: Schema.String
}) {}

class Unauthorized extends Schema.TaggedError<Unauthorized>()(
  "Unauthorized",
  { message: Schema.String },
  HttpApiSchema.annotations({ status: 401 })
) {}

class CurrentUser extends Context.Tag("CurrentUser")<CurrentUser, User>() {}

class Auth extends HttpApiMiddleware.Tag<Auth>()("Auth", {
  security: {
    bearer: HttpApiSecurity.bearer
  },
  failure: Unauthorized,
  provides: CurrentUser
}) {}

const users = HttpApiGroup.make("users")
  .add(
    HttpApiEndpoint.get("me", "/users/me")
      .addSuccess(User)
  )
  .middleware(Auth)

class Api extends HttpApi.make("api").add(users) {}

const AuthLive = Layer.succeed(
  Auth,
  Auth.of({
    bearer: (token) =>
      Redacted.value(token) === "secret"
        ? Effect.succeed(new User({ id: 1, name: "Ada" }))
        : Effect.fail(new Unauthorized({ message: "Invalid token" }))
  })
)

const UsersLive = HttpApiBuilder.group(Api, "users", (handlers) =>
  handlers.handle("me", () =>
    CurrentUser
  )
)

const ApiLive = HttpApiBuilder.api(Api).pipe(
  Layer.provide(UsersLive),
  Layer.provide(AuthLive)
)

const ServerLive = HttpApiBuilder.serve(HttpMiddleware.logger).pipe(
  Layer.provide(HttpApiSwagger.layer()),
  Layer.provide(ApiLive),
  HttpServer.withLogAddress,
  Layer.provide(NodeHttpServer.layer(createServer, { port: 3000 }))
)

Layer.launch(ServerLive).pipe(NodeRuntime.runMain)
```

The handler does not parse the `authorization` header. The security middleware
handles decoding and provides `CurrentUser`.

Notice that `CurrentUser` is read inside the request handler. Middleware-provided
services are per-request context, not services to read once while constructing
the group layer.

## Security Schemes

`HttpApiSecurity` supports:

| Constructor | Source |
|---|---|
| `HttpApiSecurity.bearer` | `authorization: Bearer ...` |
| `HttpApiSecurity.basic` | `authorization: Basic ...` |
| `HttpApiSecurity.apiKey({ in: "header", key })` | header |
| `HttpApiSecurity.apiKey({ in: "query", key })` | query parameter |
| `HttpApiSecurity.apiKey({ in: "cookie", key })` | cookie |

For header API keys, use lowercase keys.

```typescript
const apiKey = HttpApiSecurity.apiKey({
  in: "header",
  key: "x-api-key"
})
```

## Optional Middleware

Middleware can be optional. Optional middleware failure skips the provided
service instead of failing the request.

```typescript
class OptionalUser extends HttpApiMiddleware.Tag<OptionalUser>()("OptionalUser", {
  optional: true,
  provides: CurrentUser
}) {}
```

Use optional middleware for enrichment, not required authorization.

## Non-Security Middleware

Non-security middleware can run any effect and optionally provide a service.

```typescript
import { HttpApiMiddleware } from "@effect/platform"
import { Context, Effect } from "effect"

class RequestId extends Context.Tag("RequestId")<RequestId, string>() {}

class RequestIdMiddleware extends HttpApiMiddleware.Tag<RequestIdMiddleware>()(
  "RequestIdMiddleware",
  { provides: RequestId }
) {}

const RequestIdLive = Layer.succeed(
  RequestIdMiddleware,
  RequestIdMiddleware.of(
    Effect.succeed("generated-request-id")
  )
)
```

Use ordinary HTTP middleware from `HttpMiddleware` for request/response
transformations like logging or CORS.

## Attachment Levels

| Attachment | Scope |
|---|---|
| `api.middleware(Auth)` | every group and endpoint |
| `group.middleware(Auth)` | every endpoint in the group |
| `endpoint.middleware(Auth)` | one endpoint |

Prefer the narrowest level that matches the domain rule.

## Cross-references

See also: [05-headers.md](05-headers.md), [08-error-responses.md](08-error-responses.md), [10-cors-and-logger.md](10-cors-and-logger.md), [15-serving.md](15-serving.md)
