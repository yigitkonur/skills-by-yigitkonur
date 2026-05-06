# The Effect Type
Understand `Effect<A, E, R>` as a lazy, immutable description with success, failure, and requirement channels.

## Shape

`Effect.Effect<A, E, R>` is the central type in Effect v3.

Read it left to right:

| Channel | Meaning | Example |
|---|---|---|
| `A` | success value | `User` |
| `E` | expected failure | `NotFound` |
| `R` | required services | `Database` |

An effect does not run when it is constructed. It describes work that can be
run later by a runtime. That laziness is what lets Effect preserve typed
errors, interruption, supervision, tracing, retries, timeouts, scopes, and
service injection across a whole program.

```typescript
import { Effect } from "effect"

type User = {
  readonly id: string
  readonly name: string
}

type NotFound = {
  readonly _tag: "NotFound"
  readonly id: string
}

type Database = {
  readonly findUser: (id: string) => Effect.Effect<User, NotFound>
}

declare const findUser: (
  id: string
) => Effect.Effect<User, NotFound, Database>
```

This type says: running the effect may produce a `User`, may fail with
`NotFound`, and cannot run until a `Database` service is provided.

## The Three Channels

The success channel is the value you get when the effect completes normally.
`Effect.succeed(1)` has success type `number`.

The error channel is for expected, recoverable failures. `Effect.fail(error)`
has success type `never` because it cannot produce a value on that path.

The requirement channel is the environment. It tracks services needed to run the
effect. Pure effects have `R = never`, which means they need no services.

```typescript
import { Effect } from "effect"

const value: Effect.Effect<number> = Effect.succeed(42)

const failure: Effect.Effect<never, "InvalidInput"> =
  Effect.fail("InvalidInput")

type Clock = {
  readonly now: Effect.Effect<Date>
}

declare const currentTime: Effect.Effect<Date, never, Clock>
```

`never` is important in all three channels:

| Position | Meaning |
|---|---|
| `Effect<A, never, R>` | cannot fail with expected errors |
| `Effect<never, E, R>` | cannot succeed |
| `Effect<A, E, never>` | needs no services |

## Lazy, Not Eager

Constructing an effect is pure. Running it is effectful.

```typescript
import { Effect } from "effect"

let counter = 0

const eagerValue = counter + 1
const lazyEffect = Effect.sync(() => counter + 1)

counter = 10

const program = Effect.gen(function* () {
  const value = yield* lazyEffect
  yield* Effect.log(`eager=${eagerValue}, lazy=${value}`)
})
```

`eagerValue` is computed immediately. `lazyEffect` computes when the runtime
executes it. Prefer effect constructors around side effects so retries,
timeouts, and interruption re-run the work under runtime control.

## Immutable Descriptions

Combinators do not mutate an effect. They return a new effect.

```typescript
import { Effect } from "effect"

const base = Effect.succeed(10)

const doubled = base.pipe(Effect.map((n) => n * 2))
const labeled = base.pipe(Effect.map((n) => `value=${n}`))
```

`base` is still the same description. `doubled` and `labeled` are new
descriptions that can be run independently.

## Type Inference

Effect combines channels through composition.

```typescript
import { Effect } from "effect"

type Missing = { readonly _tag: "Missing" }
type Denied = { readonly _tag: "Denied" }
type Users = { readonly get: Effect.Effect<string, Missing> }
type Auth = { readonly check: Effect.Effect<void, Denied> }

declare const checkAuth: Effect.Effect<void, Denied, Auth>
declare const getName: Effect.Effect<string, Missing, Users>

const program = Effect.gen(function* () {
  yield* checkAuth
  return yield* getName
})
```

The inferred type is equivalent to:

```typescript
import { Effect } from "effect"

type Missing = { readonly _tag: "Missing" }
type Denied = { readonly _tag: "Denied" }
type Users = { readonly get: Effect.Effect<string, Missing> }
type Auth = { readonly check: Effect.Effect<void, Denied> }

declare const program: Effect.Effect<string, Missing | Denied, Users | Auth>
```

When code reads as normal TypeScript but keeps error and service types, you are
using the model correctly.

## Mental Model

An Effect value is not a Promise. A Promise is already running and has one
untyped rejection path. An Effect is a typed recipe that the runtime can
interpret with supervision, cancellation, error accumulation, resource scopes,
fiber-local context, and service injection.

Use Promise-returning APIs at system boundaries by wrapping them in
`Effect.tryPromise` or `Effect.promise`. Keep internal application logic in the
Effect world until the final runtime edge.

## Common Mistakes

Do not erase the error channel by converting to Promise in service or library
code. That throws away typed failures and removes the work from the fiber tree.

Do not encode missing values with `null` or `undefined` in domain types. Use
`Option.Option<A>` when absence is a normal case, or a typed failure when
absence should stop the workflow.

Do not put side effects in constructors like `Effect.succeed(doWork())`.
`succeed` receives an already computed value. Use `Effect.sync`,
`Effect.try`, `Effect.promise`, or `Effect.tryPromise` for work that happens
when the effect runs.

## Cross-references

See also: [creating effects](02-creating-effects.md), [running effects](03-running-effects.md), [generators](05-generators.md), [effect all](08-effect-all.md).
