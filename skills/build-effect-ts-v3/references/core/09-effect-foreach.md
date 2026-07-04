# Effect Foreach
Use collection combinators to map inputs into effects with explicit concurrency and error accumulation behavior.

## `Effect.forEach`

`Effect.forEach` applies an effectful function to each item and collects the
successes.

```typescript
import { Effect } from "effect"

const program = Effect.forEach(
  ["u1", "u2", "u3"],
  (id) => loadUser(id),
  { concurrency: 3 }
)

declare const loadUser: (
  id: string
) => Effect.Effect<{ readonly id: string }, "MissingUser">
```

The result is an Effect that succeeds with an array of users. In default mode,
the first failure fails the whole operation.

## Data-last Form

Use data-last form in pipelines.

```typescript
import { Effect, pipe } from "effect"

const loadAll = (ids: ReadonlyArray<string>) =>
  pipe(
    ids,
    Effect.forEach(
      (id) => loadUser(id),
      { concurrency: 8 }
    )
  )

declare const loadUser: (
  id: string
) => Effect.Effect<{ readonly id: string }, "MissingUser">
```

For plain arrays, many teams prefer the data-first form because it is familiar.
Use the form that keeps the surrounding code simplest.

## Index Argument

The mapping function receives the item and its index.

```typescript
import { Effect } from "effect"

const program = Effect.forEach(
  ["a", "b", "c"],
  (value, index) =>
    Effect.succeed({
      index,
      value
    }),
  { concurrency: 1 }
)
```

Use the index for stable labels or position-aware validation. Do not use it to
smuggle mutable state through concurrent operations.

## Discarding Results

Use `discard: true` when results are not needed.

```typescript
import { Effect } from "effect"

const program = Effect.forEach(
  ["cache:a", "cache:b", "cache:c"],
  (key) => invalidate(key),
  { concurrency: 3, discard: true }
)

declare const invalidate: (
  key: string
) => Effect.Effect<void, "InvalidateFailed">
```

The success type is `void`, which documents that only the effects matter.

## `Effect.partition`

Use `partition` when you need both failures and successes as data.

```typescript
import { Effect } from "effect"

const program = Effect.partition(
  ["1", "x", "2"],
  (input) => parseIntEffect(input),
  { concurrency: 3 }
)

declare const parseIntEffect: (
  input: string
) => Effect.Effect<number, "NotInteger">
```

The success value is `[excluded, satisfying]`: an array of errors and an array
of successes. The combined effect itself does not fail for item failures.

## `Effect.validateAll`

Use `validateAll` when every item should be checked and any failures should be
accumulated.

```typescript
import { Effect } from "effect"

const program = Effect.validateAll(
  ["Ada", "", "Grace"],
  (name) =>
    name.length === 0
      ? Effect.fail("EmptyName")
      : Effect.succeed(name),
  { concurrency: 3 }
)
```

If any item fails, successes are discarded and the error channel contains a
non-empty array of failures. Use `partition` if you need to keep successes too.

## `Effect.validateFirst`

Use `validateFirst` when you need the first success, or all failures if none
succeed.

```typescript
import { Effect } from "effect"

const program = Effect.validateFirst(
  ["primary", "replica"],
  (name) => connect(name),
  { concurrency: 1 }
)

declare const connect: (
  name: string
) => Effect.Effect<{ readonly name: string }, "Unavailable">
```

With sequential concurrency, it behaves like ordered fallback. With concurrent
execution, it can return whichever success completes first.

## Choosing a Collection Combinator

| Need | Use |
|---|---|
| map every item and stop on first failure | `Effect.forEach` |
| run existing effects and preserve input shape | `Effect.all` |
| collect successes and failures separately | `Effect.partition` |
| collect every failure, discard successes on failure | `Effect.validateAll` |
| first success, all errors if no success | `Effect.validateFirst` |

For dynamic collections, prefer `forEach` over constructing an array of effects
manually. It keeps input mapping and concurrency policy in one call.

## Concurrency Rules

Use `concurrency: 1` when order and external side effects must be sequential.

Use a bounded number for network, filesystem, database, and API fan-out.

Use unbounded concurrency only for small, controlled collections. If the input
can grow with user or database size, unbounded fan-out is a production risk.

## Cross-references

See also: [effect all](08-effect-all.md), [short-circuiting](11-short-circuiting.md), [generators](05-generators.md), [gen vs pipe](06-gen-vs-pipe.md).
