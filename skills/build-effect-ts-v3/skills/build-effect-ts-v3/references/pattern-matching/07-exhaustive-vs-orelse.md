# Exhaustive Versus orElse
Choose `Match.exhaustive` for closed inputs and `Match.orElse` for open inputs.

The finalizer is the design decision in a `Match` pipeline. It says whether
unmatched values are a compile-time bug or a legitimate runtime possibility.

## Decision Matrix

| Input | Use | Why |
|---|---|---|
| Closed union | `Match.exhaustive` | TypeScript knows every member, so missing cases should fail compilation. |
| Open union | `Match.orElse` | Some members are intentionally handled elsewhere or by a fallback. |
| `string` | `Match.orElse` | A broad string has infinitely many values. |
| `number` | `Match.orElse` | A broad number has too many values to enumerate. |
| Closed string-literal union | `Match.exhaustive` | Every literal can be consumed. |
| Boundary input | `Match.orElse` | External data must have an explicit fallback or failure. |
| Partial classifier | `Match.option` or `Match.either` | A miss is meaningful information, not a default. |

Default to `Match.exhaustive` for domain unions. Default to `Match.orElse` for
raw boundary values.

## Closed Union

```typescript
import { Match } from "effect"

type BuildState =
  | { readonly _tag: "Queued"; readonly id: string }
  | { readonly _tag: "Running"; readonly id: string }
  | { readonly _tag: "Passed"; readonly id: string }
  | { readonly _tag: "Failed"; readonly id: string; readonly reason: string }

const buildLabel = Match.type<BuildState>().pipe(
  Match.tag("Queued", (build) => `queued ${build.id}`),
  Match.tag("Running", (build) => `running ${build.id}`),
  Match.tag("Passed", (build) => `passed ${build.id}`),
  Match.tag("Failed", (build) => `failed ${build.reason}`),
  Match.exhaustive
)
```

This is the strongest form. A new tag becomes a compiler task instead of a hidden
runtime path.

## Closed Primitive Union

```typescript
import { Match } from "effect"

type SortDirection = "ascending" | "descending"

const sortDirectionSql = Match.type<SortDirection>().pipe(
  Match.when("ascending", () => "ASC"),
  Match.when("descending", () => "DESC"),
  Match.exhaustive
)
```

Literal unions are closed. Use `Match.exhaustive`.

## Open String

```typescript
import { Effect, Match } from "effect"

class UnknownSortDirectionError {
  readonly _tag = "UnknownSortDirectionError"
  constructor(readonly value: string) {}
}

const parseSortDirection = (value: string) =>
  Match.value(value).pipe(
    Match.when("asc", () => Effect.succeed("ascending" as const)),
    Match.when("desc", () => Effect.succeed("descending" as const)),
    Match.orElse((other) => Effect.fail(new UnknownSortDirectionError(other)))
  )
```

The input type is `string`, so `Match.exhaustive` is not honest. There are
unhandled strings by design.

## Open Number

```typescript
import { Effect, Match } from "effect"

class InvalidRetryCountError {
  readonly _tag = "InvalidRetryCountError"
  constructor(readonly value: number) {}
}

const parseRetryCount = (value: number) =>
  Match.value(value).pipe(
    Match.when(0, () => Effect.succeed({ retries: 0 as const })),
    Match.when((count) => Number.isInteger(count) && count > 0 && count <= 5, (count) =>
      Effect.succeed({ retries: count })
    ),
    Match.orElse((count) => Effect.fail(new InvalidRetryCountError(count)))
  )
```

Broad numbers need a fallback. Predicates do not make the number domain closed.

## Open Union

An open union is a type where the current matcher intentionally handles only part
of the domain.

```typescript
import { Match } from "effect"

type Event =
  | { readonly _tag: "UserCreated"; readonly id: string }
  | { readonly _tag: "UserDeleted"; readonly id: string }
  | { readonly _tag: "BillingEvent"; readonly id: string }

const auditUserEvent = Match.type<Event>().pipe(
  Match.tag("UserCreated", (event) => `created ${event.id}`),
  Match.tag("UserDeleted", (event) => `deleted ${event.id}`),
  Match.orElse((event) => `ignored ${event._tag}`)
)
```

Use this only when the fallback is a real policy. If `"BillingEvent"` should be
handled explicitly, use `Match.exhaustive` instead.

## `orElseAbsurd`

`Match.orElseAbsurd` exists in Effect v3, but it should be rare in skill examples.
It finalizes by treating the remaining case as absurd. Prefer
`Match.exhaustive` for closed unions because it exposes the missing-case
constraint directly.

Reach for `orElseAbsurd` only when you are deliberately working with a matcher
whose remaining type is already impossible and the surrounding type expression
makes that hard to express with `Match.exhaustive`.

## Agent Rule

When converting branch chains:

1. If the input is a domain union, use `Match.exhaustive`.
2. If the input is a raw `string` or `number`, use `Match.orElse`.
3. If a fallback is hiding a missing domain case, remove the fallback and make
   the matcher exhaustive.
4. If the caller needs to inspect misses, use `Match.either`.
5. If the caller only needs presence, use `Match.option`.

The strongest matcher is the one that matches the true shape of the input.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-match-value.md](02-match-value.md), [04-match-tag.md](04-match-tag.md), [05-match-when.md](05-match-when.md), [06-not-or-either.md](06-not-or-either.md)
