# Greenfield HTTP API
Build a CRUD HTTP API with Effect v3 `HttpApi`, typed schemas, auth middleware, layers, and test overrides.

Use this for a new Node HTTP service. The official `examples/http-server` project wires `HttpApiBuilder.api`, feature handler layers, Swagger, middleware, and `NodeHttpServer.layer`; this file compresses that pattern into one runnable starting point.

## Primitive index

| Primitive | Read first |
|---|---|
| `HttpApi`, groups, endpoints, handlers | [http-server](../http-server/02-defining-endpoints.md), [http-server](../http-server/06-grouping.md), [http-server](../http-server/07-handlers.md) |
| path params, payloads, responses | [http-server](../http-server/03-path-params.md), [http-server](../http-server/04-query-and-payload.md), [http-server](../http-server/08-error-responses.md) |
| `Schema.Class`, decoding, tagged errors | [schema](../schema/03-schema-class.md), [schema](../schema/10-decoding.md), [error-handling](../error-handling/03-schema-tagged-error.md) |
| service and layer graph | [services-layers](../services-layers/03-effect-service.md), [services-layers](../services-layers/10-layer-provide.md), [services-layers](../services-layers/11-layer-providemerge.md) |
| server runtime, CORS, logging, tests | [platform](../platform/12-node-runtime.md), [http-server](../http-server/10-cors-and-logger.md), [testing](../testing/05-it-layer.md) |

## 1. Package setup

```typescript
{
  "type": "module",
  "scripts": {
    "dev": "tsx src/main.ts",
    "build": "tsc -p tsconfig.json",
    "test": "vitest"
  },
  "dependencies": {
    "@effect/platform": "^0.95.0",
    "@effect/platform-node": "^0.90.0",
    "effect": "^3.21.2"
  },
  "devDependencies": {
    "@effect/vitest": "^0.28.0",
    "tsx": "^4.20.0",
    "typescript": "^5.9.0",
    "vitest": "^4.0.0"
  }
}
```

## 2. Entry point

`src/main.ts` launches a layer. A server is a resource, so use `Layer.launch` at the edge.

```typescript
import { NodeRuntime } from "@effect/platform-node"
import { Layer } from "effect"
import { HttpLive } from "./http.js"

HttpLive.pipe(
  Layer.launch,
  NodeRuntime.runMain
)
```

This is the same entry-point shape used by the official HTTP example. Keep the server graph in `http.ts` so tests can reuse the API and handlers without starting a port.

## 3. Main API orchestration

`src/api.ts` describes the contract. It has no live dependencies.

```typescript
import { HttpApi, HttpApiEndpoint, HttpApiGroup } from "@effect/platform"
import { Schema } from "effect"

export class User extends Schema.Class<User>("User")({
  id: Schema.String,
  email: Schema.String,
  name: Schema.String
}) {}

export class CreateUser extends Schema.Class<CreateUser>("CreateUser")({
  email: Schema.String,
  name: Schema.String
}) {}

export class Unauthorized extends Schema.TaggedError<Unauthorized>()("Unauthorized", {
  message: Schema.String
}) {}

export class UserNotFound extends Schema.TaggedError<UserNotFound>()("UserNotFound", {
  id: Schema.String
}) {}

const AuthHeaders = Schema.Struct({ authorization: Schema.String })

export class UsersGroup extends HttpApiGroup.make("users")
  .add(HttpApiEndpoint.get("list", "/users").setHeaders(AuthHeaders).addSuccess(Schema.Array(User)))
  .add(HttpApiEndpoint.post("create", "/users").setHeaders(AuthHeaders).setPayload(CreateUser).addSuccess(User))
  .add(HttpApiEndpoint.get("get", "/users/:id").setHeaders(AuthHeaders).addSuccess(User).addError(UserNotFound))
  .addError(Unauthorized)
{}

export class Api extends HttpApi.make("api").add(UsersGroup) {}
```

## 4. Per-feature service definitions

`src/users.ts` owns storage and auth policy. The in-memory implementation is intentionally replaceable.

```typescript
import { Effect, Layer, Ref } from "effect"
import { CreateUser, Unauthorized, User, UserNotFound } from "./api.js"

export class Users extends Effect.Service<Users>()("app/Users", {
  effect: Effect.gen(function*() {
    const store = yield* Ref.make(new Map<string, User>())

    const authorize = (authorization: string) =>
      authorization === "Bearer dev-token"
        ? Effect.void
        : Effect.fail(new Unauthorized({ message: "invalid token" }))

    const list = (authorization: string) =>
      authorize(authorization).pipe(Effect.zipRight(Ref.get(store)), Effect.map((map) => [...map.values()]))

    const create = (authorization: string, input: CreateUser) =>
      Effect.gen(function*() {
        yield* authorize(authorization)
        const id = `user-${Date.now()}`
        const user = new User({ id, ...input })
        yield* Ref.update(store, (map) => new Map(map).set(id, user))
        return user
      })

    const get = (authorization: string, id: string) =>
      Effect.gen(function*() {
        yield* authorize(authorization)
        const map = yield* Ref.get(store)
        const user = map.get(id)
        if (user) {
          return user
        }
        return yield* Effect.fail(new UserNotFound({ id }))
      })

    return { list, create, get } as const
  })
}) {}

export const UsersTest = Layer.succeed(Users, {
  list: () => Effect.succeed([new User({ id: "u1", email: "a@example.com", name: "Ada" })]),
  create: (_authorization, input) => Effect.succeed(new User({ id: "u2", ...input })),
  get: (_authorization, id) => Effect.succeed(new User({ id, email: "a@example.com", name: "Ada" }))
})
```

## 5. Layer wiring

`src/http.ts` binds the contract to handlers and supplies platform layers.

```typescript
import { HttpApiBuilder, HttpApiSwagger, HttpMiddleware, HttpServer } from "@effect/platform"
import { NodeHttpServer } from "@effect/platform-node"
import { Effect, Layer } from "effect"
import { createServer } from "node:http"
import { Api, UsersGroup } from "./api.js"
import { Users } from "./users.js"

const UsersHandlers = HttpApiBuilder.group(Api, "users", (handlers) =>
  Effect.gen(function*() {
    const users = yield* Users
    return handlers
      .handle("list", ({ headers }) => users.list(headers.authorization))
      .handle("create", ({ headers, payload }) => users.create(headers.authorization, payload))
      .handle("get", ({ headers, path }) => users.get(headers.authorization, path.id))
  })
)

const ApiLive = HttpApiBuilder.api(Api).pipe(
  Layer.provide(UsersHandlers),
  Layer.provide(Users.Default)
)

export const HttpLive = HttpApiBuilder.serve(HttpMiddleware.logger).pipe(
  Layer.provide(HttpApiSwagger.layer()),
  Layer.provide(HttpApiBuilder.middlewareOpenApi()),
  Layer.provide(HttpApiBuilder.middlewareCors()),
  Layer.provide(ApiLive),
  HttpServer.withLogAddress,
  Layer.provide(NodeHttpServer.layer(createServer, { port: 3000 }))
)
```

## 6. Test layer override

Override `Users` and run handler-level tests without a network port.

```typescript
import { it } from "@effect/vitest"
import { Effect } from "effect"
import { Users, UsersTest } from "../src/users.js"

it.effect("lists users through a test layer", () =>
  Effect.gen(function*() {
    const users = yield* Users
    const result = yield* users.list("Bearer test")
    expect(result).toHaveLength(1)
  }).pipe(Effect.provide(UsersTest))
)
```

For full HTTP tests, build a test server layer with a random port and use [http-client response decoding](../http-client/04-response-decoding.md). Keep auth failure tests explicit with [catchTag](../error-handling/04-catch-tag.md).

## Workflow checklist

1. Define schemas before handlers.
2. Define error schemas before implementation errors appear.
3. Keep auth requirements in the API contract or middleware.
4. Keep handler functions as adapters around services.
5. Provide feature handler layers into `HttpApiBuilder.api`.
6. Provide feature service layers below handler layers.
7. Provide Swagger, CORS, and logging at the server edge.
8. Use `HttpServer.withLogAddress` for local feedback.
9. Keep storage replaceable until SQL is actually required.
10. Use one route group per resource area.
11. Add one integration test per route group.
12. Add service tests for business rules.
13. Decode payloads through endpoint schemas, not manual casts.
14. Map typed failures to declared endpoint errors.
15. Keep authorization failures uniform across the group.
16. Do not start a listening port for pure handler tests.
17. Add request tracing after route names stabilize.
18. Add OpenAPI annotations before external consumers depend on the API.
19. Keep deployment config behind `Config`.
20. Keep the server layer as the only launched layer.
21. Review [Layer.provide](../services-layers/10-layer-provide.md) before changing layer order.
22. Review [Layer.provideMerge](../services-layers/11-layer-providemerge.md) before adding shared dependencies.
23. Keep examples runnable with `tsx src/main.ts`.
24. Keep the first CRUD service small enough to replace in tests.
25. Verify 401, 404, and success paths.
26. Do not hide handler defects with catch-all recovery.
27. Add [headers](../http-server/05-headers.md) before handler code expects them.
28. Keep route path parameters documented in the endpoint definitions.
29. Add [multipart](../http-server/12-multipart.md) only when the first upload route appears.
30. Add [streaming responses](../http-server/13-streaming-responses.md) only for real streaming needs.
31. Use [custom encoding](../http-server/14-custom-encoding.md) for non-JSON protocols.
32. Use [platform router](../http-server/16-platform-router.md) when mixing raw routes and `HttpApi`.
33. Review [shutdown and signals](../http-server/17-shutdown-and-signals.md) before production.
34. Keep the OpenAPI document generated from the same contract the server runs.

## 7. Deployment

Run the compiled `src/main.js` under Node in a container or VM. The HTTP layer owns server lifetime, so process shutdown interrupts the layer and lets finalizers run. Put production secrets behind `Config.redacted` and provide a `ConfigProvider` layer for platform-specific sources.

## Cross-references

See also: [microservice](06-microservice.md), [Next.js fullstack](04-greenfield-nextjs.md), [MCP server](08-mcp-server.md), [HTTP server overview](../http-server/01-overview.md).
