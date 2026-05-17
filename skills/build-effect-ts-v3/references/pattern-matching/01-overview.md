# Pattern Matching Overview
Use `Match` to replace fragile branching with typed, explicit case handling.

Effect v3 ships the `Match` module from the `"effect"` barrel. It gives TypeScript
code a pattern-matching style without waiting for JavaScript syntax support.

The point is not aesthetics. The point is making missing cases visible to the type
checker when the input is a closed union.

Use `Match` when code is shaped like this:

- a tagged union with `_tag`
- a domain status with known variants
- a configuration variant
- a request or event union
- an error union after `Effect.catchTag` or `Effect.catchTags`
- a primitive union such as `string | number`

Avoid using `Match` for ordinary sequential business logic where every branch has
different side effects and no shared input shape. In that case, `Effect.gen`,
small functions, and direct composition are usually clearer.

## The Core Shape

Every matcher has three phases:

1. Start with `Match.value(input)` or `Match.type<Input>()`.
2. Add cases with `Match.when`, `Match.tag`, `Match.not`, or related helpers.
3. Finish with `Match.exhaustive`, `Match.orElse`, `Match.either`, or `Match.option`.

```typescript
import { Match } from "effect"

type Command =
  | { readonly _tag: "Create"; readonly name: string }
  | { readonly _tag: "Archive"; readonly id: string }
  | { readonly _tag: "Restore"; readonly id: string }

const describeCommand = (command: Command): string =>
  Match.value(command).pipe(
    Match.tag("Create", (create) => `create ${create.name}`),
    Match.tag("Archive", (archive) => `archive ${archive.id}`),
    Match.tag("Restore", (restore) => `restore ${restore.id}`),
    Match.exhaustive
  )
```

That example uses `Match.value` because the input value already exists.
`Match.exhaustive` is the important finalizer: if a new `Command` case is added,
the matcher stops compiling until the new case is handled.

## Value Matchers

`Match.value(input)` creates a one-shot matcher for a concrete value. It is best
when the match is local to one function.

```typescript
import { Match } from "effect"

type Mode = "readonly" | "editable" | "admin"

const labelMode = (mode: Mode): string =>
  Match.value(mode).pipe(
    Match.when("readonly", () => "read only"),
    Match.when("editable", () => "can edit"),
    Match.when("admin", () => "administrator"),
    Match.exhaustive
  )
```

Use it when extracting, rendering, normalizing, or routing a single value.

## Type Matchers

`Match.type<Input>()` builds a reusable function. It is best when the same case
handling is used in multiple call sites.

```typescript
import { Match } from "effect"

type Health =
  | { readonly _tag: "Healthy" }
  | { readonly _tag: "Degraded"; readonly reason: string }
  | { readonly _tag: "Down"; readonly service: string }

const renderHealth = Match.type<Health>().pipe(
  Match.tag("Healthy", () => "healthy"),
  Match.tag("Degraded", (health) => `degraded: ${health.reason}`),
  Match.tag("Down", (health) => `down: ${health.service}`),
  Match.exhaustive
)
```

The result is a function:

```typescript
const text = renderHealth({ _tag: "Degraded", reason: "slow database" })
```

## Why It Replaces `switch`

A `switch` over `_tag` looks familiar, but it is easy to leave stale after a union
changes. A default branch often hides the problem.

With `Match`, the residual type is tracked through the pipeline. Each case removes
part of the input union. `Match.exhaustive` only accepts a matcher whose residual
type is `never`.

That gives the agent and the compiler a shared goal:

- every known case is listed
- every handler receives the narrowed case
- newly added cases break the right line
- default behavior is explicit with `Match.orElse`

## Choosing The Finalizer

Use the finalizer to declare whether the input is closed or open.

| Input shape | Finalizer | Reason |
|---|---|---|
| Closed tagged union | `Match.exhaustive` | Missing cases should be compile errors. |
| Closed primitive union | `Match.exhaustive` | Each literal or refined type can be consumed. |
| Dynamic string or number | `Match.orElse` | The input has values the type checker cannot enumerate. |
| Optional classification | `Match.option` | No match is a normal outcome. |
| Two-track classification | `Match.either` | Preserve the unmatched value for later handling. |

Do not add `Match.orElse` to a closed union out of habit. It weakens the main
benefit of the module.

## Match And Effect Errors

Effect errors are commonly tagged objects. `Effect.catchTag` and
`Effect.catchTags` recover from selected error tags inside an Effect pipeline.
`Match` is the natural pair when you already have an error value and need to
render, classify, or convert it.

Use this split:

- use `Effect.catchTag` to recover while still inside the Effect error channel
- use `Match.tag` to handle a tagged value you already hold
- use `Match.exhaustive` when the error union is closed
- use `Match.orElse` when third-party or boundary errors can still appear

## Agent Rule

When you see a `switch (value._tag)` or an `if` chain checking `_tag`, try to
replace it with `Match.tag` and `Match.exhaustive`. Keep the old branch order
only if it encodes a real priority. For plain tagged unions, order should not
matter.

## Cross-references

See also: [02-match-value.md](02-match-value.md), [03-match-type.md](03-match-type.md), [04-match-tag.md](04-match-tag.md), [07-exhaustive-vs-orelse.md](07-exhaustive-vs-orelse.md), [../error-handling/04-catch-tag.md](../error-handling/04-catch-tag.md)
