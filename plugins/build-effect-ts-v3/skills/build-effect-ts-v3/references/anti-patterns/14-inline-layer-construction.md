# Inline Layer Construction
Use this when reusable layers are constructed inside functions, loops, or route handlers.

## Symptom — Bad Code
```typescript
import { Context, Effect, Layer } from "effect"

class Cache extends Context.Tag("Cache")<Cache, { readonly get: (key: string) => Effect.Effect<string> }>() {}

declare const makeCache: Effect.Effect<{ readonly get: (key: string) => Effect.Effect<string> }>

const handler = (key: string) =>
  Effect.gen(function* () {
    const layer = Layer.effect(Cache, makeCache)
    const cache = yield* Effect.provide(Cache, layer)
    return yield* cache.get(key)
  })
```

## Why Bad
The layer is recreated each time the handler description is built.
Inline layers hide application composition and memoization behavior.
Assistants often duplicate inline live layers instead of reusing canonical layers.

## Fix — Correct Pattern
```typescript
import { Context, Effect, Layer } from "effect"

class Cache extends Context.Tag("Cache")<Cache, { readonly get: (key: string) => Effect.Effect<string> }>() {}

declare const makeCache: Effect.Effect<{ readonly get: (key: string) => Effect.Effect<string> }>

const CacheLive = Layer.effect(Cache, makeCache)

const handler = (key: string) =>
  Effect.gen(function* () {
    const cache = yield* Cache
    return yield* cache.get(key)
  }).pipe(Effect.provide(CacheLive))
```

## Cross-references
See also: [layer composition gotchas](../services-layers/12-layer-composition-gotchas.md), [layer composition](../services-layers/09-layer-merge.md), [context tags](../services-layers/02-context-tag.md).
