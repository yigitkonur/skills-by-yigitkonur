# Unbounded Parallelism
Use this when a dynamic collection starts all effects at once without an explicit concurrency bound.

## Symptom — Bad Code
```typescript
import { Effect } from "effect"

declare const fetchProfile: (id: string) => Effect.Effect<{ readonly id: string }, Error>

const loadProfiles = (ids: ReadonlyArray<string>) =>
  Effect.all(ids.map((id) => fetchProfile(id)))
```

## Why Bad
For fixed tiny tuples this can be fine; for user-sized collections it is unsafe.
Unbounded fibers can overwhelm APIs, pools, file descriptors, and retry budgets.
The missing bound is operational, not a type error.

## Fix — Correct Pattern
```typescript
import { Effect } from "effect"

declare const fetchProfile: (id: string) => Effect.Effect<{ readonly id: string }, Error>

const loadProfiles = (ids: ReadonlyArray<string>) =>
  Effect.all(
    ids.map((id) => fetchProfile(id)),
    { concurrency: 8 }
  )
```

## Notes
Require explicit concurrency when input comes from a request, database, file, queue, API page, crawler, or any source that can exceed five items.

## Cross-references
See also: [concurrency overview](../concurrency/01-overview.md), [Effect.all](../concurrency/05-effect-all-concurrency.md), [interruption](../concurrency/11-interruption.md).
