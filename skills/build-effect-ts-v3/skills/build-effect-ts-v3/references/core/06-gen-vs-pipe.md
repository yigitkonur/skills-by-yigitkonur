# Gen vs Pipe
Choose `Effect.gen` for control flow and `pipe` for linear transformations.

## Decision Matrix

| Situation | Prefer | Why |
|---|---|---|
| one subject, many transformations | `.pipe()` | reads top to bottom |
| reusable pure function composition | `flow` | returns a normal function |
| branch with `if` or `switch` | `Effect.gen` | native control flow |
| loop with early return | `Effect.gen` | avoids encoding loops as combinators |
| many named intermediates | `Effect.gen` | values remain visible |
| simple map or flatMap chain | `.pipe()` | less syntax |
| independent effects run together | `Effect.all` | explicit concurrency and result shape |
| dependent sequential steps | `Effect.gen` | dependency order is obvious |

The choice is about readability and correctness, not personal style.

## Prefer Pipe for Linear Work

```typescript
import { Effect } from "effect"

const displayName = (input: string) =>
  Effect.succeed(input).pipe(
    Effect.map((value) => value.trim()),
    Effect.filterOrFail(
      (value) => value.length > 0,
      () => "EmptyName"
    ),
    Effect.map((value) => value.toUpperCase())
  )
```

There is one value moving through a sequence. A generator would add ceremony
without improving clarity.

## Prefer Gen for Branching

```typescript
import { Effect } from "effect"

const decide = (score: number) =>
  Effect.gen(function* () {
    if (score < 0) {
      return yield* Effect.fail("NegativeScore")
    }

    if (score >= 90) {
      yield* Effect.log("excellent")
      return "A"
    }

    return "B"
  })
```

The branches are the important part, so write branches directly.

## Prefer Gen for Several Values

```typescript
import { Effect } from "effect"

const checkout = (cartId: string) =>
  Effect.gen(function* () {
    const cart = yield* loadCart(cartId)
    const customer = yield* loadCustomer(cart.customerId)
    const total = yield* priceCart(cart)

    return {
      cartId: cart.id,
      customerId: customer.id,
      total
    }
  })

declare const loadCart: (
  id: string
) => Effect.Effect<{ readonly id: string; readonly customerId: string }, "MissingCart">
declare const loadCustomer: (
  id: string
) => Effect.Effect<{ readonly id: string }, "MissingCustomer">
declare const priceCart: (
  cart: { readonly id: string }
) => Effect.Effect<number, "PricingFailed">
```

The generator avoids tuple plumbing and keeps domain names intact.

## Mix Them Deliberately

`Effect.gen` and pipelines compose well. Use a generator for workflow shape and
pipe for local transformations.

```typescript
import { Effect } from "effect"

const program = Effect.gen(function* () {
  const user = yield* loadUser("u1").pipe(
    Effect.tap((user) => Effect.log(`loaded ${user.id}`))
  )

  return user.name.trim()
})

declare const loadUser: (
  id: string
) => Effect.Effect<{ readonly id: string; readonly name: string }, "MissingUser">
```

Do not force one style across a whole file. Use the local shape that exposes
the intent with the least machinery.

## Smell Checklist

Switch from pipe to gen when:

- you are nesting `flatMap` more than one level
- you are building tuples only to keep old values
- a validation branch needs `return yield*`
- a loop is clearer than `forEach`
- TypeScript narrowing matters after a branch

Switch from gen to pipe when:

- the body is just a map chain
- every line transforms the same subject
- there are no branches, loops, or reused intermediates
- a named helper would be more reusable than a local generator

## Cross-references

See also: [pipelines](04-pipelines.md), [generators](05-generators.md), [effect all](08-effect-all.md), [effect foreach](09-effect-foreach.md).
