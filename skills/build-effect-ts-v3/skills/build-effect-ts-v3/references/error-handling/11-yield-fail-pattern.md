# Yield Fail Pattern
Use `return yield*` when failing inside `Effect.gen` so TypeScript and readers both see the branch terminates.

## The rule

Inside `Effect.gen`, prefer:

```typescript
import { Data, Effect } from "effect"

class InvalidInput extends Data.TaggedError("InvalidInput")<{
  readonly field: string
}> {}

const parse = (value: string) =>
  Effect.gen(function* () {
    if (value.length === 0) {
      return yield* new InvalidInput({ field: "value" })
    }
    return value.toUpperCase()
  })
```

The tagged error instance is yieldable. Yielding it fails the effect with that typed error.

## Why return yield*

`yield*` tells Effect to run or yield the failing value. `return` tells TypeScript control flow that this branch does not continue.

Without `return`, TypeScript may not narrow later code the way you expect, especially after validation branches. With `return yield*`, both the runtime effect and the static control-flow model agree: this branch has ended.

This is the generator-specific reason to use the pattern. For more generator mechanics, see [../core/05-generators.md](../core/05-generators.md).

## Validation narrowing

```typescript
import { Data, Effect } from "effect"

class MissingName extends Data.TaggedError("MissingName")<{}> {}

const greet = (input: { readonly name: string }) =>
  Effect.gen(function* () {
    if (input.name.length === 0) {
      return yield* new MissingName({})
    }
    return `hello ${input.name.toUpperCase()}`
  })
```

After the failing branch returns, `input.name` is narrowed for the success branch.

## Effect.fail still works

`Effect.fail` is valid, but the class instance form is shorter once you use yieldable tagged errors:

```typescript
import { Data, Effect } from "effect"

class MissingName extends Data.TaggedError("MissingName")<{}> {}

const withFail = Effect.gen(function* () {
  return yield* Effect.fail(new MissingName({}))
})

const withYieldable = Effect.gen(function* () {
  return yield* new MissingName({})
})
```

Prefer the yieldable form for tagged errors. Use `Effect.fail` when the error value is not yieldable or when point-free composition is clearer.

## Do not keep running

This shape is suspicious:

```typescript
import { Data, Effect } from "effect"

class InvalidInput extends Data.TaggedError("InvalidInput")<{}> {}

const bad = Effect.gen(function* () {
  yield* new InvalidInput({})
  return "still-running"
})
```

The effect fails at runtime, but the source shape tells readers the function might continue. Use `return yield*` to make the termination explicit.

## Branch discipline

Use `return yield*` for:

- validation failures
- authorization failures
- not-found branches
- state-machine impossible user transitions that are still domain failures
- early exits from guard clauses

Do not use it for success values. Return success values normally.

## In pipe-based code

Outside generators, prefer direct combinators:

```typescript
import { Data, Effect } from "effect"

class InvalidInput extends Data.TaggedError("InvalidInput")<{}> {}

const program = Effect.fail(new InvalidInput({})).pipe(
  Effect.catchTag("InvalidInput", () => Effect.succeed("fallback"))
)
```

The `return yield*` rule is specifically about generator control-flow clarity.

## Cross-references

See also: [02-data-tagged-error.md](02-data-tagged-error.md), [03-schema-tagged-error.md](03-schema-tagged-error.md), [04-catch-tag.md](04-catch-tag.md), [../core/05-generators.md](../core/05-generators.md), [12-error-taxonomy.md](12-error-taxonomy.md).
