# Pipelines
Use `pipe`, `flow`, and `.pipe()` to compose small transformations in v3 data-first style.

## Why Pipelines Matter

Effect APIs are designed for composition. Most combinators have a data-last
form for pipeline use and a data-first form for direct calls.

```typescript
import { Effect } from "effect"

const program = Effect.succeed(1).pipe(
  Effect.map((n) => n + 1),
  Effect.flatMap((n) => Effect.succeed(n * 2)),
  Effect.tap((n) => Effect.log(`computed ${n}`))
)
```

The receiver `.pipe()` form keeps the main effect at the left edge and reads
top to bottom.

## `pipe`

Use `pipe(value, f, g, h)` when you want to start with a value and apply
functions to it.

```typescript
import { Effect, pipe } from "effect"

const program = pipe(
  Effect.succeed(10),
  Effect.map((n) => n + 5),
  Effect.flatMap((n) => Effect.succeed(n.toString()))
)
```

`pipe` is exported from the `effect` barrel and implemented in `Function.ts`.
It is not Effect-specific; it composes normal functions.

## `.pipe()`

Every Effect has `.pipe()`. Prefer it when the subject is already an Effect.

```typescript
import { Effect } from "effect"

const normalize = (input: string) =>
  Effect.succeed(input).pipe(
    Effect.map((value) => value.trim()),
    Effect.filterOrFail(
      (value) => value.length > 0,
      () => "Empty"
    )
  )
```

This style avoids nested calls and makes each transformation visually separate.

## `flow`

Use `flow` to build a reusable function from smaller functions.

```typescript
import { Effect, flow } from "effect"

const parseNumber = (input: string) =>
  Number.isFinite(Number(input))
    ? Effect.succeed(Number(input))
    : Effect.fail("NotNumber")

const readPort = flow(
  (input: string) => input.trim(),
  parseNumber,
  Effect.flatMap((port) =>
    port > 0 ? Effect.succeed(port) : Effect.fail("InvalidPort")
  )
)
```

`flow(f, g, h)` returns a new function. `pipe(value, f, g, h)` immediately
applies the functions to a value.

## Data-first and Data-last

Many Effect combinators are dual:

```typescript
import { Effect } from "effect"

const dataFirst = Effect.map(Effect.succeed(1), (n) => n + 1)

const dataLast = Effect.succeed(1).pipe(
  Effect.map((n) => n + 1)
)
```

Both are valid. Prefer data-last in longer pipelines because it keeps each step
one indentation level deep. Prefer data-first when there are only one or two
operations and directness is clearer.

## Pipeline Shape

A good pipeline has one subject and a series of transformations.

```typescript
import { Effect } from "effect"

const loadDisplayName = (id: string) =>
  loadUser(id).pipe(
    Effect.map((user) => user.profile.displayName),
    Effect.tap((name) => Effect.log(`loaded ${name}`)),
    Effect.withSpan("loadDisplayName")
  )

declare const loadUser: (
  id: string
) => Effect.Effect<{
  readonly profile: { readonly displayName: string }
}, "MissingUser">
```

If a pipeline needs multiple intermediate values at once, switch to
`Effect.gen`. Do not contort a pipeline into deeply nested tuples just to avoid
generators.

## Composition Without Running

Pipelines still create descriptions. They do not run work.

```typescript
import { Effect } from "effect"

const program = Effect.sync(() => Date.now()).pipe(
  Effect.map((now) => new Date(now)),
  Effect.tap((date) => Effect.log(date.toISOString()))
)
```

`Date.now()` runs when `program` runs, not when `program` is defined.

## Error and Requirement Growth

Pipeline composition grows the type channels.

```typescript
import { Effect } from "effect"

type Missing = { readonly _tag: "Missing" }
type Denied = { readonly _tag: "Denied" }
type Users = { readonly find: Effect.Effect<string, Missing> }
type Auth = { readonly check: Effect.Effect<void, Denied> }

declare const authorize: Effect.Effect<void, Denied, Auth>
declare const readName: Effect.Effect<string, Missing, Users>

const program = authorize.pipe(
  Effect.zipRight(readName),
  Effect.map((name) => name.toUpperCase())
)
```

The result requires both services and can fail with either error.

## Keep Pipelines Linear

Prefer pipelines for:

- linear mapping and flat mapping
- validation chains
- attaching logging, spans, retry, timeout, or error handling
- adapting one effect into another

Switch to `Effect.gen` for:

- branching with `if` or `switch`
- loops
- multiple dependent values that must be named
- early failure where `return yield*` improves control flow

## Cross-references

See also: [generators](05-generators.md), [gen vs pipe](06-gen-vs-pipe.md), [zip and tap](10-zip-and-tap.md), [effect match](12-effect-match.md).
