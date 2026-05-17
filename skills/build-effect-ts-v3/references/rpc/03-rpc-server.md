# RPC Server
Use this when implementing and serving an `RpcGroup` with `RpcServer.layer`.

The server side has two separate pieces:

- handlers, provided by the shared `RpcGroup`,
- a protocol, provided by `RpcServer`.

The server layer does not bind itself to HTTP or WebSocket until you provide a
`RpcServer.Protocol`. This separation is what lets the same group run over
HTTP, WebSocket, Worker, stdio, tests, or custom transports.

## Basic server layer

```typescript
import { HttpRouter } from "@effect/platform"
import { BunHttpServer, BunRuntime } from "@effect/platform-bun"
import { Rpc, RpcGroup, RpcSerialization, RpcServer } from "@effect/rpc"
import { Effect, Layer, Schema } from "effect"

class EchoApi extends RpcGroup.make(
  Rpc.make("Echo", {
    payload: { message: Schema.String },
    success: Schema.String,
    error: Schema.Never
  })
) {}

const EchoHandlers = EchoApi.toLayer({
  Echo: ({ message }) => Effect.succeed(message)
})

const RpcLive = RpcServer.layer(EchoApi).pipe(
  Layer.provide(EchoHandlers)
)

const RpcProtocol = RpcServer.layerProtocolHttp({
  path: "/rpc"
}).pipe(
  Layer.provide(RpcSerialization.layerNdjson)
)

const Main = HttpRouter.Default.serve().pipe(
  Layer.provide(RpcLive),
  Layer.provide(RpcProtocol),
  Layer.provide(BunHttpServer.layer({ port: 3000 }))
)

BunRuntime.runMain(Layer.launch(Main))
```

The RPC server is scoped and long-running. At an application edge, use
`Layer.launch` through the platform runtime.

## Handler requirements

`RpcServer.layer(group)` requires handler services for every RPC in the group.
`group.toLayer` is the normal way to produce them:

```typescript
const Handlers = EchoApi.toLayer({
  Echo: ({ message }) =>
    Effect.gen(function*() {
      yield* Effect.logDebug(`echo request ${message.length}`)
      return message
    })
})
```

If one handler needs services, those requirements become requirements of the
handler layer. Provide those services to the handler layer, not to the protocol.

```typescript
class EchoStore extends Effect.Service<EchoStore>()("EchoStore", {
  succeed: {
    save: (message: string) => Effect.logInfo(`saved ${message.length}`)
  }
}) {}

const HandlersWithStore = EchoApi.toLayer(
  Effect.gen(function*() {
    const store = yield* EchoStore
    return {
      Echo: ({ message }) => store.save(message).pipe(Effect.as(message))
    }
  })
).pipe(
  Layer.provide(EchoStore.Default)
)
```

## Server layer options

`RpcServer.layer(group, options)` supports operational options:

| Option | Use |
|---|---|
| `disableTracing` | Disable RPC tracing spans. |
| `spanPrefix` | Change the tracing span prefix. |
| `spanAttributes` | Add static span attributes. |
| `concurrency` | Limit concurrent request handling or use `"unbounded"`. |
| `disableFatalDefects` | Prevent defects from being treated as fatal by the server. |

Prefer a numeric `concurrency` when handlers call external systems.

```typescript
const RpcLive = RpcServer.layer(EchoApi, {
  spanPrefix: "EchoRpc",
  concurrency: 64
}).pipe(
  Layer.provide(EchoHandlers)
)
```

## HTTP router protocol

`RpcServer.layerProtocolHttp` mounts streaming HTTP through the default
`HttpRouter`. Provide serialization separately:

```typescript
const HttpProtocol = RpcServer.layerProtocolHttp({
  path: "/rpc"
}).pipe(
  Layer.provide(RpcSerialization.layerNdjson)
)
```

Use `layerProtocolHttpRouter` when you already manage `HttpLayerRouter` directly.

```typescript
const RouterProtocol = RpcServer.layerProtocolHttpRouter({
  path: "/rpc"
}).pipe(
  Layer.provide(RpcSerialization.layerNdjson)
)
```

## WebSocket protocol

For bidirectional or long-lived clients, mount a WebSocket protocol:

```typescript
const WebSocketProtocol = RpcServer.layerProtocolWebsocket({
  path: "/rpc/socket"
}).pipe(
  Layer.provide(RpcSerialization.layerJson)
)
```

WebSocket and HTTP protocols serve the same group. The protocol choice should
not change the RPC declarations or handler implementation.

## Worker runner protocol

`RpcServer.layerProtocolWorkerRunner` makes a worker process receive and respond
to RPC messages. The worker still serves the same `RpcGroup`:

```typescript
import { WorkerRunner } from "@effect/platform"

const WorkerRpcLive = RpcServer.layer(EchoApi).pipe(
  Layer.provide(EchoHandlers),
  Layer.provide(RpcServer.layerProtocolWorkerRunner)
)

export const WorkerMain = WorkerRunner.launch(WorkerRpcLive)
```

The parent thread uses `RpcClient.layerProtocolWorker`; see
[04-rpc-client.md](04-rpc-client.md).

## Server-side failures

Expected domain errors must be returned through the Effect error channel:

```typescript
class EchoRejected extends Schema.TaggedError<EchoRejected>()("EchoRejected", {
  reason: Schema.String
}) {}

class EchoStrictApi extends RpcGroup.make(
  Rpc.make("EchoStrict", {
    payload: { message: Schema.String },
    success: Schema.String,
    error: EchoRejected
  })
) {}

const StrictHandlers = EchoStrictApi.toLayer({
  EchoStrict: ({ message }) =>
    message.length > 0
      ? Effect.succeed(message)
      : Effect.fail(new EchoRejected({ reason: "empty message" }))
})
```

Defects are still encoded through the RPC machinery, but they are not a
replacement for modeled errors.

## Server checklist

Before shipping a server:

- build handlers from the same group the client imports,
- choose one protocol per endpoint path,
- provide a matching serialization layer on server and client,
- set request concurrency intentionally,
- keep runtime launch calls at the application edge.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-rpc-group.md](02-rpc-group.md), [04-rpc-client.md](04-rpc-client.md), [05-rpc-middleware.md](05-rpc-middleware.md)
