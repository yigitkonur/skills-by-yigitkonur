# Shutdown And Signals
Run servers with `Layer.launch(...).pipe(NodeRuntime.runMain)` so scopes close on process shutdown.

## Process Edge

For Node applications, use `NodeRuntime.runMain` at the entry point.

```typescript
import { NodeRuntime } from "@effect/platform-node"
import { Layer } from "effect"

Layer.launch(ServerLive).pipe(NodeRuntime.runMain)
```

This is the edge where the Effect runtime owns the process lifecycle. Do not use
`Effect.runPromise` inside library or service code to start servers.

## Scoped Server Lifetime

`NodeHttpServer.layer` is scoped. When the launched layer scope closes, the
server is closed and in-flight scoped resources are released.

```typescript
import { HttpApiBuilder, HttpServer } from "@effect/platform"
import { NodeHttpServer, NodeRuntime } from "@effect/platform-node"
import { Layer } from "effect"
import { createServer } from "node:http"

const ServerLive = HttpApiBuilder.serve().pipe(
  Layer.provide(ApiLive),
  HttpServer.withLogAddress,
  Layer.provide(NodeHttpServer.layer(createServer, { port: 3000 }))
)

Layer.launch(ServerLive).pipe(NodeRuntime.runMain)
```

Keep acquisition and release in layers so shutdown is coordinated by the scope.

## In-Flight Requests

Most request effects should remain interruptible. If shutdown interrupts the
server scope, interruptible work can stop promptly.

Use uninterruptible handlers only for critical sections:

```typescript
handlers.handle(
  "commitPayment",
  ({ payload }) => Payments.charge(payload),
  { uninterruptible: true }
)
```

Do not mark long-running streams or ordinary reads as uninterruptible. That can
delay shutdown.

## Resource Cleanup

Use scoped services for resources that must close:

```typescript
import { Context, Effect, Layer } from "effect"

class Connections extends Context.Tag("Connections")<
  Connections,
  { readonly close: Effect.Effect<void> }
>() {}

const ConnectionsLive = Layer.scoped(
  Connections,
  Effect.acquireRelease(
    Effect.succeed({ close: Effect.void }),
    (connections) => connections.close
  )
)
```

Provide scoped services into handlers through layers. Do not attach cleanup to
ad hoc process event handlers when a layer can own it.

## Signals

`NodeRuntime.runMain` is the process-level runner for server entry points. It is
the right place to let Effect handle interruption and reporting behavior.

If an application needs custom signal behavior, keep it at the process edge and
interrupt the launched Effect runtime rather than bypassing layer scopes.

## Draining Work

For work that must complete after a request starts, make the smallest critical
section uninterruptible and leave the rest interruptible.

```typescript
const charge = Effect.uninterruptible(
  Payments.commitAuthorizedCharge(payload)
)
```

Do not wrap the whole server or all handlers in uninterruptible regions. That
prevents normal shutdown from interrupting long-running reads, uploads, and
streams.

## Streaming Shutdown

Streaming responses should be interruptible and resource-scoped.

```typescript
import { Effect, Stream } from "effect"

const stream = Stream.acquireRelease(
  Effect.succeed({ close: Effect.void }),
  (resource) => resource.close
).pipe(
  Stream.flatMap(() => Stream.fromIterable([new Uint8Array([1])]))
)
```

When the server scope closes, stream finalizers get a chance to release handles.

## Cross-references

See also: [15-serving.md](15-serving.md), [13-streaming-responses.md](13-streaming-responses.md), [07-handlers.md](07-handlers.md), [16-platform-router.md](16-platform-router.md)
