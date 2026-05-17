# RPC Client
Use this when building an inferred `RpcClient` over HTTP, WebSocket, or Worker transport.

`RpcClient.make(group)` turns an `RpcGroup` into callable methods. The method
names, payload argument, success type, error type, stream shape, and middleware
requirements all come from the group.

The client needs a protocol layer. This file shows all three common transports:
HTTP, WebSocket, and Worker.

## Basic client use

```typescript
import { RpcClient } from "@effect/rpc"
import { Effect } from "effect"
import { TodoApi } from "./api.js"

const program = Effect.gen(function*() {
  const client = yield* RpcClient.make(TodoApi)
  const todo = yield* client.Todos.Get({ id: "1" })
  yield* Effect.logInfo(`loaded ${todo.title}`)
})
```

The `TodoApi` group owns the method shape. The protocol layer only decides how
messages move.

## HTTP transport

HTTP is the normal browser/server boundary. It requires an HTTP client and an
RPC serialization layer:

```typescript
import { FetchHttpClient } from "@effect/platform"
import { RpcClient, RpcSerialization } from "@effect/rpc"
import { Effect, Layer } from "effect"
import { TodoApi } from "./api.js"

const HttpProtocol = RpcClient.layerProtocolHttp({
  url: "https://api.example.com/rpc"
}).pipe(
  Layer.provide([
    FetchHttpClient.layer,
    RpcSerialization.layerNdjson
  ])
)

export const httpProgram = Effect.gen(function*() {
  const client = yield* RpcClient.make(TodoApi)
  return yield* client.Todos.Get({ id: "1" })
}).pipe(
  Effect.scoped,
  Effect.provide(HttpProtocol)
)
```

Use the same serialization family as the server endpoint. If the server used
`RpcSerialization.layerNdjson`, the client should provide NDJSON too.

## WebSocket transport

WebSocket uses `RpcClient.layerProtocolSocket`, which requires a platform socket
layer. Browser and Node platforms expose socket layers; the example below uses
the browser package:

```typescript
import { BrowserSocket } from "@effect/platform-browser"
import { RpcClient, RpcSerialization } from "@effect/rpc"
import { Effect, Layer } from "effect"
import { TodoApi } from "./api.js"

const SocketProtocol = RpcClient.layerProtocolSocket().pipe(
  Layer.provide([
    BrowserSocket.layerWebSocket("wss://api.example.com/rpc/socket"),
    RpcSerialization.layerJson
  ])
)

export const socketProgram = Effect.gen(function*() {
  const client = yield* RpcClient.make(TodoApi)
  return yield* client.Todos.Get({ id: "1" })
}).pipe(
  Effect.scoped,
  Effect.provide(SocketProtocol)
)
```

Use WebSocket when the transport should stay open, the server is already serving
`RpcServer.layerProtocolWebsocket`, or streaming RPCs need lower per-request
overhead than repeated HTTP requests.

## Worker transport

Worker transport uses a platform worker implementation and a worker spawner.
The worker itself runs the server protocol; the parent builds the client
protocol:

```typescript
import { BrowserWorker } from "@effect/platform-browser"
import { RpcClient } from "@effect/rpc"
import { Effect, Layer } from "effect"
import { TodoApi } from "./api.js"

const WorkerPlatform = BrowserWorker.layerPlatform(
  () => new Worker(new URL("./rpc-worker.js", import.meta.url), {
    type: "module"
  })
)

const WorkerProtocol = RpcClient.layerProtocolWorker({
  size: 2,
  concurrency: 8
}).pipe(
  Layer.provide(WorkerPlatform)
)

export const workerProgram = Effect.gen(function*() {
  const client = yield* RpcClient.make(TodoApi)
  return yield* client.Todos.Get({ id: "1" })
}).pipe(
  Effect.scoped,
  Effect.provide(WorkerProtocol)
)
```

Use Worker transport when RPC handlers should run in a worker thread or browser
worker and the parent should keep a typed client facade.

## Headers

Per-request headers are passed in the call options:

```typescript
const program = Effect.gen(function*() {
  const client = yield* RpcClient.make(TodoApi)
  return yield* client.Todos.Get(
    { id: "1" },
    { headers: { authorization: "Bearer redacted" } }
  )
})
```

For headers that apply to multiple calls, use `RpcClient.withHeaders`:

```typescript
const withAuth = RpcClient.withHeaders({
  authorization: "Bearer redacted"
})

const program = Effect.gen(function*() {
  const client = yield* RpcClient.make(TodoApi)
  return yield* withAuth(client.Todos.Get({ id: "1" }))
})
```

Do not read environment variables directly in client code. Use `Config` at the
edge that builds the layer.

## Flattened client

By default, dotted tags become nested methods. Passing `{ flatten: true }`
returns a function-style client:

```typescript
const program = Effect.gen(function*() {
  const client = yield* RpcClient.make(TodoApi, { flatten: true })
  return yield* client("Todos.Get", { id: "1" })
})
```

Prefer the nested client for application code. The flattened client is useful
for generic proxies, test harnesses, and tooling that receives tags dynamically.

## Streaming calls

For streaming RPCs, the client method returns a `Stream` by default:

```typescript
import { Stream } from "effect"

const program = Effect.gen(function*() {
  const client = yield* RpcClient.make(TodoApi)
  const titles = yield* client.Todos.Changes({ since: 0 }).pipe(
    Stream.map((todo) => todo.title),
    Stream.runCollect
  )
  yield* Effect.logInfo(`received ${titles.length} titles`)
})
```

Passing `{ asMailbox: true }` returns a scoped mailbox for manual consumption.
Use the stream form unless the consumer needs explicit pull or buffering
control.

## Client error model

A client call can fail with:

- the RPC's declared error schema,
- failures declared by middleware,
- transport/protocol failures represented by `RpcClientError`.

Do not put transport failures in the RPC `error` schema. Keep domain failures in
the RPC contract and infrastructure failures in the protocol layer.

## Client checklist

Before shipping a client:

- import the shared `RpcGroup`, not a duplicate type,
- choose one protocol layer for the current runtime,
- provide the same serialization as the server,
- provide platform layers required by the protocol,
- scope programs that create clients or consume streams,
- provide required client middleware layers.

## Cross-references

See also: [01-overview.md](01-overview.md), [03-rpc-server.md](03-rpc-server.md), [05-rpc-middleware.md](05-rpc-middleware.md), [06-rpc-streaming.md](06-rpc-streaming.md)
