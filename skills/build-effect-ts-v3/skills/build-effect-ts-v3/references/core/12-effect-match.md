# Effect Match
Use `Effect.match`, `matchEffect`, `either`, and `exit` to turn typed outcomes into explicit values.

## `Effect.match`

Use `Effect.match` when both handlers are pure.

```typescript
import { Effect } from "effect"

const program = loadUser("u1").pipe(
  Effect.match({
    onFailure: (error) => `missing: ${error}`,
    onSuccess: (user) => `found: ${user.name}`
  })
)

declare const loadUser: (
  id: string
) => Effect.Effect<{ readonly name: string }, "MissingUser">
```

The resulting effect cannot fail with the original error because both branches
produce success values.

## `Effect.matchEffect`

Use `matchEffect` when handlers need to run effects.

```typescript
import { Effect } from "effect"

const program = loadUser("u1").pipe(
  Effect.matchEffect({
    onFailure: (error) =>
      Effect.log(`load failed: ${error}`).pipe(
        Effect.as("anonymous")
      ),
    onSuccess: (user) =>
      Effect.log(`load succeeded: ${user.name}`).pipe(
        Effect.as(user.name)
      )
  })
)

declare const loadUser: (
  id: string
) => Effect.Effect<{ readonly name: string }, "MissingUser">
```

The handler effects can introduce new error or requirement channels.

## `Effect.either`

Use `either` when you want success or failure in `Either` while staying inside
Effect.

```typescript
import { Effect, Either } from "effect"

const program = loadUser("u1").pipe(
  Effect.either,
  Effect.map((outcome) =>
    Either.match(outcome, {
      onLeft: (error) => `missing: ${error}`,
      onRight: (user) => `found: ${user.name}`
    })
  )
)

declare const loadUser: (
  id: string
) => Effect.Effect<{ readonly name: string }, "MissingUser">
```

`Effect.either` converts the expected error channel into data. It does not
expose defects or interruption details.

## `Effect.exit`

Use `exit` when you need the full outcome, including cause information.

```typescript
import { Effect, Exit } from "effect"

const program = loadUser("u1").pipe(
  Effect.exit,
  Effect.map((outcome) =>
    Exit.match(outcome, {
      onFailure: () => "failed with cause",
      onSuccess: (user) => `found: ${user.name}`
    })
  )
)

declare const loadUser: (
  id: string
) => Effect.Effect<{ readonly name: string }, "MissingUser">
```

`Exit.Exit<A, E>` is the right shape for tests, adapters, and diagnostics that
need to distinguish success from all failure causes.

## Match vs Recover

Matching converts both branches into a success value. Recovery changes only the
failure branch and keeps the success branch unchanged. Use matching when the
caller wants a single rendered or normalized value.

```typescript
import { Effect } from "effect"

const rendered = loadUser("u1").pipe(
  Effect.match({
    onFailure: () => "not found",
    onSuccess: (user) => user.name
  })
)

declare const loadUser: (
  id: string
) => Effect.Effect<{ readonly name: string }, "MissingUser">
```

If downstream code still needs to know whether the operation failed, prefer
`either` or `exit`.

## Selection Rules

Use `match` for pure handlers.

Use `matchEffect` for effectful handlers.

Use `either` for expected failures as data.

Use `exit` for complete runtime outcomes.

Use `runPromiseExit` at Promise boundaries when the external caller needs an
Exit without Promise rejection.

## Cross-references

See also: [running effects](03-running-effects.md), [zip and tap](10-zip-and-tap.md), [short-circuiting](11-short-circuiting.md), [the Effect type](01-effect-type.md).
