# Vercel AI SDK
Bridge Effect Schema to Vercel AI SDK `inputSchema` with `Schema.standardSchemaV1`, and run service-backed tool effects through a captured runtime.

## Schema Bridge

Vercel AI SDK tools use an `inputSchema` to describe and validate tool input.
Effect v3 provides `Schema.standardSchemaV1` for Standard Schema v1 interop.

Use it directly on the tool definition.

```typescript
import { Schema } from "effect"
import { tool } from "ai"

const SearchInput = Schema.Struct({
  query: Schema.String.annotations({
    description: "Search query"
  }),
  limit: Schema.Number.pipe(
    Schema.int(),
    Schema.between(1, 20)
  )
})

export const searchTool = tool({
  description: "Search project documents",
  inputSchema: Schema.standardSchemaV1(SearchInput),
  execute: async ({ query, limit }) => ({
    query,
    limit
  })
})
```

The schema remains Effect Schema.
The AI SDK receives a Standard Schema-compatible value.

## No-Argument Tools

For no-argument tools, use a schema that providers accept as an object shape.
The cached guidance recommends a record with `Schema.Never` values instead of
an empty schema.

```typescript
import { Schema } from "effect"
import { tool } from "ai"

const NoInput = Schema.Record({
  key: Schema.String,
  value: Schema.Never
})

export const healthTool = tool({
  description: "Read service health",
  inputSchema: Schema.standardSchemaV1(NoInput),
  execute: async () => ({ status: "ok" })
})
```

Use a real struct when the tool has parameters.
Use this pattern only for no-argument tools.

## Runtime Capture Pattern

When a tool needs Effect services, capture a runtime inside an Effect factory.
Then use `Runtime.runPromise(runtime)` inside the async `execute` function.

```typescript
import { Effect, Runtime, Schema } from "effect"
import { tool } from "ai"

class Inventory extends Effect.Service<Inventory>()("app/Inventory", {
  succeed: {
    reserve: (sku: string, quantity: number) =>
      Effect.succeed({
        sku,
        quantity,
        reserved: true
      })
  }
}) {}

const ReserveInput = Schema.Struct({
  sku: Schema.String,
  quantity: Schema.Number.pipe(
    Schema.int(),
    Schema.greaterThan(0)
  )
})

export const makeReserveTool = Effect.gen(function* () {
  const runtime = yield* Effect.runtime<Inventory>()

  return tool({
    description: "Reserve inventory for an order",
    inputSchema: Schema.standardSchemaV1(ReserveInput),
    execute: async ({ sku, quantity }) =>
      Runtime.runPromise(runtime)(
        Effect.gen(function* () {
          const inventory = yield* Inventory
          return yield* inventory.reserve(sku, quantity)
        })
      )
  })
})
```

This is the required pattern for service-backed AI SDK tools:
`Effect.runtime<Deps>()` plus `Runtime.runPromise`.

## Providing The Tool Factory

The factory still needs its services.
Provide the layer at the application edge that builds the tool set.

```typescript
import { Effect } from "effect"

const toolsProgram = Effect.gen(function* () {
  const reserve = yield* makeReserveTool
  return { reserve }
}).pipe(
  Effect.provide(Inventory.Default)
)
```

Run that program at the server or route boundary where Promise interop is
allowed.
Do not move the runtime run into service or domain code.

## Tool With Typed Domain Errors

AI SDK `execute` returns a Promise.
If the model-facing tool should return a structured failure payload instead of
rejecting, handle typed failures before `Runtime.runPromise` resolves.

```typescript
import { Data, Effect, Runtime, Schema } from "effect"
import { tool } from "ai"

class OutOfStock extends Data.TaggedError("OutOfStock")<{
  readonly sku: string
}> {}

class Warehouse extends Effect.Service<Warehouse>()("app/Warehouse", {
  succeed: {
    pick: (sku: string) =>
      sku === "empty"
        ? Effect.fail(new OutOfStock({ sku }))
        : Effect.succeed({ sku, picked: true })
  }
}) {}

const PickInput = Schema.Struct({
  sku: Schema.String
})

export const makePickTool = Effect.gen(function* () {
  const runtime = yield* Effect.runtime<Warehouse>()

  return tool({
    description: "Pick an item from the warehouse",
    inputSchema: Schema.standardSchemaV1(PickInput),
    execute: async ({ sku }) =>
      Runtime.runPromise(runtime)(
        Effect.gen(function* () {
          const warehouse = yield* Warehouse
          return yield* warehouse.pick(sku)
        }).pipe(
          Effect.catchTag("OutOfStock", (error) =>
            Effect.succeed({
              picked: false,
              reason: "out_of_stock",
              sku: error.sku
            })
          )
        )
      )
  })
})
```

Only translate errors at the tool boundary.
Keep internal services typed.

## Frontend Atom Relationship

Effect Atom and AI SDK tools solve different integration points.

| Need | Use |
|---|---|
| React state around an Effect query | `runtime.atom` |
| React command with waiting state | `runtime.fn` |
| AI SDK tool input validation | `Schema.standardSchemaV1` |
| AI SDK tool service execution | captured runtime plus `Runtime.runPromise` |

Do not call AI SDK tool factories from React render.
Build tools at a server or agent boundary and pass results into UI state if
needed.

## Cross-references

See also: [06 Result Builder](06-result-builder.md), [08 Mutations](08-mutations.md), [09 Cache Invalidation](09-cache-invalidation.md), [11 Runtime Bridge](11-effect-runtime-bridge.md), [../schema/15-json-schema.md](../schema/15-json-schema.md).
