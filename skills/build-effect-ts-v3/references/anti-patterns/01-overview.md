# Anti-pattern Catalog
Use this directory when Effect v3 code looks plausible but loses typed errors, requirements, interruption, logging, or source-verified API names.

## Symptom — Bad Code
The smell is misplaced Effect boundaries: running instead of composing, throwing instead of failing, direct platform access instead of services, or vague errors instead of tags.

```typescript
import { Effect } from "effect"

declare const fetchUser: (id: string) => Effect.Effect<{ readonly id: string }, Error>
declare const fetchPosts: (id: string) => Effect.Effect<ReadonlyArray<string>, Error>

const handler = async (id: string) => {
  const user = await Effect.runPromise(fetchUser(id))
  const posts = await Effect.runPromise(fetchPosts(user.id))
  return { user, posts }
}
```

## Why Bad
This splits one workflow into multiple unmanaged runtime launches.
Failures, requirements, logs, spans, and interruption stop composing.
Use this catalog as negative training, then jump to the positive reference.

## Fix — Correct Pattern
```typescript
import { Effect } from "effect"

declare const fetchUser: (id: string) => Effect.Effect<{ readonly id: string }, Error>
declare const fetchPosts: (id: string) => Effect.Effect<ReadonlyArray<string>, Error>

const workflow = (id: string) =>
  Effect.gen(function* () {
    const user = yield* fetchUser(id)
    const posts = yield* fetchPosts(user.id)
    return { user, posts }
  })
```

## Notes
Start with the concrete symptom file: generator misuse, throwing, runtime calls, unbounded concurrency, broad catches, generic errors, direct diagnostics, direct configuration, nullable domain values, unsafe Option extraction, service runtime calls, layer confusion, inline layers, manual cleanup, Promise constructor mistakes, casts, assistant hallucinations, or quarantined syntax.

## Cross-references
See also: [core generators](../core/05-generators.md), [creating effects](../core/02-creating-effects.md), [error handling](../error-handling/01-overview.md).
