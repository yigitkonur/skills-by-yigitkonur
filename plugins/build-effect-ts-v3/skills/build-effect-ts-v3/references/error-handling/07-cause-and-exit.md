# Cause And Exit
Use `Cause` and `Exit` when you need the full failure story instead of only the typed `E` value.

## Cause

`Cause<E>` is the internal tree Effect uses to represent failure. It can contain typed failures, defects, interruption, and composition.

In Effect 3.21.2 source, `Cause<E>` is a union of:

- `Empty`
- `Fail<E>`
- `Die`
- `Interrupt`
- `Sequential<E>`
- `Parallel<E>`

Most application code should not construct causes directly. You inspect them at supervision, logging, testing, or boundary code.

## Cause nodes

| Node | Meaning | Created by |
|---|---|---|
| `Empty` | no failure data | internal composition |
| `Fail` | typed expected failure | `Effect.fail`, yieldable tagged errors |
| `Die` | defect | `Effect.die`, `Effect.dieMessage`, `orDie` |
| `Interrupt` | fiber cancellation | interruption |
| `Sequential` | causes happened in sequence | sequential composition or finalizers |
| `Parallel` | causes happened concurrently | parallel composition |

The important distinction is not just "error happened"; it is how and why it happened.

## Sequential vs parallel cause

`Cause.Sequential` preserves failures that occurred one after another. This can happen when an operation fails and a finalizer also fails, or when sequential composition combines causes.

`Cause.Parallel` preserves failures from concurrent branches. For example, parallel `Effect.all` can retain multiple branch failures in one cause tree.

```typescript
import { Cause } from "effect"

const first = Cause.fail("first")
const second = Cause.fail("second")

const sequential = Cause.sequential(first, second)
const parallel = Cause.parallel(first, second)
```

Use this distinction in diagnostics. Sequential often means "primary failure plus cleanup or follow-up failure." Parallel often means "multiple concurrent branches failed."

## Exit

`Exit<A, E>` represents completed execution:

- `Exit.Success<A>` contains the success value.
- `Exit.Failure<E>` contains `cause: Cause.Cause<E>`.

Use `Effect.exit` when you want to turn an effect into a successful value describing completion:

```typescript
import { Data, Effect, Exit } from "effect"

class UserNotFound extends Data.TaggedError("UserNotFound")<{}> {}

const program = Effect.fail(new UserNotFound({}))

const inspected = Effect.gen(function* () {
  const exit = yield* Effect.exit(program)
  if (Exit.isFailure(exit)) {
    return exit.cause
  }
  return "success"
})
```

`Effect.exit` is useful for tests, supervision, and boundary adapters. It should not replace normal typed recovery in service internals.

## Inspecting failures

Use `Cause.failures` for typed failures:

```typescript
import { Cause, Data, Effect } from "effect"

class UserNotFound extends Data.TaggedError("UserNotFound")<{}> {}

const program = Effect.fail(new UserNotFound({}))

const failures = Effect.cause(program).pipe(
  Effect.map((cause) => Cause.failures(cause))
)
```

`Cause.failures` returns a `Chunk` of `E` values found in the cause.

## Inspecting defects

Use `Cause.defects`, `Cause.dieOption`, or `Cause.keepDefects` when diagnosing defects:

```typescript
import { Cause, Effect } from "effect"

const program = Effect.dieMessage("invariant failed")

const defects = Effect.cause(program).pipe(
  Effect.map((cause) => Cause.defects(cause))
)
```

Do this at reporting and supervision boundaries. Do not convert every defect into a domain failure just to make it easier to handle.

## Pattern matching on Cause

`Cause.match` lets you fold over each node:

```typescript
import { Cause, Effect } from "effect"

const describe = <E>(cause: Cause.Cause<E>) =>
  Cause.match(cause, {
    onEmpty: "empty",
    onFail: () => "failure",
    onDie: () => "defect",
    onInterrupt: () => "interrupt",
    onSequential: (left, right) => `${left} then ${right}`,
    onParallel: (left, right) => `${left} and ${right}`
  })

const program = Effect.cause(Effect.dieMessage("boom")).pipe(
  Effect.map(describe)
)
```

This is often better than manually checking tags when you need a complete cause renderer.

## Pretty printing

`Cause.pretty(cause)` renders a human-readable representation:

```typescript
import { Cause, Effect } from "effect"

const program = Effect.dieMessage("invariant failed").pipe(
  Effect.catchAllCause((cause) =>
    Effect.logError(Cause.pretty(cause))
  )
)
```

Pretty output is for humans. Do not parse it. Use `Cause` APIs for machine decisions.

## failCause

`Effect.failCause` constructs an effect that fails with an explicit cause:

```typescript
import { Cause, Effect } from "effect"

const cause = Cause.parallel(
  Cause.fail("left failed"),
  Cause.fail("right failed")
)

const program = Effect.failCause(cause)
```

This is useful in tests and advanced infrastructure. Most domain code should fail with tagged errors instead.

## cause vs sandbox

`Effect.cause(effect)` exposes the cause after failure and succeeds with it. `Effect.sandbox(effect)` moves the `Cause<E>` into the typed error channel so normal recovery combinators can inspect it.

Use `Effect.cause` for observation. Use `Effect.sandbox` when you need to recover based on cause structure and then return to normal error handling with `Effect.unsandbox`.

## Exit mapping

`Exit` also has mapping helpers for code that already has an exit value:

```typescript
import { Data, Exit } from "effect"

class DriverError extends Data.TaggedError("DriverError")<{}> {}
class StoreError extends Data.TaggedError("StoreError")<{}> {}

const exit = Exit.fail(new DriverError({}))

const mapped = Exit.mapError(exit, () => new StoreError({}))
```

Use `Exit` helpers in adapters, tests, and runtime integration code. In normal program flow, prefer `Effect.mapError`, `catchTag`, and `catchTags` before converting into `Exit`.

## Cause inspection order

For diagnostics, inspect the most specific information first:

1. `Cause.failures` for typed failures.
2. `Cause.defects` or `Cause.keepDefects` for defects.
3. `Cause.isInterrupted` for cancellation.
4. `Cause.pretty` for human-readable fallback rendering.

Do not parse pretty output to make machine decisions.

## Source anchors

Effect 3.21.2 source exports:

- `Cause.fail`, `Cause.die`, `Cause.interrupt`
- `Cause.parallel`, `Cause.sequential`
- `Cause.isFailType`, `Cause.isDieType`, `Cause.isInterruptType`
- `Cause.isSequentialType`, `Cause.isParallelType`
- `Cause.failures`, `Cause.defects`, `Cause.pretty`
- `Exit.isFailure`, `Exit.fail`, `Exit.failCause`, `Exit.mapErrorCause`

## Cross-references

See also: [06-catch-all.md](06-catch-all.md), [08-defects.md](08-defects.md), [10-error-accumulation.md](10-error-accumulation.md), [14-sandboxing.md](14-sandboxing.md), [12-error-taxonomy.md](12-error-taxonomy.md).
