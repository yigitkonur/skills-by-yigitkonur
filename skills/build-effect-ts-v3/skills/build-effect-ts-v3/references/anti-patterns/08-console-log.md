# Console Logging in Effect Code
Use this when diagnostics are written directly instead of going through Effect logging.

## Symptom — Bad Code
```typescript
import { Effect } from "effect"

const audit = (orderId: string) =>
  Effect.sync(() => {
    globalThis.console.info(`created order ${orderId}`)
  })
```

## Why Bad
Direct output bypasses fiber annotations, spans, logger replacement, filtering, and test capture.
Wrapping direct output in `Effect.sync` does not make it structured logging.
Secrets and identifiers are easier to mishandle in unstructured strings.

## Fix — Correct Pattern
```typescript
import { Effect } from "effect"

const audit = (orderId: string) =>
  Effect.logInfo("created order", { orderId })
```

## Cross-references
See also: [logging](../observability/02-logging-basics.md), [spans](../observability/06-tracing-basics.md), [core effects](../core/02-creating-effects.md).
