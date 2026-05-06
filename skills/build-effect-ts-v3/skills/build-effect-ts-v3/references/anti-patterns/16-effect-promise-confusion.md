# Effect.promise Confusion
Use this when a rejecting Promise is wrapped with Effect.promise and failures become defects.

## Symptom — Bad Code
```typescript
import { Effect } from "effect"

declare const fetchJson: (url: string) => Promise<unknown>

const load = (url: string) =>
  Effect.promise(() => fetchJson(url))
```

## Why Bad
`Effect.promise` is for async work that cannot reject in the modeled domain.
Most external IO promises can reject and should map rejection into typed failure.
The wrong constructor removes the failure from the error channel.

## Fix — Correct Pattern
```typescript
import { Data, Effect } from "effect"

class HttpRequestError extends Data.TaggedError("HttpRequestError")<{
  readonly url: string
  readonly cause: unknown
}> {}

declare const fetchJson: (url: string) => Promise<unknown>

const load = (url: string) =>
  Effect.tryPromise({
    try: () => fetchJson(url),
    catch: (cause) => new HttpRequestError({ url, cause })
  })
```

## Notes
Use `Effect.succeed` for pure values, `Effect.sync` for synchronous side effects that cannot throw, `Effect.try` for synchronous throwing work, and `Effect.tryPromise` for rejecting promises.

## Cross-references
See also: [core generators](../core/05-generators.md), [creating effects](../core/02-creating-effects.md), [error handling](../error-handling/01-overview.md).
