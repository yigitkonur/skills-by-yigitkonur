# Match.tag
Use `Match.tag` for exhaustive matching over objects that have a `_tag` field.

`Match.tag` is the Effect v3 pattern for discriminated unions whose discriminator
is named `_tag`.

It only works for objects with a `_tag` field. For unions discriminated by a
different field, use `Match.discriminator("field")` or `Match.when` with object
patterns.

## The Shape It Expects

```typescript
import { Match } from "effect"

type Download =
  | { readonly _tag: "Waiting"; readonly id: string }
  | { readonly _tag: "Started"; readonly id: string; readonly bytes: number }
  | { readonly _tag: "Finished"; readonly id: string; readonly path: string }
  | { readonly _tag: "Failed"; readonly id: string; readonly reason: string }

const renderDownload = (download: Download): string =>
  Match.value(download).pipe(
    Match.tag("Waiting", (waiting) => `waiting ${waiting.id}`),
    Match.tag("Started", (started) => `started ${started.bytes}`),
    Match.tag("Finished", (finished) => `saved ${finished.path}`),
    Match.tag("Failed", (failed) => `failed ${failed.reason}`),
    Match.exhaustive
  )
```

Each handler receives the narrowed member of the union. Inside the `"Finished"`
handler, `path` exists. Inside the `"Failed"` handler, `reason` exists.

## Manual Switch Loses The Main Guardrail

This is the branch shape agents often write:

```typescript
type Download =
  | { readonly _tag: "Waiting"; readonly id: string }
  | { readonly _tag: "Started"; readonly id: string; readonly bytes: number }
  | { readonly _tag: "Finished"; readonly id: string; readonly path: string }
  | { readonly _tag: "Failed"; readonly id: string; readonly reason: string }

const renderDownload = (download: Download): string => {
  switch (download._tag) {
    case "Waiting":
      return `waiting ${download.id}`
    case "Started":
      return `started ${download.bytes}`
    case "Finished":
      return `saved ${download.path}`
    default:
      return "not available"
  }
}
```

The `default` branch hides `"Failed"`. If a new tag is added later, the function
still compiles and silently routes that case to a generic branch.

With `Match.tag` and `Match.exhaustive`, the missing case is a type error at the
matcher finalizer:

```typescript
import { Match } from "effect"

type Download =
  | { readonly _tag: "Waiting"; readonly id: string }
  | { readonly _tag: "Started"; readonly id: string; readonly bytes: number }
  | { readonly _tag: "Finished"; readonly id: string; readonly path: string }
  | { readonly _tag: "Failed"; readonly id: string; readonly reason: string }

const renderDownload = (download: Download): string =>
  Match.value(download).pipe(
    Match.tag("Waiting", (waiting) => `waiting ${waiting.id}`),
    Match.tag("Started", (started) => `started ${started.bytes}`),
    Match.tag("Finished", (finished) => `saved ${finished.path}`),
    Match.tag("Failed", (failed) => `failed ${failed.reason}`),
    Match.exhaustive
  )
```

That is why `Match.exhaustive` is better than a manual default branch for closed
tagged unions. A default branch answers "what if I missed something?" by hiding
the miss. `Match.exhaustive` answers by refusing to compile.

## Match Multiple Tags With One Handler

`Match.tag` accepts one or more tags before the handler. Use this when cases share
the same outcome.

```typescript
import { Match } from "effect"

type QueueState =
  | { readonly _tag: "Idle" }
  | { readonly _tag: "Queued"; readonly position: number }
  | { readonly _tag: "Running"; readonly startedAt: Date }
  | { readonly _tag: "Paused"; readonly reason: string }

const isWaiting = Match.type<QueueState>().pipe(
  Match.tag("Idle", "Queued", "Paused", () => true),
  Match.tag("Running", () => false),
  Match.exhaustive
)
```

Only group cases when they really have the same behavior. If the handler starts
checking the tag again, split the cases.

## `Match.tagsExhaustive` Shorthand

When every tag maps directly to one handler, `Match.tagsExhaustive` is shorter
than several `Match.tag` calls plus `Match.exhaustive`.

```typescript
import { Match } from "effect"

type Operation =
  | { readonly _tag: "Create"; readonly name: string }
  | { readonly _tag: "Update"; readonly id: string }
  | { readonly _tag: "Remove"; readonly id: string }

const describeOperation = Match.type<Operation>().pipe(
  Match.tagsExhaustive({
    Create: (operation) => `create ${operation.name}`,
    Update: (operation) => `update ${operation.id}`,
    Remove: (operation) => `remove ${operation.id}`
  })
)
```

`Match.tagsExhaustive` requires a handler for every `_tag` in the union. Extra
keys are rejected, and missing keys are rejected.

Use it when:

- each tag has one handler
- there is no case grouping
- the handler table is easier to scan than a pipeline
- exhaustive matching is mandatory

Use chained `Match.tag` when:

- multiple tags share one handler
- you need `Match.withReturnType`
- the order of case definitions improves readability
- you combine tag cases with `Match.when`

## `_tag` Constraint

This does not fit `Match.tag`:

```typescript
type ApiEvent =
  | { readonly kind: "Opened"; readonly id: string }
  | { readonly kind: "Closed"; readonly id: string }
```

The discriminator is `kind`, not `_tag`.

Use `Match.discriminator("kind")`:

```typescript
import { Match } from "effect"

type ApiEvent =
  | { readonly kind: "Opened"; readonly id: string }
  | { readonly kind: "Closed"; readonly id: string }

const renderApiEvent = Match.type<ApiEvent>().pipe(
  Match.discriminator("kind")("Opened", (event) => `opened ${event.id}`),
  Match.discriminator("kind")("Closed", (event) => `closed ${event.id}`),
  Match.exhaustive
)
```

Do not rename domain fields only to use `Match.tag`. Use the right matcher for
the existing discriminant.

## Pairing With Tagged Error Handling

`Effect.catchTag` handles tagged failures while they are still in the Effect
error channel. `Match.tag` handles tagged values after you already have them.

```typescript
import { Match } from "effect"

type AppError =
  | { readonly _tag: "ValidationError"; readonly field: string }
  | { readonly _tag: "NetworkError"; readonly retryAfter: number }
  | { readonly _tag: "PermissionError"; readonly permission: string }

const errorMessage = Match.type<AppError>().pipe(
  Match.tag("ValidationError", (error) => `invalid ${error.field}`),
  Match.tag("NetworkError", (error) => `retry after ${error.retryAfter}`),
  Match.tag("PermissionError", (error) => `missing ${error.permission}`),
  Match.exhaustive
)
```

Reach for this after a boundary converts failures into data, or when rendering
an error in a caller that already has an `AppError` value.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-match-value.md](02-match-value.md), [03-match-type.md](03-match-type.md), [07-exhaustive-vs-orelse.md](07-exhaustive-vs-orelse.md), [../error-handling/04-catch-tag.md](../error-handling/04-catch-tag.md)
