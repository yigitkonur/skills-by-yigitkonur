# Handlers
Implement endpoint contracts with `HttpApiBuilder.group` and return typed successes or declared errors.

## Group Implementation

`HttpApiBuilder.group` implements one `HttpApiGroup` from an `HttpApi`.

```typescript
import { HttpApi, HttpApiBuilder, HttpApiEndpoint, HttpApiGroup, HttpApiSchema } from "@effect/platform"
import { Effect, Schema } from "effect"

class User extends Schema.Class<User>("User")({
  id: Schema.Int,
  name: Schema.String
}) {}

const id = HttpApiSchema.param("id", Schema.NumberFromString)

const users = HttpApiGroup.make("users")
  .add(HttpApiEndpoint.get("getUser")`/users/${id}`.addSuccess(User))

class Api extends HttpApi.make("api").add(users) {}

const UsersLive = HttpApiBuilder.group(Api, "users", (handlers) =>
  handlers.handle("getUser", ({ path }) =>
    Effect.succeed(new User({ id: path.id, name: "Ada" }))
  )
)
```

The handler key `"getUser"` is checked against the endpoint names in the
`users` group.

## Request Fields

The handler request object is derived from endpoint schemas.

| Endpoint definition | Handler field |
|---|---|
| template path params | `path` |
| `setUrlParams` | `urlParams` |
| `setPayload` | `payload` |
| `setHeaders` | `headers` |
| always | `request` |

If a schema is absent, the corresponding field is absent.

## Service Access

Handlers are normal effects. Access services with context tags and provide
their layers to the group implementation.

```typescript
import { Context, Effect, Layer, Schema } from "effect"

class UserRepo extends Context.Tag("UserRepo")<
  UserRepo,
  {
    readonly findById: (id: number) => Effect.Effect<User>
  }
>() {
  static Live = Layer.succeed(this, {
    findById: (id) => Effect.succeed(new User({ id, name: "Ada" }))
  })
}

const UsersLive = HttpApiBuilder.group(Api, "users", (handlers) =>
  Effect.gen(function*() {
    const repo = yield* UserRepo

    return handlers.handle("getUser", ({ path }) =>
      repo.findById(path.id)
    )
  })
).pipe(Layer.provide(UserRepo.Live))
```

The group layer carries any remaining requirements in its `R` channel until
provided.

## Multiple Handlers

The builder requires all endpoints to be handled.

```typescript
const UsersLive = HttpApiBuilder.group(Api, "users", (handlers) =>
  handlers
    .handle("listUsers", () => Effect.succeed([]))
    .handle("getUser", ({ path }) =>
      Effect.succeed(new User({ id: path.id, name: "Ada" }))
    )
)
```

Returning before every endpoint is handled is a type error. This is intentional:
the API declaration and implementation must stay in sync.

## Returning Server Responses

Most handlers should return the success type declared by `addSuccess`. Return
`HttpServerResponse` only when the endpoint needs manual control over status,
headers, cookies, or streaming.

```typescript
import { HttpServerResponse } from "@effect/platform"
import { Effect } from "effect"

const GroupsLive = HttpApiBuilder.group(Api, "groups", (handlers) =>
  handlers.handle("download", () =>
    Effect.succeed(
      HttpServerResponse.text("id,name\n1,Ada\n", {
        headers: { "content-type": "text/csv" }
      })
    )
  )
)
```

If the response is a stable public shape, prefer `addSuccess` with
`HttpApiSchema.withEncoding`.

## Raw Handlers

Use `handleRaw` when the endpoint declares a payload but the handler must read
the body manually.

```typescript
import { Effect } from "effect"

const GroupsLive = HttpApiBuilder.group(Api, "groups", (handlers) =>
  handlers.handleRaw("importRaw", ({ request }) =>
    Effect.gen(function*() {
      const body = yield* Effect.orDie(request.text)
      return { bytes: body.length }
    })
  )
)
```

Raw handlers still receive typed path, query, and headers. They skip automatic
payload decoding.

## Declared Failures

Handlers may fail with endpoint, group, or API-level errors.

```typescript
import { Effect } from "effect"

const UsersLive = HttpApiBuilder.group(Api, "users", (handlers) =>
  handlers.handle("getUser", ({ path }) =>
    path.id === 0
      ? Effect.fail(new NotFound({ id: path.id }))
      : Effect.succeed(new User({ id: path.id, name: "Ada" }))
  )
)
```

Do not throw from handlers for expected failures. Use `Effect.fail` with a
declared error schema.

## Handler Options

`handle` and `handleRaw` accept `{ uninterruptible: true }` for sections that
must not be interrupted once started.

```typescript
handlers.handle(
  "commitPayment",
  ({ payload }) => Payments.charge(payload),
  { uninterruptible: true }
)
```

Use this narrowly. Most request handling should remain interruptible so
shutdown and client disconnects can stop work.

## API Layer Composition

After every group is implemented, provide group layers into
`HttpApiBuilder.api(Api)`.

```typescript
import { HttpApiBuilder } from "@effect/platform"
import { Layer } from "effect"

const ApiLive = HttpApiBuilder.api(Api).pipe(
  Layer.provide(UsersLive),
  Layer.provide(GroupsLive)
)
```

The API layer is the value consumed by `HttpApiBuilder.serve`.

## Cross-references

See also: [02-defining-endpoints.md](02-defining-endpoints.md), [06-grouping.md](06-grouping.md), [08-error-responses.md](08-error-responses.md), [15-serving.md](15-serving.md)
