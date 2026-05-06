# Result Builder
Use `Result.builder` to render effectful atom states with explicit initial, waiting, tagged-error, defect, and success branches.

## Why Builder

Effectful atoms return `Result.Result<A, E>`.
That result can be initial, waiting, successful, failed with a typed error, or
failed by a defect.

`Result.builder(result)` gives React code a chainable rendering API.
The chain records the first matching branch and `render()` returns it.

The required minimum pattern for UI code is:

```typescript
import { Result } from "@effect-atom/atom-react"

declare const result: Result.Result<
  { readonly name: string },
  { readonly _tag: "NotFound"; readonly id: string }
>

const rendered = Result.builder(result)
  .onInitial(() => "Loading")
  .onErrorTag("NotFound", (error) => `Missing ${error.id}`)
  .onSuccess((user) => `Hello ${user.name}`)
  .render()
```

That chain shows the complete essential API:
`onInitial`, `onErrorTag`, `onSuccess`, and `render`.

## Builder Methods

The v3 source exposes these builder methods:

| Method | Handles |
|---|---|
| `onInitial` | initial result before a value exists |
| `onInitialOrWaiting` | initial result or any waiting result |
| `onWaiting` | any result whose `waiting` flag is true |
| `onSuccess` | successful value |
| `onFailure` | full `Cause.Cause<E>` |
| `onError` | typed failures extracted from the cause |
| `onErrorIf` | typed failures matching a predicate or refinement |
| `onErrorTag` | tagged failures by `_tag` |
| `onDefect` | defects from the cause |
| `orElse` | fallback when no branch matched |
| `orNull` | nullable fallback when no branch matched |
| `render` | return output, throw unhandled failure, or return null |

Prefer `onErrorTag` for domain errors.
Use `onFailure` only when the UI needs the complete cause.

## Tagged Errors

Use tagged errors in the Effect error channel so the UI can branch without
string matching.

```typescript
import { Atom, Result, useAtomValue } from "@effect-atom/atom-react"
import { Data, Effect } from "effect"

class UserNotFound extends Data.TaggedError("UserNotFound")<{
  readonly id: string
}> {}

class SessionExpired extends Data.TaggedError("SessionExpired")<{
  readonly loginUrl: string
}> {}

type User = {
  readonly id: string
  readonly name: string
}

const userAtom = Atom.make(
  Effect.fail(new UserNotFound({ id: "u-1" }))
)

export function UserPanel() {
  const result = useAtomValue(userAtom)

  return Result.builder(result)
    .onInitial(() => "Loading user")
    .onErrorTag("UserNotFound", (error) => `No user ${error.id}`)
    .onErrorTag("SessionExpired", (error) => `Login at ${error.loginUrl}`)
    .onSuccess((user) => `User ${user.name}`)
    .render()
}
```

This keeps UI branching aligned with typed Effect failures.

## Waiting With Previous Success

`waiting` is independent from the result tag.
A result can be `Success` and still have `waiting: true` during a background
refresh.

Handle waiting before success when the UI should show a refresh indicator.

```typescript
import { Atom, Result, useAtomValue } from "@effect-atom/atom-react"
import { Effect } from "effect"

const metricsAtom = Atom.make(
  Effect.succeed({ count: 12 }),
  { initialValue: { count: 0 } }
).pipe(Atom.keepAlive)

export function MetricsBadge() {
  const result = useAtomValue(metricsAtom)

  return Result.builder(result)
    .onInitial(() => "Preparing metrics")
    .onWaiting((current) =>
      Result.getOrElse(current, () => ({ count: 0 })).count
    )
    .onSuccess((metrics) => metrics.count)
    .render()
}
```

If waiting UI should only cover the initial load, use `onInitialOrWaiting`.
If stale data should remain visible, render success and add a separate indicator
from the `result.waiting` flag.

## Defects

Expected failures belong in the error channel.
Defects are not normal domain branches.

Use `onDefect` only at a boundary where showing a fallback is better than
letting an error boundary catch the defect.

```typescript
import { Result } from "@effect-atom/atom-react"

declare const result: Result.Result<string, { readonly _tag: "Denied" }>

const view = Result.builder(result)
  .onInitial(() => "Loading")
  .onErrorTag("Denied", () => "Access denied")
  .onDefect(() => "Unexpected failure")
  .onSuccess((value) => value)
  .render()
```

Do not convert defects into generic domain errors.

## Render Semantics

`render()` returns the selected branch output.
If no branch matched:

- unhandled failure is squashed and thrown
- unhandled initial or success states return `null`

That means a chain missing an expected error handler can surface through an
error boundary.
This is useful during development.
Do not silence all failures with a broad catch unless the UI truly has one
generic failure state.

## Builder Checklist

- Use `Result.builder(result)` near the component render boundary.
- Include `onInitial` for first load.
- Include `onErrorTag` for each expected tagged error shown differently.
- Include `onSuccess` for the happy path.
- Use `onWaiting` when background refresh needs visible state.
- Use `onDefect` only for boundary fallbacks.
- End the chain with `render()`.

## Cross-references

See also: [02 Atom.make](02-atom-make.md), [05 React Hooks](05-react-hooks.md), [08 Mutations](08-mutations.md), [09 Cache Invalidation](09-cache-invalidation.md), [11 Runtime Bridge](11-effect-runtime-bridge.md).
