# TypeBox Schema Basics

## Package Import

```typescript
// Modern package name (recommended)
import { Type, type Static } from 'typebox'

// Legacy package name (still works)
import { Type, type Static } from '@sinclair/typebox'

// Via Fastify type provider (re-exports Type and Static)
import { Type, type Static } from '@fastify/type-provider-typebox'
```

## Primitive Types

```typescript
const StringSchema = Type.String()        // { type: 'string' }
const NumberSchema = Type.Number()        // { type: 'number' }
const BooleanSchema = Type.Boolean()      // { type: 'boolean' }
const IntegerSchema = Type.Integer()      // { type: 'integer' }
const NullSchema = Type.Null()            // { type: 'null' }

// With constraints
const BoundedString = Type.String({ minLength: 1, maxLength: 255 })
const BoundedNumber = Type.Number({ minimum: 0, maximum: 100 })
const PositiveInt = Type.Integer({ minimum: 1 })
```

## Type.Object — The Core Building Block

```typescript
const UserSchema = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String({ minLength: 1 }),
  email: Type.String({ format: 'email' }),
  age: Type.Optional(Type.Integer({ minimum: 0 })),
  active: Type.Boolean(),
})

// Extract the static TypeScript type
type User = Static<typeof UserSchema>
// => { id: string; name: string; email: string; age?: number; active: boolean }
```

## Type.Array

```typescript
const TagsSchema = Type.Array(Type.String(), { minItems: 1, maxItems: 10 })
// { type: 'array', items: { type: 'string' }, minItems: 1, maxItems: 10 }

const UsersSchema = Type.Array(UserSchema)
type Users = Static<typeof UsersSchema>
// => User[]
```

## Type.Optional

```typescript
const ProfileSchema = Type.Object({
  bio: Type.Optional(Type.String()),           // field may be missing
  avatar: Type.Optional(Type.String({ format: 'uri' })),
})
// bio and avatar are optional keys in the resulting object
```

## Type.Literal

```typescript
const AdminRole = Type.Literal('admin')       // { const: 'admin' }
const StatusCode = Type.Literal(200)          // { const: 200 }
const IsTrue = Type.Literal(true)             // { const: true }
```

## Type.Union

```typescript
const StatusSchema = Type.Union([
  Type.Literal('active'),
  Type.Literal('inactive'),
  Type.Literal('pending'),
])
type Status = Static<typeof StatusSchema>
// => 'active' | 'inactive' | 'pending'

// Union of different types
const StringOrNumber = Type.Union([Type.String(), Type.Number()])
type StringOrNumber = Static<typeof StringOrNumber>
// => string | number
```

## Type.Enum (Native TypeScript Enums)

```typescript
enum Role {
  Admin = 'admin',
  User = 'user',
  Guest = 'guest',
}

const RoleSchema = Type.Enum(Role)
type RoleType = Static<typeof RoleSchema>
// => Role (i.e. Role.Admin | Role.User | Role.Guest)
```

> **Prefer Union of Literals** over Type.Enum for better JSON Schema compatibility.
> Type.Enum uses `anyOf` with `const`, which some tools handle poorly.

## Type.Tuple

```typescript
const CoordinateSchema = Type.Tuple([Type.Number(), Type.Number()])
type Coordinate = Static<typeof CoordinateSchema>
// => [number, number]
```

## Type.Record

```typescript
const MetadataSchema = Type.Record(Type.String(), Type.Unknown())
type Metadata = Static<typeof MetadataSchema>
// => Record<string, unknown>

// Constrained keys
const ScoresSchema = Type.Record(
  Type.Union([Type.Literal('math'), Type.Literal('science')]),
  Type.Number()
)
```

## Static Type Extraction

The `Static` utility is the key to avoiding duplicate type definitions:

```typescript
import { Type, type Static } from 'typebox'

const CreateUserBody = Type.Object({
  name: Type.String(),
  email: Type.String({ format: 'email' }),
})

// Derive the type — never write interface manually
type CreateUserBody = Static<typeof CreateUserBody>

// Use in function signatures
function createUser(data: CreateUserBody): void {
  console.log(data.name, data.email)
}
```

## Adding Schema Metadata

Every schema accepts standard JSON Schema annotations:

```typescript
const ProductSchema = Type.Object({
  id: Type.Integer(),
  name: Type.String({ description: 'Product display name' }),
  price: Type.Number({ description: 'Price in USD', minimum: 0 }),
}, {
  $id: 'Product',
  title: 'Product',
  description: 'A product in the catalog',
  examples: [{ id: 1, name: 'Widget', price: 9.99 }],
  additionalProperties: false,
})
```

## Type.Any, Type.Unknown, Type.Void, Type.Never

```typescript
Type.Any()      // {} — matches anything (typed as any)
Type.Unknown()  // {} — matches anything (typed as unknown, safer)
Type.Void()     // { type: 'undefined' } — for void returns
Type.Never()    // { not: {} } — matches nothing
```

## Quick Reference Table

| TypeBox | JSON Schema | TypeScript |
|---------|-------------|------------|
| `Type.String()` | `{ type: 'string' }` | `string` |
| `Type.Number()` | `{ type: 'number' }` | `number` |
| `Type.Boolean()` | `{ type: 'boolean' }` | `boolean` |
| `Type.Integer()` | `{ type: 'integer' }` | `number` |
| `Type.Null()` | `{ type: 'null' }` | `null` |
| `Type.Array(T)` | `{ type: 'array', items: T }` | `T[]` |
| `Type.Object({...})` | `{ type: 'object', properties: {...} }` | `{ ... }` |
| `Type.Optional(T)` | removes key from `required` | `T \| undefined` |
| `Type.Literal(v)` | `{ const: v }` | literal type |
| `Type.Union([...])` | `{ anyOf: [...] }` | union type |
| `Type.Enum(E)` | `{ anyOf: [{ const: ... }, ...] }` | enum type |
