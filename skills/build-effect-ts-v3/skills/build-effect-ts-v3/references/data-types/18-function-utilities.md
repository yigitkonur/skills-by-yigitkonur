# Function Utilities
Use Effect function helpers to keep data-type transformations small, pipeable, and typed.

## Pipe and flow
`pipe` sends a value through a sequence of transformations. `flow` composes functions for reuse. They are exported from the `effect` barrel and are central to idiomatic examples across the data modules.

## Pipe
```typescript
import { Option, pipe } from "effect"

const normalize = (input: string | null): string =>
  pipe(
    Option.fromNullable(input),
    Option.map((value) => value.trim()),
    Option.filter((value) => value.length > 0),
    Option.getOrElse(() => "anonymous")
  )
```

## Flow
```typescript
import { Option, flow } from "effect"

const trimOptional = flow(
  Option.fromNullable<string>,
  Option.map((value) => value.trim()),
  Option.filter((value) => value.length > 0)
)
```

## Small constants
```typescript
import { Function as Fn, Option } from "effect"

const disabled = Option.match(Option.none<string>(), {
  onNone: Fn.constant("disabled"),
  onSome: Fn.identity
})

const ignore = Fn.constVoid
```

## Dual APIs
Many Effect data-type functions are dual: they can be called as `Option.map(option, f)` or curried as `Option.map(f)` inside `pipe`. Prefer the style that keeps the transformation easiest to scan.

## Identity and constants
Use `identity` when a branch returns its input unchanged. Use `constant(value)` for callbacks that ignore their input. Use `constVoid` when a callback intentionally returns no meaningful value.

## Rules
- Prefer `pipe` for multi-step data transformations.
- Prefer direct calls for one-step transformations.
- Use `flow` when the composed function will be reused.
- Avoid point-free code when naming the intermediate value would be clearer.
- Keep function helpers supporting the data-type story, not obscuring it.

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




## Cross-references
See also: [Option](02-option.md), [Duration](12-duration.md), [ReadonlyArray](11-readonly-array.md).
