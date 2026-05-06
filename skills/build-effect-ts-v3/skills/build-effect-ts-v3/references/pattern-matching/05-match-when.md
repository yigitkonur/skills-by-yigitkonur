# Match.when
Use `Match.when` for literal, predicate, and object-pattern cases.

`Match.when` is the general case combinator. It matches values by direct equality,
safe refinements such as `Match.string`, predicate functions, or object patterns.

Use `Match.tag` for `_tag` unions. Use `Match.when` when the pattern is not
strictly a tag.

## Literal Values

```typescript
import { Match } from "effect"

type Theme = "system" | "light" | "dark"

const themeLabel = Match.type<Theme>().pipe(
  Match.when("system", () => "System"),
  Match.when("light", () => "Light"),
  Match.when("dark", () => "Dark"),
  Match.exhaustive
)
```

Literal matching is useful for small closed unions. If the value is a broad
`string`, finish with `Match.orElse` instead of `Match.exhaustive`.

## Built-In Refinements

Effect v3 exposes common refinements from `Match.ts`:

- `Match.string`
- `Match.nonEmptyString`
- `Match.number`
- `Match.boolean`
- `Match.bigint`
- `Match.symbol`
- `Match.date`
- `Match.record`
- `Match.defined`
- `Match.any`
- `Match.instanceOf`

Use them to narrow dynamic input safely.

```typescript
import { Match } from "effect"

const describeInput = (input: string | number | boolean): string =>
  Match.value(input).pipe(
    Match.when(Match.string, (text) => `text ${text.length}`),
    Match.when(Match.number, (number) => `number ${number}`),
    Match.when(Match.boolean, (flag) => `flag ${flag}`),
    Match.exhaustive
  )
```

Each handler receives the refined type.

## Predicate Patterns

Predicate functions can be embedded inside object patterns.

```typescript
import { Match } from "effect"

type Account = {
  readonly id: string
  readonly balance: number
  readonly locked: boolean
}

const accountRisk = Match.type<Account>().pipe(
  Match.when({ locked: true }, () => "locked"),
  Match.when({ balance: (amount) => amount < 0 }, (account) => `overdrawn ${account.id}`),
  Match.orElse((account) => `ok ${account.id}`)
)
```

This input is not a closed union. `Match.orElse` is correct because many account
values remain after the first two patterns.

## Object Pattern Matching

Object patterns match only the fields you list.

```typescript
import { Match } from "effect"

type Request =
  | { readonly method: "GET"; readonly path: "/health" }
  | { readonly method: "GET"; readonly path: "/users" }
  | { readonly method: "POST"; readonly path: "/users" }

const routeName = Match.type<Request>().pipe(
  Match.when({ method: "GET", path: "/health" }, () => "health"),
  Match.when({ method: "GET", path: "/users" }, () => "list users"),
  Match.when({ method: "POST", path: "/users" }, () => "create user"),
  Match.exhaustive
)
```

For closed object unions, `Match.exhaustive` works when the patterns consume all
members.

## Avoid Hidden Priority Bugs

Patterns are checked in pipeline order. Put more specific cases before broader
cases.

```typescript
import { Match } from "effect"

type FileEvent =
  | { readonly kind: "change"; readonly path: string; readonly generated: true }
  | { readonly kind: "change"; readonly path: string; readonly generated: false }
  | { readonly kind: "delete"; readonly path: string }

const classifyFileEvent = Match.type<FileEvent>().pipe(
  Match.when({ kind: "change", generated: true }, (event) => `generated ${event.path}`),
  Match.when({ kind: "change" }, (event) => `changed ${event.path}`),
  Match.when({ kind: "delete" }, (event) => `deleted ${event.path}`),
  Match.exhaustive
)
```

If the broad `"change"` case came first, the generated case would never run.

## When To Prefer Another Helper

| Situation | Prefer |
|---|---|
| Discriminant is `_tag` | `Match.tag` |
| Discriminant is another field | `Match.discriminator("field")` |
| Several patterns share one handler | `Match.whenOr` |
| A case should match everything except one pattern | `Match.not` |
| The match should return `Option` | `Match.option` finalizer |
| The match should preserve misses | `Match.either` finalizer |

`Match.when` is broad, so use the more specific helper when it communicates the
domain shape better.

## Matching Dynamic Boundary Input

Boundary input is usually open. Do not pretend a raw `string` is exhaustive.

```typescript
import { Effect, Match } from "effect"

class InvalidPortError {
  readonly _tag = "InvalidPortError"
  constructor(readonly value: number) {}
}

const parsePort = (value: number) =>
  Match.value(value).pipe(
    Match.when((port) => Number.isInteger(port) && port > 0 && port < 65536, (port) =>
      Effect.succeed(port)
    ),
    Match.orElse((port) => Effect.fail(new InvalidPortError(port)))
  )
```

The predicate narrows the acceptable range. `Match.orElse` handles every other
number.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-match-value.md](02-match-value.md), [04-match-tag.md](04-match-tag.md), [06-not-or-either.md](06-not-or-either.md), [07-exhaustive-vs-orelse.md](07-exhaustive-vs-orelse.md)
