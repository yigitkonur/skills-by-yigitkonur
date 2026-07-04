# Match.value
Use `Match.value(input)` when one known value needs local, typed branching.

`Match.value` starts a matcher from a concrete value. The matcher is finalized in
the same expression, so it reads as "classify this value now."

This is the most direct replacement for a local `switch`, ternary chain, or
single-purpose helper.

## Basic Pipeline

```typescript
import { Match } from "effect"

type PaymentState =
  | "draft"
  | "authorized"
  | "captured"
  | "refunded"

const renderPaymentState = (state: PaymentState): string =>
  Match.value(state).pipe(
    Match.when("draft", () => "Draft"),
    Match.when("authorized", () => "Authorized"),
    Match.when("captured", () => "Captured"),
    Match.when("refunded", () => "Refunded"),
    Match.exhaustive
  )
```

The input type is a closed literal union, so `Match.exhaustive` is the right
finalizer. If `PaymentState` later gets `"failed"`, this matcher stops compiling
until a handler is added.

## Match Objects By Shape

`Match.when` can match object patterns, not only primitive values.

```typescript
import { Match } from "effect"

type User =
  | { readonly status: "active"; readonly name: string }
  | { readonly status: "invited"; readonly email: string }
  | { readonly status: "suspended"; readonly reason: string }

const userLabel = (user: User): string =>
  Match.value(user).pipe(
    Match.when({ status: "active" }, (active) => active.name),
    Match.when({ status: "invited" }, (invited) => `invited: ${invited.email}`),
    Match.when({ status: "suspended" }, (suspended) => `suspended: ${suspended.reason}`),
    Match.exhaustive
  )
```

For tagged unions, prefer `Match.tag` when the discriminant is `_tag`. For other
fields, object patterns through `Match.when` are clear and v3-supported.

## Return Effects From Branches

Branch handlers can return any value, including `Effect` values. Keep the matcher
purely about selecting the branch, then let the caller yield the selected Effect.

```typescript
import { Effect, Match } from "effect"

type Platform = "darwin" | "linux" | "win32"

class UnsupportedPlatformError {
  readonly _tag = "UnsupportedPlatformError"
  constructor(readonly platform: string) {}
}

const normalizePlatform = (platform: string) =>
  Match.value(platform).pipe(
    Match.when("darwin", () => Effect.succeed("macos" as const)),
    Match.when("linux", () => Effect.succeed("linux" as const)),
    Match.when("win32", () => Effect.succeed("windows" as const)),
    Match.orElse((other) => Effect.fail(new UnsupportedPlatformError(other)))
  )
```

Here `platform` is a dynamic `string`, not a closed union. `Match.orElse` is
required because there are infinitely many possible strings.

## Prefer `Match.tag` For `_tag`

This works:

```typescript
import { Match } from "effect"

type Job =
  | { readonly _tag: "Queued"; readonly id: string }
  | { readonly _tag: "Running"; readonly id: string }
  | { readonly _tag: "Finished"; readonly id: string }

const describeJob = (job: Job): string =>
  Match.value(job).pipe(
    Match.when({ _tag: "Queued" }, (queued) => `queued ${queued.id}`),
    Match.when({ _tag: "Running" }, (running) => `running ${running.id}`),
    Match.when({ _tag: "Finished" }, (finished) => `finished ${finished.id}`),
    Match.exhaustive
  )
```

But this is better:

```typescript
import { Match } from "effect"

type Job =
  | { readonly _tag: "Queued"; readonly id: string }
  | { readonly _tag: "Running"; readonly id: string }
  | { readonly _tag: "Finished"; readonly id: string }

const describeJob = (job: Job): string =>
  Match.value(job).pipe(
    Match.tag("Queued", (queued) => `queued ${queued.id}`),
    Match.tag("Running", (running) => `running ${running.id}`),
    Match.tag("Finished", (finished) => `finished ${finished.id}`),
    Match.exhaustive
  )
```

`Match.tag` communicates that the discriminant is the Effect-style `_tag` field.

## One-Shot Means Local

Use `Match.value` when the input is already present and the matcher has no reuse
value beyond the current expression.

Good fits:

- rendering one status in a component helper
- normalizing one boundary input
- mapping one domain command to one action
- choosing one Effect based on a parsed value

Weak fits:

- the same matcher is duplicated in multiple functions
- the matcher is part of a public API
- tests need to call the matcher independently
- branch logic is large enough to deserve named handlers

When reuse matters, move to `Match.type`.

## With `Effect.gen`

Inside `Effect.gen`, yield the result if each branch returns an Effect.

```typescript
import { Effect, Match } from "effect"

type Destination =
  | { readonly _tag: "Email"; readonly address: string }
  | { readonly _tag: "Webhook"; readonly url: string }

const sendEmail = (address: string) =>
  Effect.logInfo(`email ${address}`)

const callWebhook = (url: string) =>
  Effect.logInfo(`webhook ${url}`)

const notify = (destination: Destination) =>
  Effect.gen(function* () {
    yield* Match.value(destination).pipe(
      Match.tag("Email", (email) => sendEmail(email.address)),
      Match.tag("Webhook", (webhook) => callWebhook(webhook.url)),
      Match.exhaustive
    )
  })
```

The matcher selects an Effect. `yield*` runs it.

## Cross-references

See also: [01-overview.md](01-overview.md), [03-match-type.md](03-match-type.md), [04-match-tag.md](04-match-tag.md), [05-match-when.md](05-match-when.md)
