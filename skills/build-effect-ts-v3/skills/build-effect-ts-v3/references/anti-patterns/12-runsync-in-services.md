# RunSync Inside Services
Use this when a service method executes an Effect internally instead of returning an Effect to its caller.

## Symptom — Bad Code
```typescript
import { Effect } from "effect"

declare const readConfig: Effect.Effect<{ readonly limit: number }>

export const UserServiceLive = {
  list: () => {
    const config = Effect.runSync(readConfig)
    return Effect.succeed([`limit:${config.limit}`])
  }
}
```

## Why Bad
The service method creates a hidden runtime boundary.
Requirements and failures from `readConfig` no longer compose with callers.
Synchronous execution pressures authors to cast away richer effects.

## Fix — Correct Pattern
```typescript
import { Effect } from "effect"

declare const readConfig: Effect.Effect<{ readonly limit: number }>

export const UserServiceLive = {
  list: () =>
    Effect.gen(function* () {
      const config = yield* readConfig
      return [`limit:${config.limit}`]
    })
}
```

## Cross-references
See also: [running effects](../core/03-running-effects.md), [services and layers](../services-layers/01-overview.md), [testing](../testing/01-overview.md).
