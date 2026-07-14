# Short Circuiting
Understand when Effect stops on failure, when work may already be running, and when validation keeps going.

## Sequential Short-circuiting

Sequential composition stops at the first expected failure.

```typescript
import { Effect } from "effect"

const program = Effect.gen(function* () {
  yield* stepOne
  yield* stepTwo
  return yield* stepThree
})

declare const stepOne: Effect.Effect<void, "StepOneFailed">
declare const stepTwo: Effect.Effect<void, "StepTwoFailed">
declare const stepThree: Effect.Effect<string, "StepThreeFailed">
```

If `stepOne` fails, `stepTwo` and `stepThree` do not run. If `stepTwo` fails,
`stepThree` does not run.

## Pipeline Short-circuiting

Pipelines follow the same rule.

```typescript
import { Effect } from "effect"

const program = loadUser("u1").pipe(
  Effect.flatMap((user) => loadSettings(user.id)),
  Effect.map((settings) => settings.theme)
)

declare const loadUser: (
  id: string
) => Effect.Effect<{ readonly id: string }, "MissingUser">
declare const loadSettings: (
  id: string
) => Effect.Effect<{ readonly theme: string }, "MissingSettings">
```

If `loadUser` fails, the `flatMap` function is never called.

## Concurrent Short-circuiting

Default `Effect.all` with concurrency short-circuits on first failure, but some
work may already have started.

```typescript
import { Effect } from "effect"

const program = Effect.all(
  [
    fetchOne,
    fetchTwo,
    fetchThree
  ],
  { concurrency: 3 }
)

declare const fetchOne: Effect.Effect<string, "OneFailed">
declare const fetchTwo: Effect.Effect<string, "TwoFailed">
declare const fetchThree: Effect.Effect<string, "ThreeFailed">
```

If `fetchTwo` fails first, the combined effect fails. Other running fibers are
interrupted, but external systems may already have observed started work. Use
idempotent operations or compensation when concurrent side effects matter.

## Validation Keeps Going

Validation modes are for collecting more than the first failure.

```typescript
import { Effect } from "effect"

const program = Effect.validateAll(
  ["Ada", "", "Grace", ""],
  (name) =>
    name.length === 0
      ? Effect.fail("EmptyName")
      : Effect.succeed(name),
  { concurrency: 2 }
)
```

This checks every item and accumulates failures. It is a different contract
from default short-circuiting.

## Either Mode Keeps Outcomes

`Effect.all` with `{ mode: "either" }` records each effect's outcome as data.

```typescript
import { Effect } from "effect"

const program = Effect.all(
  [
    validate("ok"),
    validate("")
  ],
  { concurrency: 2, mode: "either" }
)

declare const validate: (
  input: string
) => Effect.Effect<string, "Invalid">
```

Use this when you want a per-item report and do not want item failures in the
combined error channel.

## Rule of Thumb

Use default sequencing when later work depends on earlier success.

Use bounded concurrency when work is independent and first failure should stop
the whole operation.

Use validation or either mode when the caller needs a complete report.

Use `partition` when successes and failures are both valuable.

## Cross-references

See also: [effect all](08-effect-all.md), [effect foreach](09-effect-foreach.md), [generators](05-generators.md), [running effects](03-running-effects.md).
