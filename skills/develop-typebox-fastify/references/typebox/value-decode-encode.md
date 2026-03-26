# TypeBox Value.Decode and Value.Encode

## Overview

`Value.Decode` and `Value.Encode` work with Transform schemas to convert between wire format (JSON) and application format (rich types like Date, Set, Map, etc.).

```typescript
import { Type, type StaticDecode, type StaticEncode } from 'typebox'
import { Value } from 'typebox/value'
```

## Transform Schema Basics

A Transform schema has two directions:
- **Decode**: wire format → application format (e.g., ISO string → Date)
- **Encode**: application format → wire format (e.g., Date → ISO string)

```typescript
const DateSchema = Type.Transform(Type.String({ format: 'date-time' }))
  .Decode(value => new Date(value))        // string → Date
  .Encode(value => value.toISOString())     // Date → string

// Type inference
type Decoded = StaticDecode<typeof DateSchema>  // Date
type Encoded = StaticEncode<typeof DateSchema>  // string
```

## Value.Decode — Wire to Application

```typescript
// Decode a single date
const date = Value.Decode(DateSchema, '2024-01-15T10:30:00Z')
// => Date object: Mon Jan 15 2024 10:30:00 GMT+0000

// Decode validates BEFORE transforming — invalid input throws
try {
  Value.Decode(DateSchema, 12345)  // not a string
} catch (error) {
  // TransformDecodeError: value does not match schema
}
```

## Value.Encode — Application to Wire

```typescript
// Encode a Date back to string
const iso = Value.Encode(DateSchema, new Date('2024-01-15T10:30:00Z'))
// => '2024-01-15T10:30:00.000Z'
```

## Nested Transform Schemas

Transforms compose naturally inside objects:

```typescript
const UserSchema = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  createdAt: Type.Transform(Type.String({ format: 'date-time' }))
    .Decode(v => new Date(v))
    .Encode(v => v.toISOString()),
  tags: Type.Transform(Type.String())
    .Decode(v => new Set(v.split(',')))
    .Encode(v => [...v].join(',')),
})

type UserWire = StaticEncode<typeof UserSchema>
// { id: string; name: string; createdAt: string; tags: string }

type UserApp = StaticDecode<typeof UserSchema>
// { id: string; name: string; createdAt: Date; tags: Set<string> }

// Decode from JSON
const user = Value.Decode(UserSchema, {
  id: '550e8400-e29b-41d4-a716-446655440000',
  name: 'Alice',
  createdAt: '2024-01-15T10:30:00Z',
  tags: 'admin,editor,viewer',
})
// user.createdAt instanceof Date → true
// user.tags instanceof Set → true
// user.tags.has('admin') → true

// Encode back to JSON
const wire = Value.Encode(UserSchema, user)
// { id: '...', name: 'Alice', createdAt: '2024-01-15T10:30:00.000Z', tags: 'admin,editor,viewer' }
```

## Common Transform Patterns

### BigInt from String

```typescript
const BigIntSchema = Type.Transform(Type.String({ pattern: '^\\d+$' }))
  .Decode(v => BigInt(v))
  .Encode(v => v.toString())

type Decoded = StaticDecode<typeof BigIntSchema>  // bigint
```

### Map from Record

```typescript
const MapSchema = Type.Transform(Type.Record(Type.String(), Type.Number()))
  .Decode(v => new Map(Object.entries(v)))
  .Encode(v => Object.fromEntries(v))

type Decoded = StaticDecode<typeof MapSchema>  // Map<string, number>
```

### Trimmed String

```typescript
const TrimmedString = Type.Transform(Type.String())
  .Decode(v => v.trim())
  .Encode(v => v)
```

### Lowercase Email

```typescript
const NormalizedEmail = Type.Transform(Type.String({ format: 'email' }))
  .Decode(v => v.toLowerCase().trim())
  .Encode(v => v)
```

### Parsed JSON

```typescript
const JsonPayload = Type.Transform(Type.String())
  .Decode(v => JSON.parse(v))
  .Encode(v => JSON.stringify(v))
```

### URL Object

```typescript
const UrlSchema = Type.Transform(Type.String({ format: 'uri' }))
  .Decode(v => new URL(v))
  .Encode(v => v.toString())

type Decoded = StaticDecode<typeof UrlSchema>  // URL
```

## Using with TypeCompiler

For performance-critical decode/encode, use TypeCompiler:

```typescript
import { TypeCompiler } from 'typebox/compiler'

const compiled = TypeCompiler.Compile(DateSchema)

// Decode with compiled validator
const date = compiled.Decode('2024-01-15T10:30:00Z')

// Encode with compiled validator
const str = compiled.Encode(new Date())

// Check before decode
if (compiled.Check(rawValue)) {
  const decoded = compiled.Decode(rawValue)
}
```

## Using with Fastify

Fastify does NOT automatically call Decode/Encode on Transform schemas. You need to handle this in hooks or route handlers:

```typescript
import { TypeCompiler } from 'typebox/compiler'

const BodySchema = Type.Object({
  scheduledAt: Type.Transform(Type.String({ format: 'date-time' }))
    .Decode(v => new Date(v))
    .Encode(v => v.toISOString()),
})

const compiledBody = TypeCompiler.Compile(BodySchema)

fastify.post('/events', {
  schema: {
    body: BodySchema,  // Fastify validates the wire format
  },
}, async (request, reply) => {
  // Fastify validated request.body as { scheduledAt: string }
  // Now decode to get { scheduledAt: Date }
  const decoded = compiledBody.Decode(request.body)
  // decoded.scheduledAt instanceof Date → true
})
```

## Error Handling

```typescript
import { TransformDecodeError, TransformEncodeError } from 'typebox/value'

try {
  Value.Decode(DateSchema, 'not-a-date')
} catch (error) {
  if (error instanceof TransformDecodeError) {
    console.log(error.message)  // decode error details
    console.log(error.error)    // underlying validation error
  }
}
```

## Decode vs Check

| Operation | Validates | Transforms | Returns |
|-----------|-----------|------------|---------|
| `Value.Check(schema, value)` | Yes | No | `boolean` |
| `Value.Decode(schema, value)` | Yes | Yes | decoded value or throws |
| `Value.Encode(schema, value)` | No* | Yes | encoded value or throws |

*Encode transforms first, then validates the result against the wire schema.
