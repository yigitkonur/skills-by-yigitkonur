# TypeBox Schema Composition

## Intersect — Combining Schemas

```typescript
import { Type, type Static } from 'typebox'

const Timestamped = Type.Object({
  createdAt: Type.String({ format: 'date-time' }),
  updatedAt: Type.String({ format: 'date-time' }),
})

const SoftDeletable = Type.Object({
  deletedAt: Type.Optional(Type.String({ format: 'date-time' })),
})

const BaseEntity = Type.Object({
  id: Type.String({ format: 'uuid' }),
})

// Combine multiple schemas into one
const FullEntity = Type.Intersect([BaseEntity, Timestamped, SoftDeletable])
type FullEntity = Static<typeof FullEntity>
// => { id: string; createdAt: string; updatedAt: string; deletedAt?: string }
```

## Pick — Select Specific Properties

```typescript
const UserSchema = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  email: Type.String({ format: 'email' }),
  password: Type.String(),
  role: Type.String(),
})

const UserPublic = Type.Pick(UserSchema, ['id', 'name', 'email'])
type UserPublic = Static<typeof UserPublic>
// => { id: string; name: string; email: string }
```

## Omit — Exclude Specific Properties

```typescript
const UserWithoutPassword = Type.Omit(UserSchema, ['password'])
type UserWithoutPassword = Static<typeof UserWithoutPassword>
// => { id: string; name: string; email: string; role: string }

// Create input schema from full schema
const CreateUserInput = Type.Omit(UserSchema, ['id'])
type CreateUserInput = Static<typeof CreateUserInput>
// => { name: string; email: string; password: string; role: string }
```

## Partial — Make All Properties Optional

```typescript
const UpdateUserSchema = Type.Partial(UserSchema)
type UpdateUser = Static<typeof UpdateUserSchema>
// => { id?: string; name?: string; email?: string; password?: string; role?: string }

// Common pattern: Partial for PATCH endpoints
const PatchUserBody = Type.Partial(Type.Omit(UserSchema, ['id']))
type PatchUserBody = Static<typeof PatchUserBody>
// => { name?: string; email?: string; password?: string; role?: string }
```

## Required — Make All Properties Required

```typescript
const ConfigSchema = Type.Object({
  host: Type.Optional(Type.String()),
  port: Type.Optional(Type.Integer()),
  debug: Type.Optional(Type.Boolean()),
})

const StrictConfig = Type.Required(ConfigSchema)
type StrictConfig = Static<typeof StrictConfig>
// => { host: string; port: number; debug: boolean }
```

## Record — Dynamic Keys

```typescript
// String keys with typed values
const Headers = Type.Record(Type.String(), Type.String())
type Headers = Static<typeof Headers>
// => Record<string, string>

// Constrained keys using Union of Literals
const Env = Type.Record(
  Type.Union([Type.Literal('development'), Type.Literal('staging'), Type.Literal('production')]),
  Type.Object({ url: Type.String(), debug: Type.Boolean() })
)
type Env = Static<typeof Env>
// => Record<'development' | 'staging' | 'production', { url: string; debug: boolean }>
```

## Extending Schemas — Composition Patterns

TypeBox schemas are plain objects, so extension is done via Intersect or spread:

```typescript
// Pattern 1: Intersect (recommended — preserves JSON Schema semantics)
const BaseResponse = Type.Object({
  success: Type.Boolean(),
  timestamp: Type.String({ format: 'date-time' }),
})

const DataResponse = Type.Intersect([
  BaseResponse,
  Type.Object({
    data: Type.Array(Type.Unknown()),
    total: Type.Integer({ minimum: 0 }),
  }),
])

// Pattern 2: Spread properties into a new Type.Object
// Useful when you want a flat schema (no allOf in JSON Schema)
const FlatResponse = Type.Object({
  ...BaseResponse.properties,
  data: Type.Array(Type.Unknown()),
  total: Type.Integer({ minimum: 0 }),
})
```

> **When to use which:**
> - `Intersect` keeps schemas separate in JSON Schema (`allOf`). Good for $ref reuse.
> - Property spread creates a single flat `object` schema. Better for OpenAPI tools that struggle with `allOf`.

## Composing CRUD Schemas

A common pattern for building related schemas from a base:

```typescript
const ProductBase = Type.Object({
  name: Type.String({ minLength: 1 }),
  description: Type.String(),
  price: Type.Number({ minimum: 0 }),
  categoryId: Type.Integer(),
})

// CREATE — all base fields required
const CreateProduct = ProductBase
type CreateProduct = Static<typeof CreateProduct>

// READ — base + generated fields
const Product = Type.Intersect([
  Type.Object({ id: Type.Integer() }),
  ProductBase,
  Type.Object({
    createdAt: Type.String({ format: 'date-time' }),
    updatedAt: Type.String({ format: 'date-time' }),
  }),
])
type Product = Static<typeof Product>

// UPDATE (PUT) — all base fields required + id
const UpdateProduct = Type.Intersect([
  Type.Object({ id: Type.Integer() }),
  ProductBase,
])

// PATCH — partial base fields
const PatchProduct = Type.Partial(ProductBase)
type PatchProduct = Static<typeof PatchProduct>

// LIST response
const ProductList = Type.Object({
  items: Type.Array(Product),
  total: Type.Integer({ minimum: 0 }),
})
```

## Combining with Readonly

```typescript
const ImmutableUser = Type.Readonly(UserSchema)
// All properties become readonly in TypeScript
// JSON Schema is unchanged (readonly is TS-only)

// Readonly specific fields using Intersect + Pick
const UserWithReadonlyId = Type.Intersect([
  Type.Readonly(Type.Pick(UserSchema, ['id'])),
  Type.Omit(UserSchema, ['id']),
])
```

## KeyOf — Extract Key Union

```typescript
const UserKeys = Type.KeyOf(UserSchema)
type UserKeys = Static<typeof UserKeys>
// => 'id' | 'name' | 'email' | 'password' | 'role'

// Useful for building sort/filter params
const SortField = Type.KeyOf(Type.Omit(UserSchema, ['password']))
```

## Index — Access Nested Type

```typescript
const EmailType = Type.Index(UserSchema, ['email'])
type EmailType = Static<typeof EmailType>
// => string

// Access multiple keys
const NameOrEmail = Type.Index(UserSchema, ['name', 'email'])
type NameOrEmail = Static<typeof NameOrEmail>
// => string (union of the indexed types)
```

## Practical Tip: Schema Registry Pattern

```typescript
// schemas/base.ts
export const Id = Type.String({ format: 'uuid' })
export const Timestamps = Type.Object({
  createdAt: Type.String({ format: 'date-time' }),
  updatedAt: Type.String({ format: 'date-time' }),
})

// schemas/user.ts
import { Id, Timestamps } from './base'

const UserFields = Type.Object({
  name: Type.String(),
  email: Type.String({ format: 'email' }),
})

export const User = Type.Intersect([
  Type.Object({ id: Id }),
  UserFields,
  Timestamps,
])
export const CreateUser = UserFields
export const UpdateUser = Type.Partial(UserFields)
```
