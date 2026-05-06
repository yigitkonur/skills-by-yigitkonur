# Url
Use `Url` and `UrlParams` for immutable URL parsing, mutation, and query parameter handling.

## Module Shape

`Url` is a pure helper module, not a service tag. It wraps native `URL` values
with immutable setters and safe parsing.

Common operations:

| Function | Use |
|---|---|
| `fromString(url, base?)` | Parse to `Either<URL, IllegalArgumentException>` |
| `mutate(url, f)` | Clone and mutate the clone |
| `setProtocol(url, value)` | Replace protocol |
| `setHost(url, value)` | Replace host |
| `setHostname(url, value)` | Replace hostname |
| `setPort(url, value)` | Replace port |
| `setPathname(url, value)` | Replace pathname |
| `setSearch(url, value)` | Replace search string |
| `urlParams(url)` | Read query params as `UrlParams` |
| `setUrlParams(url, params)` | Replace query params |
| `modifyUrlParams(url, f)` | Read, transform, and write params |

## Safe Parsing

```typescript
import { Either, Effect } from "effect"
import { Url } from "@effect/platform"

export const parseEndpoint = (input: string) =>
  Url.fromString(input).pipe(
    Either.match({
      onLeft: (error) => Effect.fail(error),
      onRight: (url) => Effect.succeed(url)
    })
  )
```

`Url.fromString` returns `Either`, so parsing can happen outside an Effect
workflow. Convert to an Effect when the caller expects typed failure.

## Immutable Mutation

```typescript
import { pipe } from "effect"
import { Url } from "@effect/platform"

export const toApiEndpoint = (base: URL) =>
  pipe(
    base,
    Url.setProtocol("https:"),
    Url.setPathname("/api/v1/events"),
    Url.setSearch("")
  )
```

Each setter clones the URL. The original `base` remains unchanged.

## Query Parameters

```typescript
import { pipe } from "effect"
import { Url, UrlParams } from "@effect/platform"

export const withCursor = (url: URL, cursor: string) =>
  pipe(
    url,
    Url.modifyUrlParams(
      UrlParams.set("cursor", cursor)
    )
  )
```

Use `UrlParams` for query-string construction. It avoids hand-built escaping
and keeps transformations composable.

## Redacted Passwords

`setPassword` accepts a string or `Redacted.Redacted`. Prefer redacted values
when the password comes from configuration.

```typescript
import { Redacted } from "effect"
import { Url } from "@effect/platform"

export const attachPassword = (url: URL, password: Redacted.Redacted) =>
  Url.setPassword(url, password)
```

Do not log the resulting URL when it contains credentials.

## Base URL Parsing

```typescript
import { Either } from "effect"
import { Url } from "@effect/platform"

export const relativeToBase = Url.fromString(
  "/health",
  "https://service.internal"
).pipe(
  Either.map((url) => url.href)
)
```

This is useful for configuration that stores a service origin separately from
per-request paths.

## When to Use Path Instead

Use `Path` for file-system paths and `Url` for URLs. File URLs sit at the
boundary: convert with `Path.toFileUrl` or `Path.fromFileUrl`, then use `Url`
only after you are working with a real `URL`.

## Anti-patterns

- Building query strings with string concatenation.
- Mutating a `URL` instance that other code still owns.
- Treating file-system paths as URLs.
- Logging credential-bearing URLs.
- Throwing from URL parsing instead of using `Either` or typed failure.

## Cross-references

See also: [03-path.md](03-path.md), [07-keyvaluestore.md](07-keyvaluestore.md), [11-node-context.md](11-node-context.md)
