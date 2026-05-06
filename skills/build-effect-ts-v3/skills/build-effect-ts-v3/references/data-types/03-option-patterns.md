# Option Patterns
Keep nullability at system edges and keep `Option` in domain models.

## Boundary rule
External systems may send nullable fields. Domain code should not store nullable fields. The shorthand is: null at edges, Option in domain. Convert once, then keep `Option` until the next boundary.

Good boundary names make this visible:

- `decodeUser` may accept `string | null`.
- `User` stores `Option.Option<string>`.
- `encodeUser` decides whether to emit nullable JSON.

## Decode edge input
```typescript
import { Data, Option } from "effect"

class User extends Data.Class<{
  readonly id: string
  readonly nickname: Option.Option<string>
}> {}

const decodeUser = (input: {
  readonly id: string
  readonly nickname: string | null
}): User =>
  new User({
    id: input.id,
    nickname: Option.fromNullable(input.nickname)
  })
```

## Domain code consumes Option
```typescript
import { Option, pipe } from "effect"

type User = {
  readonly id: string
  readonly nickname: Option.Option<string>
}

const greeting = (user: User): string =>
  pipe(
    user.nickname,
    Option.match({
      onNone: () => `Hello, ${user.id}`,
      onSome: (nickname) => `Hello, ${nickname}`
    })
  )
```

## Encode at the edge
```typescript
import { Option } from "effect"

type User = {
  readonly id: string
  readonly nickname: Option.Option<string>
}

const encodeUser = (user: User): {
  readonly id: string
  readonly nickname: string | null
} => ({
  id: user.id,
  nickname: Option.getOrNull(user.nickname)
})
```

## Avoid mixed models
Do not create types like `Option.Option<string> | null`. That shape means the boundary conversion did not finish.

Do not use `Option.getOrThrow` to avoid changing downstream code. If callers need a guaranteed value, make the caller prove it with `Option.match`, `Option.filter`, or a constructor that returns a non-optional domain type.

Module mechanics are in [Option](02-option.md), and the extraction anti-pattern is documented in [option get-or-throw](../anti-patterns/11-option-getorthrow.md).

## Common patterns
- `Option.fromNullable` at JSON, database, and framework boundaries.
- `Option.match` for rendering and branching.
- `Option.getOrElse` for default values that are genuinely safe.
- `Option.flatMap` when the next lookup may also be absent.
- `Option.all` when all optional fields must be present.

## Review checklist
- Keep nullable values at module boundaries, not in domain objects.
- Prefer total constructors that return `Option` or typed failures.
- Import data modules from the `effect` barrel.
- Use `pipe` when a transformation has more than one step.
- Reach for structural equality before hand-written comparison logic.
- Keep raw JavaScript containers only where their semantics are the point.
- Convert back to plain data only at serialization or framework edges.
- Check the source when an API name feels guessed.
- Make invalid states unrepresentable where the module supports it.
- Keep examples small enough to paste into a service or test.
- Prefer explicit matching over unchecked extraction.
- Document the boundary where protected values are unwrapped.
- Use the smallest data type that communicates the invariant.
- Avoid widening precise domain values into `string` or `number` too early.
- Keep collection ordering explicit when output stability matters.
- Use module-provided `Order` and `Equivalence` instances where available.
- Do not replace Effect data types with ad hoc object conventions.
- Revisit adjacent anti-patterns when reviewing generated code.
## Boundary checks
- Identify the exact ingress where JavaScript values are decoded.
- Convert nullable input once, before it enters the domain model.
- Preserve redacted values until the external client needs the raw secret.
- Convert Effect collections back to plain arrays only for framework interop.
- Format time and decimals at output boundaries, not in core logic.
- Keep branded primitives branded after validation.
- Keep time units visible at configuration and scheduling call sites.
- Treat unsafe constructors as trusted-edge tools, not convenience helpers.
- Let `Option` communicate absence instead of sentinel strings.
- Let structural collections communicate key and member semantics.
- Use domain constructors as the only place where invariants are established.
- Avoid leaking transport shapes into service return types.
- Keep sorting rules near the output that depends on deterministic order.
- Use `DateTime.toDate` only when a library requires it.
- Use `BigDecimal.format` only where strings are required.
- Use `Redacted.value` only where a concrete credential is consumed.
- Make the boundary visible in function names such as `decode` and `encode`.
- Keep example imports shallow and source-backed.


## API checks
- Verify constructor names against the v3 source before adding examples.
- Prefer safe constructors returning `Option` when parsing external input.
- Use module-provided match functions for branching.
- Use dual APIs either directly or in `pipe`, whichever is clearer.
- Keep examples independent; each code block should include its imports.
- Avoid unchecked accessors in examples unless the section is explicitly about trusted input.
- Prefer `Arr.head`, `Chunk.head`, and map lookups that return `Option`.
- Use `Order` when any output order is visible to callers.
- Use `Equivalence` for contextual equality and `Equal.equals` for structural values.
- Avoid inventing helper functions that hide the data type being taught.
- Keep code blocks focused on one idea.
- Prefer small domain records over anonymous nested object examples.
- Use `Data` for value identity before reaching for custom `Equal` implementations.
- Keep duration strings readable and unit-bearing.
- Avoid raw date arithmetic; use `DateTime` math functions.
- Prefer `HashMap.get` over defaulting missing keys silently.
- Preserve type names that communicate the invariant.
- Keep examples compatible with `effect@3.21.2`.


## Generation checks
- Do not widen optional values back into nullable domain fields.
- Do not add deep imports from individual Effect modules.
- Do not hide failures with unchecked extraction.
- Do not serialize secrets by unwrapping them early.
- Do not use native `Set` or `Map` when keys require structural equality.
- Do not use a raw array when persistent immutable sequence semantics are required.
- Do not use `Date` as a long-lived domain field.
- Do not use floating point arithmetic for decimal money examples.
- Do not sort records without naming the `Order` used.
- Do not compare structural values with reference equality.
- Do not build ad hoc discriminated unions when `Data.taggedEnum` is the topic.
- Do not carry transport DTO names into the domain model.
- Do not add optional fields where `Option` would make absence explicit.
- Do not claim a helper exists unless source confirms it.
- Do not use unsafe constructors in boundary examples unless the trust boundary is named.
- Do not make examples depend on test-only imports.
- Do not use mutable arrays as persistent service state.
- Do not bury important conversions in callback bodies.




## Review checklist
- Keep nullable values at module boundaries, not in domain objects.
- Prefer total constructors that return `Option` or typed failures.
- Import data modules from the `effect` barrel.
- Use `pipe` when a transformation has more than one step.
- Reach for structural equality before hand-written comparison logic.
- Keep raw JavaScript containers only where their semantics are the point.
- Convert back to plain data only at serialization or framework edges.
- Check the source when an API name feels guessed.
- Make invalid states unrepresentable where the module supports it.
- Keep examples small enough to paste into a service or test.
- Prefer explicit matching over unchecked extraction.
- Document the boundary where protected values are unwrapped.
## Cross-references
See also: [Option](02-option.md), [Either](04-either.md), [Data.struct](05-data-struct.md), [ReadonlyArray](11-readonly-array.md).
