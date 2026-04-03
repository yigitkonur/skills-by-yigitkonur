# TypeBox Common Mistakes

## 1. Forgetting `ajv-formats` for Format Validation

**Mistake:** Using `format: 'email'` or `format: 'uuid'` without installing and registering `ajv-formats`. Ajv ignores unknown formats by default.

```typescript
// Schema looks right but never validates the format
const schema = Type.Object({
  email: Type.String({ format: 'email' }),
})
// "not-an-email" passes validation!
```

**Fix:**
```typescript
import ajvFormats from 'ajv-formats'

const fastify = Fastify({
  ajv: {
    plugins: [ajvFormats],
  },
})
```

## 2. Duplicating Types Instead of Using Static

**Mistake:** Writing both a schema and a separate interface.

```typescript
// These will drift apart over time
interface User {
  id: string
  name: string
  email: string
}
const UserSchema = Type.Object({
  id: Type.String(),
  name: Type.String(),
  email: Type.String(),
  role: Type.String(), // ← added to schema but not interface!
})
```

**Fix:**
```typescript
const UserSchema = Type.Object({
  id: Type.String(),
  name: Type.String(),
  email: Type.String(),
  role: Type.String(),
})
type User = Static<typeof UserSchema>  // always in sync
```

## 3. Using Value.Check in Hot Paths

**Mistake:** `Value.Check` recompiles the validator on every call.

```typescript
// Slow — recompiles on every request
function validateUser(data: unknown) {
  return Value.Check(UserSchema, data)
}
```

**Fix:**
```typescript
import { TypeCompiler } from 'typebox/compiler'

// Compile once
const userValidator = TypeCompiler.Compile(UserSchema)

// Fast — reuses compiled validator
function validateUser(data: unknown) {
  return userValidator.Check(data)
}
```

## 4. Confusing Optional with Nullable

**Mistake:** Using `Type.Optional` when you mean nullable, or vice versa.

```typescript
// This means bio can be ABSENT, not null
const Schema = Type.Object({
  bio: Type.Optional(Type.String()),
})
// { bio: null } → INVALID
// { } → valid
```

**Fix:**
```typescript
// Nullable: must be present, can be null
const Schema = Type.Object({
  bio: Type.Union([Type.String(), Type.Null()]),
})

// Optional + nullable: can be absent OR null
const Schema = Type.Object({
  bio: Type.Optional(Type.Union([Type.String(), Type.Null()])),
})
```

## 5. Not Setting additionalProperties

**Mistake:** Assuming TypeBox objects reject extra properties. They don't by default.

```typescript
const UserSchema = Type.Object({
  name: Type.String(),
})
// { name: "Alice", isAdmin: true } → VALID (extra props allowed)
```

**Fix:**
```typescript
// Option A: Schema-level
const UserSchema = Type.Object({
  name: Type.String(),
}, { additionalProperties: false })

// Option B: Fastify-level (strips extra properties)
const fastify = Fastify({
  ajv: {
    customOptions: {
      removeAdditional: 'all',
    },
  },
})
```

## 6. Expecting Transform Schemas to Work in Fastify Automatically

**Mistake:** Assuming Fastify calls `Decode`/`Encode` on Transform schemas.

```typescript
const DateType = Type.Transform(Type.String({ format: 'date-time' }))
  .Decode(v => new Date(v))
  .Encode(v => v.toISOString())

fastify.post('/events', {
  schema: { body: Type.Object({ date: DateType }) },
}, async (request) => {
  // request.body.date is still a STRING, not a Date!
  // Fastify only validates, it doesn't decode transforms
})
```

**Fix:**
```typescript
const compiled = TypeCompiler.Compile(Type.Object({ date: DateType }))

fastify.post('/events', {
  schema: { body: Type.Object({ date: DateType }) },
}, async (request) => {
  const body = compiled.Decode(request.body)
  // body.date instanceof Date → true
})
```

## 7. Using Type.Enum with String Literal Union Expectation

**Mistake:** Expecting `Type.Enum` with a TS enum to produce simple string literal types.

```typescript
enum Status { Active = 'active', Inactive = 'inactive' }
const StatusSchema = Type.Enum(Status)
type S = Static<typeof StatusSchema>
// => Status (not 'active' | 'inactive')
// This can cause type issues when comparing with string literals
```

**Fix:**
```typescript
// Use Union of Literals for cleaner string literal types
const StatusSchema = Type.Union([
  Type.Literal('active'),
  Type.Literal('inactive'),
])
type S = Static<typeof StatusSchema>
// => 'active' | 'inactive'
```

## 8. Forgetting the Type Provider

**Mistake:** Not registering the TypeBox type provider, so route handlers have `unknown` types.

```typescript
const fastify = Fastify()
// Missing: .withTypeProvider<TypeBoxTypeProvider>()

fastify.post('/users', {
  schema: { body: UserSchema },
}, async (request) => {
  request.body.name // ← TypeScript error: body is unknown
})
```

**Fix:**
```typescript
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

const fastify = Fastify().withTypeProvider<TypeBoxTypeProvider>()
```

## 9. Mutating Schema Objects

**Mistake:** TypeBox schemas are plain objects. Mutating them affects all references.

```typescript
const BaseSchema = Type.Object({ name: Type.String() })

// This mutates BaseSchema!
BaseSchema.properties.age = Type.Integer()
```

**Fix:**
```typescript
// Use composition instead of mutation
const ExtendedSchema = Type.Intersect([
  BaseSchema,
  Type.Object({ age: Type.Integer() }),
])

// Or spread properties into a new object
const ExtendedSchema = Type.Object({
  ...BaseSchema.properties,
  age: Type.Integer(),
})
```

## 10. Ignoring Response Schema Serialization

**Mistake:** Not defining response schemas, missing Fastify's security feature.

```typescript
// Without response schema, ALL object properties are sent to client
fastify.get('/users/:id', handler)
// If handler returns { id, name, email, passwordHash }
// Client receives the passwordHash!
```

**Fix:**
```typescript
fastify.get('/users/:id', {
  schema: {
    response: {
      200: Type.Object({
        id: Type.String(),
        name: Type.String(),
        email: Type.String(),
        // passwordHash is NOT listed → stripped from response
      }),
    },
  },
}, handler)
```

## Quick Checklist

- [ ] `ajv-formats` installed and registered
- [ ] Using `Static<typeof Schema>` instead of manual interfaces
- [ ] Using `TypeCompiler.Compile` for repeated validations
- [ ] Correct use of Optional vs Nullable
- [ ] `additionalProperties: false` where needed
- [ ] Transform schemas decoded manually (not by Fastify)
- [ ] Type provider registered with Fastify
- [ ] Response schemas defined for all routes
- [ ] Schema objects never mutated after creation
- [ ] Union of Literals preferred over Type.Enum
