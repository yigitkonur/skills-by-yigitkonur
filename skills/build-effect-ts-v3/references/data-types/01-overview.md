# Effect Data Types Overview
Map nullable values, raw dates, raw arrays, and structural domain records to Effect v3 data types.

## Why this layer matters
Effect data types are not decorative wrappers. They encode decisions that JavaScript primitives leave implicit: absence, recoverable error, structural identity, collection equality, time units, time zones, decimal arithmetic, redaction, and brands.

The goal is not to ban JavaScript values everywhere. The goal is boundary discipline: decode permissive input at the edge, then keep principled values in the domain and service layers.

## Replacement map
| JavaScript habit | Effect v3 type | Use when |
|---|---|---|
| `T | null` | `Option.Option<T>` | A value may be absent without being an error. |
| `value or thrown exception` | `Either.Either<A, E>` | You need a pure value-level branch. |
| mutable object literal | `Data.struct` or `Data.Class` | Equality and hashing should be structural. |
| discriminated union boilerplate | `Data.taggedEnum` | Variants need constructors, matching, and narrowing. |
| repeated array copies | `Chunk.Chunk<A>` | Immutable sequence semantics matter. |
| object keys by identity | `HashMap.HashMap<K, V>` | Keys need structural equality and hashing. |
| array as set | `HashSet.HashSet<A>` | Membership should be structural. |
| numeric milliseconds | `Duration.Duration` input | Time amounts need units and readable syntax. |
| `Date` in domain | `DateTime.DateTime` | Time values need UTC/zoned behavior and math. |
| float money math | `BigDecimal.BigDecimal` | Decimal precision matters. |
| raw secret string | `Redacted.Redacted<A>` | Logs and inspection must not reveal the value. |
| opaque string conventions | `Brand.Brand` | A primitive needs a domain name. |

## Layering rule
Use permissive JavaScript at the outside and Effect data types inside.

- HTTP, JSON, CLI, form input: parse nullable, string, number, arrays, and dates.
- Domain model: store `Option`, `Data`, `Chunk`, `HashMap`, `HashSet`, `Duration`, `DateTime`, `BigDecimal`, `Redacted`, or branded primitives.
- Persistence and transport output: encode back to plain values deliberately.

This prevents null checks, stringly typed units, accidental secret logging, and equality bugs from spreading through the codebase.

## Small example
```typescript
import { Data, DateTime, Duration, Option, Redacted } from "effect"

class Session extends Data.Class<{
  readonly userId: string
  readonly displayName: Option.Option<string>
  readonly expiresAt: DateTime.DateTime
  readonly refreshAfter: Duration.Duration
  readonly accessToken: Redacted.Redacted<string>
}> {}

const makeSession = (input: {
  readonly userId: string
  readonly displayName: string | null
  readonly expiresAt: string
  readonly accessToken: string
}) =>
  Option.map(DateTime.make(input.expiresAt), (expiresAt) =>
    new Session({
      userId: input.userId,
      displayName: Option.fromNullable(input.displayName),
      expiresAt,
      refreshAfter: Duration.decode("15 minutes"),
      accessToken: Redacted.make(input.accessToken)
    })
  )
```

## Selection heuristics
- Use `Option` for absence, not for failure details.
- Use `Either` for pure computations; use Effect failures for effectful workflows.
- Use `Data` when values should compare by content instead of reference.
- Use `Chunk` when an immutable sequence is part of your Effect-facing API.
- Use `Array` module helpers for ordinary readonly arrays and stable sorting.
- Use `DateTime` instead of carrying `Date` through services.
- Use `Duration` string syntax for readable time amounts.
- Use `Redacted` immediately after loading secrets.

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
## Cross-references
See also: [Option](02-option.md), [Option patterns](03-option-patterns.md), [Data.struct](05-data-struct.md), [DateTime](13-datetime.md), [Redacted](15-redacted.md).
