# Effect Fn
Use `Effect.fn("name")` for named effectful functions with tracing and better call-site diagnostics.

## What It Provides

`Effect.fn` wraps a function that returns or yields Effects. In v3.21.2 it is
available in `Effect.ts` under the tracing category. The named form adds a span
around each call, which makes service methods and important workflows easier to
trace.

Use it for functions that represent meaningful operations:

- service methods
- repository calls
- workflow steps
- adapters around external APIs
- domain actions with useful span names

Do not use it for every tiny inline transformation. `Effect.map` and ordinary
helpers are enough for local code.

## Named Generator Form

```typescript
import { Effect } from "effect"

const loadDisplayName = Effect.fn("Users.loadDisplayName")(function* (
  userId: string
) {
  const user = yield* loadUser(userId)
  yield* Effect.log(`loaded ${user.id}`)
  return user.displayName
})

declare const loadUser: (
  id: string
) => Effect.Effect<{
  readonly id: string
  readonly displayName: string
}, "MissingUser">
```

The returned `loadDisplayName` is a normal function. Calling it returns an
Effect. The name becomes tracing metadata when the effect runs.

## Why Not Just an Arrow

This works, but it loses the named span:

```typescript
import { Effect } from "effect"

const loadDisplayName = (userId: string) =>
  Effect.gen(function* () {
    const user = yield* loadUser(userId)
    return user.displayName
  })

declare const loadUser: (
  id: string
) => Effect.Effect<{
  readonly id: string
  readonly displayName: string
}, "MissingUser">
```

Prefer `Effect.fn("Users.loadDisplayName")` when the operation matters in logs
or traces. See [observability/06-tracing-basics.md](../observability/06-tracing-basics.md)
for how spans are exported and interpreted.

## Non-generator Form

Use the non-generator form when the body is already a simple pipeline.

```typescript
import { Effect } from "effect"

const normalizeName = Effect.fn("Users.normalizeName")((name: string) =>
  Effect.succeed(name).pipe(
    Effect.map((value) => value.trim()),
    Effect.filterOrFail(
      (value) => value.length > 0,
      () => "EmptyName"
    )
  )
)
```

The function still returns an Effect and still receives tracing behavior from
the named wrapper.

## Pipeable Post-processing

`Effect.fn` can receive pipeable transformations after the body. Use this
sparingly when every invocation should share the same wrapper behavior.

```typescript
import { Effect } from "effect"

const refreshToken = Effect.fn(
  "Auth.refreshToken"
)(function* (accountId: string) {
  const token = yield* requestToken(accountId)
  return token.value
}, Effect.timeout("5 seconds"))

declare const requestToken: (
  accountId: string
) => Effect.Effect<{ readonly value: string }, "TokenUnavailable">
```

If the extra combinators are only needed at one call site, put them at the call
site instead.

## Service Method Pattern

Use `Effect.fn` when defining service implementations so method names appear in
traces.

```typescript
import { Effect } from "effect"

type Users = {
  readonly findName: (
    id: string
  ) => Effect.Effect<string, "MissingUser">
}

const UsersLive: Users = {
  findName: Effect.fn("Users.findName")(function* (id: string) {
    const row = yield* queryUser(id)
    return row.name
  })
}

declare const queryUser: (
  id: string
) => Effect.Effect<{ readonly name: string }, "MissingUser">
```

Name spans by capability and method, not by implementation detail. Stable names
make traces more useful across refactors.

## Rules

Use a descriptive name string. `Service.method` or `Domain.action` is usually
enough.

Keep expected failures in the Effect error channel. Do not throw from the body
for domain errors.

Use `yield*` in generator bodies exactly as you would in `Effect.gen`.

Keep runners outside the function. The function should return an Effect.

Do not wrap trivial pure helpers just to add a span. Traces become noisy when
every local calculation is a span.

## Cross-references

See also: [generators](05-generators.md), [pipelines](04-pipelines.md), [running effects](03-running-effects.md), [zip and tap](10-zip-and-tap.md).
