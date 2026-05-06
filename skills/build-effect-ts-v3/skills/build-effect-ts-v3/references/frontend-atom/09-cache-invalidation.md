# Cache Invalidation
Use `reactivityKeys` and `Atom.withReactivity` to refresh query atoms after related mutations complete.

## Mental Model

Effect Atom integrates with `@effect/experimental` Reactivity.
Queries register keys.
Mutations invalidate keys.
Registered atoms refresh when their keys are invalidated.

This replaces manual refresh chains when a mutation changes data that a query
depends on.

## Register Query Keys

Use `Atom.withReactivity(keys)` on a query atom.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect, Layer } from "effect"

const runtime = Atom.runtime(Layer.empty)

const countAtom = runtime.atom(
  Effect.succeed(1)
).pipe(
  Atom.withReactivity(["count"]),
  Atom.keepAlive
)
```

The atom refreshes when the `"count"` key is invalidated.

## Invalidate From Mutations

Pass matching `reactivityKeys` to `runtime.fn`.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect, Layer } from "effect"

const runtime = Atom.runtime(Layer.empty)

const incrementAtom = runtime.fn(
  () => Effect.succeed(2),
  { reactivityKeys: ["count"] }
)
```

When `incrementAtom` finishes, the `"count"` query key is invalidated.

## Structured Keys

Keys can be an array or a readonly record of arrays.
Use structured keys when several query scopes exist under one domain.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect, Layer } from "effect"

const runtime = Atom.runtime(Layer.empty)

const projectListAtom = runtime.atom(
  Effect.succeed(["p-1"])
).pipe(
  Atom.withReactivity({ projects: ["org-1"] })
)

const renameProjectAtom = runtime.fn(
  (projectId: string) => Effect.succeed(projectId),
  { reactivityKeys: { projects: ["org-1"] } }
)
```

Keep key domains small and explicit.
Do not use one global key for unrelated data.

## RPC Queries And Mutations

`AtomRpc.Tag` query options support `reactivityKeys`.
Mutation setters also accept `reactivityKeys` in their payload.

```typescript
import { AtomRpc, Result, useAtomSet, useAtomValue } from "@effect-atom/atom-react"
import { BrowserSocket } from "@effect/platform-browser"
import { Rpc, RpcClient, RpcGroup, RpcSerialization } from "@effect/rpc"
import { Layer, Schema } from "effect"

class CountRpcs extends RpcGroup.make(
  Rpc.make("increment"),
  Rpc.make("count", { success: Schema.Number })
) {}

class CountClient extends AtomRpc.Tag<CountClient>()("CountClient", {
  group: CountRpcs,
  protocol: RpcClient.layerProtocolSocket({
    retryTransientErrors: true
  }).pipe(
    Layer.provide(BrowserSocket.layerWebSocket("ws://localhost:3000/rpc")),
    Layer.provide(RpcSerialization.layerJson)
  )
}) {}

const countAtom = CountClient.query("count", void 0, {
  reactivityKeys: ["count"]
})

export function CountButton() {
  const count = useAtomValue(countAtom)
  const increment = useAtomSet(CountClient.mutation("increment"))

  return {
    count: Result.getOrElse(count, () => 0),
    increment: () =>
      increment({
        payload: void 0,
        reactivityKeys: ["count"]
      })
  }
}
```

The query and mutation agree on the same key.

## Time To Live

RPC and HTTP API query helpers accept `timeToLive`.
Finite TTL values idle-dispose the atom after the duration.
Infinite TTL keeps the atom alive.

Use `timeToLive` for generated client queries.
Use `Atom.keepAlive` directly for custom atoms.

## Manual Invalidation

Use manual invalidation only inside Effect code that cannot use mutation options.

```typescript
import { Reactivity } from "@effect/experimental"
import { Atom } from "@effect-atom/atom-react"
import { Effect, Layer } from "effect"

const runtime = Atom.runtime(Layer.empty)

const manualMutationAtom = runtime.fn(() =>
  Effect.gen(function* () {
    yield* Effect.log("changed count")
    yield* Reactivity.invalidate(["count"])
  })
)
```

Prefer mutation options when they express the same behavior.

## Review Checklist

- Query atoms register keys with `Atom.withReactivity` or client query options.
- Mutations invalidate the same key shape.
- Keys are scoped enough to avoid broad refresh storms.
- Manual refresh is reserved for explicit user actions.
- Manual Reactivity invalidation is limited to advanced Effect code.
- Long-lived reactive queries also use `Atom.keepAlive`.

## Cross-references

See also: [03 Atom Families](03-atom-families.md), [04 Keep Alive](04-keep-alive.md), [08 Mutations](08-mutations.md), [11 Runtime Bridge](11-effect-runtime-bridge.md), [12 Vercel AI SDK](12-vercel-ai-sdk.md).
