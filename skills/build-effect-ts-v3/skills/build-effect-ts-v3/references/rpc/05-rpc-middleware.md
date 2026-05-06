# RPC Middleware
Use this when adding typed cross-cutting behavior to RPC declarations.

`RpcMiddleware` lets a group or RPC declare extra requirements around a call:
provide a handler service, fail with a typed schema, wrap the server handler,
and require a matching client-side implementation.

## Defining middleware

Use `RpcMiddleware.Tag` to create a middleware tag:

```typescript
import { RpcMiddleware } from "@effect/rpc"
import { Context, Schema } from "effect"

class CurrentUser extends Context.Tag("CurrentUser")<
  CurrentUser,
  { readonly id: string; readonly roles: ReadonlyArray<string> }
>() {}

class AuthError extends Schema.TaggedError<AuthError>()("AuthError", {
  reason: Schema.String
}) {}

export class Auth extends RpcMiddleware.Tag<Auth>()("Auth", {
  provides: CurrentUser,
  failure: AuthError,
  requiredForClient: true
}) {}
```

The tag means handlers can access `CurrentUser`, middleware can fail with
`AuthError`, and clients must provide a client middleware layer.

## Applying middleware

Apply middleware to one RPC:

```typescript
import { Rpc, RpcGroup } from "@effect/rpc"
import { Schema } from "effect"
import { Auth } from "./auth.js"

class Profile extends Schema.Class<Profile>("Profile")({
  userId: Schema.String,
  displayName: Schema.String
}) {}

export class ProfileApi extends RpcGroup.make(
  Rpc.make("Profile.Me", {
    payload: Schema.Void,
    success: Profile,
    error: Schema.Never
  }).middleware(Auth)
) {}
```

Apply middleware to every RPC already in a group:

```typescript
export class AdminApi extends RpcGroup.make(
  Rpc.make("Admin.Reindex", {
    payload: Schema.Void,
    success: Schema.Void,
    error: Schema.Never
  }),
  Rpc.make("Admin.Stats", {
    payload: Schema.Void,
    success: Schema.Struct({ count: Schema.Number }),
    error: Schema.Never
  })
).middleware(Auth) {}
```

`group.middleware(Auth)` affects RPCs currently in the group. Apply it again for
later RPCs that need it.

## Server implementation

Server middleware receives headers, payload, the RPC definition, and the client
id. Return the provided service or fail with the declared failure schema:

```typescript
import { Headers } from "@effect/platform"
import { Effect, Layer, Option } from "effect"
import { Auth, AuthError, CurrentUser } from "./auth.js"

const AuthLive: Layer.Layer<Auth> = Layer.succeed(
  Auth,
  Auth.of(({ headers }) => {
    const header = Headers.get(headers, "authorization")
    return Option.match(header, {
      onNone: () =>
        Effect.fail(new AuthError({ reason: "missing authorization" })),
      onSome: () =>
        Effect.succeed({
          id: "user-1",
          roles: ["user"]
        })
    })
  })
)
```

Handlers can then read the service declared in `provides`:

```typescript
const ProfileHandlers = ProfileApi.toLayer({
  "Profile.Me": () =>
    Effect.gen(function*() {
      const user = yield* CurrentUser
      return new Profile({
        userId: user.id,
        displayName: "Ada"
      })
    })
})
```

## Client implementation

When middleware has `requiredForClient: true`, provide a client layer with
`RpcMiddleware.layerClient`:

```typescript
import { Headers } from "@effect/platform"
import { RpcMiddleware } from "@effect/rpc"
import { Effect, Layer } from "effect"
import { Auth } from "./auth.js"

const AuthClientLive: Layer.Layer<RpcMiddleware.ForClient<Auth>> =
  RpcMiddleware.layerClient(Auth, ({ request }) =>
    Effect.succeed({
      ...request,
      headers: Headers.set(
        request.headers,
        "authorization",
        "Bearer redacted"
      )
    })
  )
```

Provide this layer to programs that call RPCs protected by `Auth`.

## Wrapping middleware

Set `wrap: true` when middleware should run around the handler instead of only
providing a service before it:

```typescript
class Audit extends RpcMiddleware.Tag<Audit>()("Audit", {
  wrap: true
}) {}

const AuditLive: Layer.Layer<Audit> = Layer.succeed(
  Audit,
  Audit.of(({ rpc, next }) =>
    Effect.gen(function*() {
      yield* Effect.logInfo(`rpc start ${rpc._tag}`)
      const result = yield* next
      yield* Effect.logInfo(`rpc end ${rpc._tag}`)
      return result
    })
  )
)
```

Use wrapping middleware for timing, logging, audit trails, and policies that
must observe handler completion.

## Error typing

Middleware failures join the client call's error channel. That means an RPC with
`error: TodoNotFound` and `Auth` middleware can fail with either `TodoNotFound`
or `AuthError`.

Keep middleware failure schemas narrow and serializable. They cross the same RPC
boundary as domain failures.

## Cross-references

See also: [02-rpc-group.md](02-rpc-group.md), [03-rpc-server.md](03-rpc-server.md), [04-rpc-client.md](04-rpc-client.md), [06-rpc-streaming.md](06-rpc-streaming.md)
