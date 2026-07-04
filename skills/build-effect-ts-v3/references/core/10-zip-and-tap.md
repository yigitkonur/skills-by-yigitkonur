# Zip and Tap
Use zip to combine effects and tap to observe effects without changing their success value.

## Zip Family

`zip`, `zipLeft`, and `zipRight` sequence two effects. They run sequentially by
default and can run concurrently with `{ concurrent: true }`.

```typescript
import { Effect } from "effect"

const program = Effect.zip(
  loadUser("u1"),
  loadSettings("u1")
)

declare const loadUser: (id: string) => Effect.Effect<string, "MissingUser">
declare const loadSettings: (id: string) => Effect.Effect<string, "MissingSettings">
```

The success value is a tuple `[user, settings]`.

## `zipLeft`

Use `zipLeft` when the second effect is needed but its value should be ignored.

```typescript
import { Effect } from "effect"

const program = saveUser("u1").pipe(
  Effect.zipLeft(Effect.log("saved user u1"))
)

declare const saveUser: (
  id: string
) => Effect.Effect<{ readonly id: string }, "SaveFailed">
```

The result is the saved user. The logging effect still runs after `saveUser`
succeeds.

## `zipRight`

Use `zipRight` when the first effect is setup and the second value is the one
you need.

```typescript
import { Effect } from "effect"

const program = ensureAuthorized("u1").pipe(
  Effect.zipRight(loadDashboard("u1"))
)

declare const ensureAuthorized: (
  id: string
) => Effect.Effect<void, "Denied">
declare const loadDashboard: (
  id: string
) => Effect.Effect<string, "DashboardFailed">
```

The result is the dashboard. If authorization fails, the dashboard is not
loaded.

## Concurrent Zip

Use concurrent zip only when both effects are independent.

```typescript
import { Effect } from "effect"

const program = Effect.zip(
  loadUser("u1"),
  loadSettings("u1"),
  { concurrent: true }
)

declare const loadUser: (id: string) => Effect.Effect<string, "MissingUser">
declare const loadSettings: (id: string) => Effect.Effect<string, "MissingSettings">
```

For three or more independent effects, prefer `Effect.all` with explicit
concurrency and a clearer result shape.

## Tap Family

`tap` observes success while preserving the original success value.

```typescript
import { Effect } from "effect"

const program = loadUser("u1").pipe(
  Effect.tap((user) => Effect.log(`loaded ${user.id}`)),
  Effect.map((user) => user.name)
)

declare const loadUser: (
  id: string
) => Effect.Effect<{ readonly id: string; readonly name: string }, "MissingUser">
```

The `tap` effect can fail. If it fails, the whole pipeline fails with that
additional error type.

## `tapError`

Use `tapError` to observe expected failures without recovering from them.

```typescript
import { Effect } from "effect"

const program = loadUser("u1").pipe(
  Effect.tapError((error) => Effect.log(`load failed: ${error}`))
)

declare const loadUser: (
  id: string
) => Effect.Effect<string, "MissingUser">
```

The original failure still propagates. Use error recovery combinators when you
want to change the outcome.

## `tapBoth`

Use `tapBoth` when success and failure need separate observations.

```typescript
import { Effect } from "effect"

const program = loadUser("u1").pipe(
  Effect.tapBoth({
    onFailure: (error) => Effect.log(`failure=${error}`),
    onSuccess: (user) => Effect.log(`success=${user}`)
  })
)

declare const loadUser: (
  id: string
) => Effect.Effect<string, "MissingUser">
```

This is useful for metrics and structured audit events.

## `tapDefect`

Use `tapDefect` to observe defects. Defects are not expected domain failures.

```typescript
import { Effect } from "effect"

const program = risky.pipe(
  Effect.tapDefect((cause) => Effect.log(`defect=${cause}`))
)

declare const risky: Effect.Effect<string, "ExpectedFailure">
```

Do not use defects as a substitute for typed errors. `tapDefect` is for
diagnostics around unexpected failures.

## Cross-references

See also: [pipelines](04-pipelines.md), [effect all](08-effect-all.md), [short-circuiting](11-short-circuiting.md), [effect match](12-effect-match.md).
