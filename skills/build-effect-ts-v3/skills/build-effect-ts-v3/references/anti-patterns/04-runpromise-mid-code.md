# RunPromise Mid-code
Use this when library, service, route, or helper internals execute an Effect instead of returning an Effect.

## Symptom — Bad Code
```typescript
import { Effect } from "effect"

declare const reserveInventory: (sku: string) => Effect.Effect<void, Error>
declare const chargeCard: (sku: string) => Effect.Effect<void, Error>

export const checkout = async (sku: string) => {
  await Effect.runPromise(reserveInventory(sku))
  await Effect.runPromise(chargeCard(sku))
}
```

## Why Bad
Every runtime call starts a separate execution boundary.
Dependencies, retry policy, logs, spans, and interruption are no longer shared.
The function exposes Promise instead of honest Effect types.

## Fix — Correct Pattern
```typescript
import { Effect } from "effect"

declare const reserveInventory: (sku: string) => Effect.Effect<void, Error>
declare const chargeCard: (sku: string) => Effect.Effect<void, Error>

export const checkout = (sku: string) =>
  Effect.gen(function* () {
    yield* reserveInventory(sku)
    yield* chargeCard(sku)
  })
```

## Notes
Runtime calls are allowed at process entry points, test assertion edges, and framework adapters. They are not allowed inside domain services, repositories, or shared helpers.

## Cross-references
See also: [running effects](../core/03-running-effects.md), [services and layers](../services-layers/01-overview.md), [testing](../testing/01-overview.md).
