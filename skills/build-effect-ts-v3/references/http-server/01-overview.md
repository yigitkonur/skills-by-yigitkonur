# HTTP Server Overview
Understand the `HttpApi` hierarchy for building typed end-to-end HTTP servers in Effect v3.

## Mental Model

`HttpApi` is the typed contract for an HTTP server.

It has three levels:

| Level | Purpose |
|---|---|
| `HttpApi` | Top-level API, global errors, global middleware, OpenAPI metadata |
| `HttpApiGroup` | A named group of related endpoints, often one resource area |
| `HttpApiEndpoint` | One method and path, with schemas for request and response |

The server is not defined by route callbacks first. Define the contract first,
then implement it with `HttpApiBuilder.group`.

```typescript
import { HttpApi, HttpApiEndpoint, HttpApiGroup } from "@effect/platform"
import { Schema } from "effect"

class User extends Schema.Class<User>("User")({
  id: Schema.Int,
  name: Schema.String
}) {}

const users = HttpApiGroup.make("users").add(
  HttpApiEndpoint.get("listUsers", "/users")
    .addSuccess(Schema.Array(User))
)

class Api extends HttpApi.make("api").add(users) {}
```

The `Api` class carries the group and endpoint types. The builder and derived
client both read from that same value, so the server and client stay aligned.

## Why Use `HttpApi`

Use `HttpApi` when the route contract matters:

- path parameters should decode before the handler runs
- query parameters should have typed shapes
- JSON payloads should be schema-validated
- headers should be typed
- response schemas should determine the success payload
- error responses should be declared and encoded consistently
- OpenAPI/Swagger should be generated from the same contract
- a client should be derived without duplicating routes

This is the Effect alternative to hand-wired Express, Fastify, or Hono route
tables where request parsing and response shape drift over time.

## Contract Before Implementation

The API declaration is pure data plus types. It does not listen on a port and it
does not perform side effects.

```typescript
import { HttpApi, HttpApiEndpoint, HttpApiGroup } from "@effect/platform"
import { Schema } from "effect"

class Todo extends Schema.Class<Todo>("Todo")({
  id: Schema.Int,
  title: Schema.String,
  done: Schema.Boolean
}) {}

const getTodo = HttpApiEndpoint.get("getTodo", "/todos/:id")
  .addSuccess(Todo)

const todos = HttpApiGroup.make("todos").add(getTodo)

class TodoApi extends HttpApi.make("todo-api").add(todos) {}
```

Template-string paths are preferred for typed path parameters. A plain string
path like `"/todos/:id"` is a raw router path and does not create a typed
`path` field for handlers. Use `HttpApiSchema.param` when the handler needs the
value.

## Implementation Is Separate

Handlers are attached later. The group name and endpoint names are type-checked
against the API declaration.

```typescript
import { HttpApiBuilder } from "@effect/platform"
import { Effect } from "effect"

const TodosLive = HttpApiBuilder.group(TodoApi, "todos", (handlers) =>
  handlers.handle("getTodo", () =>
    Effect.succeed(new Todo({ id: 1, title: "Ship API", done: false }))
  )
)
```

If an endpoint is missing, the builder type reports the missing endpoint name.
That is the main server-side advantage: incomplete route implementation is a
type error, not a runtime surprise.

## Server Assembly

Serving combines three layers:

1. the API contract layer from `HttpApiBuilder.api(Api)`
2. all group implementation layers
3. a platform `HttpServer`, such as `NodeHttpServer.layer`

```typescript
import { HttpApiBuilder, HttpMiddleware, HttpServer } from "@effect/platform"
import { NodeHttpServer, NodeRuntime } from "@effect/platform-node"
import { Layer } from "effect"
import { createServer } from "node:http"

const ApiLive = HttpApiBuilder.api(TodoApi).pipe(
  Layer.provide(TodosLive)
)

const ServerLive = HttpApiBuilder.serve(HttpMiddleware.logger).pipe(
  Layer.provide(ApiLive),
  HttpServer.withLogAddress,
  Layer.provide(NodeHttpServer.layer(createServer, { port: 3000 }))
)

Layer.launch(ServerLive).pipe(NodeRuntime.runMain)
```

`Layer.launch` keeps the scoped server alive. `NodeRuntime.runMain` is the
process edge for Node applications.

## Type Flow

Endpoint schemas flow into handler request types:

| Endpoint schema | Handler field |
|---|---|
| `setPath` or template params | `path` |
| `setUrlParams` | `urlParams` |
| `setPayload` | `payload` |
| `setHeaders` | `headers` |
| `addSuccess` | handler success value |
| `addError` | handler failure value |

The raw `request` is always present for edge cases, but most handlers should use
the decoded fields.

## When To Drop Lower

Use `HttpRouter` when the route is not part of the typed API contract:

- health checks that intentionally avoid OpenAPI
- raw proxy routes
- static assets
- framework interop
- request handling that is simpler as a low-level route

For application APIs, prefer `HttpApi` first. It gives better type feedback and
derives Swagger and clients from the same declaration.

## Cross-references

See also: [02-defining-endpoints.md](02-defining-endpoints.md), [06-grouping.md](06-grouping.md), [07-handlers.md](07-handlers.md), [15-serving.md](15-serving.md)
