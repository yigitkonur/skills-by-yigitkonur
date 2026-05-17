# Direct Environment Reads
Use this when code reads ambient environment variables directly instead of using Config.

## Symptom — Bad Code
```typescript
import { Effect } from "effect"

declare const unsafeEnvironment: Record<string, string | undefined>

const ApiKey = Effect.sync(() => unsafeEnvironment["API_KEY"] ?? "dev-key")
```

## Why Bad
Ambient reads hide configuration requirements from the Effect type and layer composition.
Silent fallbacks make deployments appear healthy when required configuration is missing.
Secret values need redaction semantics before logs or errors can touch them.

## Fix — Correct Pattern
```typescript
import { Config, Effect } from "effect"

const ApiKey = Config.redacted("API_KEY")

const program = Effect.gen(function* () {
  const apiKey = yield* ApiKey
  return apiKey
})
```

## Cross-references
See also: [config overview](../config/01-overview.md), [secrets](../config/03-config-redacted.md), [layers](../services-layers/01-overview.md).
