# Worker
Use `Worker` and `WorkerRunner` for schema-typed work in separate Node or Bun workers.

## Roles

The platform worker APIs separate caller and worker process concerns.

| Module | Side | Role |
|---|---|---|
| `Worker` | parent | Spawn workers and pools |
| `Worker.WorkerManager` | parent | Service tag for worker management |
| `Worker.Spawner` | parent | Describes how to create runtime workers |
| `WorkerRunner` | worker | Run handlers inside the worker |
| `NodeWorker` / `BunWorker` | parent | Runtime layers for worker manager and spawner |
| `NodeWorkerRunner` / `BunWorkerRunner` | worker | Runtime layer for worker runner |

Use workers for CPU-heavy or isolation-sensitive work. Do not use them for
ordinary async I/O that Effect can already schedule.

## Untyped Worker Shape

```typescript
import { Effect, Stream } from "effect"
import { Worker } from "@effect/platform"

export const runOne = (input: number) =>
  Effect.scoped(
    Effect.gen(function* () {
      const manager = yield* Worker.WorkerManager
      const worker = yield* manager.spawn<number, number, never>({})
      return yield* worker.execute(input).pipe(Stream.runHead)
    })
  )
```

The untyped API is useful for low-level adapters. Prefer serialized workers for
application messages.

## Tagged Request Schema

`Worker.makeSerialized` and `WorkerRunner.makeSerialized` use
`Schema.TaggedRequest`. Each request class declares input, success, and failure
schemas.

```typescript
import { Schema } from "effect"

class HashText extends Schema.TaggedRequest<HashText>()(
  "HashText",
  Schema.String,
  Schema.Never,
  {
    text: Schema.String
  }
) {}

export const WorkerProtocol = Schema.Union(HashText)
```

The request instance is both the message and the type-level connection to its
result.

## Parent Program

```typescript
import { Effect, Schema } from "effect"
import { Worker } from "@effect/platform"
import { NodeContext, NodeRuntime, NodeWorker } from "@effect/platform-node"

class HashText extends Schema.TaggedRequest<HashText>()(
  "HashText",
  Schema.String,
  Schema.Never,
  { text: Schema.String }
) {}

const WorkerProtocol = Schema.Union(HashText)

declare const spawnWorker: Parameters<typeof NodeWorker.layer>[0]

const WorkerLive = NodeWorker.layer(spawnWorker)

const program = Effect.scoped(
  Effect.gen(function* () {
    const worker = yield* Worker.makeSerialized<typeof WorkerProtocol.Type>({})
    const digest = yield* worker.executeEffect(new HashText({ text: "abc" }))
    yield* Effect.logInfo(`Digest: ${digest}`)
  })
)

program.pipe(
  Effect.provide(WorkerLive),
  Effect.provide(NodeContext.layer),
  NodeRuntime.runMain
)
```

`NodeWorker.layer` provides `WorkerManager` and `Spawner`. `NodeContext.layer`
already includes a default worker manager, but explicit spawners are common
when the worker file is application-specific.

## Worker Runner

```typescript
import { Effect, Schema } from "effect"
import { WorkerRunner } from "@effect/platform"
import { NodeRuntime, NodeWorkerRunner } from "@effect/platform-node"

class HashText extends Schema.TaggedRequest<HashText>()(
  "HashText",
  Schema.String,
  Schema.Never,
  { text: Schema.String }
) {}

const WorkerProtocol = Schema.Union(HashText)

const WorkerLive = WorkerRunner.layerSerialized(WorkerProtocol, {
  HashText: ({ text }) => Effect.succeed(`hash:${text.length}`)
}).pipe(
  Effect.provide(NodeWorkerRunner.layer)
)

NodeRuntime.runMain(WorkerRunner.launch(WorkerLive))
```

`WorkerRunner.launch` keeps the worker alive and interrupts it when the parent
signals closure through the platform runner.

## Worker Pools

Use `Worker.makePoolSerialized` when the parent needs bounded parallelism across
multiple workers.

```typescript
import { Effect, Schema } from "effect"
import { Worker } from "@effect/platform"

class HashText extends Schema.TaggedRequest<HashText>()(
  "HashText",
  Schema.String,
  Schema.Never,
  { text: Schema.String }
) {}

const WorkerProtocol = Schema.Union(HashText)

export const hashMany = (texts: ReadonlyArray<string>) =>
  Effect.scoped(
    Effect.gen(function* () {
      const pool = yield* Worker.makePoolSerialized<typeof WorkerProtocol.Type>({
        size: 4
      })

      return yield* Effect.all(
        texts.map((text) => pool.executeEffect(new HashText({ text }))),
        { concurrency: 4 }
      )
    })
  )
```

Keep pool size and Effect concurrency aligned with the resource you are trying
to protect.

## Initial Messages

If the request union contains an `InitialMessage` tag, serialized worker options
require `initialMessage`. Use that to send configuration once when the worker is
created.

## Layered Pools

`Worker.makePoolSerializedLayer(tag, options)` packages a serialized pool as a
layer. Reach for it when multiple services share one pool and the pool should be
acquired once with the application graph.

## Error Model

Worker APIs can fail with `WorkerError`. Serialized workers can also fail with
schema parse errors and request-specific failure schemas. Avoid collapsing these
into generic strings; preserve the typed channel until a boundary can decide
whether to retry, report, or stop.

## Anti-patterns

- Using workers for regular file or network I/O.
- Sending untyped records when `Schema.TaggedRequest` fits.
- Creating an unbounded worker pool.
- Forgetting `Effect.scoped` around spawned workers.
- Hiding worker startup inside reusable business functions.

## Cross-references

See also: [08-ndjson.md](08-ndjson.md), [11-node-context.md](11-node-context.md), [12-node-runtime.md](12-node-runtime.md), [13-bun-platform.md](13-bun-platform.md)
