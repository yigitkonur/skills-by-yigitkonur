# TypeBox Value Operations

The `Value` module provides runtime operations on values against TypeBox schemas. These work independently of Fastify and Ajv.

```typescript
import { Value } from 'typebox/value'
// or: import { Value } from '@sinclair/typebox/value'
```

## Value.Check — Validate a Value

Returns `true` if the value matches the schema, `false` otherwise:

```typescript
import { Type } from 'typebox'
import { Value } from 'typebox/value'

const UserSchema = Type.Object({
  name: Type.String({ minLength: 1 }),
  age: Type.Integer({ minimum: 0 }),
})

Value.Check(UserSchema, { name: 'Alice', age: 30 })  // true
Value.Check(UserSchema, { name: '', age: 30 })        // false (minLength)
Value.Check(UserSchema, { name: 'Alice' })             // false (missing age)
Value.Check(UserSchema, 'not an object')               // false
```

## Value.Errors — Get Validation Errors

Returns an iterator of validation errors with paths and messages:

```typescript
const errors = [...Value.Errors(UserSchema, { name: '', age: -1 })]
// [
//   { path: '/name', message: 'Expected string length >= 1', ... },
//   { path: '/age', message: 'Expected integer >= 0', ... },
// ]

// Iterate lazily
for (const error of Value.Errors(UserSchema, badData)) {
  console.log(`${error.path}: ${error.message}`)
}

// Get first error only (efficient — stops after first)
const firstError = Value.Errors(UserSchema, badData).First()
```

## Value.Cast — Coerce to Match Schema

Attempts to cast a value to match the schema. Preserves valid properties, fills missing ones with defaults or type-appropriate values:

```typescript
const result = Value.Cast(UserSchema, { name: 'Alice' })
// { name: 'Alice', age: 0 }  — age filled with default for Integer

Value.Cast(UserSchema, { name: 123, age: 'hello', extra: true })
// { name: '', age: 0 }  — invalid types replaced, extra properties removed

Value.Cast(Type.String(), 42)
// ''  — non-string cast to empty string
```

> **Use case:** Sanitizing partially-valid input data before processing.

## Value.Clean — Remove Extra Properties

Removes properties not defined in the schema:

```typescript
const cleaned = Value.Clean(UserSchema, {
  name: 'Alice',
  age: 30,
  hackAttempt: '<script>alert("xss")</script>',
  __proto__: {},
})
// { name: 'Alice', age: 30 }  — extra properties stripped
```

## Value.Clone — Deep Clone

Deep clones a value (no shared references):

```typescript
const original = { name: 'Alice', tags: ['admin'] }
const cloned = Value.Clone(original)
cloned.tags.push('user')
// original.tags is still ['admin']
```

## Value.Convert — Type Coercion

Attempts to convert values to match the expected types:

```typescript
// String to number
Value.Convert(Type.Number(), '42')
// 42

// String to boolean
Value.Convert(Type.Boolean(), 'true')
// true

// String to integer
Value.Convert(Type.Integer(), '100')
// 100

// Nested conversion in objects
const schema = Type.Object({
  port: Type.Integer(),
  debug: Type.Boolean(),
  name: Type.String(),
})

Value.Convert(schema, { port: '3000', debug: 'false', name: 'app' })
// { port: 3000, debug: false, name: 'app' }
```

> **Use case:** Processing query strings where everything arrives as strings.

## Value.Create — Generate Default Instance

Creates a value that conforms to the schema using defaults:

```typescript
const ConfigSchema = Type.Object({
  host: Type.String({ default: 'localhost' }),
  port: Type.Integer({ default: 3000 }),
  debug: Type.Boolean({ default: false }),
  tags: Type.Array(Type.String(), { default: [] }),
})

const config = Value.Create(ConfigSchema)
// { host: 'localhost', port: 3000, debug: false, tags: [] }

// Without defaults, uses type-appropriate zero values
const bare = Value.Create(Type.Object({
  name: Type.String(),
  count: Type.Integer(),
}))
// { name: '', count: 0 }
```

## Value.Default — Apply Default Values

Mutates the value in-place, filling only missing/undefined properties with their schema defaults:

```typescript
const schema = Type.Object({
  host: Type.String({ default: 'localhost' }),
  port: Type.Integer({ default: 3000 }),
  debug: Type.Boolean({ default: false }),
})

const partial = { host: 'myhost' }
Value.Default(schema, partial)
// partial is now { host: 'myhost', port: 3000, debug: false }
// Note: host was NOT overwritten because it already had a value
```

## Value.Diff and Value.Patch — Structural Diffing

Compute and apply JSON Patch-like diffs:

```typescript
const before = { name: 'Alice', age: 30, role: 'user' }
const after = { name: 'Alice', age: 31, role: 'admin' }

const diff = Value.Diff(before, after)
// [
//   { type: 'update', path: '/age', value: 31 },
//   { type: 'update', path: '/role', value: 'admin' },
// ]

// Apply the diff to reconstruct the target
const patched = Value.Patch(before, diff)
// { name: 'Alice', age: 31, role: 'admin' }
```

## Value.Equal — Deep Equality

```typescript
Value.Equal(
  { a: 1, b: [2, 3] },
  { a: 1, b: [2, 3] },
) // true

Value.Equal(
  { a: 1, b: [2, 3] },
  { a: 1, b: [2, 4] },
) // false
```

## Value.Hash — Deterministic Hashing

```typescript
const hash = Value.Hash({ name: 'Alice', age: 30 })
// Returns a bigint hash value

// Same structure always produces same hash
Value.Hash({ a: 1 }) === Value.Hash({ a: 1 }) // true

// Useful for caching, deduplication, change detection
```

## Chaining Operations — Common Pipeline

A typical validation pipeline:

```typescript
function processInput<T extends TSchema>(schema: T, raw: unknown): Static<T> {
  // 1. Apply defaults for missing fields
  Value.Default(schema, raw)

  // 2. Convert string types (query params, env vars)
  const converted = Value.Convert(schema, raw)

  // 3. Remove extra properties
  const cleaned = Value.Clean(schema, converted)

  // 4. Validate
  if (!Value.Check(schema, cleaned)) {
    const errors = [...Value.Errors(schema, cleaned)]
    throw new ValidationError(errors)
  }

  return cleaned as Static<T>
}
```

## Performance Note

`Value.Check` recompiles the validator on every call. For hot paths, use `TypeCompiler.Compile` instead (see type-compiler.md). The `Value.*` operations are convenient for one-off usage, scripts, and tests.
