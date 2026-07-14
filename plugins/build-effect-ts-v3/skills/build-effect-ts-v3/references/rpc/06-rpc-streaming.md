# RPC Streaming
Use this when an RPC should return a `Stream` from the server and a typed `Stream` on the client.

Streaming RPCs are declared with `stream: true` on `Rpc.make`. The `success`
schema becomes the stream item schema, and the `error` schema becomes the stream
failure schema inside `RpcSchema.Stream`.

The server handler returns a `Stream` instead of a single `Effect` success.

## Declaring a streaming RPC

```typescript
import { Rpc, RpcGroup } from "@effect/rpc"
import { Schema } from "effect"

class TodoEvent extends Schema.Class<TodoEvent>("TodoEvent")({
  id: Schema.String,
  title: Schema.String,
  revision: Schema.Number
}) {}

class TodoStreamError extends Schema.TaggedError<TodoStreamError>()(
  "TodoStreamError",
  { reason: Schema.String }
) {}

export class TodoEventsApi extends RpcGroup.make(
  Rpc.make("Todos.Events", {
    payload: { sinceRevision: Schema.Number },
    success: TodoEvent,
    error: TodoStreamError,
    stream: true
  })
) {}
```

Do not wrap the success schema in `Stream.Stream` yourself. `stream: true` tells
`Rpc.make` to construct the RPC stream schema.

## Server handler

The handler for a streaming RPC returns a `Stream`:

```typescript
import { Effect, Stream } from "effect"
import { TodoEventsApi } from "./api.js"

const TodoEventsHandlers = TodoEventsApi.toLayer({
  "Todos.Events": ({ sinceRevision }) =>
    Stream.fromIterable([
      new TodoEvent({
        id: "1",
        title: "Write docs",
        revision: sinceRevision + 1
      }),
      new TodoEvent({
        id: "2",
        title: "Review docs",
        revision: sinceRevision + 2
      })
    ]).pipe(
      Stream.tap((event) => Effect.logDebug(`emit ${event.id}`))
    )
})
```

The stream can fail with the declared stream error:

```typescript
const failingHandler = TodoEventsApi.toLayer({
  "Todos.Events": () =>
    Stream.fail(new TodoStreamError({ reason: "event source unavailable" }))
})
```

## Client consumption

The client method returns a `Stream` by default:

```typescript
import { RpcClient } from "@effect/rpc"
import { Effect, Stream } from "effect"
import { TodoEventsApi } from "./api.js"

const program = Effect.gen(function*() {
  const client = yield* RpcClient.make(TodoEventsApi)

  const count = yield* client.Todos.Events({ sinceRevision: 10 }).pipe(
    Stream.tap((event) => Effect.logInfo(`received ${event.id}`)),
    Stream.runCount
  )

  yield* Effect.logInfo(`received ${count} events`)
})
```

Scope the program when providing a protocol layer. Streams use scoped protocol
resources and request tracking.

## Mailbox mode

Passing `{ asMailbox: true }` returns a scoped `ReadonlyMailbox` instead of a
`Stream`. This is lower level and useful when a consumer needs explicit mailbox
operations:

```typescript
const mailboxProgram = Effect.gen(function*() {
  const client = yield* RpcClient.make(TodoEventsApi)
  const mailbox = yield* client.Todos.Events(
    { sinceRevision: 10 },
    { asMailbox: true, streamBufferSize: 32 }
  )
  yield* Effect.logInfo(`mailbox ready ${mailbox}`)
})
```

Prefer normal stream consumption for application workflows.

## Streaming errors

For streaming RPCs, the declared `error` schema is not the top-level RPC error
schema. It is encoded as the stream failure schema. On the client, stream
consumption can fail with:

- the stream error declared in `Rpc.make`,
- middleware failures,
- protocol failures from the client transport.

Handle stream failures with stream operators, not try/catch:

```typescript
const resilient = Effect.gen(function*() {
  const client = yield* RpcClient.make(TodoEventsApi)
  return yield* client.Todos.Events({ sinceRevision: 0 }).pipe(
    Stream.catchAll((error) =>
      Stream.fromEffect(Effect.logWarning(`stream failed ${error}`)).pipe(
        Stream.drain
      )
    ),
    Stream.runDrain
  )
})
```

## Transport choice

Streaming works across the RPC protocols, but operational behavior differs:

| Transport | Fit |
|---|---|
| HTTP | Good default for request/response and streaming HTTP endpoints. |
| WebSocket | Good for long-lived bidirectional sessions and repeated streams. |
| Worker | Good when the producer runs inside a worker process or browser worker. |

Choose transport at the layer boundary. Do not change the `RpcGroup` to switch
transports.

## Streaming checklist

Before shipping a streaming RPC:

- set `stream: true` on `Rpc.make`,
- make `success` the item schema,
- make `error` the stream failure schema,
- return `Stream` from the server handler,
- consume the client method as a `Stream`,
- scope the program that opens the stream,
- set protocol and serialization layers consistently on both sides.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-rpc-group.md](02-rpc-group.md), [03-rpc-server.md](03-rpc-server.md), [04-rpc-client.md](04-rpc-client.md)
