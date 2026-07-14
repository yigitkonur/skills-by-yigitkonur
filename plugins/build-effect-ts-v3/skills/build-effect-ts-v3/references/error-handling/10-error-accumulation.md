# Error Accumulation
Use accumulation when you need all validation failures or per-item outcomes instead of fail-fast behavior.

## Fail-fast vs accumulation

Most Effect composition fails fast. That is right for dependencies where later work cannot proceed after a failure.

Validation and batch processing often need a different shape:

- collect all invalid fields
- return successes and failures per item
- validate independent checks concurrently
- keep enough information for a form or report

Effect v3 supports this with `Effect.all` modes, `Effect.partition`, `Effect.validate`, `Effect.validateAll`, and related helpers.

## Effect.all mode either

`{ mode: "either" }` turns each branch outcome into `Either` and removes the outer error channel:

```typescript
import { Data, Effect } from "effect"

class FieldInvalid extends Data.TaggedError("FieldInvalid")<{
  readonly field: string
}> {}

const checks = [
  Effect.succeed("name"),
  Effect.fail(new FieldInvalid({ field: "email" }))
]

const outcomes = Effect.all(checks, {
  concurrency: 2,
  mode: "either"
})
```

Use this when callers need one outcome per input.

## Effect.all mode validate

`{ mode: "validate" }` accumulates failures as `Option` values:

```typescript
import { Data, Effect } from "effect"

class FieldInvalid extends Data.TaggedError("FieldInvalid")<{
  readonly field: string
}> {}

const checks = [
  Effect.succeed("name"),
  Effect.fail(new FieldInvalid({ field: "email" }))
]

const validation = Effect.all(checks, {
  concurrency: 2,
  mode: "validate"
})
```

Use this for validation-style checks where every independent branch should run.

## partition

`Effect.partition` separates failures from successes:

```typescript
import { Data, Effect } from "effect"

class OddNumber extends Data.TaggedError("OddNumber")<{
  readonly value: number
}> {}

const partitioned = Effect.partition([1, 2, 3, 4], (value) =>
  value % 2 === 0
    ? Effect.succeed(value)
    : Effect.fail(new OddNumber({ value }))
)
```

Use it for batch workflows where partial success is expected.

## validateAll

`Effect.validateAll` runs validations across an iterable and accumulates failures:

```typescript
import { Data, Effect } from "effect"

class TooLarge extends Data.TaggedError("TooLarge")<{
  readonly value: number
}> {}

const validateNumbers = Effect.validateAll([1, 2, 100], (value) =>
  value <= 10
    ? Effect.succeed(value)
    : Effect.fail(new TooLarge({ value }))
)
```

Use it when a single success array or an accumulated failure collection is the desired contract.

## Choosing a shape

| Need | Tool |
|---|---|
| every item returns success or failure | `Effect.all` with `mode: "either"` |
| validation failures accumulate | `Effect.all` with `mode: "validate"` |
| separate success and failure collections | `Effect.partition` |
| validate iterable and collect failures | `Effect.validateAll` |
| first successful validation wins | `Effect.validateFirst` or `Effect.firstSuccessOf` |

Avoid using accumulation to hide critical dependency failures. If one failure makes later work meaningless, fail fast.

## Typed accumulation

Accumulated errors should still be tagged:

```typescript
import { Data, Effect } from "effect"

class MissingField extends Data.TaggedError("MissingField")<{
  readonly field: string
}> {}

const required = (field: string, value: string) =>
  value.length > 0
    ? Effect.succeed(value)
    : Effect.fail(new MissingField({ field }))
```

This lets the UI or API layer render field-specific messages without parsing strings.

## Concurrency

When using `Effect.all` with more than a small fixed set, set concurrency explicitly. Validation can still overload a dependency if every check performs I/O.

For in-memory validation, concurrency mostly documents intent. For remote validation, it is a safety control.

## Cross-references

See also: [07-cause-and-exit.md](07-cause-and-exit.md), [09-recovery-patterns.md](09-recovery-patterns.md), [12-error-taxonomy.md](12-error-taxonomy.md), [13-error-remapping.md](13-error-remapping.md), [14-sandboxing.md](14-sandboxing.md).
