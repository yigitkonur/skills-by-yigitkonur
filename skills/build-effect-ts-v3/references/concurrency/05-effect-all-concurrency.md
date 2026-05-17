# Effect All Concurrency
Use this to combine many effects while making the concurrency budget explicit.

## What `Effect.all` Does

`Effect.all` combines effects into one effect.

It accepts tuples, iterables, structs, and records of effects. The output keeps
the same shape:

- tuple input returns a tuple-like result
- iterable input returns an array
- struct input returns a struct
- record input returns a record

```typescript
import { Effect } from "effect"

const loadUser = Effect.succeed({ id: "user-1" })
const loadSettings = Effect.succeed({ theme: "dark" })

const program = Effect.all({
  user: loadUser,
  settings: loadSettings
})
```

By default, effects run sequentially. Add `concurrency` when you want parallel
execution.

## The Concurrency Option

The v3 source defines:

```typescript
type Concurrency = number | "unbounded" | "inherit"
```

`Effect.all` accepts:

```typescript
import { Effect } from "effect"

declare const effects: ReadonlyArray<Effect.Effect<number>>

const program = Effect.all(effects, {
  concurrency: 4
})
```

The option is a production control. It decides how much pressure the program can
apply at once.

## Sequential Default

No `concurrency` option means sequential execution.

```typescript
import { Effect } from "effect"

const steps = [
  Effect.logInfo("one"),
  Effect.logInfo("two"),
  Effect.logInfo("three")
]

const program = Effect.all(steps)
```

Sequential is often correct for fixed startup checks or ordered operations. It
is not a hidden performance feature. If the tasks are independent and numerous,
choose a number.

## Numbered Concurrency

Use a number for normal production fan-out.

```typescript
import { Effect } from "effect"

declare const ids: ReadonlyArray<string>
declare const hydrateUser: (id: string) => Effect.Effect<{ id: string }>

const program = Effect.all(
  ids.map((id) => hydrateUser(id)),
  { concurrency: 8 }
)
```

This starts at most eight effects at a time. Results stay ordered according to
the input, not completion order.

Choose the number from the bottleneck:

- database pool size
- API rate limit
- CPU profile
- downstream queue capacity
- memory per in-flight task

Do not choose it from today's sample size.

## `"unbounded"`

`concurrency: "unbounded"` starts all effects concurrently.

```typescript
import { Effect } from "effect"

const independentStartupChecks = [
  Effect.logInfo("check config"),
  Effect.logInfo("check routes"),
  Effect.logInfo("check telemetry")
]

const program = Effect.all(independentStartupChecks, {
  concurrency: "unbounded"
})
```

Use `"unbounded"` only for small, fixed-size collections where the maximum count
is known from the code. It is not acceptable for request payloads, database
rows, queue batches, user selections, search results, or any collection that can
grow outside this file.

## `"inherit"`

`concurrency: "inherit"` reads the ambient concurrency setting from
`Effect.withConcurrency`. If no ambient setting exists, official docs state it
defaults to `"unbounded"`.

```typescript
import { Effect } from "effect"

declare const jobs: ReadonlyArray<Effect.Effect<void>>

const child = Effect.all(jobs, {
  concurrency: "inherit",
  discard: true
})

const parent = child.pipe(
  Effect.withConcurrency(5)
)
```

Use `"inherit"` for helper functions that should respect the caller's budget.
Do not use it to avoid deciding. At the edge of the workflow, set the budget.

## `discard`

Use `discard: true` when the results are not needed.

```typescript
import { Effect } from "effect"

declare const notifications: ReadonlyArray<Effect.Effect<void>>

const sendAll = Effect.all(notifications, {
  concurrency: 10,
  discard: true
})
```

This makes intent and memory behavior clearer. The program is performing work,
not collecting a result array.

## Failure Modes

The default mode is fail-fast. If one effect fails, the combined effect fails
and concurrent siblings may be interrupted.

Use `mode: "either"` when every effect should run and each result should be
captured as success or failure data.

```typescript
import { Effect } from "effect"

declare const checks: ReadonlyArray<Effect.Effect<string, string>>

const audit = Effect.all(checks, {
  concurrency: 6,
  mode: "either"
})
```

Use `mode: "validate"` when you want all validation errors collected in the
error channel. Keep concurrency explicit there too.

## Tuple and Struct Inputs

For small fixed groups, `Effect.all` makes dependency-free parallelism easy.

```typescript
import { Effect } from "effect"

const loadPage = Effect.all(
  {
    profile: Effect.succeed("profile"),
    billing: Effect.succeed("billing"),
    flags: Effect.succeed("flags")
  },
  { concurrency: 3 }
)
```

Even fixed groups benefit from explicit concurrency because the next maintainer
can see the intent. If there are only two or three local effects, `concurrency:
"unbounded"` is acceptable; if the shape may grow, use a number.

## Review Checklist

When reviewing `Effect.all`, ask:

- Is the input fixed-size or dynamic?
- If dynamic, is there a numeric concurrency budget?
- If `"unbounded"` appears, is the maximum input size proven by code?
- If `"inherit"` appears, where is the ambient budget set?
- Are results needed, or should `discard: true` be used?
- Should failures fail fast, collect as `Either`, or validate all?
- Would `Effect.forEach` avoid building an intermediate array?

## Cross-References

See also:

- [06-effect-foreach-concurrency.md](06-effect-foreach-concurrency.md)
- [07-bounded-parallelism.md](07-bounded-parallelism.md)
- [08-semaphore.md](08-semaphore.md)
- [11-interruption.md](11-interruption.md)
