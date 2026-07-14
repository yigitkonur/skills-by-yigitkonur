# Generators
Use `Effect.gen` for sequential effectful code with branching, loops, named intermediates, and precise control flow.

## Basic Form

`Effect.gen` lets you write effectful workflows in generator syntax.

```typescript
import { Effect } from "effect"

const program = Effect.gen(function* () {
  const user = yield* loadUser("u1")
  const profile = yield* loadProfile(user.profileId)
  return {
    user,
    profile
  }
})

declare const loadUser: (
  id: string
) => Effect.Effect<{ readonly profileId: string }, "MissingUser">

declare const loadProfile: (
  id: string
) => Effect.Effect<{ readonly displayName: string }, "MissingProfile">
```

The generator yields Effects. The final `return` becomes the success value.
Error and requirement channels are inferred from every yielded effect.

## Always Use `yield*`

Inside `Effect.gen`, use `yield* effect`, not `yield effect`.

```typescript
import { Effect } from "effect"

const wrong = Effect.gen(function* () {
  const value = yield Effect.succeed(1)
  return value
})

const right = Effect.gen(function* () {
  const value = yield* Effect.succeed(1)
  return value
})
```

The wrong version yields the Effect object itself. The right version runs the
effect inside the generator and binds the success value.

This is one of the easiest silent bugs for agents to write. Scan generated code
for `yield Effect.` and replace it with `yield* Effect.`.

## Early Failure

Use `return yield*` when a branch should stop the generator with an effect
failure.

```typescript
import { Effect } from "effect"

type InvalidPort = {
  readonly _tag: "InvalidPort"
  readonly input: string
}

const parsePort = (input: string) =>
  Effect.gen(function* () {
    const port = Number(input)

    if (!Number.isInteger(port) || port <= 0) {
      return yield* Effect.fail({
        _tag: "InvalidPort",
        input
      })
    }

    return port
  })
```

The `return` tells TypeScript the branch terminates the function. Without it,
TypeScript can continue reasoning as if later code is reachable in ways that
make unions and narrowing worse.

## Branching

Generators are best when control flow matters.

```typescript
import { Effect } from "effect"

type User = {
  readonly id: string
  readonly role: "admin" | "member"
}

type Denied = {
  readonly _tag: "Denied"
}

const requireAdmin = (id: string) =>
  Effect.gen(function* () {
    const user = yield* loadUser(id)

    if (user.role !== "admin") {
      return yield* Effect.fail({ _tag: "Denied" })
    }

    yield* Effect.log(`admin ${user.id} authorized`)
    return user
  })

declare const loadUser: (
  id: string
) => Effect.Effect<User, "MissingUser">
```

The same logic in `pipe` would usually require nested `flatMap` calls and
harder-to-read branches.

## Loops

Use normal loops when each step depends on the previous step or when early exit
is clearer than collection combinators.

```typescript
import { Effect } from "effect"

const firstAvailable = (ids: ReadonlyArray<string>) =>
  Effect.gen(function* () {
    for (const id of ids) {
      const available = yield* isAvailable(id)
      if (available) {
        return id
      }
    }

    return yield* Effect.fail("NoAvailableId")
  })

declare const isAvailable: (
  id: string
) => Effect.Effect<boolean, "LookupFailed">
```

For independent collection processing, prefer `Effect.forEach` or
`Effect.all` with explicit concurrency.

## Multiple Named Values

Generators keep intermediate values visible.

```typescript
import { Effect } from "effect"

const quote = (sku: string, quantity: number) =>
  Effect.gen(function* () {
    const product = yield* loadProduct(sku)
    const price = yield* loadPrice(product.priceId)
    const subtotal = price.amount * quantity
    const tax = yield* calculateTax(subtotal)

    return {
      sku,
      subtotal,
      tax,
      total: subtotal + tax
    }
  })

declare const loadProduct: (
  sku: string
) => Effect.Effect<{ readonly priceId: string }, "MissingProduct">

declare const loadPrice: (
  id: string
) => Effect.Effect<{ readonly amount: number }, "MissingPrice">

declare const calculateTax: (
  subtotal: number
) => Effect.Effect<number, "TaxFailed">
```

If a pipeline starts carrying `[a, b, c]` tuples solely to keep values around,
switch to a generator.

## Sequential by Default

Effects yielded in a generator run in order.

```typescript
import { Effect } from "effect"

const program = Effect.gen(function* () {
  const one = yield* task("one")
  const two = yield* task("two")
  return [one, two] as const
})

declare const task: (name: string) => Effect.Effect<string, "Failed">
```

For independent effects, use `Effect.all` inside the generator:

```typescript
import { Effect } from "effect"

const program = Effect.gen(function* () {
  const [user, settings] = yield* Effect.all(
    [loadUser("u1"), loadSettings("u1")],
    { concurrency: 2 }
  )

  return { user, settings }
})

declare const loadUser: (id: string) => Effect.Effect<string, "MissingUser">
declare const loadSettings: (id: string) => Effect.Effect<string, "MissingSettings">
```

This keeps dependency order honest and makes concurrency explicit.

## Generator Rules

Use `function*`, not an arrow function, for generator bodies.

Use `yield*` for every Effect.

Use `return yield* Effect.fail(...)` for terminating failure branches.

Do not call runners inside the generator. Yield effects and let the outer
runtime run the final program.

Do not throw for expected failures. Use the error channel.

## Cross-references

See also: [pipelines](04-pipelines.md), [gen vs pipe](06-gen-vs-pipe.md), [effect all](08-effect-all.md), [short-circuiting](11-short-circuiting.md).
