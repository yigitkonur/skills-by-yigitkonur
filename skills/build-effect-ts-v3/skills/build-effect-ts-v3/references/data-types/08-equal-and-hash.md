# Equal And Hash
Use Effect equality and hashing when values should compare by meaning instead of identity.

## The problem
JavaScript reference equality is not domain equality. Effect collections and `Data` values use `Equal` and `Hash` so structurally equal values can act like the same key or member.

## Data values already participate
```typescript
import { Data, Equal, Hash } from "effect"

const a = Data.struct({ id: "a", version: 1 })
const b = Data.struct({ id: "a", version: 1 })

const equal = Equal.equals(a, b)
const sameHash = Hash.hash(a) === Hash.hash(b)
```

## Custom equality
Most application code should prefer `Data` constructors instead of hand-writing `Equal` and `Hash`. Implement custom equality only when the domain value cannot be represented by the built-in structural forms.

## Custom implementation shape
```typescript
import { Equal, Hash, pipe } from "effect"

class CaseInsensitiveName implements Equal.Equal {
  constructor(readonly value: string) {}

  [Equal.symbol](that: unknown): boolean {
    return that instanceof CaseInsensitiveName &&
      this.value.toLowerCase() === that.value.toLowerCase()
  }

  [Hash.symbol](): number {
    return pipe(
      Hash.hash("CaseInsensitiveName"),
      Hash.combine(Hash.string(this.value.toLowerCase()))
    )
  }
}

const same = Equal.equals(
  new CaseInsensitiveName("ADA"),
  new CaseInsensitiveName("ada")
)
```

## Collection payoff
```typescript
import { Data, HashMap } from "effect"

const keyA = Data.struct({ tenant: "a", id: "1" })
const keyB = Data.struct({ tenant: "a", id: "1" })

const map = HashMap.make([keyA, "cached"])
const value = HashMap.get(map, keyB)
```

## Rules
- Equal values must have equal hashes.
- Include a stable type marker in custom hashes to avoid accidental collisions across concepts.
- Do not mutate fields that contribute to equality or hashing.
- Prefer `Data.struct`, `Data.Class`, or `Data.taggedEnum` before custom implementations.

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
## Cross-references
See also: [Data.struct](05-data-struct.md), [Data case](07-data-case.md), [HashSet and HashMap](10-hashset-hashmap.md), [Order and Equivalence](17-order-and-equivalence.md).
