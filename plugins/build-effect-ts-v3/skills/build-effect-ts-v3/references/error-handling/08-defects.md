# Defects
Use defects for unrecoverable bugs and invariant failures, not for ordinary domain outcomes.

## What defects are

Defects are unexpected failures outside the typed `E` channel. They appear in `Cause.Die` and are normally handled by runtime supervision, logging, or process boundaries.

Use a defect when continuing would be misleading or unsafe:

- impossible state reached
- corrupted in-memory invariant
- callback contract violated by foreign code
- a typed failure is intentionally escalated as unrecoverable
- a boundary must report and terminate a fiber

Do not use defects for user input, missing rows, rate limits, or upstream service failures callers can recover from.

## die

`Effect.die` fails the fiber with a defect:

```typescript
import { Effect } from "effect"

const invariantFailed = Effect.die(new Error("cart total became negative"))
```

The error type is `never` because this is not a recoverable `E` value.

## dieMessage

`Effect.dieMessage` creates a runtime exception defect from text:

```typescript
import { Effect } from "effect"

const impossible = Effect.dieMessage("impossible order state")
```

Use this when a descriptive message is enough. Prefer structured typed errors for recoverable cases.

## orDie

`Effect.orDie` turns every typed failure into a defect:

```typescript
import { Data, Effect } from "effect"

class ConfigInvalid extends Data.TaggedError("ConfigInvalid")<{}> {}

const loadRequiredConfig = Effect.fail(new ConfigInvalid({})).pipe(
  Effect.orDie
)
```

This is appropriate only when there is no meaningful local recovery and startup or runtime should fail hard.

## orDieWith

`Effect.orDieWith` maps a typed failure into a defect value:

```typescript
import { Data, Effect } from "effect"

class ConfigInvalid extends Data.TaggedError("ConfigInvalid")<{
  readonly key: string
}> {}

const loadRequiredConfig = Effect.fail(new ConfigInvalid({ key: "DATABASE_URL" })).pipe(
  Effect.orDieWith((error) => new Error(`required config invalid: ${error.key}`))
)
```

Use it when the defect should carry a clearer diagnostic than the original failure.

## Catching defects

Defects can be inspected with `catchAllDefect`:

```typescript
import { Effect } from "effect"

const program = Effect.dieMessage("render invariant failed").pipe(
  Effect.catchAllDefect((defect) =>
    Effect.logError(String(defect)).pipe(
      Effect.as("reported")
    )
  )
)
```

This is not a normal application recovery tool. It is for reporting, cleanup, or converting to a process-boundary response.

## Typed failure first

If a caller can take a different action, do not use a defect:

```typescript
import { Data, Effect } from "effect"

class UserNotFound extends Data.TaggedError("UserNotFound")<{
  readonly userId: string
}> {}

const loadUser = (userId: string) =>
  Effect.gen(function* () {
    return yield* new UserNotFound({ userId })
  })
```

The caller can branch on `UserNotFound`. Turning it into a defect would remove that choice from the type system.

## Defects in Cause

Defects appear as `Cause.Die`. You can inspect them with:

- `Cause.defects`
- `Cause.dieOption`
- `Cause.keepDefects`
- `Cause.pretty`
- `Effect.catchAllCause`
- `Effect.catchAllDefect`

Inspecting is not the same as recovering. Default to reporting and re-failing unless the boundary has an explicit graceful-degradation policy.

## Boundary policy

At a server or worker boundary:

1. Report the defect.
2. Include a correlation id if one exists in context.
3. Return a generic protocol failure if required.
4. Preserve the original cause for observability.

Do not expose defect internals to untrusted clients.

## Escalation checklist

Before using `orDie` or `orDieWith`, verify:

- the failure is unrecoverable for this program
- the caller cannot provide better input or credentials
- retry would not change the outcome
- the defect will be visible to supervision or reporting
- tests do not depend on hiding the failure

If any item is false, keep the value in the typed error channel.

## Cross-references

See also: [01-overview.md](01-overview.md), [06-catch-all.md](06-catch-all.md), [07-cause-and-exit.md](07-cause-and-exit.md), [12-error-taxonomy.md](12-error-taxonomy.md), [14-sandboxing.md](14-sandboxing.md).
