# RPC Overview
Use this when choosing `@effect/rpc` for typed client/server boundaries instead of ad hoc HTTP handlers.

`@effect/rpc` describes a remote API once, implements it once on the server,
and derives a client whose methods, payloads, successes, failures, middleware,
and streaming responses are all inferred from the same `RpcGroup`.

The central gravity is simple:

1. Define each procedure with `Rpc.make`.
2. Put procedures in a `RpcGroup`.
3. Implement handlers from that group.
4. Serve the group through a protocol layer.
5. Build a client from the same group and a matching client protocol.

That gives typed end-to-end RPC over HTTP, WebSocket, Worker, and lower-level
protocols without rewriting the contract for each transport.

## Package imports

Use the package barrel in application examples:

```typescript
import {
  Rpc,
  RpcClient,
  RpcGroup,
  RpcMiddleware,
  RpcSchema,
  RpcSerialization,
  RpcServer
} from "@effect/rpc"
import { Effect, Layer, Schema, Stream } from "effect"
```

The cloned source uses internal deep imports for implementation, but examples in
this skill should use `"effect"` and named `@effect/*` packages.

## Contract model

Every RPC declares three schema slots:

| Slot | Meaning |
|---|---|
| `payload` | The request body accepted by the remote method. |
| `success` | The successful response, or the stream item schema for streaming RPCs. |
| `error` | The typed expected failure channel. |

When a slot is omitted, v3 defaults apply: payload is `Schema.Void`, success is
`Schema.Void`, and error is `Schema.Never`.

Prefer explicit schemas anyway. Agents reading the contract need to see the wire
shape without guessing:

```typescript
import { Rpc, RpcGroup } from "@effect/rpc"
import { Schema } from "effect"

class User extends Schema.Class<User>("User")({
  id: Schema.String,
  name: Schema.String
}) {}

class NotFound extends Schema.TaggedError<NotFound>()("NotFound", {
  id: Schema.String
}) {}

export class UsersApi extends RpcGroup.make(
  Rpc.make("Users.Get", {
    payload: { id: Schema.String },
    success: User,
    error: NotFound
  })
) {}
```

## Runtime architecture

`RpcGroup` is the shared type-level and runtime registry. The group carries a
map from RPC tag to `Rpc` definition and exposes helpers to implement handlers.

`RpcServer.layer(group)` starts the server-side message processor. It requires:

- a `RpcServer.Protocol` layer, such as HTTP or WebSocket,
- handler services produced by `group.toLayer` or `group.toLayerHandler`,
- schema contexts required by payload, success, error, and middleware schemas,
- middleware implementations for RPCs that declare middleware.

`RpcClient.make(group)` builds an inferred client. It requires:

- a `RpcClient.Protocol` layer, such as HTTP, WebSocket, or Worker,
- client middleware layers for middleware marked `requiredForClient`,
- schema contexts required by the group,
- `Scope.Scope`, because requests, streams, and protocol resources are scoped.

## Protocol versus serialization

The protocol moves RPC messages. Serialization encodes and decodes them.

Server protocols include:

- `RpcServer.layerProtocolHttp` for streaming HTTP mounted on an HTTP router.
- `RpcServer.layerProtocolWebsocket` for WebSocket RPC.
- `RpcServer.layerProtocolWorkerRunner` for worker-side serving.
- `RpcServer.toHttpApp` and `RpcServer.toHttpAppWebsocket` for directly
  producing HTTP apps.

Client protocols include:

- `RpcClient.layerProtocolHttp({ url })`.
- `RpcClient.layerProtocolSocket()`, supplied with a platform `Socket.Socket`.
- `RpcClient.layerProtocolWorker(options)`, supplied with platform worker
  services.

Serialization layers include JSON, NDJSON, JSON-RPC, NDJSON-RPC, and MessagePack
variants from `RpcSerialization`.

## Handler shape

Handlers are ordinary Effect functions derived from the group. A non-streaming
handler returns an `Effect`; a streaming handler returns a `Stream` or a
mailbox-backed stream shape accepted by the handler type.

```typescript
import { Rpc, RpcGroup } from "@effect/rpc"
import { Effect, Layer, Schema } from "effect"

class PingApi extends RpcGroup.make(
  Rpc.make("Ping", {
    payload: { message: Schema.String },
    success: Schema.String,
    error: Schema.Never
  })
) {}

const PingHandlers = PingApi.toLayer({
  Ping: ({ message }) => Effect.succeed(`pong:${message}`)
})

export const PingLayer: Layer.Layer<Rpc.Handler<"Ping">> = PingHandlers
```

## Client shape

The client mirrors tag names. A tag such as `"Users.Get"` is exposed under a
prefix object, so `client.Users.Get(payload)` is inferred from the matching
`Rpc.make` definition.

```typescript
import { RpcClient } from "@effect/rpc"
import { Effect } from "effect"
import { UsersApi } from "./api.js"

const program = Effect.gen(function*() {
  const client = yield* RpcClient.make(UsersApi)
  const user = yield* client.Users.Get({ id: "1" })
  yield* Effect.logInfo(`loaded user ${user.id}`)
})
```

Without dotted tags, methods appear directly on the client object.

## When to use RPC

Use `@effect/rpc` when the API is internal or first-party and both sides can
share TypeScript contracts. It is especially useful when handlers already return
`Effect` or `Stream` values and you want typed failure channels to cross the
transport boundary.

Use an HTTP API module instead when the public contract is OpenAPI-first,
resource-oriented, or needs broad non-TypeScript consumer support.

## Cross-references

See also: [02-rpc-group.md](02-rpc-group.md), [03-rpc-server.md](03-rpc-server.md), [04-rpc-client.md](04-rpc-client.md), [06-rpc-streaming.md](06-rpc-streaming.md)
