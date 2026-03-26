# TypeBox TypeCompiler

## Overview

`TypeCompiler.Compile` generates optimized validation functions from TypeBox schemas. It is significantly faster than `Value.Check` for repeated validations.

```typescript
import { TypeCompiler } from 'typebox/compiler'
// or: import { TypeCompiler } from '@sinclair/typebox/compiler'
import { Type } from 'typebox'
```

## Basic Usage

```typescript
const UserSchema = Type.Object({
  name: Type.String({ minLength: 1 }),
  email: Type.String({ format: 'email' }),
  age: Type.Integer({ minimum: 0, maximum: 150 }),
})

// Compile once at startup
const UserValidator = TypeCompiler.Compile(UserSchema)

// Check many times (fast)
UserValidator.Check({ name: 'Alice', email: 'alice@example.com', age: 30 })  // true
UserValidator.Check({ name: '', email: 'bad', age: -1 })                      // false
```

## Compiled Validator Methods

```typescript
const validator = TypeCompiler.Compile(schema)

// Check — returns boolean
validator.Check(value)

// Errors — returns iterator of validation errors
validator.Errors(value)

// Code — returns the generated validation function source
validator.Code()

// Decode — validate then apply Transform decode
validator.Decode(value)

// Encode — apply Transform encode then validate
validator.Encode(value)
```

## Error Iteration

```typescript
const validator = TypeCompiler.Compile(UserSchema)

const badData = { name: '', email: 'not-email', age: -5 }

// Get all errors
const errors = [...validator.Errors(badData)]
for (const error of errors) {
  console.log({
    path: error.path,       // '/name', '/email', '/age'
    value: error.value,     // the actual value at that path
    message: error.message, // human-readable message
    schema: error.schema,   // the sub-schema that failed
  })
}

// Get first error only (efficient — stops iteration early)
const first = validator.Errors(badData).First()
if (first) {
  console.log(`Validation failed at ${first.path}: ${first.message}`)
}
```

## Compile with References

When schemas use `Type.Ref`, pass referenced schemas to Compile:

```typescript
const AddressSchema = Type.Object({
  street: Type.String(),
  city: Type.String(),
  zip: Type.String(),
}, { $id: 'Address' })

const PersonSchema = Type.Object({
  name: Type.String(),
  address: Type.Ref(AddressSchema),
}, { $id: 'Person' })

// Pass references as additional arguments
const validator = TypeCompiler.Compile(PersonSchema, [AddressSchema])

validator.Check({
  name: 'Alice',
  address: { street: '123 Main', city: 'NYC', zip: '10001' },
}) // true
```

## Performance: TypeCompiler vs Value.Check vs Ajv

```typescript
import { TypeCompiler } from 'typebox/compiler'
import { Value } from 'typebox/value'
import Ajv from 'ajv'

const schema = Type.Object({
  x: Type.Number(),
  y: Type.Number(),
  z: Type.Number(),
})

const data = { x: 1, y: 2, z: 3 }

// TypeCompiler — fastest for TypeBox schemas
const compiled = TypeCompiler.Compile(schema)
compiled.Check(data) // ~180M ops/sec (benchmark varies by hardware)

// Value.Check — convenient but recompiles each call
Value.Check(schema, data) // ~2M ops/sec

// Ajv — comparable to TypeCompiler
const ajv = new Ajv()
const validate = ajv.compile(schema)
validate(data) // ~150M ops/sec
```

> **Rule of thumb:** Use `TypeCompiler.Compile` for any schema validated more than once. Use `Value.Check` for one-off validations in scripts/tests.

## Caching Compiled Validators

```typescript
// Pattern: compile at module level
const validators = {
  user: TypeCompiler.Compile(UserSchema),
  product: TypeCompiler.Compile(ProductSchema),
  order: TypeCompiler.Compile(OrderSchema),
}

export function validateUser(data: unknown) {
  if (!validators.user.Check(data)) {
    throw new ValidationError([...validators.user.Errors(data)])
  }
  return data as Static<typeof UserSchema>
}
```

## Using with Fastify

Fastify already uses Ajv internally for schema validation. TypeCompiler is useful when you need validation outside of route handlers:

```typescript
import { TypeCompiler } from 'typebox/compiler'

const EventSchema = Type.Object({
  type: Type.String(),
  payload: Type.Unknown(),
  timestamp: Type.String({ format: 'date-time' }),
})

const eventValidator = TypeCompiler.Compile(EventSchema)

// Use in message queue consumer, WebSocket handler, etc.
async function handleMessage(raw: string) {
  const parsed = JSON.parse(raw)
  if (!eventValidator.Check(parsed)) {
    const errors = [...eventValidator.Errors(parsed)]
    logger.warn('Invalid event', { errors })
    return
  }
  // parsed is valid EventSchema
  await processEvent(parsed)
}
```

## Decode/Encode with TypeCompiler

```typescript
const DateTransform = Type.Transform(Type.String({ format: 'date-time' }))
  .Decode(v => new Date(v))
  .Encode(v => v.toISOString())

const EventSchema = Type.Object({
  name: Type.String(),
  occurredAt: DateTransform,
})

const compiled = TypeCompiler.Compile(EventSchema)

// Decode: validate wire format, then transform
const decoded = compiled.Decode({
  name: 'signup',
  occurredAt: '2024-01-15T10:30:00Z',
})
// decoded.occurredAt instanceof Date → true

// Encode: transform back to wire, then validate
const encoded = compiled.Encode({
  name: 'signup',
  occurredAt: new Date('2024-01-15T10:30:00Z'),
})
// encoded.occurredAt === '2024-01-15T10:30:00.000Z'
```

## Inspecting Generated Code

```typescript
const validator = TypeCompiler.Compile(
  Type.Object({
    name: Type.String({ minLength: 1 }),
    age: Type.Integer({ minimum: 0 }),
  })
)

// View the generated validation function
console.log(validator.Code())
// Outputs optimized JavaScript validation code
// Useful for debugging or understanding what TypeCompiler does
```

## Error Formatting Helper

```typescript
function formatErrors(validator: ReturnType<typeof TypeCompiler.Compile>, data: unknown) {
  return [...validator.Errors(data)].map(e => ({
    field: e.path.replace(/^\//, '').replace(/\//g, '.') || '(root)',
    message: e.message,
    value: e.value,
  }))
}

// Usage
const errs = formatErrors(UserValidator, badInput)
// [{ field: 'name', message: 'Expected string length >= 1', value: '' }]
```
