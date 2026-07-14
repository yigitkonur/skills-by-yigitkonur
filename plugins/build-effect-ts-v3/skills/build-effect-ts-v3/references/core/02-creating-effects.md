# Creating Effects
Choose the smallest constructor that preserves laziness, failure typing, and interruption semantics.

## Constructor Matrix

| Constructor | Use when | Failure channel |
|---|---|---|
| `Effect.succeed(value)` | value is already computed | `never` |
| `Effect.fail(error)` | expected failure is already known | `E` |
| `Effect.sync(thunk)` | synchronous work cannot fail as expected | `never` |
| `Effect.try(options)` | synchronous work may throw | mapped `E` |
| `Effect.promise(thunk)` | async work cannot reject as expected | `never` |
| `Effect.tryPromise(options)` | async work may reject | mapped `E` |
| `Effect.async(register)` | callback API needs integration | `E` |
| `Effect.suspend(thunk)` | effect construction itself must be delayed | inferred |

The key question is not "is this code async?" The key question is "what does
the runtime need to control?" If the work can fail, block, allocate, register a
callback, or depend on fresh state, construct it lazily.

## Already Computed Values

Use `succeed` only when the value is already available.

```typescript
import { Effect } from "effect"

const answer = Effect.succeed(42)

const greeting = (name: string) =>
  Effect.succeed(`hello ${name}`)
```

Do not hide work inside the argument passed to `succeed`. The argument is
evaluated before the Effect exists.

```typescript
import { Effect } from "effect"

const parse = (input: string): Effect.Effect<unknown> =>
  Effect.sync(() => JSON.parse(input))
```

The `sync` version delays parsing until the effect runs.

## Expected Failures

Use `fail` for typed, expected failures.

```typescript
import { Effect } from "effect"

type EmptyName = {
  readonly _tag: "EmptyName"
}

const validateName = (name: string): Effect.Effect<string, EmptyName> =>
  name.trim().length === 0
    ? Effect.fail({ _tag: "EmptyName" })
    : Effect.succeed(name.trim())
```

Use data errors instead of throwing. A typed error channel lets callers recover
with `Effect.catchTag`, `Effect.catchTags`, `Effect.catchAll`, or matching.

## Synchronous Work

Use `Effect.sync` for synchronous work that is not expected to throw.

```typescript
import { Effect } from "effect"

const makeId = Effect.sync(() => crypto.randomUUID())

const program = makeId.pipe(
  Effect.tap((id) => Effect.log(`created ${id}`))
)
```

If the thunk throws, Effect treats that as a defect. Defects are for unexpected
programmer or system failures, not normal domain decisions.

## Synchronous Work That May Throw

Use `Effect.try` when calling a throwing API and map the unknown error into a
domain error.

```typescript
import { Effect } from "effect"

type JsonError = {
  readonly _tag: "JsonError"
  readonly message: string
}

const parseJson = (input: string): Effect.Effect<unknown, JsonError> =>
  Effect.try({
    try: () => JSON.parse(input),
    catch: (error) => ({
      _tag: "JsonError",
      message: error instanceof Error ? error.message : String(error)
    })
  })
```

The `catch` property is part of the constructor options. It is not an Effect
error combinator.

## Async Work That Cannot Reject

Use `Effect.promise` when rejection would be a defect because the API contract
says it cannot reject.

```typescript
import { Effect } from "effect"

const wait = (milliseconds: number) =>
  Effect.promise<void>(
    () =>
      new Promise((resolve) => {
        setTimeout(resolve, milliseconds)
      })
  )
```

Most real external I/O can reject. In those cases prefer `tryPromise`.

## Async Work That May Reject

Use `Effect.tryPromise` for Promise APIs that can reject. The callback receives
an `AbortSignal`, which lets compatible APIs participate in interruption.

```typescript
import { Effect } from "effect"

type HttpError = {
  readonly _tag: "HttpError"
  readonly reason: string
}

const getText = (url: string): Effect.Effect<string, HttpError> =>
  Effect.tryPromise({
    try: (signal) =>
      fetch(url, { signal }).then((response) => response.text()),
    catch: (error) => ({
      _tag: "HttpError",
      reason: error instanceof Error ? error.message : String(error)
    })
  })
```

Prefer mapping to your own error type at the boundary. Letting unknown errors
leak inward makes recovery branches harder to write correctly.

## Callback APIs

Use `Effect.async` when the API completes by invoking a callback.

```typescript
import { Effect } from "effect"

type TimeoutError = {
  readonly _tag: "TimeoutError"
}

const delayValue = (value: string, milliseconds: number) =>
  Effect.async<string, TimeoutError>((resume, signal) => {
    const timer = setTimeout(() => {
      resume(Effect.succeed(value))
    }, milliseconds)

    signal.addEventListener("abort", () => {
      clearTimeout(timer)
      resume(Effect.fail({ _tag: "TimeoutError" }))
    })
  })
```

The callback resumes with an Effect, not with a raw value. That lets callback
completion succeed or fail using the same typed channels as the rest of the
program.

## Delaying Construction

Use `Effect.suspend` when selecting or building the effect should happen lazily.

```typescript
import { Effect } from "effect"

type DivideByZero = {
  readonly _tag: "DivideByZero"
}

const divide = (left: number, right: number) =>
  Effect.suspend(() =>
    right === 0
      ? Effect.fail({ _tag: "DivideByZero" })
      : Effect.succeed(left / right)
  )
```

`suspend` is useful for recursion, branch type inference, and avoiding eager
captures. It delays the decision that returns the next effect.

## Constructor Selection Rules

Use `succeed` and `fail` for already-known values.

Use `sync` and `try` for synchronous work. Pick `try` only when the external API
can throw as part of its normal contract.

Use `promise` and `tryPromise` for Promise APIs. Pick `tryPromise` unless you
can defend rejection as a defect.

Use `async` only when there is no Promise API and you must adapt callbacks.

Use `suspend` when the effect description itself must be recreated or chosen at
runtime.

## Cross-references

See also: [the Effect type](01-effect-type.md), [running effects](03-running-effects.md), [generators](05-generators.md), [effect match](12-effect-match.md).
