# Match.not, Match.whenOr, And Match.either
Use secondary match helpers when a plain positive case is not the clearest shape.

Effect v3 has `Match.not`, `Match.whenOr`, `Match.whenAnd`, `Match.either`, and
`Match.option`. It does not export a `Match.or` helper in `Match.ts`; use
`Match.whenOr` for "any of these patterns" matching.

## `Match.not`

`Match.not(pattern, handler)` matches values that do not match the pattern.

```typescript
import { Match } from "effect"

type Status = "draft" | "published" | "archived"

const isVisible = Match.type<Status>().pipe(
  Match.not("archived", () => true),
  Match.when("archived", () => false),
  Match.exhaustive
)
```

This is useful when the exceptional case is easier to name than every allowed
case.

Do not use `Match.not` if it makes the domain less obvious. Listing explicit
cases is often clearer for tagged unions.

## `Match.whenOr`

Use `Match.whenOr` when several patterns share one handler.

```typescript
import { Match } from "effect"

type HttpMethod = "GET" | "HEAD" | "POST" | "PUT" | "DELETE"

const methodKind = Match.type<HttpMethod>().pipe(
  Match.whenOr("GET", "HEAD", () => "read"),
  Match.whenOr("POST", "PUT", "DELETE", () => "write"),
  Match.exhaustive
)
```

The v3 name is `whenOr`, not `or`. If an agent writes `Match.or`, check
`Match.ts` and replace it with `Match.whenOr` or separate `Match.when` calls.

## `Match.whenAnd`

Use `Match.whenAnd` when several patterns must match at the same time.

```typescript
import { Match } from "effect"

type User = {
  readonly role: "admin" | "member"
  readonly active: boolean
}

const accessLevel = Match.type<User>().pipe(
  Match.whenAnd({ role: "admin" }, { active: true }, () => "admin"),
  Match.when({ active: true }, () => "member"),
  Match.orElse(() => "blocked")
)
```

`whenAnd` is ordered like every other case. Put stricter cases before broader
cases.

## `Match.either`

`Match.either` finalizes a matcher without forcing a default. It returns
`Either.Either<Matched, Remaining>`.

```typescript
import { Either, Match } from "effect"

type Token =
  | { readonly _tag: "Word"; readonly value: string }
  | { readonly _tag: "Number"; readonly value: number }
  | { readonly _tag: "Space" }

const classifyWord = Match.type<Token>().pipe(
  Match.tag("Word", (token) => token.value),
  Match.either
)

const renderWord = (token: Token): string =>
  Either.match(classifyWord(token), {
    onLeft: () => "not a word",
    onRight: (word) => word
  })
```

Use `Match.either` when a miss is not failure and the caller still needs the
unmatched value's type.

## `Match.option`

`Match.option` is similar, but it discards the unmatched value.

```typescript
import { Match, Option } from "effect"

type Token =
  | { readonly _tag: "Word"; readonly value: string }
  | { readonly _tag: "Number"; readonly value: number }
  | { readonly _tag: "Space" }

const wordOption = Match.type<Token>().pipe(
  Match.tag("Word", (token) => token.value),
  Match.option
)

const wordLength = (token: Token): number =>
  Option.match(wordOption(token), {
    onNone: () => 0,
    onSome: (word) => word.length
  })
```

Use `Option` when only presence or absence matters.

## Choosing The Helper

| Need | Helper |
|---|---|
| Match every case except one pattern | `Match.not` |
| Match any of several patterns | `Match.whenOr` |
| Match all listed patterns | `Match.whenAnd` |
| Keep unmatched values typed | `Match.either` |
| Ignore unmatched values but avoid fallback strings | `Match.option` |

Keep the matcher easy to read. If a helper makes the branch harder to understand,
use explicit cases.

## Cross-references

See also: [01-overview.md](01-overview.md), [05-match-when.md](05-match-when.md), [07-exhaustive-vs-orelse.md](07-exhaustive-vs-orelse.md)
