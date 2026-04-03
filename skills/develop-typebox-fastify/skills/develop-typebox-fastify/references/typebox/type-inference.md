# TypeBox Type Inference

## The Core Idea: Single Source of Truth

TypeBox eliminates the need to define both a runtime schema and a TypeScript type. Define the schema once, extract the type with `Static`.

```typescript
import { Type, type Static } from 'typebox'

// Define schema ONCE
const UserSchema = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String({ minLength: 1 }),
  email: Type.String({ format: 'email' }),
  role: Type.Union([Type.Literal('admin'), Type.Literal('user')]),
  createdAt: Type.String({ format: 'date-time' }),
})

// Extract type — NEVER write this manually
type User = Static<typeof UserSchema>
// Equivalent to:
// type User = {
//   id: string
//   name: string
//   email: string
//   role: 'admin' | 'user'
//   createdAt: string
// }
```

## Static, StaticDecode, StaticEncode

TypeBox provides three type extraction utilities:

```typescript
import { Type, type Static, type StaticDecode, type StaticEncode } from 'typebox'

// For plain schemas (no Transform), all three are identical:
const PlainSchema = Type.Object({ name: Type.String() })
type A = Static<typeof PlainSchema>        // { name: string }
type B = StaticDecode<typeof PlainSchema>  // { name: string }
type C = StaticEncode<typeof PlainSchema>  // { name: string }

// For Transform schemas, they differ:
const DateSchema = Type.Transform(Type.String({ format: 'date-time' }))
  .Decode(v => new Date(v))
  .Encode(v => v.toISOString())

type Wire = StaticEncode<typeof DateSchema>    // string (JSON wire format)
type App = StaticDecode<typeof DateSchema>     // Date (application format)
type Default = Static<typeof DateSchema>       // StaticDecode → Date
```

## Avoiding Duplicate Type Definitions

### The Anti-Pattern

```typescript
// DON'T do this — types diverge from schemas over time
interface User {
  id: string
  name: string
  email: string
}

const UserSchema = Type.Object({
  id: Type.String(),
  name: Type.String(),
  email: Type.String(),
})

// If you add a field to one but forget the other → silent bugs
```

### The Correct Pattern

```typescript
// DO this — schema is the single source of truth
const UserSchema = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  email: Type.String({ format: 'email' }),
})
type User = Static<typeof UserSchema>

// Use the type in function signatures, return types, etc.
function getUser(id: string): Promise<User> { ... }
function createUser(data: Omit<User, 'id'>): Promise<User> { ... }
```

## Using with Function Signatures

```typescript
const CreateUserBody = Type.Object({
  name: Type.String({ minLength: 1 }),
  email: Type.String({ format: 'email' }),
})
type CreateUserBody = Static<typeof CreateUserBody>

const UserResponse = Type.Intersect([
  Type.Object({ id: Type.String({ format: 'uuid' }) }),
  CreateUserBody,
  Type.Object({ createdAt: Type.String({ format: 'date-time' }) }),
])
type UserResponse = Static<typeof UserResponse>

// Service layer uses the derived types
class UserService {
  async create(input: CreateUserBody): Promise<UserResponse> {
    const id = crypto.randomUUID()
    const user = { id, ...input, createdAt: new Date().toISOString() }
    await this.db.insert(user)
    return user
  }
}
```

## Type Inference in Fastify Routes

With `@fastify/type-provider-typebox`, Fastify infers types from schemas automatically:

```typescript
import Fastify from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

const fastify = Fastify().withTypeProvider<TypeBoxTypeProvider>()

fastify.post('/users', {
  schema: {
    body: Type.Object({
      name: Type.String(),
      email: Type.String({ format: 'email' }),
    }),
    response: {
      201: Type.Object({
        id: Type.String(),
        name: Type.String(),
        email: Type.String(),
      }),
    },
  },
}, async (request, reply) => {
  // request.body is automatically typed as { name: string; email: string }
  const { name, email } = request.body  // full autocomplete
  // reply.send() checks against response schema type
  return reply.status(201).send({ id: '...', name, email })
})
```

## Deriving Related Types from a Base Schema

```typescript
const ProductSchema = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  price: Type.Number({ minimum: 0 }),
  active: Type.Boolean(),
  createdAt: Type.String({ format: 'date-time' }),
})

// Derive all variants from the base
type Product = Static<typeof ProductSchema>
type CreateProduct = Static<typeof CreateProductBody>
type UpdateProduct = Static<typeof UpdateProductBody>
type ProductSummary = Static<typeof ProductSummarySchema>

const CreateProductBody = Type.Omit(ProductSchema, ['id', 'createdAt'])
const UpdateProductBody = Type.Partial(Type.Omit(ProductSchema, ['id', 'createdAt']))
const ProductSummarySchema = Type.Pick(ProductSchema, ['id', 'name', 'price'])
```

## Generic Functions with TSchema

```typescript
import { type TSchema, type Static } from 'typebox'
import { TypeCompiler } from 'typebox/compiler'

function validate<T extends TSchema>(
  schema: T,
  data: unknown
): Static<T> {
  const compiled = TypeCompiler.Compile(schema)
  if (!compiled.Check(data)) {
    const errors = [...compiled.Errors(data)]
    throw new Error(`Validation failed: ${errors[0]?.message}`)
  }
  return data as Static<T>
}

// Type is inferred from the schema argument
const user = validate(UserSchema, rawData)
// user is typed as User (Static<typeof UserSchema>)
```

## Index Types

Access the type of a specific property:

```typescript
const UserSchema = Type.Object({
  id: Type.String(),
  profile: Type.Object({
    bio: Type.String(),
    avatar: Type.String({ format: 'uri' }),
  }),
})

// Extract nested type
type UserProfile = Static<typeof UserSchema>['profile']
// => { bio: string; avatar: string }

// Or use Type.Index for schema-level access
const ProfileSchema = Type.Index(UserSchema, ['profile'])
type Profile = Static<typeof ProfileSchema>
```

## Array Element Types

```typescript
const ItemsSchema = Type.Array(Type.Object({
  id: Type.String(),
  name: Type.String(),
}))

type Items = Static<typeof ItemsSchema>        // Array<{ id: string; name: string }>
type Item = Static<typeof ItemsSchema>[number]  // { id: string; name: string }
```

## Key Takeaways

1. Always define the **schema** first, then derive the **type** with `Static`
2. Use the same name for both (TypeScript allows a type and value with the same name)
3. Use `StaticDecode`/`StaticEncode` when working with Transform schemas
4. Compose types using TypeBox composition (Pick, Omit, Partial) rather than TypeScript utility types
5. Let Fastify's type provider infer route handler types from schemas
